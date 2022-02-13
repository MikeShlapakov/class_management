import sys
import socket
import numpy as np
from PIL import Image
import win32api, win32gui, win32ui, win32con, atexit
from ctypes import *
from ctypes.wintypes import DWORD, WPARAM, LPARAM
from threading import Thread
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QPushButton, QAction, QMessageBox, QLineEdit
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QRect, Qt, QSize, QObject, QThread, pyqtSignal
from pynput import mouse, keyboard
from pynput.mouse import Button
from pynput.keyboard import Key
import time
import io
import json
import cv2
from client_ui import client_ui as UI
import admin


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
                        self.admin_connected.emit(msg['address'])
                    except TypeError:
                        self.admin_connected.emit(tuple(msg['address']))
                elif msg['msg'] == 'admin_disconnected':
                    self.disconnect.emit()
        self.finished.emit()


def send_screenshot():
    global SOCKETS
    sock = SOCKETS['screen_sharing_sock']
    screenSize = [win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)]
    sock.send(str(screenSize).encode('utf-8'))
    sock.recv(1)
    scale = 0.5
    try:
        while True:
            data = get_screenshot()
            img = cv2.cvtColor(data, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)  # converting the array to image
            new_scale = (int(img.size[0] * scale), int(img.size[1] * scale))  # compress the image with scale 0.5
            img = img.resize(new_scale, Image.ANTIALIAS)
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG', optimize=True,
                     quality=80)  # optimize the image and convert it to bytes
            # send image
            msg = img_bytes.getvalue()
            msg_len = len(msg)
            # print(msg_len)
            # while msg_len > 50000:
            #     header = str(50000) + ' ' * (16 - len(str(50000)))
            #     sock.send(header.encode())
            #     sock.recv(1)
            #     sock.send(msg[:50000])
            #     msg_len -= 50000
            #     print(msg_len, len(msg[:50000]), len(msg[50000:]))
            #     msg = msg[50000:]
            header = str(msg_len) + ' ' * (16 - len(str(msg_len)))
            sock.send(header.encode())
            sock.send(msg)
    except ConnectionResetError:
        print("screen-sharing stopped: admin disconnected")
    except Exception as e:
        print(f'screen-sharing stopped: {e}')
    return


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
            print(msg)
            try:
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


def Connect(addr):
    global SOCKETS

    block_input(True)

    SOCKETS['admin_sock'] = socket.socket()
    SOCKETS['admin_sock'].connect(addr)

    msg = get_msg(SOCKETS['admin_sock'])
    if not msg:
        return
    screen_saring_port = msg['port']
    SOCKETS['screen_sharing_sock'] = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    SOCKETS['screen_sharing_sock'].connect((addr[0], screen_saring_port))
    screansharing = Thread(target=send_screenshot, daemon=True)
    screansharing.start()

    msg = get_msg(SOCKETS['admin_sock'])
    if not msg:
        return
    control_port = msg['port']
    SOCKETS['control_sock'] = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    SOCKETS['control_sock'].connect((addr[0], control_port))
    controling = Thread(target=controller, daemon=True)
    controling.start()

    msg = get_msg(SOCKETS['admin_sock'])
    if not msg:
        return
    send_msg_port = msg['port']
    SOCKETS['msg_sock'] = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    SOCKETS['msg_sock'].connect((addr[0], send_msg_port))


def Disconnect():
    global SOCKETS
    block_input(False)
    for sock in SOCKETS:
        if sock == 'server_sock':
            continue
        SOCKETS[sock].close()


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
        self.listener = Listener(SOCKETS['server_sock'])
        self.listener.moveToThread(self.listener_thread)
        self.listener_thread.started.connect(self.listener.run)
        self.listener.finished.connect(self.listener_thread.quit)
        self.listener.finished.connect(self.listener.deleteLater)
        self.listener_thread.finished.connect(self.listener_thread.deleteLater)
        self.listener.admin_connected.connect(Connect)
        self.listener.disconnect.connect(Disconnect)
        self.listener_thread.start()

    def login(self, command, name, password):
        global SOCKETS
        if name and password:
            SOCKETS['server_sock'] = socket.socket()
            SOCKETS['server_sock'].connect((ADDR, 12121))
            print('connected')
            if send_msg(SOCKETS['server_sock'], 'command', command=command, username=name, password=password):
                msg = get_msg(SOCKETS['server_sock'])
                if not msg:
                    SOCKETS['server_sock'].close()
                    print('left login')
                    return
                if msg['type'] == 'message':
                    if msg['priority'] == 'admin':
                        # print("admin")
                        admin.main(SOCKETS['server_sock'])
                    else:
                        self.login_as_client()
                elif msg['type'] == 'error':
                    dlg = UI.CustomDialog(self, 'ERROR', msg['msg'])
                    dlg.exec_()
                    SOCKETS['server_sock'].close()
                    print('left login')
            else:
                SOCKETS['server_sock'].close()
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


def alert(sock):
    if sock:
        msg = "ALERT"
        msg_len = len(msg)
        sock.send((str(msg_len) + ' ' * (64 - len(str(msg_len)))).encode())
        sock.send(msg.encode())


if __name__ == '__main__':
    BLOCK_INPUT = False
    ADDR = '192.168.66.148'
    # ADDR = '192.168.31.101'
    # ADDR = '172.16.1.23'
    BUFSIZE = 16  # Buffer size
    SOCKETS = {'server_sock': None,
               'admin_sock': None,
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