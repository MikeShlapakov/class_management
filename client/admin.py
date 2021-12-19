import socket
from os import getlogin
from PIL import Image, ImageQt, ImageChops
import io
from random import randint
from pynput import mouse, keyboard
from threading import Thread
import time
import win32api as win
import numpy
# PyQt5
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QPushButton, QAction, QMessageBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QRect, Qt
from client_ui import client_ui as UI

class Dekstop(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def ScreenSharing(self):
        global scale_x, scale_y
        try:
            # self.setGeometry(400, 200, eval(screenSize)[0] // scale_x, eval(screenSize)[1] // scale_y)
            while True:
                img_len = conn.recv(64)
                img = conn.recv(eval(img_len.decode()))
                while len(img) != eval(img_len.decode()):
                    img += conn.recv(eval(img_len.decode()) - len(img))
                # image = QImage(eval(img).data, eval(img).shape[1],eval(img).shape[0],eval(img).shape[1]*3,QImage.Format_RGB888)
                # conn.send(b'1')
                self.pixmap.loadFromData(img)
                self.label.setScaledContents(True)
                self.label.resize(self.width(), self.height())
                self.label.setPixmap(QPixmap(self.pixmap))

        except ConnectionResetError:
            QMessageBox.about(self, "ERROR", "[SERVER]: The remote host forcibly terminated the existing connection!")
            conn.close()
        except Exception as e:
            print(e)

    def Controlling(self):
        new_conn = socket.socket()
        new_conn.bind((ADDR, 13131))
        new_conn.listen()
        conn, addr = new_conn.accept()

        def on_move(x, y):
            win_x, win_y = self.frameGeometry().x() + (
                    self.frameGeometry().width() - self.label.width()), self.frameGeometry().y() + (
                                   self.frameGeometry().height() - self.label.height())
            win_width, win_height = self.label.width(), self.label.height()
            if win_x <= x <= win_x + win_width and win_y <= y <= win_y + win_height:
                x = x - win_x
                y = y - win_y
                command = str(['MOVE', x * scale_x, y * scale_y])
                conn.send(command.encode())
                conn.recv(256)
            # print('Pointer moved to {0}'.format((x, y)))

        def on_click(x, y, button, pressed):
            win_x, win_y = self.frameGeometry().x() + (
                    self.frameGeometry().width() - self.label.width()), self.frameGeometry().y() + (
                                   self.frameGeometry().height() - self.label.height())
            win_width, win_height = self.label.width(), self.label.height()
            if win_x <= x <= win_x + win_width and win_y <= y <= win_y + win_height:
                command = str(['CLICK' if pressed else 'RELEASE', str(button)])
                conn.send(command.encode())
                conn.recv(256)
            # print('{0} at {1} {2}'.format('Pressed' if pressed else 'Released',(x, y), button))

        def on_scroll(x, y, dx, dy):
            win_x, win_y = self.frameGeometry().x() + (
                    self.frameGeometry().width() - self.label.width()), self.frameGeometry().y() + (
                                   self.frameGeometry().height() - self.label.height())
            win_width, win_height = self.label.width(), self.label.height()
            if win_x <= x <= win_x + win_width and win_y <= y <= win_y + win_height:
                command = str(['SCROLL', dy])
                conn.send(command.encode())
                conn.recv(256)
            # print('Scrolled {0} at {1}'.format('down' if dy < 0 else 'up',(x, y)))

        listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        listener.start()

        def on_press(key):
            ms = mouse.Controller()
            x, y = ms.position
            win_x, win_y = self.frameGeometry().x() + (
                    self.frameGeometry().width() - self.label.width()), self.frameGeometry().y() + (
                                   self.frameGeometry().height() - self.label.height())
            win_width, win_height = self.label.width(), self.label.height()
            if win_x <= x <= win_x + win_width and win_y <= y <= win_y + win_height:
                command = str(['KEY', str(key)])
                conn.send(command.encode())
                conn.recv(256)

        listener = keyboard.Listener(on_press=on_press)
        listener.start()

    def initUI(self):
        global scale_x, scale_y
        try:
            print("[SERVER]: CONNECTED: {0}!".format(addr[0]))
            screenSize = conn.recv(64)
            print(screenSize)
            screenSize = screenSize.decode()
            self.setGeometry(win.GetSystemMetrics(0) // 4, win.GetSystemMetrics(0) // 4, eval(screenSize)[0] // scale_x,
                             eval(screenSize)[1] // scale_y)
            self.setFixedSize(self.width(), self.height())
            print(1)
            conn.send(b'1')
            self.pixmap = QPixmap()
            self.label = QLabel(self)
            self.label.resize(self.width(), self.height())
            self.setWindowTitle("[SERVER] Remote Desktop")
            # self.setGeometry(600, 200, 1920//scale_x, 1080//scale_y)
            self.screenSharing = Thread(target=self.ScreenSharing, daemon=True)
            self.screenSharing.start()
            self.controlling = Thread(target=self.Controlling, daemon=True)
            self.controlling.start()
        except ConnectionResetError:
            QMessageBox.about(self, "ERROR", "[SERVER]: The remote host forcibly terminated the existing connection!")
            conn.close()


def new_connection(conn_socket, address):
    if app_windows['main_window']:
        pass
    return


def listener():
    ADMIN = socket.socket()
    ADDR = '192.168.31.186'
    # ADDR = '192.168.31.101'
    # ADDR = '172.16.1.123'
    # ADDR = '172.16.5.148'
    ADMIN.bind((ADDR, 12121))
    ADMIN.listen()
    windows = {}

    scale_x, scale_y = 2, 2
    while True:
        try:
            conn, addr = ADMIN.accept()  # establish connection with client
            # threading between clients and server
            new_connection_thread = Thread(target=new_connection, args=(conn, addr), daemon=True)
            new_connection_thread.start()
        except OSError:
            sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    listener_thread = Thread(target=listener, daemon=True)
    listener_thread.start()
    # ex = Dekstop()
    # ex.show()
    sys.exit(app.exec())
