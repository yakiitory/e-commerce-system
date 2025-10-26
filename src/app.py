from flask import Flask, render_template, url_for, jsonify, request, abort, flash, redirect
from dataclasses import asdict
from datetime import datetime
import os

from . import backend

app = Flask(__name__, template_folder='../templates', static_folder='../static')

app.secret_key = 'yo_mama_gay'

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login-page', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        result = backend.mock_login(username, password)

        if result["status"]:
            flash(result["message"], "success")
            return redirect(url_for('index'))
        else:
            flash(result["message"], "error")

    return render_template('login.html')

@app.route('/register-page', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        
        result = backend.mock_register(request.form)
        flash(result["message"], "success")
        return redirect(url_for('login_page'))

    return render_template('register.html')

@app.route('/products-page')
def products_page(): 
    products = backend.mock_get_all_products()
    return render_template('products.html', products=products)

@app.route('/product-page/<int:product_id>')
def product_page(product_id: int):
    product = backend.mock_get_product_by_id(product_id)
    if product is None:
        abort(404)
    return render_template('product_detail.html', product=product)

if __name__ == '__main__':
    app.run(debug=True)