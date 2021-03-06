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
    address TEXT,
    priority TEXT);
    ''')
    # address - is user's address given when user connected
    # priority - is user's priority (admin/client)

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS classes(
    classID INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    users TEXT);
    ''')
    # users - users who in the class
    db.commit()


# ---------------------------------------------------------------------------------------
# Working with user database
def sign_in(username, password, address, *args):
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
        if result[0][3] is not None:
            return "This user is already in"
        # update user's address with given address
        cursor.execute('''UPDATE users SET address = ? WHERE username = ?''', (address, username))
        db.commit()
        return "Welcome to MyClass"
    else:
        return "Check your username or password"


def sign_up(username, password, address, *args):
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
        cursor.execute(''' INSERT INTO users(username,password, address, priority)
        VALUES(?,?,?,?)''', (username, password, address, 'client'))
        db.commit()
        return "Welcome to MyClass"


def sign_out(address, *args):
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


def user_get(needed_var, searched_var_type, searched_var, *args):
    """
    Find given variable from users table with matching another variable.
    input: 'username', 'address', '(10.1.1.0)'
    output: 'Bob'
    :param needed_var: needed variable (string)
    :param searched_var_type: searched variable type (string)
    :param searched_var: searched variable (string)
    :return: message (can be what you're searching for or an error) (string)
    """
    with sqlite3.connect("./model/Database.db") as db:
        cursor = db.cursor()
        cursor.execute(f"SELECT {needed_var} FROM users WHERE {searched_var_type} = ?", (searched_var,))
        result = cursor.fetchall()
        if result:
            return result[0][0]
        else:
            return "This user doesn't exist"


def add_class(class_name, users):
    """
    Adds new class to classes table
    :param class_name: class name (string)
    :param users: users names whose in the class (list)
    :return: string
    """
    with sqlite3.connect("./model/Database.db") as db:
        cursor = db.cursor()
    # find user with matching name
    cursor.execute("SELECT address FROM users WHERE priority = ?", ('admin',))
    result = cursor.fetchall()
    if result:
        if result[0][0] is None:
            return "Admin offline"
        cursor.execute("SELECT * FROM classes WHERE name = ?", (class_name,))
        result = cursor.fetchall()
        if result:
            return "This class is already exist, try another name"
        # insert into classes table new class
        cursor.execute(''' INSERT INTO classes(name, users) VALUES(?,?)''', (class_name, users))
        db.commit()
        return f"Class {class_name} added"
    return "Something gone wrong. Can't find the admin in the system."


def delete_class(class_name):
    """
    Delete the class from classes table
    :param class_name: class name (string)
    :return: string
    """
    with sqlite3.connect("./model/Database.db") as db:
        cursor = db.cursor()

    # find project with matching name and password
    cursor.execute("SELECT * FROM classes WHERE name = ?", (class_name,))
    result = cursor.fetchall()
    if result:
        cursor.execute('''DELETE FROM classes WHERE name = ?''', (class_name,))
        db.commit()
        return "Class deleted successfully"
    return f"Couldn\'t find class named \"{class_name}\""


def add_user(class_name, user_name):
    """
    Adds new class to classes table
    :param class_name: class name (string)
    :param user_name: user's name (string)
    :return: string
    """
    with sqlite3.connect("./model/Database.db") as db:
        cursor = db.cursor()
    # find user with matching name
    cursor.execute("SELECT address FROM users WHERE priority = ?", ('admin',))
    result = cursor.fetchall()
    if result:
        if result[0][0] is None:
            return "Admin offline"
        cursor.execute("SELECT * FROM classes WHERE name = ?", (class_name,))
        result = cursor.fetchall()
        if result:
            users = eval(result[0][1])
            if user_name in users:
                return f"This user is already in this class"
            users.append(user_name)
            # insert into classes table new class
            cursor.execute('''UPDATE classes SET users = ? WHERE name = ?''', (str(users), class_name))
            db.commit()
            return f"User {user_name} added to {class_name}"
        return "Something gone wrong. Can't find the class in the system"
    return "Something gone wrong. Can't find the admin in the system."