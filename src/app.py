from flask import Flask, render_template, url_for, jsonify, request, abort, flash, redirect, session
from dataclasses import asdict
from datetime import datetime
import os

import backend

app = Flask(__name__, template_folder='../templates', static_folder='../static')

app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'yo_mama_gay')

@app.context_processor
def inject_user():
    """Injects user information into the template context.

    If a 'username' is present in the session, it fetches the user object
    and makes it available to all templates as 'current_user'.

    Returns:
        dict: A dictionary containing the current_user, or None if not logged in.
    """
    current_user = None
    if 'username' in session:
        current_user = backend.mock_get_user_by_username(session['username'])
    return dict(current_user=current_user)

@app.route('/')
def index():
    """Renders the home page.

    Returns:
        str: The rendered HTML of the index page.
    """
    # If a merchant is logged in, redirect them to their dashboard.
    if 'username' in session:
        user = backend.mock_get_user_by_username(session['username'])
        if user and user.role == 'merchant':
            return redirect(url_for('merchant_dashboard_page'))

    categories = backend.mock_get_all_categories()
    all_products = backend.mock_get_all_products()

    # Enrich product data with category names for display
    for product in all_products:
        category = backend.mock_get_category_by_id(product.category_id)
        address = backend.mock_get_address_by_id(product.address_id)
        metadata = backend.mock_get_product_metadata(product.id)

        product.category_name = category.name if category else "Uncategorized"
        product.city = address.city if address else "N/A"
        product.sold_count = metadata.sold_count if metadata else 0
        product.rating_avg = metadata.rating_avg if metadata else 0

    trending_products = all_products[:4]
    new_arrivals = all_products[-4:]
    top_rated = all_products[:4]
    best_sellers = all_products[:4]
    deal_of_the_day = all_products[0] if all_products else None
    deal_of_the_day_total_stock = 0

    if deal_of_the_day:
        deal_of_the_day_total_stock = 50

    popular_lately = all_products[:8]

    return render_template('index.html', categories=categories, trending_products=trending_products,
                           new_arrivals=new_arrivals, top_rated=top_rated, best_sellers=best_sellers,
                           deal_of_the_day=deal_of_the_day, deal_of_the_day_total_stock=deal_of_the_day_total_stock, popular_lately=popular_lately)


@app.route('/login-page', methods=['GET', 'POST'])
def login_page():
    """Handles user login.

    On GET, it displays the login page. On POST, it processes login
    credentials, sets the user session on success, and flashes messages.

    Returns:
        response or str: A redirect to the index page on
        successful login, otherwise the rendered login page HTML.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        result = backend.mock_login(username, password)

        if result["status"]:
            session['username'] = username
            flash(result["message"], "success")
            
            # Redirect merchants to their dashboard, others to index.
            user = backend.mock_get_user_by_username(username)
            if user and user.role == 'merchant':
                return redirect(url_for('merchant_dashboard_page'))
            return redirect(url_for('index'))
        else:
            flash(result["message"], "error")

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logs the current user out.

    Removes the 'username' from the session and redirects to the home page.

    Returns:
        A redirect to the index page.
    """
    session.pop('username', None) 
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))

@app.route('/register-page', methods=['GET', 'POST'])
def register_page():
    """Handles user registration from a single page.

    Returns:
        str: The rendered HTML of the registration page.
    """
    if request.method == 'POST':
        full_form_data = session.get('registration_data', {})
        full_form_data.update(request.form.to_dict())
        
        result = backend.mock_register(full_form_data)
            
        flash(result["message"], "success" if result["status"] else "error")
        return redirect(url_for('login_page'))

    return render_template('register.html')

@app.route('/register-user-page', methods=['GET', 'POST'])
def register_user_page():
    """Handles the first step of user registration (user details).

    On POST, it stores the user details from the form into the session and
    redirects to the authentication details registration page.

    Returns: 
        response or str: A redirect on POST, or the rendered
        HTML for the user registration page on GET.
    """
    if request.method == 'POST':
        session['registration_data'] = request.form.to.dict()
        return redirect(url_for('register_auth_page'))
    return render_template('register-user.html')

