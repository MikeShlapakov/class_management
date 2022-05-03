from socket import *
import json
import threading
import time
import datetime
from model.server_model import *
import os


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
    msg_len = len(msg.encode())
    try:
        conn.send((str(msg_len) + ' ' * (BUFSIZE - len(str(msg_len)))).encode())
        conn.send(msg.encode())
    except (ConnectionAbortedError, ConnectionResetError, TimeoutError):
        print(f"{conn.getpeername()} left")
        return False
    print(f"sent {conn.getpeername()}: {msg}")
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
    except (ConnectionAbortedError, ConnectionResetError, TimeoutError):
        print(f"{conn.getpeername()} left")
        return False
    print(f"got {conn.getpeername()}: {msg}")
    return json.loads(msg)


def login(command, conn, username, password):
    """
    :param command: func to execute (string)
    :param conn: client socket (socket)
    :param vars: ['username','password'] (list)
    :return: noting
    """
    global conn_list
    addr = conn.getpeername()
    msg = str(sign_in(username, password, str(addr))) if command == "signin" \
        else str(sign_up(username, password, str(addr)))
    if msg == "Welcome to MyClass":
        send_msg(conn, 'message', msg=msg, priority=user_get('priority', 'address', str(addr)))
        conn_list[conn].update({'priority': user_get('priority', 'address', str(addr))})
        return
    send_msg(conn, 'error', msg=msg)
    return


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
    conn_list[conn] = {'connected_to_admin': False}  # add connection to the list
    while True:
        msg = get_msg(conn)
        if not msg:
            break

        print(f'{addr}: {msg}')

        commands = {'signin': lambda msg: login('signin', conn, msg['username'], msg['password']),
                    'signup': lambda msg: login('signup', conn, msg['username'], msg['password'])}

        if msg['type'] == 'command':
            func = commands[msg['command']](msg)
            # func()
            # if msg['command'] in ['signin', 'signup']:
            #     sign_in(msg['data'])
        if msg['type'] == 'message':
            if msg['msg'] == 'admin_connected':
                for connection in conn_list:
                    if connection == conn:
                        continue
                    if not conn_list[connection]['connected_to_admin']:
                        send_msg(conn, 'message', msg='client_connected', name=user_get('username', 'address', str(connection.getpeername())))
                        conn_list[connection]['connected_to_admin'] = True
                        send_msg(connection, 'message', msg='admin_connected', address=msg['address'], name=user_get('username', 'address', str(conn.getpeername())))
            if msg['msg'] == 'client_connected':
                for connection in conn_list:
                    if conn_list[connection].get('priority', 'none') == 'admin':
                        send_msg(connection, 'message', msg='client_connected', name=user_get('username', 'address', str(conn.getpeername())))
                        conn_list[conn]['connected_to_admin'] = True
                        send_msg(conn, 'message', msg='admin_connected', address=(connection.getpeername()[0], 13131), name=user_get('username', 'address', str(connection.getpeername())))
        if msg['type'] == 'chat':
            if msg.get('command'):
                pass
                if msg['command'] == 'broadcast':
                    pass
            else:
                #private message
                if msg.get('name'):
                    print(conn_list)
                    for connection in conn_list:
                        if user_get('username', 'address', str(connection.getpeername())) == msg['name']:
                            # print(msg['msg'])
                            send_msg(conn, 'chat', msg=f"YOU: {msg['msg']}", name=msg['name'])
                            send_msg(connection, 'chat', msg=f"{user_get('username', 'address', str(conn.getpeername()))}: {msg['msg']}", name=user_get('username', 'address', str(conn.getpeername())))


    sign_out(str(addr))
    if conn_list[conn].get('priority', 'none') == 'admin':
        for connection in conn_list:
            if connection == conn or not conn_list[connection]['connected_to_admin']:
                continue
            send_msg(connection, 'message', msg='admin_disconnected')
            conn_list[connection]['connected_to_admin'] = False
    elif conn_list[conn].get('priority', 'none') == 'client':
        for connection in conn_list:
            if conn_list[connection].get('priority', 'none') == 'admin':
                send_msg(connection, 'message', msg='client_disconnected', address=conn.getpeername())
    conn_list.pop(conn)  # remove connection from the list
    conn.close()


if __name__ == '__main__':
    SERVER = socket()
    ADDR = '192.168.31.208'
    # ADDR = '192.168.31.101'
    # ADDR = '172.16.1.23'
    # ADDR = '172.16.5.148'
    SERVER.bind((ADDR, 12121))
    BUFSIZE = 16  # Buffer size
    SERVER.listen(5)
    conn_list = {}  # A dictionary of connections (clients) with a var that represent if the client has chat
    create_database()
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
