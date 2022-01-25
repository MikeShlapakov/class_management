from socket import *
import json
import threading
import time
import datetime
from model.server_model import *
import os


def send_msg(conn, type="", *args):
    """
    Send message to client
    :param conn: client socket (socket)
    :param msg: message (string)
    :return: sent the message (True/False)
    """
    global BUFSIZE, conn_list
    msg = {'type': type}
    msg_len = len(json.dumps(msg.encode()))
    try:
        conn.send((str(msg_len) + ' ' * (BUFSIZE - len(str(msg_len)))).encode())
        conn.send(msg.encode())
    except ConnectionResetError:
        print(f"{conn} left")
        return False
    except ConnectionAbortedError:
        print(f"{conn} left")
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
        return False
    except ConnectionAbortedError:
        return False
    return json.loads(msg)


def login(command, conn, vars):
    """
    The controller of the server.
    Gets message from the client and directs to the command function
    :param command: func to execute (string)
    :param conn: client socket (socket)
    :param vars: ['username','password'] (list)
    :return: noting
    """
    username = vars[0]
    password = vars[1]
    addr = conn.getpeername()
    msg = str(sign_in(username, password, str(addr))) if command == "sign_in" \
        else str(sign_up(username, password, str(addr)))
    send_msg(conn, msg)
    if msg == "Welcome to MyColab":
        send_msg(conn, str(temp_socket.getsockname()))
        temp_conn, temp_addr = temp_socket.accept()
        conn_list[conn] = temp_conn


def new_connection(conn, addr):
    """
    The controller of the server.
    Gets message from the client and directs to the command function
    :param conn: client socket (socket)
    :param addr: client address (stringed tuple)
    :return: noting
    """
    global SERVER, conn_list, temp_socket, projects
    # SERVER - server socket, conn_list - connection list(dict)
    print(f"{addr} connected to the server")
    conn_list[conn] = False  # add connection to the list
    while True:
        msg = get_msg(conn)
        if not msg:
            break

        print(f'{addr}: {msg}')

        commands = {'signin': lambda x: sign_in(msg['data'])}
        if msg['type'] == 'command':
            if msg['command'] in ['signin', 'signup']:
                sign_in(msg['data'])


    # signout(str(addr))
    conn_list.pop(conn)  # remove connection from the list
    conn.close()
    print(f"{addr} left the server")


if __name__ == '__main__':
    SERVER = socket()
    ADDR = '192.168.31.244'
    # ADDR = '192.168.31.101'
    # ADDR = '172.16.1.123'
    # ADDR = '172.16.5.148'
    SERVER.bind((ADDR, 12121))
    BUFSIZE = 64  # Buffer size
    SERVER.listen(5)
    conn_list = {}  # A dictionary of connections (clients) with a var that represent if the client has chat
    # create_database()
    # signup("admin", '1234', None)
    print(f"Hello world! My name is {ADDR} and I'm ready to get clients")
    while True:
        try:
            conn, addr = SERVER.accept()  # establish connection with client
            # threading between clients and server
            new_connection_thread = threading.Thread(target=new_connection, args=(conn, addr), daemon=True)
            new_connection_thread.start()
        except OSError:
            exit()
