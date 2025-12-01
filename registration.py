import bcrypt
from getpass import getpass

def register_user():
    username = input("Enter username: ")
    password = getpass("Enter password: ")
    
    # Hash the password using bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Store the hashed password in your database (mocked here as a dictionary)
    users_db = {}
    users_db[username] = hashed_password
    print(f"User {username} registered successfully!")
    return users_db

def login_user(users_db):
    username = input("Enter username: ")
    password = getpass("Enter password: ")

    # Check if user exists and verify password
    if username in users_db and bcrypt.checkpw(password.encode('utf-8'), users_db[username]):
        print("Login successful!")
        return True
    else:
        print("Login failed!")
        return False
