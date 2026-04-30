from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps
from database.db import (
    init_db, get_all_products, add_product, get_all_orders, add_order,
    delete_order, deactivate_product, activate_product,
    get_all_products_including_inactive, get_all_expenses, add_expense,
    update_order_status, get_daily_summary, get_top_products, get_monthly_summary,
    get_all_ingredients, add_ingredient, add_ingredient_price,
    get_ingredient_price_history, get_ingredient_prices_for_chart,
    add_payment, get_payments_by_order, get_product_by_id, update_product,
    get_order_by_id, update_order, get_order_detail,
    get_user_by_username, get_user_by_id, create_user, verify_password,
    upload_payment_screenshot,
    # User management
    get_all_users, update_user_role, delete_user, update_user_password
)
import os
from werkzeug.utils import secure_filename

# ─── CONFIG ───

UPLOAD_FOLDER = os.path.join('static', 'uploads', 'payments')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)

# Generate and persist a stable secret key so sessions survive server restarts
_SECRET_KEY_FILE = os.path.join(os.path.dirname(__file__), 'secret.key')
if os.path.exists(_SECRET_KEY_FILE):
    with open(_SECRET_KEY_FILE, 'rb') as _f:
        app.secret_key = _f.read()
else:
    _key = os.urandom(32)
    with open(_SECRET_KEY_FILE, 'wb') as _f:
        _f.write(_key)
    app.secret_key = _key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Login dulu ya!'
login_manager.login_message_category = 'warning'

# ─── USER MODEL ───

class User(UserMixin):
    def __init__(self, id, username, password_hash, role='user'):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role

    @property
    def is_admin(self):
        return self.role == 'admin'

@login_manager.user_loader
def load_user(user_id):
    row = get_user_by_id(user_id)
    if row:
        return User(row['id'], row['username'], row['password_hash'], row['role'])
    return None

# ─── DECORATORS ───

