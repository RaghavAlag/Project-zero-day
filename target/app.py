import flask
import sqlite3
import os
import subprocess
import database

app = flask.Flask(__name__)

# Initialize DB on startup
database.init_db()

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET'])
def index():
    return """
    <html>
        <head><title>Project Zero-Day Arena</title></head>
        <body>
            <h1>Project Zero-Day Arena</h1>
            <p>Welcome to the testing arena. Below are the available endpoints.</p>
            
            <h2>Admin Login Portal</h2>
            <form action="/login" method="POST" id="login-form">
                <input type="text" name="username" placeholder="Username" />
                <input type="password" name="password" placeholder="Password" />
                <button type="submit">Login</button>
            </form>
            
            <h2>Network Diagnostics Utility</h2>
            <form action="/ping" method="POST" id="ping-form">
                <input type="text" name="host" placeholder="Hostname or IP Address" />
                <button type="submit">Ping Host</button>
            </form>
        </body>
    </html>
    """

@app.route('/login', methods=['POST'])
def login():
    data = flask.request.json if flask.request.is_json else flask.request.form
    if not data:
        data = {}
    username = data.get('username', '')
    password = data.get('password', '')
    
    query = "SELECT * FROM users WHERE username=? AND password=?"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, (username, password))
        rows = cursor.fetchall()
        conn.close()
        if rows:
            users = [dict(row) for row in rows]
            return flask.jsonify({"status": "success", "user": users})
        else:
            return flask.jsonify({"status": "fail"})
    except Exception as e:
        conn.close()
        return flask.jsonify({"status": "error", "message": str(e)})

@app.route('/ping', methods=['POST'])
def ping():
    data = flask.request.json if flask.request.is_json else flask.request.form
    if not data:
        data = {}
    host = data.get('host', '')
    
    if not host:
        return flask.jsonify({"status": "error", "message": "Host is required"})
    
    try:
        output = subprocess.check_output(["ping", "-c", "1", host]).decode("utf-8")
        return flask.jsonify({"output": output})
    except subprocess.CalledProcessError as e:
        return flask.jsonify({"status": "error", "message": str(e)})
    except Exception as e:
        return flask.jsonify({"status": "error", "message": str(e)})

@app.route('/health', methods=['GET'])
def health():
    return flask.jsonify({"status": "alive"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)