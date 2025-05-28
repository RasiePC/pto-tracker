from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'pto_tracker.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            hire_date TEXT NOT NULL,
            pto_used REAL DEFAULT 0,
            sick_used REAL DEFAULT 0
        )
        ''')
        conn.commit()

@app.route('/')
def index():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM employees")
        employees = c.fetchall()
    today = datetime.today()
    def calculate_accrual(hire_date):
        hire_date = datetime.strptime(hire_date, '%Y-%m-%d')
        periods = max(0, (today.year - hire_date.year) * 24 + (today.month - hire_date.month) * 2)
        periods = min(periods, 24)
        return round(min(periods * 1.25, 30), 2), round(min(periods * 0.75, 18), 2)
    processed = []
    for emp in employees:
        pto_acc, sick_acc = calculate_accrual(emp[2])
        processed.append({
            'id': emp[0],
            'name': emp[1],
            'hire_date': emp[2],
            'pto_used': emp[3],
            'pto_balance': round(pto_acc - emp[3], 2),
            'sick_used': emp[4],
            'sick_balance': round(sick_acc - emp[4], 2)
        })
    return render_template('index.html', employees=processed)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['logged_in'] = True
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    hire_date = request.form['hire_date']
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO employees (name, hire_date) VALUES (?, ?)", (name, hire_date))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/update/<int:emp_id>', methods=['POST'])
def update(emp_id):
    pto_used = float(request.form['pto_used'])
    sick_used = float(request.form['sick_used'])
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("UPDATE employees SET pto_used=?, sick_used=? WHERE id=?", (pto_used, sick_used, emp_id))
        conn.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)