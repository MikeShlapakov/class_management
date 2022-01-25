import sqlite3


def create_database():
    """
    Create a new database (if it doesn't exists already) with 2 Tables in it.
    Table "users" - userID, username, password, address
    :return: new database
    """
    with sqlite3.connect("./model/Database.db") as db:
        cursor = db.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
    userID INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    address TEXT);
    ''')
    # address - is user's address given when user connected
    db.commit()


# ---------------------------------------------------------------------------------------
# Working with user database
def sign_in(username, password, address):
    """
    Search the for the given user and log him into the server.
    input: 'Bob','1234','(10.1.1.0)'
    output: "Welcome to MyColab"
    :param username: user's name (string)
    :param password: user's password (string)
    :param address: user's address (stringed tuple)
    :return: message (string)
    """
    with sqlite3.connect("./model/Database.db") as db:
        cursor = db.cursor()
    # find user by name and password
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchall()
    if result:
        # if user already has address it means the user is already logged in
        if result[0][-1] is not None:
            return "This user is already in"
        # update user's address with given address
        cursor.execute('''UPDATE users SET address = ? WHERE username = ?''', (address, username))
        db.commit()
        return "Welcome to MyClass"
    else:
        return "Check your username or password"


def sign_up(username, password, address):
    """
    Search the for the given user and if there is no such user sign him up to the server.
    input: 'Bob','1234','(10.1.1.0)'
    output: "Welcome to MyColab"
    :param username: user's name (string)
    :param password: user's password (string)
    :param address: user's address (stringed tuple)
    :return: message (string)
    """
    with sqlite3.connect("./model/Database.db") as db:
        cursor = db.cursor()
    # find user with matching name
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    result = cursor.fetchall()
    if result:
        return "This user is already exists"
    else:
        # insert into users table new user
        cursor.execute(''' INSERT INTO users(username,password, address)
        VALUES(?,?,?)''', (username, password, address))
        db.commit()
        return "Welcome to MyColab"


def sign_out(address):
    """
    Sign out user with matching address (by deleting his address).
    input: '(10.1.1.0)'
    output: True/False
    :param address: user's address (stringed tuple)
    :return: True if success else False (bool)
    """
    with sqlite3.connect("./model/Database.db") as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE address = ?", (address,))
        user = cursor.fetchall()
        if user:
            cursor.execute("UPDATE users SET address = NULL WHERE username = ?", (user[0][1],))
            return True
    return False


def user_get(*args):
    """
    Find given var from users table with matching another var.
    input: ['username', 'address', '(10.1.1.0)']
    output: 'Bob'
    :param args: [needed_var, searched_var_type, searched_var] (list)
    :return: message (can be what you're searching for or an error) (string)
    """
    with sqlite3.connect("./model/Database.db") as db:
        cursor = db.cursor()
        cursor.execute(f"SELECT {args[0]} FROM users WHERE {args[1]} = ?", (args[2],))
        result = cursor.fetchall()
        if result:
            return result[0][0]
        else:
            return "This user doesn't exist"
