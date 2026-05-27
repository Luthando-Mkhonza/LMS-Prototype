import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = "instance/lms.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    full_name TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS leave_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    leave_type TEXT NOT NULL,
                    reason TEXT,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY (employee_id) REFERENCES users (id))''')
    # Insert sample users (hashed passwords: "pass123")
    admin_pass = generate_password_hash("pass123")
    emp_pass = generate_password_hash("pass123")
    try:
        c.execute("INSERT INTO users (username, password, role, full_name) VALUES (?,?,?,?)",
                  ("john.employee", emp_pass, "employee", "John Doe"))
        c.execute("INSERT INTO users (username, password, role, full_name) VALUES (?,?,?,?)",
                  ("jane.manager", admin_pass, "manager", "Jane Smith"))
    except:
        pass  # already exists
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn