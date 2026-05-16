import sqlite3
import os

DB_PATH = 'enterprise.db'

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE employees (
            emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            department TEXT,
            salary INTEGER
        )
    ''')
    
    employees = [
        ('John Doe', 'Engineering', 95000),
        ('Jane Smith', 'Security', 120000),
        ('Admin User', 'System', 0)
    ]
    
    c.executemany('INSERT INTO employees (full_name, department, salary) VALUES (?, ?, ?)', employees)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
