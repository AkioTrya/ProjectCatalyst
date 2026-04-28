from flask import Flask, render_template, request, redirect, url_for
from database.db import init_db, get_all_products, add_product

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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)