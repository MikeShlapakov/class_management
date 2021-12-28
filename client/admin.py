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
        connections[addr]['comp'].clicked.connect(self.choose_monitor)

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
        return

    def screen_sharing(self, addr):
        conn = connections[addr]['screen_sharing_conn']
        comp_screen = connections[addr]['comp']
        pixmap = QPixmap()
        screenSize = conn.recv(64).decode()
        print(screenSize)
        connections[addr].update({"size": screenSize})
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

    def choose_monitor(self, action):
        """
        checks the action. if double-clicked on a screen: start to control it
        """
        print(action)
        if action['action'] == "Double Click":
            for address in connections:
                if connections[address]['comp'].objectName() == action["name"]:
                    addr = address
                    break
            if connections[addr]['comp'].pixmap():
                layout = self.gridLayout
                for i in reversed(range(layout.count())):
                    item = layout.itemAt(i)
                    if isinstance(item, QWidgetItem):
                        print("widget" + str(item))
                        item.widget().close()
                        # or
                        # item.widget().setParent(None)
                    elif isinstance(item, QSpacerItem):
                        print("spacer " + str(item))
                        # no need to do extra stuff
                    else:
                        print("layout " + str(item))
                        self.clearLayout(item.layout())
                    # remove the item from layout
                    layout.removeItem(item)

                self.verticalLayout = QVBoxLayout()
                self.verticalLayout.setObjectName(u"verticalLayout")
                self.back_to_main_btn = QPushButton(self.centralwidget)
                self.back_to_main_btn.setObjectName(u"back_to_main_btn")
                self.back_to_main_btn.setFont(QFont("Calibri", 14, QFont.Bold))
                self.back_to_main_btn.setCursor(QCursor(Qt.PointingHandCursor))
                self.back_to_main_btn.setStyleSheet(u"QPushButton{border: 2px solid rgb(50, 50, 80);\n"
                                                    "border-radius: 5px;\n"
                                                    "color: rgb(30, 30, 40);\n"
                                                    "padding-left: 20px;\n"
                                                    "padding-right: 20px;\n"
                                                    "background-color: rgb(65, 65, 90);}"
                                                    "QPushButton:hover{border: 2px solid rgb(115, 115, 180);\n"
                                                    "color:rgb(180, 180, 180);\n"
                                                    "background-color: rgb(80, 80, 120);}")

                self.verticalLayout.addWidget(self.back_to_main_btn)

                self.tabWidget = UI.ComputerScreenTab(self.centralwidget)
                for address in connections:
                    self.tabWidget.addTab(connections[address]['comp'], f'{address}')
                self.tabWidget.clicked.connect(self.start_controlling)

                self.verticalLayout.addWidget(self.tabWidget)

                self.gridLayout.addLayout(self.verticalLayout, 1, 1, 1, 1)

                connections[addr]['comp'].disconnect()
                connections[addr]['comp'].setMaximumSize(QSize(10000, 10000))
            else:
                print("you cant connect to this computer")

    def start_controlling(self, action):
        print(f"start_controlling - {action}")
        print(f"threads running - {threading.active_count()}")
        print(f"connections - {connections}")
        for address in connections:
            if connections[address]['comp'].objectName() == action["name"]:
                addr = address
                break
            else:
                if connections[address]['control_thread']:
                    connections[address]['control_thread']['thread'].join()
                    connections[address]['control_thread']['mouse_listener'].stop()
                    connections[address]['control_thread']['mouse_listener'].join()
                    connections[address]['control_thread']['kb_listener'].stop()
                    connections[address]['control_thread']['kb_listener'].join()
                    connections[address]['control_thread'] = None

        Controlling = Thread(target=self.controlling, args=(addr,), daemon=True)
        Controlling.start()
        connections[addr].update({'control_thread': {'thread': Controlling}})

    def controlling(self, addr):
        conn = connections[addr]['control_conn']
        size = connections[addr]['size']

        def on_move(x, y):
            win_x, win_y = self.frameGeometry().x() + (
                    self.frameGeometry().width() - connections[addr]['comp'].width()), self.frameGeometry().y() + (
                                   self.frameGeometry().height() - connections[addr]['comp'].height())
            win_width, win_height = connections[addr]['comp'].width(), connections[addr]['comp'].height()
            if win_x <= x <= win_x + win_width and win_y <= y <= win_y + win_height:
                x = x - win_x
                y = y - win_y
                command = str(['MOVE', x, y])
                conn.send(command.encode('utf-8').strip())
                conn.recv(256)

        def on_click(x, y, button, pressed):
            win_x, win_y = self.frameGeometry().x() + (
                    self.frameGeometry().width() - connections[addr]['comp'].width()), self.frameGeometry().y() + (
                                   self.frameGeometry().height() - connections[addr]['comp'].height())
            win_width, win_height = connections[addr]['comp'].width(), connections[addr]['comp'].height()
            if win_x <= x <= win_x + win_width and win_y <= y <= win_y + win_height:
                command = str(['CLICK' if pressed else 'RELEASE', str(button)])
                conn.send(command.encode('utf-8').strip())
                conn.recv(256)

        def on_scroll(x, y, dx, dy):
            win_x, win_y = self.frameGeometry().x() + (
                    self.frameGeometry().width() - connections[addr]['comp'].width()), self.frameGeometry().y() + (
                                   self.frameGeometry().height() - connections[addr]['comp'].height())
            win_width, win_height = connections[addr]['comp'].width(), connections[addr]['comp'].height()
            if win_x <= x <= win_x + win_width and win_y <= y <= win_y + win_height:
                command = str(['SCROLL', dy])
                conn.send(command.encode('utf-8').strip())
                conn.recv(256)

        mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        mouse_listener.start()

        def on_press(key):
            ms = mouse.Controller()
            x, y = ms.position
            win_x, win_y = self.frameGeometry().x() + (
                    self.frameGeometry().width() - connections[addr]['comp'].width()), self.frameGeometry().y() + (
                                   self.frameGeometry().height() - connections[addr]['comp'].height())
            win_width, win_height = connections[addr]['comp'].width(), connections[addr]['comp'].height()
            if win_x <= x <= win_x + win_width and win_y <= y <= win_y + win_height:
                command = str(['KEY', str(key)])
                conn.send(command.encode('utf-8').strip())
                conn.recv(256)

        kb_listener = keyboard.Listener(on_press=on_press)
        kb_listener.start()

        connections[addr]['control_thread'].update({'mouse_listener': mouse_listener, 'kb_listener':kb_listener})


def main():
    ADMIN = socket.socket()
    ADDR = '192.168.31.156'
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
