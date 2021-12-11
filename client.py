from socket import *
import numpy as np
from PIL import Image
import win32gui, win32ui, win32con
from threading import Thread
import sys
import win32api as win
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QPushButton, QAction, QMessageBox, QLineEdit
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QRect, Qt
from pynput import mouse, keyboard
from pynput.mouse import Button
from pynput.keyboard import Key
import time
import io
import os
import cv2
from client_ui import client_ui as UI

# ADDR = '192.168.31.186'
ADDR = '192.168.31.101'
# ADDR = '172.16.1.123'


class Desktop(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def StartThread(self):
        self.start.start()

    def get_screenshot(self):
        """
        Takes screenshot.
        :return: img array
        """
        # define your monitor width and height
        w, h = win.GetSystemMetrics(0), win.GetSystemMetrics(1)
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
        img = np.fromstring(signedIntsArray, dtype='uint8')
        img.shape = (h, w, 4)

        # free resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, wDC)
        win32gui.DeleteObject(bmp.GetHandle())

        return img

    def send_screenshot(self):
        # if len(self.ip.text()) != 0 and len(self.port.text()):
        sock = socket()
        #     print(self.ip.text(), int(self.port.text()))
        #     sock.connect((self.ip.text(), int(self.port.text()))) # 192.168.31.229 9091
        sock.connect((ADDR, 12121))
        screenSize = [win.GetSystemMetrics(0),win.GetSystemMetrics(1)]
        sock.send(str(screenSize).encode())
        sock.recv(1)
        self.controling = Thread(target=self.MouseAndKeyboardController, daemon=True)
        self.controling.start()
        scale = 0.5
        while True:
            data = self.get_screenshot()
            img = cv2.cvtColor(data, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)  # converting the array to image
            new_scale = (int(img.size[0]*scale), int(img.size[1]*scale))  # compress the image with scale 0.5
            img = img.resize(new_scale, Image.ANTIALIAS)
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG', optimize=True, quality=80)  # optimize the image and convert it to bytes
            # send image
            sock.send((str(len(img_bytes.getvalue()))+' '*(64-len(str(len(img_bytes.getvalue()))))).encode())
            sock.send(img_bytes.getvalue())
            # sock.recv(1)
        sock.close()


    def MouseAndKeyboardController(self):
        new_conn = socket()
        new_conn.connect((ADDR, 13131))
        ms = mouse.Controller()
        kb = keyboard.Controller()

        def on_move(x,y):
            ms.position = (x,y)
            new_conn.send(("got it").encode())

        def on_click(button):
            ms.press(Button.left if button.find('left') else Button.right)
            new_conn.send(("got it").encode())
            msg = new_conn.recv(256).decode()
            try:
                command = eval(msg)
            except Exception as e:
                print(e)
            else:
                while command[0] != "RELEASE":
                    func = commands[command[0]]
                    func(command)
                    msg = new_conn.recv(256).decode()
                    try:
                        command = eval(msg)
                    except Exception as e:
                        print(e)
                new_conn.send(("got it").encode())
            ms.release(Button.left if button.find('left') else Button.right)

        def on_scroll(scroll):
            ms.scroll(0, scroll)
            new_conn.send(("got it").encode())

        def on_key(key):
            kb.press(eval(key))
            kb.release(eval(key))
            new_conn.send(("got it").encode())

        commands = {"MOVE": lambda arr: on_move(arr[1], arr[2]),
                "CLICK": lambda arr: on_click(arr[1]),
                "SCROLL": lambda arr: on_scroll(arr[1]),
                "KEY": lambda arr: on_key(arr[1])}

        while True:
            msg = new_conn.recv(256).decode()
            try:
                command = eval(msg)
            except Exception as e:
                print(e)
                pass
            else:
                func = commands[command[0]]
                func(command)


    def initUI(self):
        self.pixmap = QPixmap()
        self.label = QLabel(self)
        self.label.resize(self.width(), self.height())
        self.setGeometry(QRect(win.GetSystemMetrics(0)// 4,win.GetSystemMetrics(1)  // 4, 400, 100))
        self.setFixedSize(self.width(), self.height())
        self.setWindowTitle("[CLIENT] Remote Desktop")
        self.start = Thread(target=self.send_screenshot, daemon=True)
        self.btn = QPushButton(self)
        self.btn.move(5, 55)
        self.btn.resize(390, 30)
        self.btn.setText("Start Demo")
        self.btn.clicked.connect(self.StartThread)
        self.ip = QLineEdit(self)
        self.ip.move(5, 5)
        self.ip.resize(390, 20)
        self.ip.setPlaceholderText("IP")
        self.port = QLineEdit(self)
        self.port.move(5, 30)
        self.port.resize(390, 20)
        self.port.setPlaceholderText("PORT")


def LoginWindow():

    def signin(name, password):
        print(name, password)

    def signup():
        print("signup")

    ui = UI.Login_UI()
    window = QMainWindow()
    windows['login'] = window
    ui.setupUi(window)
    window.show()
    ui.signin_btn.clicked.connect(lambda: signin(ui.username_entry.text(),ui.password_entry.text()))
    ui.signup_btn.clicked.connect(lambda: signup(ui.username_entry.text(), ui.password_entry.text()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    windows = {}
    LoginWindow()
    # ex = Desktop()
    # ex.show()
    time.sleep(3)
    sys.exit(app.exec())