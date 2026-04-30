import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Path ke file database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'catalyst.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())
    # Migration: add role column to existing users tables that don't have it
    try:
        conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
        conn.commit()
        print("Migration: added 'role' column to users.")
    except Exception:
        pass  # Column already exists — safe to ignore
        
    # Auto-bootstrap first admin if table is empty
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    
    if count == 0:
        create_user('admin', 'admin123', 'admin')
        print("Auto-bootstrapped default admin account: admin / admin123")
        
    print("Database initialized!")

def create_user(username, password, role='user'):
    """Create a new user. role must be 'admin' or 'user'."""
    if role not in ('admin', 'user'):
        role = 'user'
    conn = get_connection()
    try:
        conn.execute(
            'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
            (username, generate_password_hash(password), role)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_all_users():
    """Return all users (id, username, role, created_at)."""
    conn = get_connection()
    users = conn.execute(
        "SELECT id, username, role, created_at FROM users ORDER BY created_at ASC"
    ).fetchall()
    conn.close()
    return users

def update_user_role(user_id, role):
    """Change the role of a user. role must be 'admin' or 'user'."""
    if role not in ('admin', 'user'):
        return False
    conn = get_connection()
    conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    conn.commit()
    conn.close()
    return True

def delete_user(user_id):
    """Permanently delete a user by id."""
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def update_user_password(user_id, new_password):
    """Reset a user's password (admin action)."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (generate_password_hash(new_password), user_id)
    )
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = get_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def verify_password(stored_hash, password):
    return check_password_hash(stored_hash, password)

def get_all_products():
    conn = get_connection()
    products = conn.execute(
        "SELECT * FROM products WHERE is_active = 1 ORDER BY name"
    ).fetchall()
    conn.close()
    return products

def add_product(name, price, unit):
    conn = get_connection()
    conn.execute(
        "INSERT INTO products (name, price, unit) VALUES (?, ?, ?)",
        (name, price, unit)
    )
    conn.commit()
    conn.close()

def get_all_orders():
    conn = get_connection()
    orders = conn.execute("""
        SELECT o.*, 
               COUNT(oi.id) as total_items,
               SUM(oi.quantity * oi.price) as total_harga
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        GROUP BY o.id
        ORDER BY o.created_at DESC
    """).fetchall()
    conn.close()
    return orders

def add_order(customer_name, customer_phone, order_date, pickup_date, payment_method, notes, items):
    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO orders 
        (customer_name, customer_phone, order_date, pickup_date, payment_method, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (customer_name, customer_phone, order_date, pickup_date, payment_method, notes))
    
    order_id = cursor.lastrowid
    
    for item in items:
        conn.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (order_id, item['product_id'], item['quantity'], item['price']))

    conn.commit()
    conn.close()
    return order_id
 
def delete_order(order_id):
    conn = get_connection()
    conn.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
    conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

def deactivate_product(product_id):
    conn = get_connection()
    conn.execute(
        "UPDATE products SET is_active = 0 WHERE id = ?",
        (product_id,)
    )
    conn.commit()
    conn.close()

def get_all_products_including_inactive():
    conn = get_connection()
    products = conn.execute(
        "SELECT * FROM products ORDER BY is_active DESC, name"
    ).fetchall()
    conn.close()
    return products

def activate_product(product_id):
    conn = get_connection()
    conn.execute(
        "UPDATE products SET is_active = 1 WHERE id = ?",
        (product_id,)
    )
    conn.commit()
    conn.close()

def get_all_expenses():
    conn = get_connection()
    expenses = conn.execute(
        "SELECT * FROM expenses ORDER BY date DESC"
    ).fetchall()
    conn.close()
    return expenses

def add_expense(category, description, amount, date):
    conn = get_connection()
    conn.execute(
        "INSERT INTO expenses (category, description, amount, date) VALUES (?, ?, ?, ?)",
        (category, description, amount, date)
    )
    conn.commit()
    conn.close()

def update_order_status(order_id, status):
    conn = get_connection()
    conn.execute(
        "UPDATE orders SET status = ? WHERE id = ?",
        (status, order_id)
    )
    conn.commit()
    conn.close()

def get_daily_summary(date):
    conn = get_connection()
    
    total_orders = conn.execute("""
        SELECT COUNT(*) as total_orders,
               SUM(oi.quantity * oi.price) as total_penjualan
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE o.order_date = ? AND o.status != 'cancelled'
    """, (date,)).fetchone()
    
    total_expenses = conn.execute("""
        SELECT SUM(amount) as total_pengeluaran
        FROM expenses
        WHERE date = ?
    """, (date,)).fetchone()
    
    conn.close()
    return total_orders, total_expenses

def get_top_products():
    conn = get_connection()
    products = conn.execute("""
        SELECT p.name,
               SUM(oi.quantity) as total_terjual,
               SUM(oi.quantity * oi.price) as total_pendapatan
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.status != 'cancelled'
        GROUP BY p.id
        ORDER BY total_terjual DESC
        LIMIT 5
    """).fetchall()
    conn.close()
    return products

def get_monthly_summary():
    conn = get_connection()
    summary = conn.execute("""
        SELECT o.order_date,
               COUNT(DISTINCT o.id) as total_order,
               SUM(oi.quantity * oi.price) as total_penjualan
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE o.status != 'cancelled'
        AND o.order_date >= DATE('now', '-30 days')
        GROUP BY o.order_date
        ORDER BY o.order_date ASC
    """).fetchall()
    conn.close()
    return summary

def get_all_ingredients():
    conn = get_connection()
    ingredients = conn.execute(
        "SELECT * FROM ingredients ORDER BY name"
    ).fetchall()
    conn.close()
    return ingredients

def add_ingredient(name, unit):
    conn = get_connection()
    conn.execute(
        "INSERT INTO ingredients (name, unit) VALUES (?, ?)",
        (name, unit)
    )
    conn.commit()
    conn.close()

def add_ingredient_price(ingredient_id, price, date, notes):
    conn = get_connection()
    conn.execute(
        "INSERT INTO ingredient_prices (ingredient_id, price, date, notes) VALUES (?, ?, ?, ?)",
        (ingredient_id, price, date, notes)
    )
    conn.commit()
    conn.close()

def get_ingredient_price_history():
    conn = get_connection()
    history = conn.execute("""
        SELECT i.name, i.unit, ip.price, ip.date, ip.notes
        FROM ingredient_prices ip
        JOIN ingredients i ON ip.ingredient_id = i.id
        ORDER BY ip.date DESC
    """).fetchall()
    conn.close()
    return history

def get_ingredient_prices_for_chart():
    conn = get_connection()
    ingredients = conn.execute("SELECT * FROM ingredients ORDER BY name").fetchall()
    
    chart_data = []
    for ingredient in ingredients:
        prices = conn.execute("""
            SELECT date, price FROM ingredient_prices
            WHERE ingredient_id = ?
            ORDER BY date ASC
        """, (ingredient['id'],)).fetchall()
        
        if prices:
            chart_data.append({
                'name': ingredient['name'],
                'dates': [p['date'] for p in prices],
                'prices': [p['price'] for p in prices]
            })
    conn.close()
    return chart_data

def add_ingredient_price(ingredient_id, price, date, notes):
    conn = get_connection()
    
    # Ambil nama ingredient dulu
    ingredient = conn.execute(
        "SELECT * FROM ingredients WHERE id = ?", 
        (ingredient_id,)
    ).fetchone()
    
    # Insert ke ingredient_prices
    conn.execute(
        "INSERT INTO ingredient_prices (ingredient_id, price, date, notes) VALUES (?, ?, ?, ?)",
        (ingredient_id, price, date, notes)
    )
    
    # Otomatis insert ke expenses juga
    conn.execute(
        "INSERT INTO expenses (category, description, amount, date) VALUES (?, ?, ?, ?)",
        ('bahan_baku', f"Beli {ingredient['name']}", price, date)
    )
    
    conn.commit()
    conn.close()

def add_payment(order_id, amount, payment_method, payment_type, notes, screenshot_path=None):
    conn = get_connection()
    conn.execute("""
        INSERT INTO payments (order_id, amount, payment_method, payment_type, notes, screenshot_path)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (order_id, amount, payment_method, payment_type, notes, screenshot_path))
    
    total_order = conn.execute("""
        SELECT SUM(quantity * price) as total
        FROM order_items WHERE order_id = ?
    """, (order_id,)).fetchone()['total']
    
    total_paid = conn.execute("""
        SELECT SUM(amount) as total
        FROM payments WHERE order_id = ?
    """, (order_id,)).fetchone()['total']
    
    if total_paid >= total_order:
        conn.execute("UPDATE orders SET payment_status = 'paid' WHERE id = ?", (order_id,))
    else:
        conn.execute("UPDATE orders SET payment_status = 'dp' WHERE id = ?", (order_id,))
    
    conn.commit()
    conn.close()

