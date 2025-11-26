from flask import Flask, render_template, url_for, jsonify, request, abort, flash, redirect, session
from dataclasses import asdict
from datetime import datetime
import os

import backend

app = Flask(__name__, template_folder='../templates', static_folder='../static')

app.secret_key = 'yo_mama_gay'

@app.context_processor
def inject_user():
    current_user = None
    if 'username' in session:
        current_user = backend.mock_get_user_by_username(session['username'])
    return dict(current_user=current_user)

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
            session['username'] = username
            flash(result["message"], "success")
            return redirect(url_for('index'))
        else:
            flash(result["message"], "error")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None) 
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))

@app.route('/register-page', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        full_form_data = session.get('registration_data', {})
        full_form_data.update(request.form.to_dict())
        
        result = backend.mock_register(full_form_data)
            
        flash(result["message"], "success" if result["status"] else "error")
        return redirect(url_for('login_page'))

    return render_template('register.html')

@app.route('/register-user-page', methods=['GET', 'POST'])
def register_user_page():
    if request.method == 'POST':
        session['registration_data'] = request.form.to.dict()
        return redirect(url_for('register_auth_page'))
    return render_template('register-user.html')

@app.route('/register-merchant-page')
def register_merchant_page():
    if request.method == 'POST':
        session['registration_data'] = request.form.to.dict()
        return redirect(url_for('register_auth_page'))
    return render_template('register-merchant.html')

@app.route('/register-auth-page', methods=['GET', 'POST'])
def register_auth_page():
    if request.method == 'POST':
        full_form_data = session.get('registration_data', {}).copy() 
        full_form_data.update(request.form.to_dict())
        
        result = backend.mock_register(full_form_data)
        if result["status"]:
            session.pop('registration_data', None)
            flash(result["message"], "success")
            return redirect(url_for('login_page'))
        else:
            flash(result["message"], "error")

    return render_template('register-auth.html')

@app.route('/products-page')
def products_page(): 
    products = backend.mock_get_all_products()
    for product in products:
        category = backend.mock_get_category_by_id(product.category_id)
        address = backend.mock_get_address_by_id(product.address_id)
        
        product.category_name = category.name if category else "Uncategorized"
        product.city = address.city if address else "N/A"

    return render_template('products.html', products=products)

@app.route('/product-page/<int:product_id>')
def product_page(product_id: int):
    product = backend.mock_get_product_by_id(product_id)
    reviews = backend.mock_get_reviews_by_product_id(product_id)
    merchant = None
    can_review = False

    if 'username' in session:
        user = backend.mock_get_user_by_username(session['username'])
        if user:
            user_orders = backend.mock_get_orders_by_user_id(user.id)
            for order in user_orders:
                if order.status == backend.Status.DELIVERED:
                    for item in order.orders:
                        if item.product_id == product_id:
                            can_review = True
                            break
                if can_review:
                    break

    if product:
        merchant = next((user for user in backend.mock_users.values() if user.id == product.merchant_id), None)
        product.store_name = merchant.store_name if merchant and hasattr(merchant, 'store_name') else "Unknown Store"

    for review in reviews:
        review.user = next((user for user in backend.mock_users.values() if user.id == review.user_id), None)

    if product is None:
        abort(404)

    return render_template('product_detail.html', product=product, reviews=reviews, merchant=merchant, can_review=can_review)

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
    flash(result['message'], 'success' if result['status'] else 'error')
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