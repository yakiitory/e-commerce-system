from flask import Flask, render_template, url_for, jsonify, request, abort, flash, redirect, session
from dataclasses import asdict
from datetime import datetime
import os

import backend

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
            session['username'] = username # Set the user in the session
            flash(result["message"], "success")
            return redirect(url_for('index'))
        else:
            flash(result["message"], "error")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None) # Clear the user from the session
    flash("You have been logged out.", "success")
    return redirect(url_for('login_page'))

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
    reviews = backend.mock_get_reviews_by_product_id(product_id)
    if product is None:
        abort(404)
    return render_template('product_detail.html', product=product, reviews=reviews)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if 'username' not in session:
        flash("Please log in to add items to your cart.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    cart = backend.mock_get_cart_by_user_id(user.id)
    
    product_id = int(request.form.get('product_id'))
    quantity = int(request.form.get('quantity', 1))

    result = backend.mock_add_item_to_cart(cart.id, {'product_id': product_id, 'product_quantity': quantity})

    if result['status']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'error')

    return redirect(url_for('product_page', product_id=product_id))

@app.route('/add-review/<int:product_id>', methods=['POST'])
def add_review(product_id: int):
    if 'username' not in session:
        flash("Please log in to submit a review.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    
    review_data = {
        "user_id": user.id,
        "product_id": product_id,
        "rating": float(request.form.get('rating')),
        "description": request.form.get('description'),
        "attached": [],
        "likes": 0
    }

    result = backend.mock_create_review(review_data)
    flash(result['message'], 'success' if result['status'] else 'error')

    return redirect(url_for('product_page', product_id=product_id))

if __name__ == '__main__':
    app.run(debug=True)