import socket
import io
import threading
from pynput import mouse, keyboard
from threading import Thread
import json
import time
import win32api
import numpy
from mss import mss
from zlib import compress, decompress
from PIL import Image
# PyQt5
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QPushButton, QAction, QMessageBox, QSizePolicy, \
    QSpacerItem, QVBoxLayout, QHBoxLayout, QWidgetItem, QSpacerItem, QTabWidget, QGridLayout, QFrame, QFileDialog
from PyQt5.QtGui import QPixmap, QImage, QFont, QCursor, QColor
from PyQt5.QtCore import QRect, Qt, QSize, QObject, QThread, pyqtSignal, QDir
from client_ui import client_ui as UI
import os
import ast

WINDOWS = {}
connections = {}  # {'addr': {'conn': conn,'comp_num':Computer}]}
BUFSIZE = 16  # Buffer size

lock = threading.Lock()

all_codecs = ['ascii', 'big5', 'big5hkscs', 'cp037', 'cp273', 'cp424', 'cp437',
'cp500', 'cp720', 'cp737', 'cp775', 'cp850', 'cp852', 'cp855', 'cp856', 'cp857',
'cp858', 'cp860', 'cp861', 'cp862', 'cp863', 'cp864', 'cp865', 'cp866', 'cp869',
'cp874', 'cp875', 'cp932', 'cp949', 'cp950', 'cp1006', 'cp1026', 'cp1125',
'cp1140', 'cp1250', 'cp1251', 'cp1252', 'cp1253', 'cp1254', 'cp1255', 'cp1256',
'cp1257', 'cp1258', 'euc_jp', 'euc_jis_2004', 'euc_jisx0213', 'euc_kr',
'gb2312', 'gbk', 'gb18030', 'hz', 'iso2022_jp', 'iso2022_jp_1', 'iso2022_jp_2',
'iso2022_jp_2004', 'iso2022_jp_3', 'iso2022_jp_ext', 'iso2022_kr', 'latin_1',
'iso8859_2', 'iso8859_3', 'iso8859_4', 'iso8859_5', 'iso8859_6', 'iso8859_7',
'iso8859_8', 'iso8859_9', 'iso8859_10', 'iso8859_11', 'iso8859_13',
'iso8859_14', 'iso8859_15', 'iso8859_16', 'johab', 'koi8_r', 'koi8_t', 'koi8_u',
'kz1048', 'mac_cyrillic', 'mac_greek', 'mac_iceland', 'mac_latin2', 'mac_roman',
'mac_turkish', 'ptcp154', 'shift_jis', 'shift_jis_2004', 'shift_jisx0213',
'utf_32', 'utf_32_be', 'utf_32_le', 'utf_16', 'utf_16_be', 'utf_16_le', 'utf_7',
'utf_8', 'utf_8_sig']

def send_msg(conn, type="", **kwargs):
    """
    Send message to connection
    :param conn: socket (socket)
    :param type: message type (string)
    :return: sent the message (True/False)
    """
    global BUFSIZE, conn_list
    msg = {'type': type}
    msg.update(dict(**kwargs))
    msg = json.dumps(msg)
    # print(msg)
    msg_len = len(msg.encode())
    try:
        conn.send((str(msg_len) + ' ' * (BUFSIZE - len(str(msg_len)))).encode())
        conn.send(msg.encode())
    except ConnectionResetError:
        print(f"connection with {conn.getpeername()} lost")
        return False
    except ConnectionAbortedError:
        print(f"connection with {conn.getpeername()} lost")
        return False
    if msg.find('MOVE') == -1:
        print("admin sent", msg)
    return True


def get_msg(conn):
    """
    Get message from the connection
    :param conn: socket (socket)
    :return: message (string)/ False (bool)
    """
    global BUFSIZE
    try:
        msg_len = conn.recv(BUFSIZE)
        if not msg_len or not msg_len.decode():
            return False
        msg = conn.recv(int(msg_len.decode())).decode()
    except ConnectionResetError:
        print(f"connection with {conn.getpeername()} lost")
        return False
    except ConnectionAbortedError:
        print(f"connection with {conn.getpeername()} lost")
        return False
    print(f"got from {conn.getpeername()}:", msg)
    return json.loads(msg)


def get_open_port():
    """
    Use socket's built in ability to find an open port.
    """
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    print(port)
    return port


