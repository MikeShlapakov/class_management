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
import admin


class Desktop():
    def __init__(self):
        self.main_sock = socket()
        self.main_sock.connect((ADDR, 12121))

        msg_len = self.main_sock.recv(64)
        self.screen_saring_port = eval(self.main_sock.recv(eval(msg_len.decode())).decode())
        print(self.screen_saring_port)
        self.screen_sharing_sock = socket(family=AF_INET, type=SOCK_DGRAM)
        self.screansharing = Thread(target=self.send_screenshot, daemon=True)
        self.screansharing.start()

        msg_len = self.main_sock.recv(64)
        self.control_port = eval(self.main_sock.recv(eval(msg_len.decode())).decode())
        print(self.control_port)
        self.control_sock = socket(family=AF_INET, type=SOCK_DGRAM)
        self.control_sock.bind((self.main_sock.getsockname()[0], self.control_port))
        self.controling = Thread(target=self.controller, daemon=True)
        self.controling.start()

        msg_len = self.main_sock.recv(64)
        self.send_msg_port = eval(self.main_sock.recv(eval(msg_len.decode())).decode())
        print(self.send_msg_port)
        self.send_msg_sock = socket(family=AF_INET, type=SOCK_DGRAM)
        self.send_msg_sock.bind((self.main_sock.getsockname()[0], self.send_msg_port))

        # mouse_listener = mouse.Listener(on_move=self.alert, on_click=self.alert,on_scroll=self.alert)
        # mouse_listener.start()

        kb_listener = keyboard.Listener(on_press=self.alert)
        kb_listener.start()


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
        screenSize = [win.GetSystemMetrics(0),win.GetSystemMetrics(1)]
        addr = (ADDR,self.screen_saring_port)
        self.screen_sharing_sock.sendto(str(screenSize).encode('utf-8'), addr)
        self.screen_sharing_sock.recvfrom(1)
        scale = 0.5
        try:
            while True:
                data = self.get_screenshot()
                img = cv2.cvtColor(data, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img)  # converting the array to image
                new_scale = (int(img.size[0]*scale), int(img.size[1]*scale))  # compress the image with scale 0.5
                img = img.resize(new_scale, Image.ANTIALIAS)
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='JPEG', optimize=True, quality=80)  # optimize the image and convert it to bytes
                # send image
                self.screen_sharing_sock.sendto((str(len(img_bytes.getvalue()))+' '*(64-len(str(len(img_bytes.getvalue()))))).encode(), addr)
                self.screen_sharing_sock.sendto(img_bytes.getvalue(), addr)
        except ConnectionResetError:
            print("server disconnected")


    def controller(self):
        conn = self.control_sock
        addr = (ADDR, self.control_port)
        ms = mouse.Controller()
        kb = keyboard.Controller()

        def on_move(x,y):
            ms.position = (x,y)

        def on_click(button):
            ms.press(Button.left if button.find('left') else Button.right)
            msg = conn.recvfrom(256)[0].decode()
            try:
                command = eval(msg)
            except Exception as e:
                print(e)
            else:
                while command[0] != "RELEASE":
                    func = commands[command[0]]
                    func(command)
                    msg = conn.recvfrom(256)[0].decode()
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
                msg = conn.recvfrom(256)[0].decode()
                try:
                    command = eval(msg)
                except Exception as e:
                    print(e)
                    pass
                else:
                    func = commands[command[0]]
                    func(command)
        except ConnectionResetError:
            print("server disconnected")

    def alert(self, *args):
        msg = "ALERT"
        addr = (ADDR, self.send_msg_port)
        msg_len = len(msg)
        self.send_msg_sock.sendto((str(msg_len) + ' ' * (64 - len(str(msg_len)))).encode(), addr)
        self.send_msg_sock.sendto(msg.encode(), addr)


def LoginWindow():  # TODO splash screen

    def signin(name, password):
        if name == 'asd':
            admin.main()
            print(name, password)
        else:
            # window.close()
            Desktop()

    def signup(name, password):
        if name == 'asd':
            admin.main()
            print(name, password)

    ui = UI.Login_UI()
    window = QMainWindow()
    windows['login'] = window
    ui.setupUi(window)
    window.show()
    ui.signin_btn.clicked.connect(lambda: signin(ui.username_entry.text(),ui.password_entry.text()))
    ui.signup_btn.clicked.connect(lambda: signup(ui.username_entry.text(), ui.password_entry.text()))
if __name__ == '__main__':
    ADDR = '192.168.31.156'
    # ADDR = '192.168.31.101'
    # ADDR = '172.16.1.123'

    app = QApplication(sys.argv)
    windows = {}
    LoginWindow()
    sys.exit(app.exec())