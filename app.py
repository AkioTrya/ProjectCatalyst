from flask import Flask, render_template, request, redirect, url_for
from database.db import init_db, get_all_products, add_product, get_all_orders, add_order, delete_order, deactivate_product, activate_product, get_all_products_including_inactive, get_all_expenses, add_expense

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/products')
def products():
    all_products = get_all_products()
    return render_template('products.html', products=all_products)

@app.route('/products/add', methods=['POST'])
def add_product_route():
    name = request.form['name']
    price = request.form['price']
    unit = request.form['unit']
    add_product(name, float(price), unit)
    return redirect(url_for('products'))

@app.route('/orders')
def orders():
    all_orders = get_all_orders()
    all_products = get_all_products()
    return render_template('orders.html', orders=all_orders, products=all_products)

@app.route('/orders/add', methods=['POST'])
def add_order_route():
    customer_name = request.form['customer_name']
    customer_phone = request.form['customer_phone']
    order_date = request.form['order_date']
    pickup_date = request.form['pickup_date']
    payment_method = request.form['payment_method']
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
def delete_order_route(order_id):
    delete_order(order_id)
    return redirect(url_for('orders'))

@app.route('/products/delete/<int:product_id>', methods=['POST'])
def deactivate_product_route(product_id):
    deactivate_product(product_id)
    return redirect(url_for('products'))

@app.route('/products/manage')
def manage_products():
    all_products = get_all_products_including_inactive()
    return render_template('manage_products.html', products=all_products)

@app.route('/products/activate/<int:product_id>', methods=['POST'])
def activate_product_route(product_id):
    activate_product(product_id)
    return redirect(url_for('manage_products'))

@app.route('/products/deactivate/<int:product_id>', methods=['POST'])
def deactivate_product_route_manage(product_id):
    deactivate_product(product_id)
    return redirect(url_for('manage_products'))

@app.route('/cashflow')
def cashflow():
    expenses = get_all_expenses()
    return render_template('cashflow.html', expenses=expenses)

@app.route('/cashflow/add', methods=['POST'])
def add_expense_route():
    category = request.form['category']
    description = request.form['description']
    amount = request.form['amount']
    date = request.form['date']
    add_expense(category, description, float(amount), date)
    return redirect(url_for('cashflow'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)