def upload_payment_screenshot(payment_id, screenshot_path):
    conn = get_connection()
    conn.execute(
        "UPDATE payments SET screenshot_path = ? WHERE id = ?",
        (screenshot_path, payment_id)
    )
    conn.commit()
    conn.close()

def get_payments_by_order(order_id):
    conn = get_connection()
    payments = conn.execute("""
        SELECT * FROM payments WHERE order_id = ?
        ORDER BY paid_at ASC
    """, (order_id,)).fetchall()
    conn.close()
    return payments

def get_product_by_id(product_id):
    conn = get_connection()
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()
    conn.close()
    return product

def update_product(product_id, name, price, unit):
    conn = get_connection()
    conn.execute(
        "UPDATE products SET name = ?, price = ?, unit = ? WHERE id = ?",
        (name, price, unit, product_id)
    )
    conn.commit()
    conn.close()

def get_order_by_id(order_id):
    conn = get_connection()
    order = conn.execute(
        "SELECT * FROM orders WHERE id = ?",
        (order_id,)
    ).fetchone()
    conn.close()
    return order

def update_order(order_id, customer_name, customer_phone, order_date, pickup_date, notes):
    conn = get_connection()
    conn.execute("""
        UPDATE orders 
        SET customer_name = ?, customer_phone = ?, 
            order_date = ?, pickup_date = ?, notes = ?
        WHERE id = ?
    """, (customer_name, customer_phone, order_date, pickup_date, notes, order_id))
    conn.commit()
    conn.close()

def get_order_detail(order_id):
    conn = get_connection()
    
    order = conn.execute(
        "SELECT * FROM orders WHERE id = ?",
        (order_id,)
    ).fetchone()
    
    items = conn.execute("""
        SELECT oi.*, p.name as product_name
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    """, (order_id,)).fetchall()
    
    payments = conn.execute(
        "SELECT * FROM payments WHERE order_id = ? ORDER BY paid_at ASC",
        (order_id,)
    ).fetchall()
    
    total_order = conn.execute("""
        SELECT SUM(quantity * price) as total
        FROM order_items WHERE order_id = ?
    """, (order_id,)).fetchone()['total']
    
    total_paid = conn.execute("""
        SELECT SUM(amount) as total
        FROM payments WHERE order_id = ?
    """, (order_id,)).fetchone()['total'] or 0
    
    conn.close()
    return order, items, payments, total_order, total_paid