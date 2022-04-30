import sys
import socket
import numpy as np
from PIL import Image, ImageChops
from zlib import compress, decompress
from mss import mss
import win32api, win32gui, win32ui, win32con, atexit
from ctypes import *
from ctypes.wintypes import DWORD, WPARAM, LPARAM
from threading import Thread
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QPushButton, QAction, QMessageBox, QLineEdit, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QRect, Qt, QSize, QObject, QThread, pyqtSignal, QDir
from pynput import mouse, keyboard
from pynput.mouse import Button
from pynput.keyboard import Key
import time
import io
import json
import cv2
from client_ui import client_ui as UI
import admin
import os


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


def send_msg(conn, type="", **kwargs):
    """
    Send message to client
    :param conn: client socket (socket)
    :param type: message type (string)
    :return: sent the message (True/False)
    """
    global BUFSIZE, conn_list
    msg = {'type': type}
    msg.update(dict(**kwargs))
    msg = json.dumps(msg)
    print(msg)
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
    print("sent", msg)
    return True


def get_msg(conn):
    """
    Get message from the client
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
    if msg.find('MOVE') == -1:
        print("got", msg)
    return json.loads(msg)


def get_screenshot():
    """
    Takes screenshot.
    :return: img array
    """
    # define your monitor width and height
    w, h = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)
    hwnd = None
    # get the window image data
    wDC = win32gui.GetWindowDC(hwnd)
    dcObj = win32ui.CreateDCFromHandle(wDC)
    cDC = dcObj.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()  # BitMap
    bmp.CreateCompatibleBitmap(dcObj, w, h)
    cDC.SelectObject(bmp)
    cDC.BitBlt((0, 0), (w, h), dcObj, (0, 0), win32con.SRCCOPY)

    # convert the raw data into a format opencv can read
    signedIntsArray = bmp.GetBitmapBits(True)
    img = np.frombuffer(signedIntsArray, dtype='uint8')
    img.shape = (h, w, 4)

    # free resources
    dcObj.DeleteDC()
    cDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, wDC)
    win32gui.DeleteObject(bmp.GetHandle())

    return img


class Listener(QObject):
    finished = pyqtSignal()
    admin_connected = pyqtSignal(tuple)
    disconnect = pyqtSignal()

    def __init__(self, sock):
        super().__init__()
        self.sock = sock

    def run(self):
        """handle incoming messages from the server"""
        send_msg(self.sock, 'message', msg='client_connected')
        while True:
            msg = get_msg(self.sock)  # get message
            if not msg:
                break
            if msg['type'] == 'message':
                if msg['msg'] == 'admin_connected':
                    try:
                        SOCKETS['admin_ip'] = msg['ip']
                        self.admin_connected.emit(msg['address'])
                    except TypeError:
                        self.admin_connected.emit(tuple(msg['address']))
                elif msg['msg'] == 'admin_disconnected':
                    self.disconnect.emit()
            elif msg['type'] == 'chat':
                WINDOWS['chat_ui'].show()
                WINDOWS['chat_ui'].listWidget.addItem(msg['msg'])
                # self.listener.chat_msg.connect(Chat)
                # self.chat_msg.emit(msg['msg'])
        self.finished.emit()


def imagesDifference(imageA, imageB ):
    diff1 = np.array(ImageChops.subtract(imageA, imageB, 1))
    vec1 = np.argwhere(diff1[:,:,0] > 20)
    diff2 = np.array(ImageChops.subtract(imageA, imageB, -1))
    vec2 = np.argwhere(diff2[:,:,0] >20)
    return np.concatenate((-diff1[vec1[:,0],vec1[:,1], :], diff2[vec2[:,0],vec2[:,1], :])), np.concatenate((vec1,vec2))


def send_screenshot(rect, sock):
    global SOCKETS
    # sock = SOCKETS['screen_sharing_sock']
    scale = 0.5

    with mss() as sct:
        # prev = time.time()
        sct_img = sct.grab(rect)
        # Tweak the compression level here (0-9)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        new_scale = (int(img.size[0] * scale), int(img.size[1] * scale))  # compress the image with scale 0.5
        img = img.resize(new_scale, Image.ANTIALIAS)
        prev_img = img
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', optimize=True,
                 quality=80)  # optimize the image and convert it to bytes
        # send image
        msg = compress(img_bytes.getvalue(), 9)
        msg_len = len(msg)
        header = str(msg_len) + ' ' * (16 - len(str(msg_len)))
        sock.send(header.encode())
        sock.send(msg)
        while True:
            try:
                sct_img = sct.grab(rect)
                # Tweak the compression level here (0-9)
                new_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                new_scale = (int(new_img.size[0] * scale), int(new_img.size[1] * scale))  # compress the image with scale 0.5
                new_img = new_img.resize(new_scale, Image.ANTIALIAS)
                # diff, index = imagesDifference(prev_img, new_img)
                img_bytes = io.BytesIO()
                new_img.save(img_bytes, format='JPEG', optimize=True,
                         quality=80)  # optimize the image and convert it to bytes
                # send image
                msg = compress(img_bytes.getvalue(), 9)
                msg_len = len(msg)
                header = str(msg_len) + ' ' * (16 - len(str(msg_len)))
                sock.send(header.encode('utf-8'))
                sock.send(msg)

            except (ConnectionResetError, WindowsError) as e:
                print("screen-sharing: admin disconnected", e)
                if e.winerror == 10040:
                    print(e)
                    sock.send(header.encode())
                else:
                    break
            except Exception as e:
                print(f'screen-sharing: {e}')
    return


def StartShareScreen(share):
    if not share:
        for rect in ['rect', 'rect2', 'rect3', 'rect4']:
            SOCKETS[f'{rect}'].close()
            SOCKETS.pop(f'{rect}')
            THREADS[f'{rect}'].join()
            THREADS.pop(f'{rect}')
        return

    rects = {'rect' : {'top': 0, 'left': 0, 'width': win32api.GetSystemMetrics(0)//2, 'height': win32api.GetSystemMetrics(1)//2},
    'rect2' : {'top': 0, 'left': win32api.GetSystemMetrics(0) // 2, 'width': win32api.GetSystemMetrics(0) // 2,
            'height': win32api.GetSystemMetrics(1) // 2},
    'rect3' : {'top': win32api.GetSystemMetrics(1) // 2, 'left': 0, 'width': win32api.GetSystemMetrics(0) // 2,
            'height': win32api.GetSystemMetrics(1) // 2},
    'rect4' : {'top': win32api.GetSystemMetrics(1) // 2, 'left': win32api.GetSystemMetrics(0) // 2, 'width': win32api.GetSystemMetrics(0) // 2,
            'height': win32api.GetSystemMetrics(1) // 2}}
    for rect in rects:
        msg = get_msg(SOCKETS['screen_sharing_sock'])
        if not msg or msg['type'] != 'bind':
            return
        SOCKETS[f'{rect}'] = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        SOCKETS[f'{rect}'].connect(tuple(msg['address']))
        THREADS[f'{rect}'] = Thread(target=send_screenshot, args=(rects[rect], SOCKETS[f'{rect}']), daemon=True)
        THREADS[f'{rect}'].start()


def screen_sharing(rect):
    sock = SOCKETS[f'{rect}_sock']
    pixmap = QPixmap()
    while True:
        try:
            img_len = sock.recvfrom(16)[0]
            img = sock.recvfrom(eval(img_len.decode()))[0]
            if len(img) != eval(img_len.decode()):
                continue
            # print(img_len)
            pixmap.loadFromData(decompress(img))
            # pixmap.scaled(WINDOWS['share_screen'].widget.width(), WINDOWS['share_screen'].widget.height(),
            #               Qt.KeepAspectRatio, Qt.SmoothTransformation)
            for label in [WINDOWS['share_screen'].top_left, WINDOWS['share_screen'].top_right, WINDOWS['share_screen'].bottom_left, WINDOWS['share_screen'].bottom_right]:
                if label.objectName() == rect:
                    label.setScaledContents(True)
                    label.setPixmap(QPixmap(pixmap))
                    label.setAlignment(Qt.AlignCenter)
                    break
        except (ConnectionResetError, WindowsError) as e:
            print(f"screen_sharing stopped: {sock} disconnected", e)
            if e.winerror == 10038:
                break
        except Exception as e:
            print(f'screen_sharing stopped: {e}')


class ShareScreen(UI.ShareScreenWindow):
    def __init__(self, share):
        global WINDOWS
        super(ShareScreen, self).__init__()
        WINDOWS['share_screen'] = self
        WINDOWS['share_screen'].show()
        if not share:
            for i in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
            # if SOCKETS.get('share_sock'):
                print('share stopped')
                SOCKETS[f'{i}_sock'].close()
                SOCKETS.pop(f'{i}_sock')
                THREADS[f'{i}_thread'].join()
                THREADS.pop(f'{i}_thread')
                if WINDOWS['share_screen'].isVisible():
                    WINDOWS['share_screen'].close()
            return

        for i in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
            SOCKETS[f'{i}_sock'] = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            SOCKETS[f'{i}_sock'].bind((SOCKETS['admin'].getsockname()[0], get_open_port()))
            send_msg(SOCKETS['admin'], 'bind', address=SOCKETS[f'{i}_sock'].getsockname())
            THREADS[f'{i}_thread'] = Thread(target=screen_sharing, args=(i,), daemon=True)
            THREADS[f'{i}_thread'].start()


class BlockScreen(UI.BlockScreenWindow):
    def __init__(self, block):
        global WINDOWS
        super(BlockScreen, self).__init__()
        WINDOWS['block_screen'] = self
        WINDOWS['block_screen'].show()
        if not block:
            print('block screen stopped')
            if WINDOWS['block_screen'].isVisible():
                WINDOWS['block_screen'].close()
            return
        block_screen_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        port = get_open_port()
        block_screen_sock.bind((SOCKETS['admin'].getsockname()[0], port))
        block_screen_sock.listen(1)
        send_msg(SOCKETS['admin'], 'bind', address=(SOCKETS['admin'].getsockname()[0], port))
        conn, addr = block_screen_sock.accept()
        img_len = conn.recv(16)
        if not img_len:
            print('block screen stopped')
            if WINDOWS['block_screen'].isVisible():
                WINDOWS['block_screen'].close()
            conn.close()
            block_screen_sock.close()
            return
        img = b''
        while img_len:
            msg = conn.recv(eval(img_len.decode('utf-8')))
            while len(msg) != eval(img_len.decode('utf-8')):
                msg += conn.recv(eval(img_len.decode('utf-8'))-len(msg))
            img += msg
            img_len = conn.recv(16)
        pixmap = QPixmap()
        pixmap.loadFromData(decompress(img))
        pixmap.scaled(self.widget.width(), self.widget.height(),
                      Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.widget.setScaledContents(True)
        self.widget.setPixmap(QPixmap(pixmap))
        self.widget.setAlignment(Qt.AlignCenter)
        conn.close()
        block_screen_sock.close()


class RecvFile():
    def __init__(self):
        global WINDOWS
        super(RecvFile, self).__init__()
        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        port = get_open_port()
        sock.bind((SOCKETS['admin'].getsockname()[0], port))
        sock.listen(1)
        send_msg(SOCKETS['admin'], 'bind', address=(SOCKETS['admin'].getsockname()[0], port))
        conn, addr = sock.accept()
        msg = get_msg(conn)
        if not msg or msg['type']!='file_name' :
            return
        file_name = eval(msg['name']).decode(msg['encoder'])
        msg = get_msg(conn)
        if not msg or msg['type'] != 'encoder':
            return
        encoder = msg['encoder']
        msg_len = conn.recv(16)
        msg = b''
        while msg_len:
            print(msg_len)
            msg += conn.recv(eval(msg_len.decode()))
            time.sleep(0.02)
            msg_len = conn.recv(16)
            print(msg_len)
            print(msg_len.decode())
        # msg = decompress(msg).decode()
        with open(f'{os.path.split(__file__)[0]}/{file_name}', 'wb') as f:#, encoding=encoder) as f:
            f.write(msg)
        sock.close()
        conn.close()


def controller():
    global SOCKETS
    sock = SOCKETS['control_sock']
    ms = mouse.Controller()
    kb = keyboard.Controller()

    def on_move(x, y):
        ms.position = (x, y)

    def on_click(button):
        ms.press(Button.left if button.find('left') else Button.right)
        msg = get_msg(sock)
        try:
            command = msg['command']
        except Exception as e:
            print(f'RELEASE caught an error: {e}. {msg}')
        else:
            while command[0] != "RELEASE":
                func = commands[command[0]]
                func(command)
                msg = get_msg(sock)
                try:
                    command = msg['command']
                except Exception as e:
                    print(f'RELEASE2 caught an error: {e}. {msg}')
        ms.release(Button.left if button.find('left') else Button.right)

    def on_scroll(scroll):
        ms.scroll(0, scroll)

    def on_key(key):
        kb.press(eval(key))
        kb.release(eval(key))

    try:
        commands = {"MOVE": lambda arr: on_move(arr[1], arr[2]),
                    "CLICK": lambda arr: on_click(arr[1]),
                    "RELEASE": lambda arr: print(arr),
                    "SCROLL": lambda arr: on_scroll(arr[1]),
                    "KEY": lambda arr: on_key(arr[1])}

        while True:
            msg = get_msg(sock)
            if not msg:
                return
            try:
                if msg['type'] == 'block_input':
                    block_input(msg['block_input'])
                    continue
                command = msg['command']
            except Exception as e:
                print(f'control caught an error: {e}. {msg}')
                pass
            else:
                func = commands[command[0]]
                func(command)
    except ConnectionResetError:
        print("controlling stopped: admin disconnected")
    except Exception as e:
        print(f'controlling stopped: {e}')
    return


def block_input(block):
    global BLOCK_INPUT, WINDOWS
    if block:
        BLOCK_INPUT = True
        return
    BLOCK_INPUT = False
    return


class AdminHandle(QObject):
    screenShare = pyqtSignal(bool)
    shareScreen = pyqtSignal(bool)
    blockScreen = pyqtSignal(bool)
    receiveFile = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        global SOCKETS
        self.sock = SOCKETS['admin_msg_sock']

    def run(self):
        """handle incoming messages from the admin"""
        try:
            while True:
                msg = get_msg(self.sock)
                if not msg:
                    return
                if msg['type'] == 'screen_share':
                    self.screenShare.emit(msg['share'])
                if msg['type'] == 'share':
                    self.shareScreen.emit(msg['share'])
                if msg['type'] == 'block_screen':
                    self.blockScreen.emit(msg['block'])
                if msg['type'] == 'share_file':
                    self.receiveFile.emit()
        except ConnectionResetError:
            print("admin_msg_sock stopped: admin disconnected")
        except Exception as e:
            print(f'admin_msg_sock stopped: {e}')
        self.finished.emit()


class Connect(QObject):
    def __init__(self, addr):
        super().__init__()
        global SOCKETS

        # block_input(True)
        WINDOWS['Connect'] = self

        SOCKETS['admin'] = socket.socket()
        SOCKETS['admin'].connect(addr)

        send_msg(SOCKETS['admin'] , 'ScreenSize',size=[win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)])

        msg = get_msg(SOCKETS['admin'])
        if not msg:
            return
        # screen_saring_port = msg['port']
        SOCKETS['screen_sharing_sock'] = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        SOCKETS['screen_sharing_sock'].connect(tuple(msg['address']))
        screansharing = Thread(target=StartShareScreen, args=(True,), daemon=True)
        screansharing.start()

        msg = get_msg(SOCKETS['admin'])
        if not msg:
            return
        control_port = msg['port']
        SOCKETS['control_sock'] = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        SOCKETS['control_sock'].connect((addr[0], control_port))
        controling = Thread(target=controller, daemon=True)
        controling.start()

        msg = get_msg(SOCKETS['admin'])
        if not msg:
            return
        send_msg_port = msg['port']
        SOCKETS['admin_msg_sock'] = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        SOCKETS['admin_msg_sock'].connect((addr[0], send_msg_port))
        self.start_admin_thread()

    def start_admin_thread(self):
        self.admin_handle_thread = QThread()
        self.admin_handle = AdminHandle()
        self.admin_handle.moveToThread(self.admin_handle_thread)
        self.admin_handle_thread.started.connect(self.admin_handle.run)
        self.admin_handle.screenShare.connect(StartShareScreen)
        self.admin_handle.shareScreen.connect(ShareScreen)
        self.admin_handle.blockScreen.connect(BlockScreen)
        self.admin_handle.receiveFile.connect(RecvFile)
        self.admin_handle.finished.connect(self.admin_handle_thread.quit)
        self.admin_handle.finished.connect(self.admin_handle.deleteLater)
        self.admin_handle_thread.finished.connect(self.admin_handle_thread.deleteLater)
        self.admin_handle_thread.start()


def Disconnect():
    global SOCKETS
    block_input(False)
    for sock in SOCKETS:
        if sock == 'server':
            continue
        try:
            SOCKETS[sock].close()
        except AttributeError:
            pass
    for window in WINDOWS:
        if window in ['block_screen', 'share_screen']:
            if WINDOWS[window].isVisible():
                WINDOWS[window].close()


class Chat(QObject):
    def __init__(self, msg=None):
        super().__init__()
        global SOCKETS
        self.ui = UI.ChatBox_UI()
        WINDOWS['chat_ui'] = self.ui
        self.ui.show()
        self.ui.lineEdit.returnPressed.connect(self.on_press)

    def on_press(self):
        if SOCKETS['admin']:
            send_msg(SOCKETS['server'], 'chat', recv=SOCKETS['admin_ip'], msg=self.ui.lineEdit.text())
            return
        send_msg(SOCKETS['server'], 'chat', msg=self.ui.lineEdit.text())
        # print(self.ui.lineEdit.text())

def alert():
    if SOCKETS['admin_msg_sock']:
        send_msg(SOCKETS['admin_msg_sock'], 'alert', addr=SOCKETS['admin'].getsockname(), alert='Trying take over the keyboard')


class LoginWindow(QMainWindow):  # TODO splash screen
    def __init__(self, parent=None):
        global WINDOWS
        super().__init__(parent)
        self.ui = UI.Login_UI()
        self.ui.setupUi(self)
        self.show()
        WINDOWS['login'] = self
        self.ui.signin_btn.clicked.connect(lambda: self.login('signin', self.ui.username_entry.text(), self.ui.password_entry.text()))
        self.ui.signup_btn.clicked.connect(lambda: self.login('signup', self.ui.username_entry.text(), self.ui.password_entry.text()))

    def login_as_client(self):
        # print("client")
        self.showMinimized()
        self.listener_thread = QThread()
        self.listener = Listener(SOCKETS['server'])
        self.listener.moveToThread(self.listener_thread)
        self.listener_thread.started.connect(self.listener.run)
        self.listener.finished.connect(self.listener_thread.quit)
        self.listener.finished.connect(self.listener.deleteLater)
        self.listener_thread.finished.connect(self.listener_thread.deleteLater)
        self.listener.admin_connected.connect(Connect)
        self.listener.disconnect.connect(Disconnect)
        self.listener_thread.start()
        WINDOWS['chat'] = Chat()

    def login(self, command, name, password):
        global SOCKETS
        if name and password:
            SOCKETS['server'] = socket.socket()
            SOCKETS['server'].connect((ADDR, 12121))
            print('connected')
            if send_msg(SOCKETS['server'], 'command', command=command, username=name, password=password):
                msg = get_msg(SOCKETS['server'])
                if not msg:
                    SOCKETS['server'].close()
                    print('left login')
                    return
                if msg['type'] == 'message':
                    if msg['priority'] == 'admin':
                        # print("admin")
                        admin.main(SOCKETS['server'])
                    else:
                        self.login_as_client()
                elif msg['type'] == 'error':
                    dlg = UI.CustomDialog(self, 'ERROR', msg['msg'])
                    dlg.exec_()
                    SOCKETS['server'].close()
                    print('left login')
            else:
                SOCKETS['server'].close()
                print('left login')


class MSLLHOOKSTRUCT(Structure): _fields_ = [
    ('x', DWORD),
    ('y', DWORD),
    ('mouseData', DWORD),
    ('flags', DWORD),
    ('time', DWORD),
    ('dwExtraInfo', DWORD)]


class KBDLLHOOKSTRUCT(Structure): _fields_ = [
    ('vkCode', DWORD),
    ('scanCode', DWORD),
    ('flags', DWORD),
    ('time', DWORD),
    ('dwExtraInfo', DWORD)]


def mouse_and_keyboard_hook():
    """
    mouse and keyboard event receiver. This is a blocking call.
    """
    # Adapted from http://www.hackerthreads.org/Topic-42395

    def mouse_handler(nCode, wParam, lParam):
        """
        Processes a low level Windows mouse event.
        """
        global BLOCK_INPUT
        if nCode == win32con.HC_ACTION:
            ms = MSLLHOOKSTRUCT.from_address(lParam)
            if ms.flags == 1 or not BLOCK_INPUT:
                # call the next hook unless you want to block it
                return windll.user32.CallNextHookEx(ms_hook, nCode, wParam, lParam)
        return 1
        # print(f"pt - {[ms.x, ms.y]}, mouseData - {ms.mouseData}, flags - {ms.flags}")

    def keyboard_handler(nCode, wParam, lParam):
        """
        Processes a low level Windows keyboard event.
        """
        global BLOCK_INPUT
        if nCode == win32con.HC_ACTION:
            kb = KBDLLHOOKSTRUCT.from_address(lParam)
            if kb.flags == 16 or kb.flags == 144 or not BLOCK_INPUT:
                # call the next hook unless you want to block it
                return windll.user32.CallNextHookEx(kb_hook, nCode, wParam, lParam)
        alert()
        return 1
        # print(f"vkCode - {kb.vkCode}, scanCode - {kb.scanCode}, flags - {kb.flags}")

    # Our low level handler signature.
    HOOKPROC = WINFUNCTYPE(HRESULT, c_int, WPARAM, LPARAM)
    # Convert the Python handler into C pointer.
    ms_pointer = HOOKPROC(mouse_handler)
    kb_pointer = HOOKPROC(keyboard_handler)

    # Hook both mouse keyboard events
    ms_hook = windll.user32.SetWindowsHookExA(win32con.WH_MOUSE_LL, ms_pointer, 0, 0)
    kb_hook = windll.user32.SetWindowsHookExA(win32con.WH_KEYBOARD_LL, kb_pointer, 0, 0)

    # Register to remove the hook when the interpreter exits. Unfortunately a
    # try/finally block doesn't seem to work here.
    atexit.register(windll.user32.UnhookWindowsHookEx, ms_hook)
    atexit.register(windll.user32.UnhookWindowsHookEx, kb_hook)

    while True:
        msg = win32gui.GetMessage(None, 0, 0)


if __name__ == '__main__':
    BLOCK_INPUT = False
    # ADDR = '192.168.66.148'
    ADDR = '192.168.31.208'
    # ADDR = '172.16.1.23'
    BUFSIZE = 16  # Buffer size
    SOCKETS = {'server': None,
               'admin': None,
               'screen_sharing_sock': None,
               'control_sock': None,
               'msg_sock': None}
    THREADS = {'hook_thread': Thread(target=mouse_and_keyboard_hook, daemon=True), 'screen_sharing_thread': None,
               'control_thread': None, 'msg_thread': None}
    THREADS['hook_thread'].start()
    app = QApplication(sys.argv)
    WINDOWS = {}
    LoginWindow()
    sys.exit(app.exec_())