class Listener(QObject):
    finished = pyqtSignal()
    client_connected = pyqtSignal(tuple)
    client_disconnected = pyqtSignal(tuple)

    def __init__(self, sock):
        super().__init__()
        self.server = sock
        self.client_sock = socket.socket()
        self.client_sock.bind((self.server.getsockname()[0], 13131))
        self.client_sock.listen(1)
        print(self.client_sock)

    def run(self):
        """handle incoming messages from the server"""
        send_msg(self.server, 'message', msg='admin_connected', address=self.client_sock.getsockname())
        while True:
            msg = get_msg(self.server)  # get message
            if not msg:
                break
            if msg['type'] == 'message':
                if msg['msg'] == 'client_connected':
                    conn, addr = self.client_sock.accept()  # establish connection with client
                    connections[addr] = {'conn': conn, 'name':msg['name']}
                    try:
                        self.client_connected.emit(addr)
                    except TypeError:
                        self.client_connected.emit(tuple(addr))
                else:
                    try:
                        self.client_disconnected.emit(msg['address'])
                    except TypeError:
                        self.client_disconnected.emit(tuple(msg['address']))
            if msg['type'] == 'chat':
                for addr in connections:
                    if connections[addr]['name'] == msg['name']:
                        if connections[addr].get('chat'):
                            connections[addr]['chat'].listWidget.addItem(msg['msg'])
        self.finished.emit()


class ShowMessage(QObject):
    finished = pyqtSignal(QMessageBox)
    progress = pyqtSignal(tuple)

    def __init__(self, parent=None, addr=''):
        super().__init__()
        self.addr = addr
        self.parent = parent

    def run(self):
        """Long-running task."""
        button = QMessageBox.warning(
            self.parent,
            "ALERT!",
            f"{self.addr} is trying to take control over the keyboard",
        )
        self.finished.emit(button)


def Disconnect(addr):
    lock.acquire()
    global connections
    try:
        try:
            items = list(connections[addr].keys())
        except TypeError:
            lock.release()
            return
        for item in items:
            if item == "comp":
                connections[addr][item].setParent(None)
            elif item in ["conn", "screen_sharing_sock", "control_sock", 'sharing_sock']:
                connections[addr][item].close()
            elif item == 'control_thread':
                if connections[addr][item]:
                    connections[addr][item]['thread'].join()
                    connections[addr][item]['mouse_listener'].stop()
                    connections[addr][item]['mouse_listener'].join()
                    connections[addr][item]['kb_listener'].stop()
                    connections[addr][item]['kb_listener'].join()
                    connections[addr][item] = None
                connections[addr].pop(item)
        connections.pop(addr)
    except KeyError as e:
        print(f'Disconnect - {e}')
    lock.release()
    return


def block_input(comp, block):
    if comp == 'all':
        for addr in connections:
            send_msg(connections[addr]['control_conn'], 'block_input', block_input=block)
            connections[addr]['block_input'] = block
        return
    for addr in connections:
        if connections[addr]['comp'] == comp:
            send_msg(connections[addr]['control_conn'], 'block_input', block_input=block)
            connections[addr]['block_input'] = block


def imagesDifference(imageA, imageB ):
    # image_one = Image.open(imageA, 'r').convert('RGB')
    # image_two = Image.open(imageB, 'r').convert('RGB')

    diff1 = np.array(ImageChops.subtract(imageA, imageB, 1))
    vec1 = np.argwhere(diff1[:,:,0] >20)
    diff2 = np.array(ImageChops.subtract(imageA, imageB, -1))
    vec2 = np.argwhere(diff2[:,:,0] >20)
    return np.concatenate((-diff1[vec1[:,0],vec1[:,1], :], diff2[vec2[:,0],vec2[:,1], :])), np.concatenate((vec1,vec2))


def screen_sharing(addr, conn, num):
    # connections[addr]['comp'] = connections[addr]['comp']
    pixmap = QPixmap()
    while connections[addr]['screen_sharing']:
        try:
            img_len = conn.recv(16)
            img = conn.recv(eval(img_len.decode()))
            if len(img) != eval(img_len.decode()):
                continue
            pixmap.loadFromData(decompress(img))
            # pixmap.scaled(connections[addr]['comp'].width(), connections[addr]['comp'].height(), Qt.KeepAspectRatio,
            #               Qt.SmoothTransformation)
            # label = connections[addr]['comp'].findChild(QLabel, num)
            for label in [connections[addr]['comp'].top_left, connections[addr]['comp'].top_right, connections[addr]['comp'].bottom_left, connections[addr]['comp'].bottom_right]:
                if label.objectName() == num:
                    label.setScaledContents(True)
                    label.setPixmap(QPixmap(pixmap))
                    label.setAlignment(Qt.AlignCenter)
                    break

        except (ConnectionResetError,WindowsError) as e:
            print(f"screen_sharing: {addr} disconnected, {e}")
            if e.winerror == 10040:
                continue
            Thread(target=Disconnect, args=(addr,), daemon=True).start()
            break
        except Exception as e:
            print(f'screen_sharing: {e}')
    print('screen_sharing done')


def StartShareScreen(addr):
    for i in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
        connections[addr][f'{i}'] = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        connections[addr][f'{i}'].bind((connections[addr]['conn'].getsockname()[0], get_open_port()))
        send_msg(connections[addr]['screen_sharing_conn'], 'bind', address=connections[addr][f'{i}'].getsockname())
        connections[addr][f'thread{i}'] = Thread(target=screen_sharing, args=(addr, connections[addr][f'{i}'], i), daemon=True)
        connections[addr][f'thread{i}'].start()


