from flask import Flask, render_template, request, redirect, url_for
from database.db import init_db, get_all_products, add_product, get_all_orders, add_order, delete_order, deactivate_product, activate_product, get_all_products_including_inactive, get_all_expenses, add_expense, update_order_status, get_daily_summary, get_top_products, get_monthly_summary, get_all_ingredients, add_ingredient, add_ingredient_price, get_ingredient_price_history, get_ingredient_prices_for_chart, add_payment, get_payments_by_order, get_product_by_id, update_product, get_order_by_id, update_order, get_order_detail
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

@app.route('/orders/status/<int:order_id>', methods=['POST'])
def update_order_status_route(order_id):
    status = request.form['status']
    update_order_status(order_id, status)
    return redirect(url_for('orders'))

@app.route('/reports')
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

@app.route('/ingredients')
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
def add_ingredient_route():
    name = request.form['name']
    unit = request.form['unit']
    add_ingredient(name, unit)
    return redirect(url_for('ingredients'))

@app.route('/ingredients/price/add', methods=['POST'])
def add_ingredient_price_route():
    ingredient_id = request.form['ingredient_id']
    price = request.form['price']
    date = request.form['date']
    notes = request.form['notes']
    add_ingredient_price(int(ingredient_id), float(price), date, notes)
    return redirect(url_for('ingredients'))

@app.route('/orders/payment/<int:order_id>', methods=['POST'])
def add_payment_route(order_id):
    amount = request.form['amount']
    payment_method = request.form['payment_method']
    payment_type = request.form['payment_type']
    notes = request.form['notes']
    add_payment(order_id, float(amount), payment_method, payment_type, notes)
    return redirect(url_for('orders'))

@app.route('/products/edit/<int:product_id>')
def edit_product_page(product_id):
    product = get_product_by_id(product_id)
    return render_template('edit_product.html', product=product)

@app.route('/products/edit/<int:product_id>', methods=['POST'])
def edit_product_route(product_id):
    name = request.form['name']
    price = request.form['price']
    unit = request.form['unit']
    update_product(product_id, name, float(price), unit)
    return redirect(url_for('products'))

@app.route('/orders/edit/<int:order_id>')
def edit_order_page(order_id):
    order = get_order_by_id(order_id)
    return render_template('edit_order.html', order=order)

@app.route('/orders/edit/<int:order_id>', methods=['POST'])
def edit_order_route(order_id):
    customer_name = request.form['customer_name']
    customer_phone = request.form['customer_phone']
    order_date = request.form['order_date']
    pickup_date = request.form['pickup_date']
    notes = request.form['notes']
    update_order(order_id, customer_name, customer_phone, order_date, pickup_date, notes)
    return redirect(url_for('orders'))

@app.route('/orders/<int:order_id>')
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

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0')