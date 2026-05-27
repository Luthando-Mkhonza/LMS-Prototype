from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import init_db, get_db_connection
from werkzeug.security import check_password_hash
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your-secure-random-key-change-in-production"

init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'manager':
            flash("Access denied. Manager only.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            flash(f"Welcome {user['full_name']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    if session['role'] == 'employee':
        leaves = conn.execute("SELECT * FROM leave_requests WHERE employee_id = ? ORDER BY id DESC", (session['user_id'],)).fetchall()
    else:
        leaves = conn.execute("SELECT l.*, u.full_name FROM leave_requests l JOIN users u ON l.employee_id = u.id ORDER BY l.id DESC").fetchall()
    conn.close()
    return render_template('dashboard.html', leaves=leaves, role=session['role'])

@app.route('/apply', methods=['GET', 'POST'])
@login_required
def apply_leave():
    if session['role'] != 'employee':
        flash("Only employees can apply for leave", "warning")
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        leave_type = request.form['leave_type']
        reason = request.form['reason']
        # Input validation
        if not start_date or not end_date or not leave_type:
            flash("All fields are required", "danger")
            return redirect(url_for('apply_leave'))
        if datetime.strptime(start_date, '%Y-%m-%d') > datetime.strptime(end_date, '%Y-%m-%d'):
            flash("End date must be after start date", "danger")
            return redirect(url_for('apply_leave'))
        conn = get_db_connection()
        conn.execute("INSERT INTO leave_requests (employee_id, start_date, end_date, leave_type, reason) VALUES (?,?,?,?,?)",
                     (session['user_id'], start_date, end_date, leave_type, reason))
        conn.commit()
        conn.close()
        flash("Leave request submitted", "success")
        return redirect(url_for('dashboard'))
    return render_template('apply_leave.html')

@app.route('/approve/<int:leave_id>')
@login_required
@manager_required
def approve_leave(leave_id):
    conn = get_db_connection()
    conn.execute("UPDATE leave_requests SET status = 'approved' WHERE id = ?", (leave_id,))
    conn.commit()
    conn.close()
    flash("Leave request approved", "success")
    return redirect(url_for('dashboard'))

@app.route('/reject/<int:leave_id>')
@login_required
@manager_required
def reject_leave(leave_id):
    conn = get_db_connection()
    conn.execute("UPDATE leave_requests SET status = 'rejected' WHERE id = ?", (leave_id,))
    conn.commit()
    conn.close()
    flash("Leave request rejected", "warning")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)