def send_screenshots(rect, addr, address, sock):

    with mss() as sct:
        # prev = time.time()
        sct_img = sct.grab(rect)
        # Tweak the compression level here (0-9)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        new_scale = (int(img.size[0] * 0.5), int(img.size[1] * 0.5))  # compress the image with scale 0.5
        img = img.resize(new_scale, Image.ANTIALIAS)
        prev_img = img
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', optimize=True,
                 quality=80)  # optimize the image and convert it to bytes
        # send image
        msg = compress(img_bytes.getvalue(), 9)
        msg_len = len(msg)
        header = str(msg_len) + ' ' * (16 - len(str(msg_len)))
        sock.sendto(header.encode(), address)
        sock.sendto(msg, address)

        try:
            while connections[addr]['sharing_screen']:
                try:
                    # prev = time.time()
                    sct_img = sct.grab(rect)
                    # Tweak the compression level here (0-9)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    new_scale = (int(img.size[0] * 0.5), int(img.size[1] * 0.5))  # compress the image with scale 0.5
                    img = img.resize(new_scale, Image.ANTIALIAS)
                    img_bytes = io.BytesIO()
                    # optimize the image and convert it to bytes
                    img.save(img_bytes, format='JPEG', optimize=True, quality=80)

                    msg = compress(img_bytes.getvalue(), 9)
                    # send image
                    msg_len = len(msg)
                    header = str(msg_len) + ' ' * (16 - len(str(msg_len)))
                    sock.sendto(header.encode(), address)
                    sock.sendto(msg, address)

                # except (ConnectionResetError, WindowsError) as e:
                #     print("screen-sharing stopped: admin disconnected", e)
                #     if e.winerror == 10040:
                #         print(e)
                #         sock.send(header.encode())
                #     else:
                #         break
                except Exception as e:
                    print(f'screen-sharing stopped: {e}')
        except KeyError as e:
            print("screen-sharing stopped: admin disconnected", e)
    return


