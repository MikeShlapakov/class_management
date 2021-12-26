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
connections = {}


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

class MainWindow(UI.MainWindow_UI):
    def __init__(self, socket):
        super(MainWindow, self).__init__()
        self.sock = socket

        self.column_limit = 2
        self.row_limit = 2
        listener_thread = Thread(target=self.listener, daemon=True)
        listener_thread.start()
    def listener(self):
        while True:
            try:
                self.conn, addr = self.sock.accept()  # establish connection with client
                # threading between clients and server
                new_connection_thread = Thread(target=self.new_connection, daemon=True)
                new_connection_thread.start()
            except OSError:
                sys.exit()

    def new_connection(self):
        global connections
        print(f'{self.conn.getpeername()[0]} connected to the server')
        comp_num = len(connections)
        connections[f"comp{comp_num}"] = [self.conn.getpeername()[0]]
        connections[f"comp{comp_num}"].append(eval(f'self.comp{comp_num}'))
        connections[f"comp{comp_num}"][1].setObjectName(f"comp{comp_num}")
        connections[f"comp{comp_num}"][1].setToolTip(f"{self.conn.getpeername()[0]}'s computer")
        connections[f"comp{comp_num}"][1].setStyleSheet(u"QLabel{background-color: rgb(150, 150, 150);\n"
                                                        u"border-radius: 5px;}\n"
                                                        u"QLabel:hover{\n"
                                                        u"border: 5px solid rgb(80, 180, 80);\n"
                                                        u"border-radius: 5px;\n"
                                                        u"}")
        connections[f"comp{comp_num}"][1].clicked.connect(self.choose_monitor)


        column = 0
        row = 0
        i = 0
        while i < comp_num:
            if column == (self.column_limit-1):
                column = 0
                row += 1
            else:
                column += 1
            i += 1
        print(connections)
        print(row, column)
        self.gridLayout_2.addWidget(connections[f"comp{comp_num}"][1], row, column, 1, 1)

        self.screen_sharing_sock = socket.socket()
        screen_sharing_port = get_open_port()
        self.screen_sharing_sock.bind((self.conn.getsockname()[0], screen_sharing_port))
        self.screen_sharing_sock.listen()
        print((str(len(str(screen_sharing_port)))+' '*(64-len(str(len(str(screen_sharing_port)))))).encode())
        self.conn.send((str(len(str(screen_sharing_port)))+' '*(64-len(str(len(str(screen_sharing_port)))))).encode())
        self.conn.send(str(screen_sharing_port).encode())
        self.screen_sharing_conn, self.addr = self.screen_sharing_sock.accept()
        self.ScreenSharing = Thread(target=self.screen_sharing, args=(connections[f"comp{comp_num}"][1],), daemon=True)
        self.ScreenSharing.start()

        self.control_sock = socket.socket()
        control_port = get_open_port()
        self.control_sock.bind((self.conn.getsockname()[0], control_port))
        self.control_sock.listen()
        self.conn.send((str(len(str(control_port)))+' '*(64-len(str(len(str(control_port)))))).encode())
        self.conn.send(str(control_port).encode())
        self.control_conn, self.addr = self.control_sock.accept()
        return

    def screen_sharing(self, comp_screen):
        self.pixmap = QPixmap()
        self.screenSize = self.screen_sharing_conn.recv(64)
        print(self.screenSize)
        self.screen_sharing_conn.send(b'1')
        try:
            while True:
                img_len = self.screen_sharing_conn.recv(64)
                img = self.screen_sharing_conn.recv(eval(img_len.decode()))
                while len(img) != eval(img_len.decode()):
                    img += self.screen_sharing_conn.recv(eval(img_len.decode()) - len(img))
                self.pixmap.loadFromData(img)
                self.pixmap.scaled(comp_screen.width(), comp_screen.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                comp_screen.setScaledContents(True)
                comp_screen.setPixmap(QPixmap(self.pixmap))
                comp_screen.setAlignment(Qt.AlignCenter)

        except ConnectionResetError:
            QMessageBox.about(QWidget(), "ERROR",
                              "[SERVER]: The remote host forcibly terminated the existing self.connection!")
            self.screen_sharing_conn.close()
        except Exception as e:
            print(e)

    def choose_monitor(self, action):
        """
        checks the action. if double-clicked on a screen: start to control it
        """
        print(1)
        if action == "Double Click":
            if self.comp1.pixmap():
                self.Controlling = Thread(target=self.controlling,args=(connections[f"comp{4}"][1],), daemon=True)
                self.Controlling.start()
            else:
                print("you cant connect to this computer")

    def controlling(self):
        scale_x, scale_y = 2, 2

        def on_move(x, y):
            win_x, win_y = self.frameGeometry().x() + (
                    self.frameGeometry().width() - self.label.width()), self.frameGeometry().y() + (
                                   self.frameGeometry().height() - self.label.height())
            win_width, win_height = self.label.width(), self.label.height()
            if win_x <= x <= win_x + win_width and win_y <= y <= win_y + win_height:
                x = x - win_x
                y = y - win_y
                command = str(['MOVE', x * scale_x, y * scale_y])
                self.new_conn.send(command.encode())
                self.new_conn.recv(256)
            # print('Pointer moved to {0}'.format((x, y)))

        def on_click(x, y, button, pressed):
            win_x, win_y = self.frameGeometry().x() + (
                    self.frameGeometry().width() - self.label.width()), self.frameGeometry().y() + (
                                   self.frameGeometry().height() - self.label.height())
            win_width, win_height = self.label.width(), self.label.height()
            if win_x <= x <= win_x + win_width and win_y <= y <= win_y + win_height:
                command = str(['CLICK' if pressed else 'RELEASE', str(button)])
                self.new_conn.send(command.encode())
                self.new_conn.recv(256)
            # print('{0} at {1} {2}'.format('Pressed' if pressed else 'Released',(x, y), button))

        def on_scroll(x, y, dx, dy):
            win_x, win_y = self.frameGeometry().x() + (
                    self.frameGeometry().width() - self.label.width()), self.frameGeometry().y() + (
                                   self.frameGeometry().height() - self.label.height())
            win_width, win_height = self.label.width(), self.label.height()
            if win_x <= x <= win_x + win_width and win_y <= y <= win_y + win_height:
                command = str(['SCROLL', dy])
                self.new_conn.send(command.encode())
                self.new_conn.recv(256)
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
                self.new_conn.send(command.encode())
                self.new_conn.recv(256)

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
            QMessageBox.about(self, "ERROR",
                              "[SERVER]: The remote host forcibly terminated the existing self.connection!")
            self.conn.close()


def main():
    ADMIN = socket.socket()
    ADDR = '192.168.31.149'
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
