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

windows = {}

class MainWindow(UI.MainWindow_UI):
    def __init__(self, socket):
        super().__init__()
        self.sock = socket
        # ui = UI.MainWindow_UI()
        # print(self)
        # ui.setupUi(self)

        listener_thread = Thread(target=self.listener, daemon=True)
        listener_thread.start()


    def listener(self):
        while True:
            try:
                self.conn, addr = self.sock.accept()  # establish connection with client
                # threading between clients and server
                new_connection_thread = Thread(target=self.new_connection, args=(self.conn, addr), daemon=True)
                new_connection_thread.start()
            except OSError:
                sys.exit()

    def new_connection(self, connection, address):
        print(f'{address} connected to the server')
        print(1)
        self.screenSharing = Thread(target=self.ScreenSharing, daemon=True)
        self.screenSharing.start()
        # self.controlling = Thread(target=self.Controlling, daemon=True)
        # self.controlling.start()
        return

    def ScreenSharing(self):
        self.pixmap = QPixmap()
        screenSize = self.conn.recv(64)
        print(screenSize)
        self.conn.send(b'1')
        try:
            # self.setGeometry(400, 200, eval(screenSize)[0] // scale_x, eval(screenSize)[1] // scale_y)
            while True:
                img_len = self.conn.recv(64)
                print(img_len)
                img = self.conn.recv(eval(img_len.decode()))
                while len(img) != eval(img_len.decode()):
                    img += self.conn.recv(eval(img_len.decode()) - len(img))
                # image = QImage(eval(img).data, eval(img).shape[1],eval(img).shape[0],eval(img).shape[1]*3,QImage.Format_RGB888)
                # self.conn.send(b'1')
                self.pixmap.loadFromData(img)
                print(1)
                self.label.setScaledContents(True)
                # self.label.resize(self.width(), self.height())
                self.label.setPixmap(QPixmap(self.pixmap))

        except ConnectionResetError:
            QMessageBox.about(self, "ERROR", "[SERVER]: The remote host forcibly terminated the existing self.connection!")
            self.conn.close()
        except Exception as e:
            print(e)

    def Controlling(self):
        scale_x, scale_y = 2, 2
        self.new_conn = socket.socket()
        print(self.conn.getpeername()[0])
        self.new_conn.bind((self.conn.getpeername()[0], 13131))
        self.new_conn.listen()
        new_conn, addr = self.new_conn.accept()

        def on_move(x, y):
            win_x, win_y = self.frameGeometry().x() + (
                    self.frameGeometry().width() - self.label.width()), self.frameGeometry().y() + (
                                   self.frameGeometry().height() - self.label.height())
            win_width, win_height = self.label.width(), self.label.height()
            if win_x <= x <= win_x + win_width and win_y <= y <= win_y + win_height:
                x = x - win_x
                y = y - win_y
                command = str(['MOVE', x * scale_x, y * scale_y])
                new_conn.send(command.encode())
                new_conn.recv(256)
            # print('Pointer moved to {0}'.format((x, y)))

        def on_click(x, y, button, pressed):
            win_x, win_y = self.frameGeometry().x() + (
                    self.frameGeometry().width() - self.label.width()), self.frameGeometry().y() + (
                                   self.frameGeometry().height() - self.label.height())
            win_width, win_height = self.label.width(), self.label.height()
            if win_x <= x <= win_x + win_width and win_y <= y <= win_y + win_height:
                command = str(['CLICK' if pressed else 'RELEASE', str(button)])
                new_conn.send(command.encode())
                new_conn.recv(256)
            # print('{0} at {1} {2}'.format('Pressed' if pressed else 'Released',(x, y), button))

        def on_scroll(x, y, dx, dy):
            win_x, win_y = self.frameGeometry().x() + (
                    self.frameGeometry().width() - self.label.width()), self.frameGeometry().y() + (
                                   self.frameGeometry().height() - self.label.height())
            win_width, win_height = self.label.width(), self.label.height()
            if win_x <= x <= win_x + win_width and win_y <= y <= win_y + win_height:
                command = str(['SCROLL', dy])
                new_conn.send(command.encode())
                new_conn.recv(256)
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
                new_conn.send(command.encode())
                new_conn.recv(256)

        listener = keyboard.Listener(on_press=on_press)
        listener.start()

    def initUI(self):
        global scale_x, scale_y
        try:
            print("[SERVER]: self.CONNECTED: {0}!".format(self.conn.getpeername()[0]))
            screenSize = self.conn.recv(64)
            print(screenSize)
            screenSize = screenSize.decode()
            self.setGeometry(win.GetSystemMetrics(0) // 4, win.GetSystemMetrics(0) // 4, eval(screenSize)[0] // scale_x,
                             eval(screenSize)[1] // scale_y)
            self.setFixedSize(self.width(), self.height())
            print(1)

            self.pixmap = QPixmap()
            self.label = QLabel(self)
            self.label.resize(self.width(), self.height())
            self.setWindowTitle("[SERVER] Remote Desktop")
            # self.setGeometry(600, 200, 1920//scale_x, 1080//scale_y)

        except self.ConnectionResetError:
            QMessageBox.about(self, "ERROR", "[SERVER]: The remote host forcibly terminated the existing self.connection!")
            self.conn.close()


def main():
    ADMIN = socket.socket()
    ADDR = '192.168.31.186'
    # ADDR = '192.168.31.101'
    # ADDR = '172.16.1.123'
    # ADDR = '172.16.5.148'
    ADMIN.bind((ADDR, 12121))
    ADMIN.listen()
    global windows
    window = QMainWindow()
    windows['main_window'] = window
    print(windows)
    main_window = MainWindow(ADMIN)
    main_window.setupUi(window)
    window.show()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    # listener_thread = Thread(target=listen
    main()
    sys.exit(app.exec_())