@app.route('/register-merchant-page', methods=['GET', 'POST'])
def register_merchant_page():
    """Handles the first step of merchant registration (merchant details).

    On POST, it stores the merchant details from the form into the session and
    redirects to the authentication details registration page.

    Returns: 
        response or str: A redirect on POST, or the rendered
        HTML for the merchant registration page on GET.
    """
    if request.method == 'POST':
        session['registration_data'] = request.form.to_dict()
        return redirect(url_for('register_auth_page'))
    return render_template('register-merchant.html')

@app.route('/register-auth-page', methods=['GET', 'POST'])
def register_auth_page():
    """Handles the second step of registration (authentication details).

    On POST, it combines session data with the current form data to register
    the user or merchant.

    Returns:
        response or str: A redirect to the login page on
        successful registration, otherwise the rendered registration auth page.
    """
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

@app.route('/account-details-page')
def account_details_page():
    return render_template('account-details.html')

@app.route('/orders')
def orders_page():
    """Renders the page that displays the user's order history."""
    if 'username' not in session:
        flash("Please log in to view your orders.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    orders = backend.mock_get_orders_by_user_id(user.id)

    status_filter_str = request.args.get('status')
    if status_filter_str:
        try:
            status_filter = backend.Status[status_filter_str.upper()]
            orders = [o for o in orders if o.status == status_filter]
        except KeyError:
            # Handle invalid status string
            flash("Invalid status filter.", "error")

    # Sort all orders by creation date, newest first
    orders.sort(key=lambda o: o.order_created, reverse=True)

    for order in orders:
        total_price = 0
        for item in order.orders:
            item.product = backend.mock_get_product_by_id(item.product_id)
            total_price += item.total_price
        order.total_price = total_price
    
    # Pass the selected status to the template to highlight the active button
    return render_template('orders.html', orders=orders, Status=backend.Status, selected_status=status_filter_str)

@app.route('/cancel-order/<int:order_id>', methods=['POST'])
def cancel_order(order_id: int):
    """Cancels a user's order."""
    if 'username' not in session:
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    order = next((o for o in backend.mock_get_orders_by_user_id(user.id) if o.id == order_id), None)

    if not order:
        flash("Order not found or you do not have permission to cancel it.", "error")
        return redirect(url_for('orders_page'))

    result = backend.mock_update_order_status(order.id, backend.Status.CANCELLED)
    flash(result['message'], 'success' if result['status'] else 'error')
    return redirect(url_for('orders_page'))

@app.route('/confirm-delivery/<int:order_id>', methods=['POST'])
def confirm_delivery(order_id: int):
    """Confirms that an order has been delivered."""
    if 'username' not in session:
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    order = next((o for o in backend.mock_get_orders_by_user_id(user.id) if o.id == order_id), None)

    result = backend.mock_update_order_status(order.id, backend.Status.DELIVERED)
    return redirect(url_for('orders_page'))

@app.route('/invoice/<int:order_id>')
def invoice_page(order_id: int):
    """Renders the invoice page for a specific order."""
    if 'username' not in session:
        flash("Please log in to view this page.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    order = next((o for o in backend.mock_get_orders_by_user_id(user.id) if o.id == order_id), None)

    if not order:
        flash("Order not found or you do not have permission to view it.", "error")
        return redirect(url_for('orders_page'))

    invoice = backend.mock_get_invoice_by_order_id(order.id)
    if not invoice:
        flash("Invoice for this order could not be found.", "error")
        return redirect(url_for('orders_page'))

    address = backend.mock_get_address_by_id(invoice.address_id)
    
    total_price = 0
    for item in order.orders:
        item.product = backend.mock_get_product_by_id(item.product_id)
        total_price += item.total_price
    order.total_price = total_price

    return render_template('invoice.html', order=order, invoice=invoice, address=address)

@app.route('/login-security')
def login_security_page():
    """Renders the login and security settings page."""
    if 'username' not in session:
        flash("Please log in to view this page.", "error")
        return redirect(url_for('login_page'))
    return render_template('login-security.html')

@app.route('/change-password', methods=['GET', 'POST'])
def change_password_page():
    """Handles the password change process."""
    if 'username' not in session:
        flash("Please log in to change your password.", "error")
        return redirect(url_for('login_page'))

    if request.method == 'POST':
        username = session['username']
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return redirect(url_for('change_password_page'))

        result = backend.mock_change_password(username, old_password, new_password)
        flash(result['message'], 'success' if result['status'] else 'error')
        
        if result['status']:
            return redirect(url_for('login_security_page'))
        else:
            return redirect(url_for('change_password_page'))

    return render_template('change-password.html')

@app.route('/user-addresses')
def user_addresses_page():
    """Renders the page that displays the user's saved addresses."""
    if 'username' not in session:
        flash("Please log in to view this page.", "error")
        return redirect(url_for('login_page'))
    
    user = backend.mock_get_user_by_username(session['username'])
    addresses = backend.mock_get_addresses_by_user_id(user.id)
    return render_template('user-addresses.html', addresses=addresses)

@app.route('/add-address', methods=['POST'])
def add_address():
    """Handles adding a new address for the current user."""
    if 'username' not in session:
        flash("Please log in to add an address.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    address_data = request.form.to_dict()
    
    result = backend.mock_create_address(address_data, user_id=user.id)
    flash(result['message'], 'success' if result['status'] else 'error')
    return redirect(url_for('user_addresses_page'))

@app.route('/edit-address/<int:address_id>', methods=['POST'])
def edit_address(address_id: int):
    """Handles editing an existing address."""
    if 'username' not in session:
        flash("Please log in to edit an address.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    user_addresses = backend.mock_get_addresses_by_user_id(user.id)

    if address_id not in [addr.id for addr in user_addresses]:
        flash("Address not found or you do not have permission to edit it.", "error")
        return redirect(url_for('user_addresses_page'))

    result = backend.mock_update_address(address_id, request.form.to_dict())
    flash(result['message'], 'success' if result['status'] else 'error')
    return redirect(url_for('user_addresses_page'))

@app.route('/delete-address/<int:address_id>', methods=['POST'])
def delete_address(address_id: int):
    """Handles deleting an address."""
    if 'username' not in session:
        flash("Please log in to delete an address.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    user_addresses = backend.mock_get_addresses_by_user_id(user.id)

    if address_id not in [addr.id for addr in user_addresses]:
        flash("Address not found or you do not have permission to delete it.", "error")
        return redirect(url_for('user_addresses_page'))

    backend.mock_delete_address(address_id)
    flash("Address deleted successfully.", "success")
    return redirect(url_for('user_addresses_page'))

@app.route('/merchant-dashboard')
def merchant_dashboard_page():
    """Renders the merchant dashboard page."""
    if 'username' not in session:
        flash("Please log in to view this page.", "error")
        return redirect(url_for('login_page'))
    
    user = backend.mock_get_user_by_username(session['username'])
    if user.role != 'merchant':
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for('index'))

    products = backend.mock_get_products_by_merchant_id(user.id)
    return render_template('merchant-dashboard.html', products=products)

@app.route('/merchant-orders')
def merchant_orders_page():
    """Renders the page for merchants to manage their orders."""
    if 'username' not in session:
        return redirect(url_for('login_page'))
    
    user = backend.mock_get_user_by_username(session['username'])
    if user.role != 'merchant':
        return redirect(url_for('index'))

    orders = backend.mock_get_orders_by_merchant_id(user.id)
    for order in orders:
        customer = next((u for u in backend.mock_users.values() if u.id == order.user_id), None)
        order.customer_name = f"{customer.first_name} {customer.last_name}" if customer else "Unknown User"

        order.total_price = sum(item.total_price for item in order.orders)
        for item in order.orders:
            item.product = backend.mock_get_product_by_id(item.product_id)


    return render_template('merchant-orders.html', orders=orders, Status=backend.Status)

@app.route('/merchant-ship-order/<int:order_id>', methods=['POST'])
def merchant_ship_order(order_id: int):
    """Allows a merchant to mark an order as shipped."""
    if 'username' not in session:
        return redirect(url_for('login_page'))
    
    user = backend.mock_get_user_by_username(session['username'])
    if user.role != 'merchant':
        return redirect(url_for('index'))

    result = backend.mock_update_order_status(order_id, backend.Status.SHIPPED)
    flash(result['message'], 'success' if result['status'] else 'error')
    return redirect(url_for('merchant_orders_page'))

@app.route('/merchant-cancel-order/<int:order_id>', methods=['POST'])
def merchant_cancel_order(order_id: int):
    """Allows a merchant to cancel a pending order."""
    if 'username' not in session:
        return redirect(url_for('login_page'))
    
    user = backend.mock_get_user_by_username(session['username'])
    if user.role != 'merchant':
        return redirect(url_for('index'))

    result = backend.mock_update_order_status(order_id, backend.Status.CANCELLED)
    flash(result['message'], 'success' if result['status'] else 'error')
    return redirect(url_for('merchant_orders_page'))


@app.route('/add-product', methods=['GET', 'POST'])
def add_product_page():
    """Renders the page for adding a new product and handles form submission."""
    if 'username' not in session:
        flash("Please log in to add a product.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    if user.role != 'merchant':
        flash("You do not have permission to perform this action.", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        form_data = request.form.to_dict()
        
        form_data['merchant_id'] = user.id
        form_data['price'] = float(form_data.get('price', 0))
        form_data['original_price'] = float(form_data.get('original_price', form_data['price']))
        form_data['quantity_available'] = int(form_data.get('quantity_available', 0))
        form_data['category_id'] = int(form_data.get('category_id'))
        
        merchant_addresses = backend.mock_get_addresses_by_user_id(user.id)
        if not merchant_addresses:
            flash("You must have a saved address to add a product.", "error")
            return redirect(url_for('user_addresses_page'))
        form_data['address_id'] = merchant_addresses[0].id

        form_data['images'] = [img.strip() for img in form_data.get('images', '').split(',') if img.strip()]

        result = backend.mock_create_product(form_data)
        flash(result['message'], 'success' if result['status'] else 'error')
        return redirect(url_for('merchant_dashboard_page'))

    # For GET request
    categories = backend.mock_get_all_categories()
    return render_template('add-product.html', categories=categories)

@app.route('/edit-product/<int:product_id>', methods=['GET', 'POST'])
def edit_product_page(product_id: int):
    """Renders the page for editing an existing product and handles updates."""
    if 'username' not in session:
        flash("Please log in to edit a product.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    if user.role != 'merchant':
        flash("You do not have permission to perform this action.", "error")
        return redirect(url_for('index'))

    product = backend.mock_get_product_by_id(product_id)

    # Ensure the product belongs to the logged-in merchant
    if not product or product.merchant_id != user.id:
        flash("Product not found or you do not have permission to edit it.", "error")
        return redirect(url_for('merchant_dashboard_page'))

    if request.method == 'POST':
        form_data = request.form.to_dict()

        # Convert types
        form_data['price'] = float(form_data.get('price', 0))
        form_data['original_price'] = float(form_data.get('original_price', form_data['price']))
        form_data['quantity_available'] = int(form_data.get('quantity_available', 0))
        form_data['category_id'] = int(form_data.get('category_id'))

        # Handle images
        form_data['images'] = [img.strip() for img in form_data.get('images', '').split(',') if img.strip()]

        # Remove fields that shouldn't be updated directly
        form_data.pop('merchant_id', None)
        form_data.pop('address_id', None)

        result = backend.mock_update_product(product_id, form_data)
        flash(result['message'], 'success' if result['status'] else 'error')
        return redirect(url_for('merchant_dashboard_page'))

    # For GET request
    categories = backend.mock_get_all_categories()
    return render_template('edit-product.html', product=product, categories=categories)


@app.route('/payments')
def payments_page():
    """Renders the user's payments page, showing virtual card and history."""
    if 'username' not in session:
        flash("Please log in to view your payment information.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    virtual_card = backend.mock_get_virtual_card_by_owner_id(user.id)
    payment_history = backend.mock_get_user_payments(user.id)

    # payment history with sender/receiver names
    for payment in payment_history:
        sender = next((u for u in backend.mock_users.values() if u.id == payment.sender_id), None)
        receiver = next((u for u in backend.mock_users.values() if u.id == payment.receiver_id), None)
        payment.sender_name = sender.username if sender else "N/A"
        payment.receiver_name = receiver.username if receiver else "N/A"

    return render_template('payments.html', virtual_card=virtual_card, payment_history=payment_history)

@app.route('/activate-card', methods=['POST'])
def activate_card():
    """Activates a virtual card for the current user."""
    if 'username' not in session:
        flash("Please log in to activate a card.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    result = backend.mock_create_virtual_card(user.id)
    flash(result['message'], 'success' if result['status'] else 'error')
    return redirect(url_for('payments_page'))

@app.route('/deposit-to-card', methods=['POST'])
def deposit_to_card():
    """Handles deposits to the user's virtual card."""
    if 'username' not in session:
        flash("Please log in to make a deposit.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    virtual_card = backend.mock_get_virtual_card_by_owner_id(user.id)

    if not virtual_card:
        flash("You don't have an active virtual card.", "error")
        return redirect(url_for('payments_page'))

    amount = request.form.get('amount', type=float)
    if not amount or amount <= 0:
        flash("Please enter a valid deposit amount.", "error")
        return redirect(url_for('payments_page'))

    result = backend.mock_deposit_to_virtual_card(virtual_card.id, amount)
    flash(result['message'], 'success' if result['status'] else 'error')
    return redirect(url_for('payments_page'))

@app.route('/cart')
def cart_page():
    """Renders the shopping cart page for the current user."""
    if 'username' not in session:
        flash("Please log in to view your cart.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    cart = backend.mock_get_cart_by_user_id(user.id)
    
    total_price = 0
    for item in cart.items:
        item.product = backend.mock_get_product_by_id(item.product_id)
        total_price += item.product_price * item.product_quantity

    return render_template('cart.html', cart_items=cart.items, total_price=total_price)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout_page():
    """Handles the checkout process."""
    if 'username' not in session:
        flash("Please log in to proceed to checkout.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    cart = backend.mock_get_cart_by_user_id(user.id)

    if not cart.items:
        flash("Your cart is empty.", "error")
        return redirect(url_for('cart_page'))

    if request.method == 'POST':
        address_id = request.form.get('address_id', type=int)
        if not address_id:
            flash("Please select a shipping address.", "error")
            return redirect(url_for('checkout_page'))

        # Process payment first 
        first_product_id = cart.items[0].product_id
        product = backend.mock_get_product_by_id(first_product_id)
        if not product:
            flash("An item in your cart could not be found.", "error")
            return redirect(url_for('cart_page'))

        total_price = sum(item.product_price * item.product_quantity for item in cart.items)
        payment_data = {"sender_id": user.id, "receiver_id": product.merchant_id, "amount": total_price, "type": "ORDER"}
        payment_result = backend.mock_process_payment(payment_data)

        # If payment fails, stop everything and return the user to the checkout page.
        if not payment_result['status']:
            flash(f"Payment failed: {payment_result['message']}", "error")
            return redirect(url_for('checkout_page'))

        # If payment was successful, create the order
        order_result = backend.mock_create_order_from_cart(cart.id, {"payment_type": "VirtualCard"})
        if not order_result['status']:
            flash(f"Payment succeeded, but failed to create order: {order_result['message']}", "error")
            # In a real app, you would refund the payment here.
            return redirect(url_for('cart_page'))
        
        order_id = order_result['order_id']

        # Create the invoice for the new order
        backend.mock_create_invoice(order_id, address_id)

        # Clear the user's cart
        backend.mock_clear_cart(cart.id)

        flash("Your order has been placed successfully!", "success")
        return redirect(url_for('account_details_page'))

    # For GET request
    addresses = backend.mock_get_addresses_by_user_id(user.id)
    virtual_card = backend.mock_get_virtual_card_by_owner_id(user.id)
    total_price = sum(item.product_price * item.product_quantity for item in cart.items)
    for item in cart.items:
        item.product = backend.mock_get_product_by_id(item.product_id)

    return render_template('checkout.html', cart_items=cart.items, total_price=total_price, addresses=addresses, virtual_card=virtual_card)

@app.route('/products-page')
def products_page(): 
    """Renders the page that displays all products.

    Returns:
        str: The rendered HTML of the products page with a list of all
        products.
    """
    all_products = backend.mock_get_all_products()
    categories = backend.mock_get_all_categories()

    # Capturing all user input
    search_criteria = {
        'query': request.args.get('query'),
        'category': request.args.get('category', type=int),
        'min_price': request.args.get('min_price', type=float),
        'max_price': request.args.get('max_price', type=float),
        'min_rating': request.args.get('min_rating', type=float),
        'sort_by': request.args.get('sort_by'),
        'page': request.args.get('page', 1, type=int)
    }

    # Apply filters
    filtered_products = all_products

    # Search filter
    if search_criteria['query']:
        query = search_criteria['query'].lower()
        
        def product_matches_query(product):
            category = backend.mock_get_category_by_id(product.category_id)
            return (query in product.name.lower() or
                    query in product.brand.lower() or
                    (category and query in category.name.lower()))

        filtered_products = [p for p in filtered_products if product_matches_query(p)]

    # Category filter
    if search_criteria['category']:
        selected_category_id = search_criteria['category']
        subcategory_ids = [c.id for c in categories if c.parent_id == selected_category_id]
        all_category_ids = [selected_category_id] + subcategory_ids
        filtered_products = [p for p in filtered_products if p.category_id in all_category_ids]

    # Price filter
    if search_criteria['min_price'] is not None:
        filtered_products = [p for p in filtered_products if p.price >= search_criteria['min_price']]
    if search_criteria['max_price'] is not None:
        filtered_products = [p for p in filtered_products if p.price <= search_criteria['max_price']]

    # Rating filter
    if search_criteria['min_rating'] is not None:
        filtered_products = [
            p for p in filtered_products
            if (meta := backend.mock_get_product_metadata(p.id)) and meta.rating_avg >= search_criteria['min_rating']
        ]

    # Enrich product data before sorting
    for product in filtered_products:
        category = backend.mock_get_category_by_id(product.category_id)
        address = backend.mock_get_address_by_id(product.address_id)
        metadata = backend.mock_get_product_metadata(product.id)
        
        product.category_name = category.name if category else "Uncategorized"
        product.city = address.city if address else "N/A"
        product.sold_count = metadata.sold_count if metadata else 0
        product.rating_avg = metadata.rating_avg if metadata else 0

    # Apply sorting
    if search_criteria['sort_by'] == 'sold':
        filtered_products.sort(
            key=lambda p: p.sold_count,
            reverse=True
        )
    elif search_criteria['sort_by'] == 'price_asc':
        filtered_products.sort(key=lambda p: p.price)
    elif search_criteria['sort_by'] == 'price_desc':
        filtered_products.sort(key=lambda p: p.price, reverse=True)
    elif search_criteria['sort_by'] == 'ratings':
        filtered_products.sort(key=lambda p: p.rating_avg, reverse=True)
    elif search_criteria['sort_by'] == 'brand':
        filtered_products.sort(key=lambda p: p.brand)

    # Pagination logic
    PRODUCTS_PER_PAGE = 12
    total_products = len(filtered_products)
    total_pages = (total_products + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE
    page = search_criteria['page']

    start_index = (page - 1) * PRODUCTS_PER_PAGE
    end_index = start_index + PRODUCTS_PER_PAGE
    paginated_products = filtered_products[start_index:end_index]

    selected_category = backend.mock_get_category_by_id(search_criteria['category']) if search_criteria['category'] else None

    return render_template('products.html', products=paginated_products, categories=categories, 
                           selected_category=selected_category, sort_by=search_criteria['sort_by'],
                           search_criteria=search_criteria,
                           filter_values=search_criteria, # Use search_criteria for filter values
                           page=page, total_pages=total_pages)

@app.route('/product-page/<int:product_id>')
def product_page(product_id: int):
    """Renders the detail page for a specific product.

    Fetches product details, reviews, and merchant information. It also
    determines if the currently logged-in user is allowed to review the product.

    Args:
        product_id (int): The ID of the product to display.

    Returns:
        str: The rendered HTML of the product detail page.
    """
    product = backend.mock_get_product_by_id(product_id)
    reviews = backend.mock_get_reviews_by_product_id(product_id)
    merchant = None
    can_review = False
    is_liked = False

    if 'username' in session:
        user = backend.mock_get_user_by_username(session['username'])
        if user:
            user_orders = backend.mock_get_orders_by_user_id(user.id)
            for order in user_orders:
                metadata = backend.mock_get_user_metadata(user.id)
                if metadata and product_id in metadata.liked_products:
                    is_liked = True 
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
        
        # Fetch and attach metadata
        metadata = backend.mock_get_product_metadata(product.id)
        product.sold_count = metadata.sold_count if metadata else 0
        product.rating_avg = metadata.rating_avg if metadata else 0


    for review in reviews:
        review.user = next((user for user in backend.mock_users.values() if user.id == review.user_id), None)

    if product is None:
        abort(404)

    return render_template('product_detail.html', product=product, reviews=reviews, merchant=merchant, can_review=can_review, is_liked=is_liked)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    """Adds a product to the current user's cart.

    Requires the user to be logged in. Handles form submission for adding
    a specified quantity of a product to the cart.

    Returns:
        A redirect to the product page.
    """
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

@app.route('/update-cart-item/<int:item_id>', methods=['POST'])
def update_cart_item(item_id: int):
    """Updates the quantity of an item in the user's cart."""
    if 'username' not in session:
        flash("Please log in to modify your cart.", "error")
        return redirect(url_for('cart_page'))

    user = backend.mock_get_user_by_username(session['username'])
    cart = backend.mock_get_cart_by_user_id(user.id)
    
    try:
        quantity = int(request.form.get('quantity'))
        if quantity < 1:
            flash("Quantity must be at least 1.", "error")
            return redirect(url_for('cart_page'))
    except (ValueError, TypeError):
        flash("Invalid quantity specified.", "error")
        return redirect(url_for('cart_page'))

    result = backend.mock_update_cart_item_quantity(cart.id, item_id, quantity)
    flash(result['message'], 'success' if result['status'] else 'error')
    return redirect(url_for('cart_page'))

@app.route('/remove-from-cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id: int):
    """Removes an item from the user's cart."""
    if 'username' not in session:
        flash("Please log in to modify your cart.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    cart = backend.mock_get_cart_by_user_id(user.id)

    result = backend.mock_remove_item_from_cart(cart.id, item_id)
    flash(result['message'], 'success' if result['status'] else 'error')
    return redirect(url_for('cart_page'))

@app.route('/add-review/<int:product_id>', methods=['POST'])
def add_review(product_id: int):
    """Handles the submission of a product review.

    Requires the user to be logged in. Creates a new review for the given
    product based on the submitted form data.

    Args:
        product_id (int): The ID of the product.

    Returns:
        A redirect to the product page.
    """
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

@app.route('/like-product/<int:product_id>', methods=['POST'])
def like_product(product_id: int):
    """Toggles a product in the user's liked list."""
    if 'username' not in session:
        flash("Please log in to like products.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    if not user:
        flash("User not found.", "error")
        return redirect(url_for('index'))

    result = backend.mock_like_unlike_product(user.id, product_id)
    flash(result['message'], 'success' if result['status'] else 'error')
    return redirect(request.referrer or url_for('product_page', product_id=product_id))

@app.route('/liked-products')
def liked_products_page():
    """Renders the page showing the user's liked products."""
    if 'username' not in session:
        flash("Please log in to view your liked products.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    liked_products = backend.mock_get_liked_products(user.id)

    # Enrich product data
    for product in liked_products:
        category = backend.mock_get_category_by_id(product.category_id)
        address = backend.mock_get_address_by_id(product.address_id)
        metadata = backend.mock_get_product_metadata(product.id)
        product.category_name = category.name if category else "Uncategorized"
        product.city = address.city if address else "N/A"
        product.rating_avg = metadata.rating_avg if metadata else 0

    return render_template('liked-products.html', products=liked_products)

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/product-page/<int:product_id>')
def product_page(product_id: int):
    """Renders the detail page for a specific product.

    Fetches product details, reviews, and merchant information. It also
    determines if the currently logged-in user is allowed to review the product.

    Args:
        product_id (int): The ID of the product to display.

    Returns:
        str: The rendered HTML of the product detail page.
    """
    product = backend.mock_get_product_by_id(product_id)
    reviews = backend.mock_get_reviews_by_product_id(product_id)
    merchant = None
    can_review = False
    is_liked = False

    if 'username' in session:
        user = backend.mock_get_user_by_username(session['username'])
        if user:
            user_orders = backend.mock_get_orders_by_user_id(user.id)
            for order in user_orders:
                metadata = backend.mock_get_user_metadata(user.id)
                if metadata and product_id in metadata.liked_products:
                    is_liked = True 
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
        
        # Fetch and attach metadata
        metadata = backend.mock_get_product_metadata(product.id)
        product.sold_count = metadata.sold_count if metadata else 0
        product.rating_avg = metadata.rating_avg if metadata else 0


    for review in reviews:
        review.user = next((user for user in backend.mock_users.values() if user.id == review.user_id), None)

    if product is None:
        abort(404)

    return render_template('product_detail.html', product=product, reviews=reviews, merchant=merchant, can_review=can_review, is_liked=is_liked)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    """Adds a product to the current user's cart.

    Requires the user to be logged in. Handles form submission for adding
    a specified quantity of a product to the cart.

    Returns:
        A redirect to the product page.
    """
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

@app.route('/update-cart-item/<int:item_id>', methods=['POST'])
def update_cart_item(item_id: int):
    """Updates the quantity of an item in the user's cart."""
    if 'username' not in session:
        flash("Please log in to modify your cart.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    cart = backend.mock_get_cart_by_user_id(user.id)
    
    try:
        quantity = int(request.form.get('quantity'))
        if quantity < 1:
            flash("Quantity must be at least 1.", "error")
            return redirect(url_for('cart_page'))
    except (ValueError, TypeError):
        flash("Invalid quantity specified.", "error")
        return redirect(url_for('cart_page'))

    result = backend.mock_update_cart_item_quantity(cart.id, item_id, quantity)
    flash(result['message'], 'success' if result['status'] else 'error')
    return redirect(url_for('cart_page'))

@app.route('/remove-from-cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id: int):
    """Removes an item from the user's cart."""
    if 'username' not in session:
        flash("Please log in to modify your cart.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    cart = backend.mock_get_cart_by_user_id(user.id)

    result = backend.mock_remove_item_from_cart(cart.id, item_id)
    flash(result['message'], 'success' if result['status'] else 'error')
    return redirect(url_for('cart_page'))

@app.route('/add-review/<int:product_id>', methods=['POST'])
def add_review(product_id: int):
    """Handles the submission of a product review.

    Requires the user to be logged in. Creates a new review for the given
    product based on the submitted form data.

    Args:
        product_id (int): The ID of the product.

    Returns:
        A redirect to the product page.
    """
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

@app.route('/like-product/<int:product_id>', methods=['POST'])
def like_product(product_id: int):
    """Toggles a product in the user's liked list."""
    if 'username' not in session:
        flash("Please log in to like products.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    if not user:
        flash("User not found.", "error")
        return redirect(url_for('index'))

    result = backend.mock_like_unlike_product(user.id, product_id)
    flash(result['message'], 'success' if result['status'] else 'error')
    return redirect(request.referrer or url_for('product_page', product_id=product_id))

@app.route('/liked-products')
def liked_products_page():
    """Renders the page showing the user's liked products."""
    if 'username' not in session:
        flash("Please log in to view your liked products.", "error")
        return redirect(url_for('login_page'))

    user = backend.mock_get_user_by_username(session['username'])
    liked_products = backend.mock_get_liked_products(user.id)

    # Enrich product data
    for product in liked_products:
        category = backend.mock_get_category_by_id(product.category_id)
        address = backend.mock_get_address_by_id(product.address_id)
        metadata = backend.mock_get_product_metadata(product.id)
        product.category_name = category.name if category else "Uncategorized"
        product.city = address.city if address else "N/A"
        product.rating_avg = metadata.rating_avg if metadata else 0

    return render_template('liked-products.html', products=liked_products)

if __name__ == '__main__':
    app.run(debug=True)