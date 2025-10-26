from flask import Flask, render_template, url_for, jsonify, request, abort, flash, redirect
from dataclasses import asdict
from datetime import datetime

from models.product import Product
from models.user import User

app = Flask(__name__, template_folder='../templates', static_folder='../static')

app.secret_key = 'yo_mama_gay'

mock_products = [
    Product(
        id=1,
        name="Thinkbook 14+",
        merchant_id=1,
        brand="Lenovo",
        category_id=1,
        description="",
        address_id=1,
        images=["/static/images/product1.jpg"],
        price=70000.00,
        original_price=70000.00,
        quantity_available=5
    ),
    Product(
        id=2,
        name="Loq",
        merchant_id=1,
        brand="Lenovo",
        category_id=1,
        description="",
        address_id=1,
        images=["/static/images/product1.jpg"],
        price=80000.00,
        original_price=80000.00,
        quantity_available=5
    )
]

mock_users = {
    "testuser": User(
        id=1,
        role="user",
        username="testuser",
        hash="this_is_a_mock_hash", 
        first_name="Blanca",
        last_name="Evangelista",
        phone_number="676767676767",
        email="blancaevangelista@gmail.com",
        gender="Female",
        age=30,
        created_at=datetime.now()
    )
}


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