def StartScreenSharing(comp):
    for addr in connections:
        if connections[addr]['comp'] == comp:
            if connections[addr]['sharing_screen']:
                send_msg(connections[addr]['handle_msg_conn'], 'share', share=False)
                connections[addr]['sharing_screen'] = False
                for rect in ['rect', 'rect2', 'rect3', 'rect4']:
                    connections[addr][f'{rect}_sock'].close()
                    connections[addr].pop(f'{rect}_sock')
                    connections[addr][f'{rect}_thread'].join()
                    connections[addr].pop(f'{rect}_thread')
                connections[addr]['screen_sharing'] = True
                send_msg(connections[addr]['handle_msg_conn'], 'screen_share', share=True)
                connections[addr].update(
                    {'screen_sharing_thread': Thread(target=StartShareScreen, args=(addr,), daemon=True)})
                connections[addr]['screen_sharing_thread'].start()
                return

            send_msg(connections[addr]['handle_msg_conn'], 'share', share=True)
            connections[addr]['sharing_screen'] = True
            if connections[addr]['block_screen']:
                send_msg(connections[addr]['handle_msg_conn'], 'block_screen', block=False, img=None)
                connections[addr]['block_screen'] = False
            if connections[addr]['screen_sharing']:
                send_msg(connections[addr]['handle_msg_conn'], 'screen_share', share=False)
                connections[addr]['screen_sharing'] = False
                connections[addr]['screen_sharing_thread'].join()
                connections[addr].pop('screen_sharing_thread')

            rects = {'rect' : {'top': 0, 'left': 0, 'width': win32api.GetSystemMetrics(0)//2, 'height': win32api.GetSystemMetrics(1)//2},
            'rect2' : {'top': 0, 'left': win32api.GetSystemMetrics(0) // 2, 'width': win32api.GetSystemMetrics(0) // 2,
                    'height': win32api.GetSystemMetrics(1) // 2},
            'rect3' : {'top': win32api.GetSystemMetrics(1) // 2, 'left': 0, 'width': win32api.GetSystemMetrics(0) // 2,
                    'height': win32api.GetSystemMetrics(1) // 2},
            'rect4' : {'top': win32api.GetSystemMetrics(1) // 2, 'left': win32api.GetSystemMetrics(0) // 2, 'width': win32api.GetSystemMetrics(0) // 2,
                    'height': win32api.GetSystemMetrics(1) // 2}}

            for rect in rects:
                msg = get_msg(connections[addr]['conn'])
                if not msg or msg['type']!='bind':
                    connections[addr]['sharing_screen'] = False
                    return
                connections[addr].update({f'{rect}_sock': socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)})
                connections[addr][f'{rect}_sock'].connect(tuple(msg['address']))
                connections[addr].update({f'{rect}_thread': Thread(target=send_screenshots, args=(rects[rect], addr, tuple(msg['address']), connections[addr][f'{rect}_sock']), daemon=True)})
                connections[addr][f'{rect}_thread'].start()
            return


def StartScreenSharingAll():
    for addr in connections:
        if connections[addr]['sharing_screen']:
            continue
        send_msg(connections[addr]['handle_msg_conn'], 'share', share=True)
        connections[addr]['sharing_screen'] = True
        if connections[addr]['block_screen']:
            send_msg(connections[addr]['handle_msg_conn'], 'block_screen', block=False, img=None)
            connections[addr]['block_screen'] = False
        if connections[addr]['screen_sharing']:
            send_msg(connections[addr]['handle_msg_conn'], 'screen_share', share=False)
            connections[addr]['screen_sharing'] = False
            connections[addr]['screen_sharing_thread'].join()
            connections[addr].pop('screen_sharing_thread')

        rects = {'rect' : {'top': 0, 'left': 0, 'width': win32api.GetSystemMetrics(0)//2, 'height': win32api.GetSystemMetrics(1)//2},
        'rect2' : {'top': 0, 'left': win32api.GetSystemMetrics(0) // 2, 'width': win32api.GetSystemMetrics(0) // 2,
                'height': win32api.GetSystemMetrics(1) // 2},
        'rect3' : {'top': win32api.GetSystemMetrics(1) // 2, 'left': 0, 'width': win32api.GetSystemMetrics(0) // 2,
                'height': win32api.GetSystemMetrics(1) // 2},
        'rect4' : {'top': win32api.GetSystemMetrics(1) // 2, 'left': win32api.GetSystemMetrics(0) // 2, 'width': win32api.GetSystemMetrics(0) // 2,
                'height': win32api.GetSystemMetrics(1) // 2}}

        for rect in rects:
            msg = get_msg(connections[addr]['conn'])
            if not msg or msg['type']!='bind':
                send_msg(connections[addr]['handle_msg_conn'], 'share', share=False)
                connections[addr]['sharing_screen'] = False
                for rect in ['rect', 'rect2', 'rect3', 'rect4']:
                    if connections[addr].get(f'{rect}_sock'):
                        connections[addr][f'{rect}_sock'].close()
                        connections[addr].pop(f'{rect}_sock')
                    if connections[addr].get(f'{rect}_thread'):
                        connections[addr][f'{rect}_thread'].join()
                        connections[addr].pop(f'{rect}_thread')
                connections[addr]['screen_sharing'] = True
                send_msg(connections[addr]['handle_msg_conn'], 'screen_share', share=True)
                connections[addr].update(
                    {'screen_sharing_thread': Thread(target=StartShareScreen, args=(addr,), daemon=True)})
                connections[addr]['screen_sharing_thread'].start()
                break
            connections[addr].update({f'{rect}_sock': socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)})
            connections[addr][f'{rect}_sock'].connect(tuple(msg['address']))
            connections[addr].update({f'{rect}_thread': Thread(target=send_screenshots, args=(rects[rect], addr, tuple(msg['address']), connections[addr][f'{rect}_sock']), daemon=True)})
            connections[addr][f'{rect}_thread'].start()


def StopScreenSharingAll():
    for addr in connections:
        if connections[addr]['sharing_screen']:
            send_msg(connections[addr]['handle_msg_conn'], 'share', share=False)
            connections[addr]['sharing_screen'] = False
            for rect in ['rect', 'rect2', 'rect3', 'rect4']:
                connections[addr][f'{rect}_sock'].close()
                connections[addr].pop(f'{rect}_sock')
                connections[addr][f'{rect}_thread'].join()
                connections[addr].pop(f'{rect}_thread')
            connections[addr]['screen_sharing'] = True
            send_msg(connections[addr]['handle_msg_conn'], 'screen_share', share=True)
            connections[addr].update(
                {'screen_sharing_thread': Thread(target=StartShareScreen, args=(addr,), daemon=True)})
            connections[addr]['screen_sharing_thread'].start()


class ClassWindow(UI.ClassWindow_UI):
    def __init__(self, socket):
        super(ClassWindow, self).__init__()
        self.server = socket
        self.lock = threading.Lock()
        self.column_limit = 2
        self.row_limit = 2
        self.show()
        self.listener_thread = QThread()
        self.listener = Listener(self.server)
        self.listener.moveToThread(self.listener_thread)
        self.listener_thread.started.connect(self.listener.run)
        self.listener.finished.connect(self.listener_thread.quit)
        self.listener.finished.connect(self.listener.deleteLater)
        self.listener_thread.finished.connect(self.listener_thread.deleteLater)
        self.listener.client_connected.connect(self.new_connection)
        self.listener.client_disconnected.connect(Disconnect)
        self.listener_thread.start()

    def new_connection(self, addr):
        global connections

        print(f'{addr} connected to the server')
        num = len(connections) - 1
        connections[addr].update({'comp': UI.ComputerScreen(self.widget)})
        connections[addr]['comp'].setObjectName(f"comp{num}")

        msg = get_msg(connections[addr]['conn'])
        if not msg:
            return
        connections[addr].update({"size": msg['size']})

        connections[addr]['screen_sharing'] = True

        connections[addr].update({'screen_sharing_sock': socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)})
        port = get_open_port()
        connections[addr]['screen_sharing_sock'].bind((connections[addr]['conn'].getsockname()[0], port))
        connections[addr]['screen_sharing_sock'].listen(1)
        send_msg(connections[addr]['conn'], 'message', address=(connections[addr]['conn'].getsockname()[0], port))
        connections[addr]['screen_sharing_conn'] = connections[addr]['screen_sharing_sock'].accept()[0]
        connections[addr].update({'screen_sharing_thread': Thread(target=StartShareScreen, args=(addr, ), daemon=True)})
        connections[addr]['screen_sharing_thread'].start()

        connections[addr].update({'control_sock': socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)})
        port = get_open_port()
        connections[addr]['control_sock'].bind((connections[addr]['conn'].getsockname()[0], port))
        connections[addr]['control_sock'].listen(1)
        send_msg(connections[addr]['conn'], 'message', port=port)
        connections[addr].update({'control_conn': connections[addr]['control_sock'].accept()[0]})
        connections[addr].update({'control_thread': None})

        connections[addr].update({'handle_msg_sock': socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)})
        port = get_open_port()
        connections[addr]['handle_msg_sock'].bind((connections[addr]['conn'].getsockname()[0], port))
        connections[addr]['handle_msg_sock'].listen(1)
        send_msg(connections[addr]['conn'], 'message', port=port)
        connections[addr].update({'handle_msg_conn': connections[addr]['handle_msg_sock'].accept()[0]})
        connections[addr].update({'handle_msg_thread': Thread(target=self.handle_client_msg, args=(addr,), daemon=True)})
        connections[addr]['handle_msg_thread'].start()

        connections[addr].update({'block_input': False})
        connections[addr].update({'sharing_screen': False})
        connections[addr].update({'block_screen': False})

        self.group_view()

    def group_view(self):
        self.waitingLabal.setParent(None)
        self.blockInputButton.clicked.connect(
            lambda: block_input('all', True))
        self.unblockInputButton.clicked.connect(
            lambda: block_input('all', False))
        self.blockScreenButton.clicked.connect(self.BlockAllScreens)
        self.unblockScreenButton.clicked.connect(self.UnblockAllScreens)
        self.shareScreenButton.clicked.connect(StartScreenSharingAll)
        self.stopShareScreenButton.clicked.connect(StopScreenSharingAll)
        # self.chatButton.clicked.connect(lambda: self.Chat(self.tab_view.tabWidget.currentWidget()))
        self.shareFileButton.clicked.connect(lambda: self.ShareFile('all'))
        for addr in connections:
            num = eval(connections[addr]['comp'].objectName().strip('comp'))
            for row in range(self.row_limit):
                for column in range(self.column_limit):
                    if row * self.column_limit + column == num:
                        connections[addr]['comp'] = UI.ComputerScreen(self.widget)
                        connections[addr]['comp'].setObjectName(f"comp{num}")
                        connections[addr]['comp'].setToolTip(f"{addr}\'s computer")
                        connections[addr]['comp'].setStyleSheet(f"QFrame#comp{num}"
                                                                u"{background-color: rgb(150, 150, 150);\n"
                                                                u"border-radius: 5px;}\n"
                                                                f"QFrame#comp{num}:hover"
                                                                u"{border: 5px solid rgb(80, 180, 80);\n"
                                                                u"border-radius: 5px;\n"
                                                                u"}")
                        connections[addr]['comp'].setMinimumSize(QSize(240, 135))
                        connections[addr]['comp'].setMaximumSize(QSize(480, 270))
                        self.gridLayout_2.addWidget(connections[addr]['comp'], row, column, 1, 1)
                        connections[addr]['comp'].clicked.connect(self.tab_control)
        if 'tab_view' in WINDOWS:
            WINDOWS['class_window'].show()
            WINDOWS['tab_view'].close()
        print(connections)
        return

    def tab_control(self, event):
        """
        checks the action. if double-clicked on a screen: start to control it
        """
        # print(event)
        if event['action'] == "Double Click":
            for addr in connections:
                if connections[addr]['comp'].objectName() == event['name']:
                    if connections[addr]['comp'].top_left.pixmap():
                        self.tab_view = UI.TabView_UI()
                        # tab = UI.ComputerScreenWidget(self.tab_view)
                        # connections[addr]['comp'].setParent(self.tab_view.tabWidget)
                        # tab.label = connections[addr]['comp']
                        # # tab.label.setStyleSheet(u"QLabel{background-color: rgb(150, 150, 150);\n"
                        # #               u"border-radius: 5px;}\n"
                        # #               u"QLabel:hover{\n"
                        # #               u"border: 5px solid rgb(80, 180, 80);\n"
                        # #               u"border-radius: 5px;\n"
                        # #               u"}")
                        # tab.label.setMinimumSize(QSize(240, 135))
                        # tab.listWidget.addItem('abcd')
                        # Actions
                        self.tab_view.tabWidget.addTab(connections[addr]['comp'], connections[addr]['name'])
                        self.tab_view.blockInputAction.triggered.connect(lambda: block_input(self.tab_view.tabWidget.currentWidget(), True))
                        self.tab_view.unblockInputAction.triggered.connect(lambda: block_input(self.tab_view.tabWidget.currentWidget(), False))
                        self.tab_view.shareScreenAction.triggered.connect(lambda: StartScreenSharing(self.tab_view.tabWidget.currentWidget()))
                        # Buttons
                        self.tab_view.blockInputButton.clicked.connect(lambda: block_input(self.tab_view.tabWidget.currentWidget(), True))
                        self.tab_view.unblockInputButton.clicked.connect(lambda: block_input(self.tab_view.tabWidget.currentWidget(), False))
                        self.tab_view.shareScreenButton.clicked.connect(
                            lambda: StartScreenSharing(self.tab_view.tabWidget.currentWidget()))
                        self.tab_view.blockScreenButton.clicked.connect(lambda: self.BlockScreen(self.tab_view.tabWidget.currentWidget()))
                        self.tab_view.chatButton.clicked.connect(lambda: self.Chat(self.tab_view.tabWidget.currentWidget()))
                        self.tab_view.shareFileButton.clicked.connect(lambda: self.ShareFile(self.tab_view.tabWidget.currentWidget()))
                        for address in connections:
                            connections[address]['comp'].disconnect()
                            connections[address]['comp'].setMaximumSize(QSize(10000, 10000))
                            connections[address]['comp'].clicked.connect(self.start_controlling)
                            if address != addr:
                                self.tab_view.tabWidget.addTab(connections[address]['comp'], connections[address]['name'])

                        WINDOWS['tab_view'] = self.tab_view
                        WINDOWS['tab_view'].show()
                        WINDOWS['class_window'].close()
                    else:
                        print("you cant connect to this computer")

    def start_controlling(self, event):
        print(f"start_controlling - {event}")
        # print(f"threads running - {threading.active_count()}")
        # print(f"connections - {connections}")
        try:
            if event['action'] == "Enter":
                lock.acquire()
                try:
                    for addr in connections:
                        if connections[addr]['comp'].objectName() == event["name"]:
                            if connections[addr]['control_thread']:
                                lock.release()
                                return
                            self.tab_view.back_to_main_btn.disconnect()
                            Controlling = Thread(target=self.controlling, args=(addr,), daemon=True)
                            Controlling.start()
                            connections[addr]['control_thread'] = {'thread': Controlling}
                            lock.release()
                            return
                except KeyError as e:
                    print('control error keyError:', e)
                lock.release()
            if event['action'] == "Leave":
                lock.acquire()
                self.tab_view.back_to_main_btn.clicked.connect(self.group_view)
                try:
                    for addr in connections:
                        if connections[addr]['comp'].objectName() == event["name"]:
                            if connections[addr]['control_thread']:
                                connections[addr]['control_thread']['thread'].join()
                                connections[addr]['control_thread']['mouse_listener'].stop()
                                connections[addr]['control_thread']['mouse_listener'].join()
                                connections[addr]['control_thread']['kb_listener'].stop()
                                connections[addr]['control_thread']['kb_listener'].join()
                                connections[addr]['control_thread'] = None
                                lock.release()
                                return
                except KeyError:
                    pass
                lock.release()
        except TypeError as e:
            print(f'controlling error - {e}')
            pass

    def controlling(self, addr):
        conn = connections[addr]['control_conn']
        # address = (addr[0], connections[addr]['control_sock'].getsockname()[1])
        size = connections[addr]['size']
        def get_vk(key):
            return key.vk if hasattr(key, 'vk') else key.value.vk

        def on_move(x, y):
            screen_x = self.tab_view.pos().x() + self.tab_view.tabWidget.pos().x() + 2
            screen_y = self.tab_view.pos().y() + self.tab_view.tabWidget.pos().y() + 60
            screen_width, screen_height = connections[addr]['comp'].width(), connections[addr]['comp'].height()
            width, height = size[0], size[1]
            x_ratio, y_ration = round(screen_width / width, 2), round(screen_height / height, 2)
            x = round((x - screen_x) / x_ratio)
            if x < 0 or width < x:
                x = 0 if x < 0 else width
            y = round((y - screen_y) / y_ration)
            if y < 0 or height < y:
                y = 0 if y < 0 else height
            command = ['MOVE', x, y]
            send_msg(conn, 'command', command=command)

        def on_click(x, y, button, pressed):
            command = ['CLICK' if pressed else 'RELEASE', str(button)]
            send_msg(conn, 'command', command=command)

        def on_scroll(x, y, dx, dy):
            command = ['SCROLL', dy]
            send_msg(conn, 'command', command=command)

        mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        mouse_listener.start()

        def on_press(key):
            hotkey.add(get_vk(key))
            for combo in hotkeys:
                if all([get_vk(k) in hotkey for k in combo]):
                    if connections[addr]['block_input']:
                        print('block off')
                        send_msg(conn, 'block_input', block_input=False)
                        connections[addr]['block_input'] = False
                    else:
                        print('block on')
                        send_msg(conn, 'block_input', block_input=True)
                        connections[addr]['block_input'] = True
                else:
                    command = ['KEY', str(key)]
                    send_msg(conn, 'command', command=command)

        def on_release(key):
            hotkey.remove(get_vk(key))
        # print(keyboard.KeyCode(vk=66))
        # print(get_vk(keyboard.KeyCode(vk=66)))

        hotkeys = [{keyboard.Key.ctrl_l, keyboard.Key.alt_l,  keyboard.KeyCode(vk=66)}]#,
                   #{keyboard.Key.ctrl, keyboard.Key.alt,  keyboard.KeyCode(vk=66)}]
        hotkey = set()

        kb_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        kb_listener.start()

        connections[addr]['control_thread'].update({'mouse_listener': mouse_listener, 'kb_listener': kb_listener})


    def handle_client_msg(self, addr):
        conn = connections[addr]['handle_msg_conn']
        while True:
            try:
                msg = get_msg(conn)
                print(msg)
                if not msg:
                    print(f"handle_client_msg1: {addr} disconnected")
                    Thread(target=Disconnect, args=(addr,), daemon=True).start()
                    break
                if msg['type'] == "alert":
                    if WINDOWS.get('tab_view'):
                        # print(f"ALERT! ALERT! {addr} is trying to take control over the keyboard")
                        self.tab_view.alerts.addItem(f"{connections[addr]['name']} is {msg['alert']}")
            except ConnectionResetError or OSError:
                print(f"handle_client_msg2: {addr} disconnected")
                Thread(target=Disconnect, args=(addr,), daemon=True).start()
                break


    def Chat(self, comp):
        def on_close(event):
            for addr in connections:
                if connections[addr]['chat'].objectName() == event['name']:
                    connections[addr]['chat'].setParent(None)
                    connections[addr].pop('chat')

        for addr in connections:
            if connections[addr]['comp'] == comp:
                if not connections[addr].get('chat'):
                    self.chat_ui = UI.ChatBox_UI()
                    connections[addr]['chat'] = self.chat_ui
                    connections[addr]['chat'].setObjectName(connections[addr]['name'])
                    connections[addr]['chat'].show()
                    connections[addr]['chat'].lineEdit.returnPressed.connect(lambda: on_press(comp))
                    connections[addr]['chat'].close_event.connect(on_close)
                break

        def on_press(comp):
            for addr in connections:
                if connections[addr]['comp'] == comp:
                    send_msg(self.server, 'chat', msg=connections[addr]['chat'].lineEdit.text(),
                             name=connections[addr]['name'])
                    break


    def BlockScreen(self, comp):
        for addr in connections:
            if connections[addr]['comp'] == comp:
                if connections[addr]['block_screen']:
                    block_input(comp, False)
                    send_msg(connections[addr]['handle_msg_conn'], 'block_screen', block=False, img=None)
                    connections[addr]['block_screen'] = False
                    connections[addr]['screen_sharing'] = True
                    send_msg(connections[addr]['handle_msg_conn'], 'screen_share', share=True)
                    connections[addr].update(
                        {'screen_sharing_thread': Thread(target=StartShareScreen, args=(addr,), daemon=True)})
                    connections[addr]['screen_sharing_thread'].start()
                    return
                file_name, _ = QFileDialog.getOpenFileName(self, 'Open Image File', r"<Default dir>", "Image files (*.jpg *.jpeg *.gif *png)")
                if not file_name or not _:
                    return
                connections[addr]['block_screen'] = True
                # block_input(comp, True)
                send_msg(connections[addr]['handle_msg_conn'], 'block_screen', block=True)
                msg = get_msg(connections[addr]['conn'])
                if not msg:
                    return
                if msg['type'] == 'bind':
                    if connections[addr]['sharing_screen']:
                        send_msg(connections[addr]['handle_msg_conn'], 'share', share=False)
                        connections[addr]['sharing_screen'] = False
                        connections[addr]['sharing_sock'].close()
                        connections[addr].pop('sharing_sock')
                        connections[addr]['sharing_thread'].join()
                    if connections[addr]['screen_sharing']:
                        send_msg(connections[addr]['handle_msg_conn'], 'screen_share', share=False)
                        connections[addr]['screen_sharing'] = False
                        connections[addr]['screen_sharing_thread'].join()
                        connections[addr].pop('screen_sharing_thread')
                    block_screen_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
                    block_screen_sock.connect(tuple(msg['address']))
                    with open(file_name, 'rb') as f:
                        data = f.read()
                        msg = compress(data, 9)
                        f.close()
                    msg_len = len(msg)
                    print(msg_len)
                    while msg_len > 50000:
                        header = str(50000) + ' ' * (16 - len(str(50000)))
                        block_screen_sock.send(header.encode('utf-8'))
                        block_screen_sock.send(msg[:50000])
                        msg_len = msg_len - 50000
                        msg = msg[50000:]
                    header = str(msg_len) + ' ' * (16 - len(str(msg_len)))
                    print(header)
                    block_screen_sock.send(header.encode('utf-8'))
                    block_screen_sock.send(msg[:msg_len])
                    block_screen_sock.close()
                else:
                    connections[addr]['block_screen'] = False
                return


    def BlockAllScreens(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open Image File', r"<Default dir>",
                                                   "Image files (*.jpg *.jpeg *.gif *png)")
        if not file_name or not _:
            return
        for addr in connections:
            connections[addr]['block_screen'] = True
            # block_input(comp, True)
            send_msg(connections[addr]['handle_msg_conn'], 'block_screen', block=True)
            msg = get_msg(connections[addr]['conn'])
            if not msg:
                continue
            if msg['type'] == 'bind':
                if connections[addr]['sharing_screen']:
                    send_msg(connections[addr]['handle_msg_conn'], 'share', share=False)
                    connections[addr]['sharing_screen'] = False
                    connections[addr]['sharing_sock'].close()
                    connections[addr].pop('sharing_sock')
                    connections[addr]['sharing_thread'].join()
                if connections[addr]['screen_sharing']:
                    send_msg(connections[addr]['handle_msg_conn'], 'screen_share', share=False)
                    connections[addr]['screen_sharing'] = False
                    connections[addr]['screen_sharing_thread'].join()
                    connections[addr].pop('screen_sharing_thread')
                block_screen_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
                block_screen_sock.connect(tuple(msg['address']))
                with open(file_name, 'rb') as f:
                    data = f.read()
                    msg = compress(data, 9)
                    f.close()
                msg_len = len(msg)
                while msg_len > 50000:
                    header = str(50000) + ' ' * (16 - len(str(50000)))
                    block_screen_sock.send(header.encode('utf-8'))
                    block_screen_sock.send(msg[:50000])
                    msg_len = msg_len - 50000
                    msg = msg[50000:]
                header = str(msg_len) + ' ' * (16 - len(str(msg_len)))
                block_screen_sock.send(header.encode('utf-8'))
                block_screen_sock.send(msg[:msg_len])
                block_screen_sock.close()
            else:
                connections[addr]['block_screen'] = False


    def UnblockAllScreens(self):
        for addr in connections:
            if connections[addr]['block_screen']:
                block_input(connections[addr]['comp'], False)
                send_msg(connections[addr]['handle_msg_conn'], 'block_screen', block=False, img=None)
                connections[addr]['block_screen'] = False
                connections[addr]['screen_sharing'] = True
                send_msg(connections[addr]['handle_msg_conn'], 'screen_share', share=True)
                connections[addr].update(
                    {'screen_sharing_thread': Thread(target=StartShareScreen, args=(addr,), daemon=True)})
                connections[addr]['screen_sharing_thread'].start()


    def ShareFile(self, comp):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setFilter(QDir.Files)
        file_name = []
        if dialog.exec_():
            file_name = dialog.selectedFiles()

        for file in file_name:
            for addr in connections:
                if connections[addr]['comp'] == comp or comp == 'all':
                    send_msg(connections[addr]['handle_msg_conn'], 'share_file')
                    msg = get_msg(connections[addr]['conn'])
                    if not msg:
                        return
                    if msg['type'] == 'bind':
                        share_file_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
                        share_file_sock.connect(tuple(msg['address']))
                        head, name = os.path.split(file)
                        print(name, head)
                        for e in all_codecs:
                            try:
                                name = name.encode(e)
                            except UnicodeEncodeError:
                                pass
                            else:
                                print(name, e)
                                send_msg(share_file_sock, 'file_name', name=str(name), encoder=e)
                                break
                        else:
                            print('Cant find encoder for the name')

                        for e in all_codecs:
                            try:
                                f=open(file, 'r', encoding=e)
                                data = f.read()
                                msg = data.encode()
                                # msg = compress(data.encode(), 9)
                                f.close()
                            except UnicodeDecodeError:
                                pass
                            else:
                                print(e)
                                send_msg(share_file_sock, 'encoder', encoder=e)
                                break
                        else:
                            print('Cant find encoder for the name')

                        msg_len = len(msg)
                        print(msg_len)
                        while msg_len > 50000:
                            header = str(50000) + ' ' * (16 - len(str(50000)))
                            share_file_sock.send(header.encode())
                            share_file_sock.send(msg[:50000])
                            msg_len = msg_len - 50000
                            msg = msg[50000:]
                        header = str(msg_len) + ' ' * (16 - len(str(msg_len)))
                        print(header)
                        share_file_sock.send(header.encode())
                        share_file_sock.send(msg)
                        share_file_sock.close()
                    if comp != 'all':
                        break
        return

def main(server_sock):
    global WINDOWS
    class_window = ClassWindow(server_sock)
    WINDOWS['class_window'] = class_window
    print(WINDOWS)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    ADDR = '192.168.31.131'
    # ADDR = '192.168.31.101'
    # ADDR = '172.16.1.23'
    server_sock = socket.socket()
    server_sock.connect((ADDR, 12121))
    main(server_sock)
    sys.exit(app.exec_())