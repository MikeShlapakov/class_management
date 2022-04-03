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
from zlib import compress
from PIL import Image
# PyQt5
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QPushButton, QAction, QMessageBox, QSizePolicy, \
    QSpacerItem, QVBoxLayout, QHBoxLayout, QWidgetItem, QSpacerItem, QTabWidget, QGridLayout, QFrame
from PyQt5.QtGui import QPixmap, QImage, QFont, QCursor
from PyQt5.QtCore import QRect, Qt, QSize, QObject, QThread, pyqtSignal
from client_ui import client_ui as UI

WINDOWS = {}
connections = {}  # {'addr': {'conn': conn,'comp_num':Computer}]}
BUFSIZE = 16  # Buffer size

lock = threading.Lock()

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
        self.sock = sock
        self.client_sock = socket.socket()
        self.client_sock.bind((self.sock.getsockname()[0], 13131))
        self.client_sock.listen(1)
        print(self.client_sock)

    def run(self):
        """handle incoming messages from the server"""
        send_msg(self.sock, 'message', msg='admin_connected', address=self.client_sock.getsockname())
        while True:
            msg = get_msg(self.sock)  # get message
            if not msg:
                break
            if msg['type'] == 'message':
                if msg['msg'] == 'client_connected':
                    conn, addr = self.client_sock.accept()  # establish connection with client
                    connections[addr] = {'conn': conn}
                    try:
                        self.client_connected.emit(addr)
                    except TypeError:
                        self.client_connected.emit(tuple(addr))
                else:
                    try:
                        self.client_disconnected.emit(msg['address'])
                    except TypeError:
                        self.client_disconnected.emit(tuple(msg['address']))
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
    for addr in connections:
        if connections[addr]['comp'] == comp:
            send_msg(connections[addr]['control_conn'], 'block_input', block_input=block)
            connections[addr]['block_input'] = block


def screen_sharing(addr):
    conn = connections[addr]['screen_sharing_sock']
    # connections[addr]['comp'] = connections[addr]['comp']
    pixmap = QPixmap()
    while connections[addr]['screen_sharing']:
        try:
            img_len = conn.recv(16)
            # print(img_len)
            img = b''
            # while eval(img_len.decode()) == 50000:
            #     conn.sendto(b'1', address)
            #     img += conn.recv(eval(img_len.decode()))
            #     print(f'1 {len(img)}')
            #     if len(img) == 16:
            #         print('break')
            #         break
            #     img_len = conn.recv(16)
            # else:
            img += conn.recv(eval(img_len.decode()))
            if len(img) != eval(img_len.decode()):
                continue
            pixmap.loadFromData(img)
            # pixmap.scaled(connections[addr]['comp'].width(), connections[addr]['comp'].height(), Qt.KeepAspectRatio,
            #               Qt.SmoothTransformation)
            connections[addr]['comp'].setScaledContents(True)
            connections[addr]['comp'].setPixmap(QPixmap(pixmap))
            connections[addr]['comp'].setAlignment(Qt.AlignCenter)

        except (ConnectionResetError,WindowsError) as e:
            print(f"screen_sharing: {addr} disconnected, {e}")
            if e.winerror == 10040:
                continue
            Thread(target=Disconnect, args=(addr,), daemon=True).start()
            break
        except Exception as e:
            print(f'screen_sharing: {e}')
    print('screen_sharing done')


def send_screenshots(addr, address, sock):
    rect = {'top': 0, 'left': 0, 'width': win32api.GetSystemMetrics(0), 'height': win32api.GetSystemMetrics(1)}

    with mss() as sct:
        try:
            while True:
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
                # print(len(img_bytes.getvalue()))
                # send image
                msg_len = len(msg)

                header = str(msg_len) + ' ' * (16 - len(str(msg_len)))
                sock.sendto(header.encode(), address)
                sock.sendto(msg, address)
                # print(f'FPS: {1 / (time.time() - prev)}')
        except (ConnectionResetError, WindowsError) as e:
            print("screen-sharing stopped: admin disconnected", e)
            if e.winerror == 10040:
                pass
            return
        except Exception as e:
            print(f'screen-sharing stopped: {e}')
        return


def StartScreenSharing(comp):
    print(1)
    for addr in connections:
        if connections[addr]['comp'] == comp:
            print(2)
            if connections[addr].get('sharing_sock'):
                send_msg(connections[addr]['handle_msg_conn'], 'share', share=False)
                connections[addr]['sharing_sock'].close()
                connections[addr].pop('sharing_sock')
                connections[addr]['sharing_thread'].join()
                connections[addr].pop('sharing_thread')
                connections[addr]['screen_sharing'] = True
                connections[addr].update(
                    {'screen_sharing_thread': Thread(target=screen_sharing, args=(addr,), daemon=True)})
                connections[addr]['screen_sharing_thread'].start()
                return
            send_msg(connections[addr]['handle_msg_conn'], 'share', share=True)
            msg = get_msg(connections[addr]['conn'])
            if not msg:
                return
            if msg['type'] == 'bind':
                connections[addr]['screen_sharing'] = False
                connections[addr]['screen_sharing_thread'].join()
                connections[addr].pop('screen_sharing_thread')
                # if WINDOWS['main_window'].isVisible():
                #     WINDOWS['main_window'].showMinimized()
                # elif WINDOWS['tab_view'].isVisible():
                #     WINDOWS['tab_view'].showMinimized()
                connections[addr].update({'sharing_sock': socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)})
                connections[addr]['sharing_sock'].connect(tuple(msg['address']))
                connections[addr].update({'sharing_thread': Thread(target=send_screenshots, args=(addr, tuple(msg['address']), connections[addr]['sharing_sock']), daemon=True)})
                connections[addr]['sharing_thread'].start()
                return


