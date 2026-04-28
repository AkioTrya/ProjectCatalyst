from flask import Flask, render_template, request, redirect, url_for
from database.db import init_db, get_all_products, add_product, get_all_orders, add_order

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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)