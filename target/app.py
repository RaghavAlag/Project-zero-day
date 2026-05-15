from flask import Flask, request, jsonify
import sqlite3
import os
import database

app = Flask(__name__)

# Initialize DB on startup
database.init_db()

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET'])
def index():
    return "<h1>Project Zero-Day Arena</h1><p>Login or Ping.</p>"

@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username', '')
    password = data.get('password', '')
    
    # INTENTIONAL SQL INJECTION VULNERABILITY
    query = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            # On success, return the full table dump
            users = [dict(row) for row in rows]
            return jsonify({"status": "success", "user": users})
        else:
            return jsonify({"status": "fail"})
    except Exception as e:
        conn.close()
        return jsonify({"status": "error", "message": str(e)})

@app.route('/ping', methods=['POST'])
def ping():
    data = request.json or {}
    host = data.get('host', '')
    
    # INTENTIONAL COMMAND INJECTION VULNERABILITY
    command = "ping -n 1 " + host
    output = os.popen(command).read()
    
    return jsonify({"output": output})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "alive"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
