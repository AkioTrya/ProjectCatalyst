CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    price       REAL NOT NULL,
    unit        TEXT NOT NULL,
    is_active   INTEGER DEFAULT 1,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name   TEXT NOT NULL,
    customer_phone  TEXT,
    order_date      TEXT NOT NULL,
    pickup_date     TEXT,
    status          TEXT DEFAULT 'pending',
    payment_method  TEXT NOT NULL,
    payment_status  TEXT DEFAULT 'unpaid',
    notes           TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER NOT NULL,
    product_id  INTEGER NOT NULL,
    quantity    INTEGER NOT NULL,
    price       REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS payments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL,
    amount          REAL NOT NULL,
    payment_method  TEXT NOT NULL,
    payment_type    TEXT NOT NULL,
    paid_at         TEXT DEFAULT CURRENT_TIMESTAMP,
    notes           TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT NOT NULL,
    description TEXT NOT NULL,
    amount      REAL NOT NULL,
    date        TEXT NOT NULL,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);