def handle_client_msg(addr):
    conn = connections[addr]['handle_msg_conn']
    while True:
        try:
            msg = get_msg(conn)
            if not msg:
                print(f"handle_client_msg1: {addr} disconnected")
                Thread(target=Disconnect, args=(addr,), daemon=True).start()
                break
            if msg['type'] == "alert":
                connections[addr]['comp'].listWidget2.addItem(f"ALERT! ALERT! {addr} is trying to take control over the keyboard")
                print(f"ALERT! ALERT! {addr} is trying to take control over the keyboard")
        except ConnectionResetError or OSError:
            print(f"handle_client_msg2: {addr} disconnected")
            Thread(target=Disconnect, args=(addr,), daemon=True).start()
            break


def chat_massages(addr):
    conn = connections[addr]['chat_msg_conn']
    while True:
        try:
            msg = get_msg(conn)
            if not msg:
                print(f"chat1: {addr} disconnected")
                Thread(target=Disconnect, args=(addr,), daemon=True).start()
                break
            if msg['type'] == "chat":
                connections[addr]['comp'].listWidget1.addItem(msg['message'])
        except ConnectionResetError or OSError:
            print(f"chat2: {addr} disconnected")
            Thread(target=Disconnect, args=(addr,), daemon=True).start()
            break

class MainWindow(UI.MainWindow_UI):
    def __init__(self, socket):
        super(MainWindow, self).__init__()
        self.sock = socket
        self.lock = threading.Lock()
        self.column_limit = 2
        self.row_limit = 2
        self.show()
        self.listener_thread = QThread()
        self.listener = Listener(self.sock)
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

        connections[addr].update({'screen_sharing_sock': socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)})
        port = get_open_port()
        connections[addr]['screen_sharing_sock'].bind((connections[addr]['conn'].getsockname()[0], port))
        send_msg(connections[addr]['conn'], 'message', port=port)
        connections[addr].update({'screen_sharing_thread': Thread(target=screen_sharing, args=(addr,), daemon=True)})
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
        connections[addr].update({'handle_msg_thread': Thread(target=handle_client_msg, args=(addr,), daemon=True)})
        connections[addr]['handle_msg_thread'].start()

        connections[addr].update({'block_input': False})

        self.group_view()

    def group_view(self):
        for addr in connections:
            num = eval(connections[addr]['comp'].objectName().strip('comp'))
            for row in range(self.row_limit):
                for column in range(self.column_limit):
                    if row * self.column_limit + column == num:
                        connections[addr]['comp'] = UI.ComputerScreen(self.widget)
                        connections[addr]['comp'].setObjectName(f"comp{num}")
                        connections[addr]['comp'].setToolTip(f"{addr}\'s computer")
                        connections[addr]['comp'].setStyleSheet(u"QLabel{background-color: rgb(150, 150, 150);\n"
                                                                u"border-radius: 5px;}\n"
                                                                u"QLabel:hover{\n"
                                                                u"border: 5px solid rgb(80, 180, 80);\n"
                                                                u"border-radius: 5px;\n"
                                                                u"}")
                        connections[addr]['comp'].setMinimumSize(QSize(240, 135))
                        connections[addr]['comp'].setMaximumSize(QSize(480, 270))
                        self.gridLayout_2.addWidget(connections[addr]['comp'], row, column, 1, 1)
                        connections[addr]['comp'].clicked.connect(self.tab_control)
        if 'tab_view' in WINDOWS:
            WINDOWS['main_window'].show()
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
                    if connections[addr]['comp'].pixmap():
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
                        self.tab_view.tabWidget.addTab(connections[addr]['comp'], f'{addr}')
                        self.tab_view.blockInputAction.triggered.connect(lambda: block_input(self.tab_view.tabWidget.currentWidget(), True))
                        self.tab_view.unblockInputAction.triggered.connect(lambda: block_input(self.tab_view.tabWidget.currentWidget(), False))
                        self.tab_view.shareScreenAction.triggered.connect(lambda: StartScreenSharing(self.tab_view.tabWidget.currentWidget()))
                        for address in connections:
                            connections[address]['comp'].disconnect()
                            connections[address]['comp'].setMaximumSize(QSize(10000, 10000))
                            connections[address]['comp'].clicked.connect(self.start_controlling)
                            if address != addr:
                                self.tab_view.tabWidget.addTab(connections[address]['comp'], f'{address}')

                        WINDOWS['tab_view'] = self.tab_view
                        WINDOWS['tab_view'].show()
                        WINDOWS['main_window'].close()
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


def main(server_sock):
    global WINDOWS
    main_window = MainWindow(server_sock)
    WINDOWS['main_window'] = main_window
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