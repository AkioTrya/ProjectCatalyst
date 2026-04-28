import sqlite3
import os

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
    conn.commit()
    conn.close()
    print("Database initialized!")

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
