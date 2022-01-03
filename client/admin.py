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
    QSpacerItem, QVBoxLayout, QHBoxLayout, QWidgetItem, QSpacerItem, QTabWidget, QGridLayout, QFrame
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
        self.lock = threading.Lock()
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
        num = len(connections) - 1
        connections[addr].update({'comp': eval(f'self.comp{num}')})
        connections[addr]['comp'].setObjectName(f"comp{num}")

        connections[addr].update(
            {'screen_sharing_sock': socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)})
        port = get_open_port()
        connections[addr]['screen_sharing_sock'].bind((connections[addr]['conn'].getsockname()[0], port))
        msg_len = len(str(port))
        connections[addr]['conn'].send((str(msg_len) + ' ' * (64 - len(str(msg_len)))).encode())
        connections[addr]['conn'].send(str(port).encode())
        ScreenSharing = Thread(target=self.screen_sharing, args=(addr,), daemon=True)
        ScreenSharing.start()

        connections[addr].update({'control_sock': socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)})
        port = get_open_port()
        connections[addr]['control_sock'].bind((connections[addr]['conn'].getsockname()[0], port))
        msg_len = len(str(port))
        connections[addr]['conn'].send((str(msg_len) + ' ' * (64 - len(str(msg_len)))).encode())
        connections[addr]['conn'].send(str(port).encode())
        connections[addr].update({'control_thread': None})

        connections[addr].update({'handle_msg_sock': socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)})
        port = get_open_port()
        connections[addr]['handle_msg_sock'].bind((connections[addr]['conn'].getsockname()[0], port))
        connections[addr]['handle_msg_sock'].listen(1)
        msg_len = len(str(port))
        connections[addr]['conn'].send((str(msg_len) + ' ' * (64 - len(str(msg_len)))).encode())
        connections[addr]['conn'].send(str(port).encode())
        connections[addr].update({'handle_msg_conn': connections[addr]['handle_msg_sock'].accept()[0]})
        handle_msg = Thread(target=self.handle_client_msg, args=(addr,), daemon=True)
        handle_msg.start()
        connections[addr].update({'handle_msg_thread': handle_msg})

        self.group_view()

    def group_view(self):
        for addr in connections:
            num = eval(connections[addr]['comp'].objectName().strip('comp'))
            for row in range(self.row_limit):
                for column in range(self.column_limit):
                    if row * self.column_limit + column == num:
                        if 'tab_view' in windows:
                            label = UI.ComputerScreen(self.widget)
                            connections[addr]['comp'] = label
                            connections[addr]['comp'].setObjectName(f"comp{num}")
                            connections[addr]['comp'].setToolTip(f"{addr}\'s computer")
                            connections[addr]['comp'].setStyleSheet(u"QLabel{background-color: rgb(150, 150, 150);\n"
                                                                    u"border-radius: 5px;}\n"
                                                                    u"QLabel:hover{\n"
                                                                    u"border: 5px solid rgb(80, 180, 80);\n"
                                                                    u"border-radius: 5px;\n"
                                                                    u"}")
                            connections[addr]['comp'].setMinimumSize(QSize(240, 135))
                            connections[addr]['comp'].setMaximumSize(QSize(480, 270))
                            self.gridLayout_2.addWidget(connections[addr]['comp'], row, column, 1, 1)
                        else:
                            self.gridLayout_2.addWidget(connections[addr]['comp'], row, column, 1, 1)
                        connections[addr]['comp'].clicked.connect(self.tab_control)
        if 'tab_view' in windows:
            windows['main_window'].show()
            windows['tab_view'].close()
        print(connections)
        return

    def tab_control(self, event):
        """
        checks the action. if double-clicked on a screen: start to control it
        """
        # print(event)
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

    def screen_sharing(self, addr):
        conn = connections[addr]['screen_sharing_sock']
        # connections[addr]['comp'] = connections[addr]['comp']
        pixmap = QPixmap()
        screenSize, address = conn.recvfrom(64)
        print(screenSize)
        connections[addr].update({"size": eval(screenSize.decode())})
        conn.sendto(b'1', address)
        while True:
            try:
                img_len = conn.recv(16)
                img = b''
                while eval(img_len.decode()) == 50000:
                    conn.sendto(b'1', address)
                    img += conn.recv(eval(img_len.decode()))
                    print(f'1 {len(img)}')
                    if len(img) == 16:
                        print('break')
                        break
                    img_len = conn.recv(16)
                else:
                    img += conn.recv(eval(img_len.decode()))
                    if len(img) != eval(img_len.decode()):
                        continue
                    pixmap.loadFromData(img)
                    pixmap.scaled(connections[addr]['comp'].width(), connections[addr]['comp'].height(), Qt.KeepAspectRatio,
                                  Qt.SmoothTransformation)
                    connections[addr]['comp'].setScaledContents(True)
                    connections[addr]['comp'].setPixmap(QPixmap(pixmap))
                    connections[addr]['comp'].setAlignment(Qt.AlignCenter)

            except (ConnectionResetError, OSError):
                self.lock.acquire()
                try:
                    print(f"{addr} disconnected")
                    items = list(connections[addr].keys())
                    for item in items:
                        if item == "comp":
                            connections[addr][item].setParent(None)
                        elif item in ["conn", "screen_sharing_sock", "control_sock"]:
                            connections[addr][item].close()
                        elif item == 'control_thread':
                            if connections[addr][item]:
                                connections[addr][item]['thread'].join()
                                connections[addr][item]['mouse_listener'].stop()
                                connections[addr][item]['mouse_listener'].join()
                                connections[addr][item]['kb_listener'].stop()
                                connections[addr][item]['kb_listener'].join()
                                connections[addr][item] = None
                            connections[addr].pop(item)
                    connections.pop(addr)
                    self.lock.release()
                    break
                except KeyError:
                    break
            except Exception as e:
                print(e)
        print('done')

    def start_controlling(self, event):
        # print(f"start_controlling - {event}")
        # print(f"threads running - {threading.active_count()}")
        # print(f"connections - {connections}")
        try:
            if event['action'] == "Enter":
                for addr in connections:
                    self.lock.acquire()
                    try:
                        if connections[addr]['comp'].objectName() == event["name"]:
                            if connections[addr]['control_thread']:
                                self.lock.release()
                                return
                            self.tab_view.back_to_main_btn.disconnect()
                            Controlling = Thread(target=self.controlling, args=(addr,), daemon=True)
                            Controlling.start()
                            connections[addr]['control_thread'] = {'thread': Controlling}
                            self.lock.release()
                            return
                    except KeyError:
                        break
                    self.lock.release()
            if event['action'] == "Leave":
                self.lock.acquire()
                try:
                    for addr in connections:
                        if connections[addr]['comp'].objectName() == event["name"]:
                            connections[addr]['control_thread']['thread'].join()
                            connections[addr]['control_thread']['mouse_listener'].stop()
                            connections[addr]['control_thread']['mouse_listener'].join()
                            connections[addr]['control_thread']['kb_listener'].stop()
                            connections[addr]['control_thread']['kb_listener'].join()
                            connections[addr]['control_thread'] = None
                            self.tab_view.back_to_main_btn.clicked.connect(self.group_view)
                except KeyError:
                    pass
                self.lock.release()
        except TypeError:
            pass

    def controlling(self, addr):
        conn = connections[addr]['control_sock']
        address = (addr[0], connections[addr]['control_sock'].getsockname()[1])
        size = connections[addr]['size']
        # screen = connections[addr]['comp']

        def on_move(x, y):
            screen_x = self.tab_view.pos().x() + self.tab_view.tabWidget.pos().x() + 2
            screen_y = self.tab_view.pos().y() + self.tab_view.tabWidget.pos().y() + 60
            screen_width, screen_height = connections[addr]['comp'].width(), connections[addr]['comp'].height()
            width, height = size[0], size[1]
            x_ratio, y_ration = round(screen_width / width, 2), round(screen_height / height, 2)
            x = round((x - screen_x) / x_ratio)
            if x < 0 or width < x:
                x = 0 if x < 0 else width
            y = round((y - screen_y) / y_ration)
            if y < 0 or height < y:
                y = 0 if y < 0 else height
            command = str(['MOVE', x, y])
            conn.sendto(command.encode('utf-8').strip(), address)

        def on_click(x, y, button, pressed):
            command = str(['CLICK' if pressed else 'RELEASE', str(button)])
            conn.sendto(command.encode('utf-8').strip(), address)

        def on_scroll(x, y, dx, dy):
            command = str(['SCROLL', dy])
            conn.sendto(command.encode('utf-8').strip(), address)

        mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        mouse_listener.start()

        def on_press(key):
            command = str(['KEY', str(key)])
            conn.sendto(command.encode('utf-8').strip(), address)

        kb_listener = keyboard.Listener(on_press=on_press)
        kb_listener.start()

        connections[addr]['control_thread'].update({'mouse_listener': mouse_listener, 'kb_listener': kb_listener})

    def handle_client_msg(self, addr):
        while True:
            try:
                msg_len = connections[addr]['handle_msg_conn'].recv(64).decode()
                msg = connections[addr]['handle_msg_conn'].recv(eval(msg_len)).decode()
                if msg == "ALERT":
                    print(f"ALERT! ALERT! {addr} is trying to get control over the keyboard")
                    # self.alert_message(addr)
            except ConnectionResetError or OSError:
                self.lock.acquire()
                try:
                    print(f"{addr} disconnected")
                    items = list(connections[addr].keys())
                    for item in items:
                        if item == "comp":
                            connections[addr][item].setParent(None)
                        elif item in ["conn", "screen_sharing_sock", "control_sock"]:
                            connections[addr][item].close()
                        elif item == 'control_thread':
                            if connections[addr][item]:
                                connections[addr][item]['thread'].join()
                                connections[addr][item]['mouse_listener'].stop()
                                connections[addr][item]['mouse_listener'].join()
                                connections[addr][item]['kb_listener'].stop()
                                connections[addr][item]['kb_listener'].join()
                                connections[addr][item] = None
                            connections[addr].pop(item)
                    connections.pop(addr)
                except KeyError:
                    pass
                self.lock.release()
                break

    def alert_message(self, addr):
        # QMessageBox.about(QWidget(), "ALERT",
        #                   f"ALERT! ALERT! {addr} is trying to get control over the keyboard")
        # return
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText(f"{addr} is trying to take control over the keyboard")
        msg_box.setWindowTitle("ALERT")
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        result = msg_box.exec_()


def main():
    ADMIN = socket.socket()
    ADDR = '192.168.31.233'
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
