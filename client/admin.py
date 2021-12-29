import socket
import io
import threading
from pynput import mouse, keyboard
from threading import Thread
import time
import win32api as win
import numpy
# PyQt5
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QPushButton, QAction, QMessageBox, QSizePolicy, \
    QSpacerItem, QVBoxLayout, QHBoxLayout, QWidgetItem, QSpacerItem, QTabWidget
from PyQt5.QtGui import QPixmap, QImage, QFont, QCursor
from PyQt5.QtCore import QRect, Qt, QSize
from client_ui import client_ui as UI

windows = {}
connections = {}  # {'addr': {'conn': conn,'comp_num':Computer}]}


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
                conn, addr = self.sock.accept()  # establish connection with client
                # threading between clients and server
                connections[addr] = {'conn': conn}
                new_connection_thread = Thread(target=self.new_connection, args=(addr,), daemon=True)
                new_connection_thread.start()
            except OSError:
                sys.exit()

    def new_connection(self, addr):
        global connections
        print(f'{addr} connected to the server')
        comp_num = len(connections)
        connections[addr].update({'comp': eval(f'self.comp{comp_num}')})
        connections[addr]['comp'].setObjectName(f"comp{comp_num}")
        connections[addr]['comp'].setToolTip(f"{addr}\'s computer")
        connections[addr]['comp'].setStyleSheet(u"QLabel{background-color: rgb(150, 150, 150);\n"
                                                u"border-radius: 5px;}\n"
                                                u"QLabel:hover{\n"
                                                u"border: 5px solid rgb(80, 180, 80);\n"
                                                u"border-radius: 5px;\n"
                                                u"}")
        connections[addr]['comp'].clicked.connect(self.tab_control)

        def get_position(num):
            for i in range(self.row_limit):
                for j in range(self.column_limit):
                    if i * self.column_limit + j == num:
                        return i, j

        row, column = get_position(comp_num - 1)
        self.gridLayout_2.addWidget(connections[addr]['comp'], row, column, 1, 1)
        print(connections)

        connections[addr].update({'screen_sharing_sock': socket.socket()})
        screen_sharing_port = get_open_port()
        connections[addr]['screen_sharing_sock'].bind((connections[addr]['conn'].getsockname()[0], screen_sharing_port))
        connections[addr]['screen_sharing_sock'].listen(1)
        msg_len = len(str(screen_sharing_port))
        connections[addr]['conn'].send((str(msg_len) + ' ' * (64 - len(str(msg_len)))).encode())
        connections[addr]['conn'].send(str(screen_sharing_port).encode())
        screen_sharing_conn = connections[addr]['screen_sharing_sock'].accept()[0]
        connections[addr].update({'screen_sharing_conn': screen_sharing_conn})
        ScreenSharing = Thread(target=self.screen_sharing, args=(addr,), daemon=True)
        ScreenSharing.start()

        connections[addr].update({'control_sock': socket.socket()})
        control_port = get_open_port()
        connections[addr]['control_sock'].bind((connections[addr]['conn'].getsockname()[0], control_port))
        connections[addr]['control_sock'].listen(1)
        connections[addr]['conn'].send(
            (str(len(str(control_port))) + ' ' * (64 - len(str(len(str(control_port)))))).encode())
        connections[addr]['conn'].send(str(control_port).encode())
        control_conn = connections[addr]['control_sock'].accept()[0]
        connections[addr].update({'control_conn': control_conn})

        connections[addr].update({'control_thread': None})
        return

    def screen_sharing(self, addr):
        conn = connections[addr]['screen_sharing_conn']
        comp_screen = connections[addr]['comp']
        pixmap = QPixmap()
        screenSize = conn.recv(64).decode()
        print(screenSize)
        connections[addr].update({"size": eval(screenSize)})
        conn.send(b'1')
        try:
            while True:
                img_len = conn.recv(64)
                img = conn.recv(eval(img_len.decode()))
                while len(img) != eval(img_len.decode()):
                    img += conn.recv(eval(img_len.decode()) - len(img))
                pixmap.loadFromData(img)
                pixmap.scaled(comp_screen.width(), comp_screen.height(), Qt.KeepAspectRatio,
                              Qt.SmoothTransformation)
                comp_screen.setScaledContents(True)
                comp_screen.setPixmap(QPixmap(pixmap))
                comp_screen.setAlignment(Qt.AlignCenter)

        except ConnectionResetError:
            print(f"{addr} disconnected")
            items = list(connections[addr].keys())
            for item in items:
                if item == "comp":
                    connections[addr][item].setParent(None)
                elif item in ["conn", "screen_sharing_sock", "screen_sharing_conn", "control_sock", "control_conn"]:
                    connections[addr][item].close()
                connections[addr].pop(item)
            connections.pop(addr)
        except Exception as e:
            print(e)

    def tab_control(self, event):
        """
        checks the action. if double-clicked on a screen: start to control it
        """
        print(event)
        if event['action'] == "Double Click":
            for addr in connections:
                if connections[addr]['comp'].objectName() == event['name']:
                    if connections[addr]['comp'].pixmap():
                        self.tab_view = UI.TabView_UI()
                        for address in connections:
                            self.tab_view.tabWidget.addTab(connections[address]['comp'], f'{address}')
                            connections[address]['comp'].disconnect()
                            connections[address]['comp'].setMaximumSize(QSize(10000, 10000))
                            connections[address]['comp'].clicked.connect(self.start_controlling)
                        windows['tab_view'] = self.tab_view
                        windows['tab_view'].show()
                        windows['main_window'].close()
                    else:
                        print("you cant connect to this computer")

    def start_controlling(self, event):
        # print(f"start_controlling - {event}")
        # print(f"threads running - {threading.active_count()}")
        # print(f"connections - {connections}")
        if event['action'] == "Enter":
            for addr in connections:
                if connections[addr]['comp'].objectName() == event["name"]:
                    if connections[addr]['control_thread']:
                        return
                    Controlling = Thread(target=self.controlling, args=(addr,), daemon=True)
                    Controlling.start()
                    connections[addr]['control_thread'] = {'thread': Controlling}
                    return
        if event['action'] == "Leave":
            for addr in connections:
                if connections[addr]['comp'].objectName() == event["name"]:
                    connections[addr]['control_thread']['thread'].join()
                    connections[addr]['control_thread']['mouse_listener'].stop()
                    connections[addr]['control_thread']['mouse_listener'].join()
                    connections[addr]['control_thread']['kb_listener'].stop()
                    connections[addr]['control_thread']['kb_listener'].join()
                    connections[addr]['control_thread'] = None

    def controlling(self, addr):
        conn = connections[addr]['control_conn']
        size = connections[addr]['size']
        screen = connections[addr]['comp']

        def on_move(x, y):
            screen_x = self.tab_view.pos().x() + self.tab_view.tabWidget.pos().x() + 2
            screen_y = self.tab_view.pos().y() + self.tab_view.tabWidget.pos().y() + 60
            screen_width, screen_height = screen.width(), screen.height()
            width, height = size[0], size[1]
            x_ratio, y_ration = round(screen_width / width, 2), round(screen_height / height, 2)
            x = round((x - screen_x) / x_ratio)
            if x < 0 or width < x:
                x = 0 if x < 0 else width
            y = round((y - screen_y) / y_ration)
            if y < 0 or height < y:
                y = 0 if y < 0 else height
            command = str(['MOVE', x, y])
            conn.send(command.encode('utf-8').strip())
            conn.recv(256)

        def on_click(x, y, button, pressed):
            command = str(['CLICK' if pressed else 'RELEASE', str(button)])
            conn.send(command.encode('utf-8').strip())
            conn.recv(256)

        def on_scroll(x, y, dx, dy):
            command = str(['SCROLL', dy])
            conn.send(command.encode('utf-8').strip())
            conn.recv(256)

        mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        mouse_listener.start()

        def on_press(key):
            command = str(['KEY', str(key)])
            conn.send(command.encode('utf-8').strip())
            conn.recv(256)

        kb_listener = keyboard.Listener(on_press=on_press)
        kb_listener.start()

        connections[addr]['control_thread'].update({'mouse_listener': mouse_listener, 'kb_listener': kb_listener})


def main():
    ADMIN = socket.socket()
    ADDR = '192.168.31.168'
    # ADDR = '192.168.31.101'
    # ADDR = '172.16.1.123'
    # ADDR = '172.16.5.148'
    ADMIN.bind((ADDR, 12121))
    ADMIN.listen()
    global windows
    # window = QMainWindow()
    main_window = MainWindow(ADMIN)
    windows['main_window'] = main_window
    main_window.show()
    print(windows)

    # main_window.setupUi(window)
    # window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # listener_thread = Thread(target=listen
    main()
    sys.exit(app.exec_())
