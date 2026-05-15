import sqlite3
import os

DB_PATH = 'users.db'

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
            password TEXT
        )
    ''')
    
    users = [
        ('admin', 'admin@zeroday.local', 'supersecret123'),
        ('alice', 'alice@zeroday.local', 'hunter2'),
        ('bob', 'bob@zeroday.local', 'password')
    ]
    
    c.executemany('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', users)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
