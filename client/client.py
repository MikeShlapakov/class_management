from socket import *
import numpy as np
from PIL import Image
import win32gui, win32ui, win32con
from threading import Thread
import sys
import win32api
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QPushButton, QAction, QMessageBox, QLineEdit
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QRect, Qt, QThread
from pynput import mouse, keyboard
from pynput.mouse import Button
from pynput.keyboard import Key
import time
import io
import json
import ctypes
from ctypes import *
import cv2
from client_ui import client_ui as UI
import admin
import mouseNkey_logger


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
                    self.admin_connected.emit(msg['address'])
                else:
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
        msg = sock.recv(256).decode()
        try:
            command = eval(msg)
        except Exception as e:
            print(e)
        else:
            while command[0] != "RELEASE":
                func = commands[command[0]]
                func(command)
                msg = sock.recv(256).decode()
                try:
                    command = eval(msg)
                except Exception as e:
                    print(e)
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
            msg = sock.recv(256).decode()
            try:
                command = eval(msg)
            except Exception as e:
                print(f'control caught an error: {e}')
                pass
            else:
                func = commands[command[0]]
                func(command)
    except ConnectionResetError:
        print("controlling stopped: admin disconnected")
    except Exception as e:
        print(f'controlling stopped: {e}')
    return


def Connect(addr):
    global SOCKETS

    SOCKETS['admin_sock'] = socket(family=AF_INET, type=SOCK_STREAM)
    SOCKETS['admin_sock'].connect(addr)

    msg = get_msg(SOCKETS['admin_sock'])
    if not msg:
        return
    screen_saring_port = eval(msg['port'])
    print(screen_saring_port)
    SOCKETS['screen_sharing_sock'] = socket(family=AF_INET, type=SOCK_DGRAM)
    SOCKETS['screen_sharing_sock'].connect((addr[0], screen_saring_port))
    screansharing = Thread(target=send_screenshot, daemon=True)
    screansharing.start()

    msg = get_msg(SOCKETS['admin_sock'])
    if not msg:
        return
    control_port = eval(msg['port'])
    print(control_port)
    SOCKETS['control_sock'] = socket(family=AF_INET, type=SOCK_DGRAM)
    SOCKETS['control_sock'].bind((addr[0], control_port))
    controling = Thread(target=controller, daemon=True)
    controling.start()

    msg = get_msg(SOCKETS['admin_sock'])
    if not msg:
        return
    send_msg_port = eval(msg['port'])
    print(send_msg_port)
    SOCKETS['msg_sock'] = socket(family=AF_INET, type=SOCK_STREAM)
    SOCKETS['msg_sock'].connect((addr[0], send_msg_port))


def Disconnect():
    global SOCKETS
    for sock in SOCKETS:
        if sock == 'server_sock':
            continue
        SOCKETS[sock].close()


def LoginWindow():  # TODO splash screen

    def login(command, name, password):
        global SOCKETS
        if name and password:
            SOCKETS['server_sock'] = socket()
            SOCKETS['server_sock'].connect((ADDR, 12121))
            print('connected')
            if send_msg(SOCKETS['server_sock'], 'command', command=command, username=name, password=password):
                msg = get_msg(SOCKETS['server_sock'])
                if not msg:
                    return
                if msg['type'] == 'message':
                    if msg['priority'] == 'admin':
                        print("admin")
                        # admin.main()
                    else:
                        # print("client")
                        window.showMinimized()
                        listener_thread = QThread()
                        listener = Listener(SOCKETS['server_sock'])
                        listener.moveToThread(listener_thread)
                        listener_thread.started.connect(listener.run)
                        listener.finished.connect(listener_thread.quit)
                        listener.finished.connect(listener.deleteLater)
                        listener_thread.finished.connect(listener_thread.deleteLater)
                        listener.admin_connected.connect(Desktop)
                        listener.disconnect.connect(Disconnect)
                        listener_thread.start()
                elif msg['type'] == 'error':
                    dlg = UI.CustomDialog(window, 'ERROR', msg['msg'])
                    dlg.exec_()
            SOCKETS['server_sock'].close()
            print('left login')

    ui = UI.Login_UI()
    window = QMainWindow()
    WINDOWS['login'] = window
    ui.setupUi(window)
    window.show()
    ui.signin_btn.clicked.connect(lambda: login('signin', ui.username_entry.text(), ui.password_entry.text()))
    ui.signup_btn.clicked.connect(lambda: login('signup', ui.username_entry.text(), ui.password_entry.text()))


def hookProc(nCode, wParam, lParam):
    # if mouseNkey_logger.user32.GetKeyState(win32con.VK_CONTROL) & 0x8000:
    #     print("\nCtrl pressed, call uninstallHook()")
    #     KeyLogger.uninstalHookProc()
    #     return 0
    if nCode == win32con.HC_ACTION and wParam == win32con.WM_KEYDOWN:
        kb = mouseNkey_logger.KBDLLHOOKSTRUCT.from_address(lParam)
        if kb.flags == 0 or kb.flags == 1:
            pass
            # start_hook_keyboard = Thread(target=set_hook_keyboard, daemon=True)
            # start_hook_keyboard.start()
        elif kb.flags == 16:
            pass
            # if kb.vkCode in mouseNkey_logger.VK_CODE.values():
            #     print(list(mouseNkey_logger.VK_CODE.keys())[list(mouseNkey_logger.VK_CODE.values()).index(kb.vkCode)])
            # print(mouseNkey_logger.VK_CODE[kb.vkCode])
        # print(kb.vkCode)
        # return {'vkCode': kb.vkCode, 'scanCode': kb.scanCode, 'flags': kb.flags, 'time': kb.time, 'dwExtraInfo': kb.dwExtraInfo}
    return mouseNkey_logger.user32.CallNextHookEx(KeyLogger.hooked, nCode, wParam, lParam)


def set_hook_keyboard():
    time.sleep(0.0001)
    win32api.keybd_event(0x11, 0, 0, 0)
    win32api.keybd_event(0x5A, 0, 0, 0)
    win32api.keybd_event(0x5A, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
    global msg_sock
    alert(msg_sock)


def alert(sock):
    if sock:
        msg = "ALERT"
        msg_len = len(msg)
        sock.send((str(msg_len) + ' ' * (64 - len(str(msg_len)))).encode())
        sock.send(msg.encode())


if __name__ == '__main__':
    # HOOKPROC = WINFUNCTYPE(HRESULT, c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)
    # KeyLogger = mouseNkey_logger.KeyLogger()
    # pointer = HOOKPROC(hookProc)
    # if KeyLogger.installHookProc(pointer):
    #     print("Hook installed")
    ADDR = '192.168.31.131'
    # ADDR = '192.168.31.101'
    # ADDR = '172.16.1.23'
    BUFSIZE = 16  # Buffer size
    SOCKETS = {'server_sock': None,
               'admin_sock': None,
               'screen_sharing_sock': None,
               'control_sock': None,
               'msg_sock': None}
    THREADS = {'screen_sharing_thread':None, 'control_thread':None, 'msg_thread': None}
    app = QApplication(sys.argv)
    WINDOWS = {}
    LoginWindow()
    sys.exit(app.exec_())
    # else:
    #     print("Hook not installed")