def admin_required(f):
    """Restrict a route to admin users only. Returns 403 for staff."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

# ─── AUTH ───

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_row = get_user_by_username(username)
        if user_row and verify_password(user_row['password_hash'], password):
            user = User(user_row['id'], user_row['username'], user_row['password_hash'], user_row['role'])
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Username atau password salah.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Berhasil logout.', 'success')
    return redirect(url_for('login'))

# ─── MAIN ───

@app.route('/')
@login_required
def index():
    return render_template('index.html')

# ─── PRODUCTS ───

@app.route('/products')
@login_required
def products():
    all_products = get_all_products()
    return render_template('products.html', products=all_products)

@app.route('/products/add', methods=['POST'])
@admin_required
def add_product_route():
    name = request.form['name']
    price = request.form['price']
    unit = request.form['unit']
    add_product(name, float(price), unit)
    return redirect(url_for('products'))

@app.route('/products/manage')
@admin_required
def manage_products():
    all_products = get_all_products_including_inactive()
    return render_template('manage_products.html', products=all_products)

@app.route('/products/activate/<int:product_id>', methods=['POST'])
@admin_required
def activate_product_route(product_id):
    activate_product(product_id)
    return redirect(url_for('manage_products'))

@app.route('/products/deactivate/<int:product_id>', methods=['POST'])
@admin_required
def deactivate_product_route_manage(product_id):
    deactivate_product(product_id)
    return redirect(url_for('manage_products'))

@app.route('/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def deactivate_product_route(product_id):
    deactivate_product(product_id)
    return redirect(url_for('products'))

@app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product_page(product_id):
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        unit = request.form['unit']
        update_product(product_id, name, float(price), unit)
        return redirect(url_for('products'))
    product = get_product_by_id(product_id)
    return render_template('edit_product.html', product=product)

# ─── ORDERS ───

@app.route('/orders')
@login_required
def orders():
    all_orders = get_all_orders()
    all_products = get_all_products()
    return render_template('orders.html', orders=all_orders, products=all_products)

@app.route('/orders/add', methods=['POST'])
@login_required
def add_order_route():
    customer_name = request.form['customer_name']
    customer_phone = request.form['customer_phone']
    order_date = request.form['order_date']
    pickup_date = request.form['pickup_date']
    payment_method = 'pending'
    notes = request.form['notes']
    product_ids = request.form.getlist('product_id[]')
    quantities = request.form.getlist('quantity[]')
    items = []
    for i in range(len(product_ids)):
        if product_ids[i] and quantities[i]:
            product = next(p for p in get_all_products() if p['id'] == int(product_ids[i]))
            items.append({
                'product_id': int(product_ids[i]),
                'quantity': int(quantities[i]),
                'price': product['price']
            })
    add_order(customer_name, customer_phone, order_date, pickup_date, payment_method, notes, items)
    return redirect(url_for('orders'))

@app.route('/orders/delete/<int:order_id>', methods=['POST'])
@admin_required
def delete_order_route(order_id):
    delete_order(order_id)
    return redirect(url_for('orders'))

@app.route('/orders/status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status_route(order_id):
    status = request.form['status']
    update_order_status(order_id, status)
    return redirect(url_for('orders'))

@app.route('/orders/edit/<int:order_id>', methods=['GET', 'POST'])
@login_required
def edit_order_page(order_id):
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        customer_phone = request.form['customer_phone']
        order_date = request.form['order_date']
        pickup_date = request.form['pickup_date']
        notes = request.form['notes']
        update_order(order_id, customer_name, customer_phone, order_date, pickup_date, notes)
        return redirect(url_for('orders'))
    order = get_order_by_id(order_id)
    return render_template('edit_order.html', order=order)

@app.route('/orders/payment/<int:order_id>', methods=['POST'])
@login_required
def add_payment_route(order_id):
    amount = request.form['amount']
    payment_method = request.form['payment_method']
    payment_type = request.form['payment_type']
    notes = request.form['notes']

    screenshot_path = None
    if 'screenshot' in request.files:
        file = request.files['screenshot']
        if file and file.filename != '' and allowed_file(file.filename):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = secure_filename(f"order{order_id}_{file.filename}")
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            screenshot_path = f"uploads/payments/{filename}"

    add_payment(order_id, float(amount), payment_method, payment_type, notes, screenshot_path)
    return redirect(url_for('order_detail', order_id=order_id))

@app.route('/payments/upload/<int:payment_id>', methods=['POST'])
@login_required
def upload_screenshot_route(payment_id):
    order_id = request.form['order_id']
    if 'screenshot' in request.files:
        file = request.files['screenshot']
        if file and file.filename != '' and allowed_file(file.filename):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = secure_filename(f"payment{payment_id}_{file.filename}")
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            screenshot_path = f"uploads/payments/{filename}"
            upload_payment_screenshot(payment_id, screenshot_path)
    return redirect(url_for('order_detail', order_id=order_id))

@app.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order, items, payments, total_order, total_paid = get_order_detail(order_id)
    return render_template('order_detail.html',
        order=order,
        items=items,
        payments=payments,
        total_order=total_order,
        total_paid=total_paid,
        sisa=total_order - total_paid
    )

# ─── CASHFLOW ───

@app.route('/cashflow')
@admin_required
def cashflow():
    expenses = get_all_expenses()
    return render_template('cashflow.html', expenses=expenses)

@app.route('/cashflow/add', methods=['POST'])
@admin_required
def add_expense_route():
    category = request.form['category']
    description = request.form['description']
    amount = request.form['amount']
    date = request.form['date']
    add_expense(category, description, float(amount), date)
    return redirect(url_for('cashflow'))

# ─── REPORTS ───

@app.route('/reports')
@admin_required
def reports():
    from datetime import date
    today = date.today().isoformat()
    daily_orders, daily_expenses = get_daily_summary(today)
    top_products = get_top_products()
    monthly = get_monthly_summary()
    return render_template('reports.html',
        daily_orders=daily_orders,
        daily_expenses=daily_expenses,
        top_products=top_products,
        monthly=monthly,
        today=today
    )

# ─── INGREDIENTS ───

@app.route('/ingredients')
@admin_required
def ingredients():
    all_ingredients = get_all_ingredients()
    history = get_ingredient_price_history()
    chart_data = get_ingredient_prices_for_chart()
    return render_template('ingredients.html',
        ingredients=all_ingredients,
        history=history,
        chart_data=chart_data
    )

@app.route('/ingredients/add', methods=['POST'])
@admin_required
def add_ingredient_route():
    name = request.form['name']
    unit = request.form['unit']
    add_ingredient(name, unit)
    return redirect(url_for('ingredients'))

@app.route('/ingredients/price/add', methods=['POST'])
@admin_required
def add_ingredient_price_route():
    ingredient_id = request.form['ingredient_id']
    price = request.form['price']
    date = request.form['date']
    notes = request.form['notes']
    add_ingredient_price(int(ingredient_id), float(price), date, notes)
    return redirect(url_for('ingredients'))

# ─── ADMIN — USER MANAGEMENT ───

@app.route('/admin/users')
@admin_required
def admin_users():
    users = get_all_users()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/add', methods=['POST'])
@admin_required
def admin_add_user():
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    role = request.form.get('role', 'user')
    if not username or not password:
        flash('Username dan password tidak boleh kosong.', 'danger')
        return redirect(url_for('admin_users'))
    success = create_user(username, password, role)
    if success:
        flash(f"User '{username}' ({role}) berhasil dibuat.", 'success')
    else:
        flash(f"Username '{username}' sudah digunakan.", 'danger')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/role/<int:user_id>', methods=['POST'])
@admin_required
def admin_change_role(user_id):
    if user_id == current_user.id:
        flash('Tidak bisa mengubah role diri sendiri.', 'warning')
        return redirect(url_for('admin_users'))
    new_role = request.form.get('role', 'user')
    update_user_role(user_id, new_role)
    flash('Role berhasil diubah.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/password/<int:user_id>', methods=['POST'])
@admin_required
def admin_reset_password(user_id):
    new_password = request.form.get('new_password', '').strip()
    if not new_password:
        flash('Password baru tidak boleh kosong.', 'danger')
        return redirect(url_for('admin_users'))
    update_user_password(user_id, new_password)
    flash('Password berhasil direset.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    if user_id == current_user.id:
        flash('Tidak bisa menghapus akun sendiri.', 'warning')
        return redirect(url_for('admin_users'))
    delete_user(user_id)
    flash('User berhasil dihapus.', 'success')
    return redirect(url_for('admin_users'))

# ─── RUN ───

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0')