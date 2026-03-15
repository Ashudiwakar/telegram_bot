import sqlite3
from datetime import datetime

DB_NAME = "bot_database.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            balance REAL DEFAULT 0.0,
            total_spent REAL DEFAULT 0.0,
            join_date TEXT DEFAULT ''
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS gmail_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            is_sold INTEGER DEFAULT 0,
            sold_to INTEGER DEFAULT 0,
            added_date TEXT DEFAULT '',
            sold_date TEXT DEFAULT ''
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS pending_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT '',
            approved_at TEXT DEFAULT ''
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS purchase_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            gmail_count INTEGER NOT NULL,
            purchase_date TEXT DEFAULT ''
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")


def register_user(user_id, username, first_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO users 
        (user_id, username, first_name, balance, join_date)
        VALUES (?, ?, ?, 0.0, ?)
    ''', (user_id, username or '', first_name or '', 
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def get_balance(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT balance FROM users WHERE user_id = ?', 
              (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return row['balance']
    return 0.0


def add_balance(user_id, amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE users SET balance = balance + ? 
        WHERE user_id = ?
    ''', (amount, user_id))
    conn.commit()
    conn.close()


def set_balance(user_id, amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE users SET balance = ? 
        WHERE user_id = ?
    ''', (amount, user_id))
    conn.commit()
    conn.close()


def deduct_balance(user_id, amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE users 
        SET balance = balance - ?, total_spent = total_spent + ?
        WHERE user_id = ?
    ''', (amount, amount, user_id))
    conn.commit()
    conn.close()


def get_available_gmails(count):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT id, email, password FROM gmail_stock 
        WHERE is_sold = 0 
        LIMIT ?
    ''', (count,))
    rows = c.fetchall()
    conn.close()
    return rows


def mark_gmail_sold(gmail_id, user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE gmail_stock 
        SET is_sold = 1, sold_to = ?, 
            sold_date = ?
        WHERE id = ?
    ''', (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
          gmail_id))
    conn.commit()
    conn.close()


def add_gmail_to_stock(email, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO gmail_stock (email, password, added_date)
        VALUES (?, ?, ?)
    ''', (email, password, 
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def get_stock_count():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(*) as count FROM gmail_stock 
        WHERE is_sold = 0
    ''')
    row = c.fetchone()
    conn.close()
    return row['count'] if row else 0


def create_payment_request(user_id, amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO pending_payments 
        (user_id, amount, status, created_at)
        VALUES (?, ?, 'pending', ?)
    ''', (user_id, amount, 
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    payment_id = c.lastrowid
    conn.commit()
    conn.close()
    return payment_id


def approve_payment(payment_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute('''
        SELECT user_id, amount, status FROM pending_payments 
        WHERE id = ?
    ''', (payment_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return None, "Payment ID not found!"

    if row['status'] != 'pending':
        conn.close()
        return None, "Payment already processed!"

    user_id = row['user_id']
    amount = row['amount']

    c.execute('''
        UPDATE pending_payments 
        SET status = 'approved', approved_at = ?
        WHERE id = ?
    ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
          payment_id))

    c.execute('''
        UPDATE users SET balance = balance + ? 
        WHERE user_id = ?
    ''', (amount, user_id))

    conn.commit()
    conn.close()
    return user_id, amount


def reject_payment(payment_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute('''
        SELECT user_id, amount, status FROM pending_payments 
        WHERE id = ?
    ''', (payment_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return None, "Payment ID not found!"

    if row['status'] != 'pending':
        conn.close()
        return None, "Payment already processed!"

    c.execute('''
        UPDATE pending_payments SET status = 'rejected' 
        WHERE id = ?
    ''', (payment_id,))

    conn.commit()
    conn.close()
    return row['user_id'], "rejected"


def add_purchase_history(user_id, amount, gmail_count):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO purchase_history 
        (user_id, amount, gmail_count, purchase_date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, amount, gmail_count,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users')
    rows = c.fetchall()
    conn.close()
    return rows


def get_pending_payments():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT p.*, u.username, u.first_name 
        FROM pending_payments p
        JOIN users u ON p.user_id = u.user_id
        WHERE p.status = 'pending'
        ORDER BY p.created_at DESC
    ''')
    rows = c.fetchall()
    conn.close()
    return rows
