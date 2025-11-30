from flask import Flask, render_template, url_for, jsonify, request, abort, flash, redirect, session
from typing import cast
from models.status import Status
import os
from werkzeug.utils import secure_filename

from PIL import Image
from services import AddressService, AuthService, CategoryService, InteractionService, ProductService, OrderService, MediaService, ReviewService, TransactionService
from repositories import (
    AdminRepository,
    CartRepository,
    CategoryRepository,
    MerchantRepository,
    AddressRepository,
    OrderRepository,
    PaymentRepository,
    ProductMetadataRepository,
    ProductRepository,
    ReviewRepository,
    UserMetadataRepository,
    UserRepository,
    VirtualCardRepository,
)
from database.database import Database
from models.products import ProductCreate, ProductMetadata

db = Database()
admin_repository            = AdminRepository(db)
address_repository          = AddressRepository(db)
merchant_repository         = MerchantRepository(db)
category_repository         = CategoryRepository(db)
payment_repository          = PaymentRepository(db)
product_metadata_repository = ProductMetadataRepository(db)
review_repository           = ReviewRepository(db)
user_metadata_repository    = UserMetadataRepository(db)
user_repository             = UserRepository(db)
virtual_card_repository     = VirtualCardRepository(db)
product_repository          = ProductRepository(db)
cart_repository             = CartRepository(db, product_metadata_repository)
order_repository            = OrderRepository(db, cart_repository=cart_repository)

address_service = AddressService(
    db=db,
    address_repo=address_repository
)
category_service = CategoryService(
    category_repo=category_repository
)
auth_service = AuthService(
    user_repo=user_repository,
    merchant_repo=merchant_repository,
    admin_repo=admin_repository
)
interaction_service = InteractionService(
    db=db, 
    user_repo=user_repository, 
    product_repo=product_repository, 
    cart_repo=cart_repository
)
transaction_service = TransactionService(
    db=db,
    payment_repo=payment_repository,
    virtual_card_repo=virtual_card_repository,
    user_repo=user_repository,
    merchant_repo=merchant_repository
)
product_service = ProductService(
    db=db,
    product_repo=product_repository,
)
order_service = OrderService(
    db=db,
    order_repo=order_repository,
    product_repo=product_repository,
    transaction_service=transaction_service,
    cart_repo=cart_repository
)
review_service = ReviewService(
    db=db,
    review_repo=review_repository,
    order_repo=order_repository,
    product_repo=product_repository
)

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'yo_mama_gay')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    return app

app = create_app()

with app.app_context():
    category_service.seed_categories()
    # Create dummy accounts if they don't exist
    if not user_repository.get_by_username("JohnDoe"):
        user_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'JohnDoe',
            'email': 'johndoe@example.com',
            'password': 'password',
            're_password': 'password',
            'age': 30
        }
        success, message = auth_service.register(user_data, 'user')
        if success:
            print("Successfully created dummy user 'JohnDoe'")
        else:
            print(f"Failed to create dummy user: {message}")

    if not merchant_repository.get_by_username("JaneDoe"):
        merchant_data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'store_name': 'Jane\'s Wares',
            'username': 'JaneDoe',
            'email': 'janedoe@example.com',
            'password': 'password',
            're_password': 'password',
            'phone_number': '09123456789'
        }
        success, message = auth_service.register(merchant_data, 'merchant')
        if success:
            print("Successfully created dummy merchant 'JaneDoe'")
        else:
            print(f"Failed to create dummy merchant: {message}")

@app.context_processor
def inject_user():
    """Injects user information into the template context.

    If a 'username' is present in the session, it fetches the user object
    and makes it available to all templates as 'current_user'.

    Returns:
        dict: A dictionary containing the current_user, or None if not logged in.
    """
    current_user = None
    if 'username' in session and 'role' in session:
        username = session['username']
        role = session['role']

        # Use the stored role to query the correct repository
        if role == 'user':
            current_user = user_repository.get_by_username(username)
        elif role == 'merchant':
            current_user = merchant_repository.get_by_username(username)
        elif role in ['admin', 'superadmin']: # Assuming admin roles
            current_user = admin_repository.get_by_username(username)
    return dict(current_user=current_user)

@app.route('/')
def index():
    """Renders the home page.

    Returns:
        str: The rendered HTML of the index page.
    """
    # If a merchant is logged in, redirect them to their dashboard.
    if 'username' in session:
        user = merchant_repository.get_by_username(session['username'])
        if user and user.role == 'merchant':
            return redirect(url_for('merchant_dashboard_page'))

    # Fetch specific product lists using the new service methods
    _, trending_products = product_service.get_trending_products(limit=4)
    _, new_arrivals = product_service.get_new_arrivals(limit=4)
    _, top_rated = product_service.get_top_rated_products(limit=4)
    _, best_sellers = product_service.get_best_selling_products(limit=8) # Example: fetch more for this section
    _, popular_lately = product_service.get_trending_products(limit=8)

    categories = product_service.get_all_categories() or []

    # Ensure lists are empty on failure to prevent template errors
    trending_products = trending_products or []
    new_arrivals = new_arrivals or []
    top_rated = top_rated or []
    best_sellers = best_sellers or []
    popular_lately = popular_lately or []

    # Deal of the day can be the top trending product
    deal_of_the_day = trending_products[0] if trending_products else None
    deal_of_the_day_total_stock = 0
    if deal_of_the_day:
        deal_of_the_day_total_stock = 50

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

        is_success, account_or_message = auth_service.login(username or "", password or "")

        if is_success and account_or_message:
            session['username'] = username
            session['role'] = account_or_message.role
            flash(f"Welcome back, {username}!", "success")
            
            # Redirect merchants to their dashboard, others to index.
            if account_or_message.role == 'merchant':
                return redirect(url_for('merchant_dashboard_page'))
            return redirect(url_for('index'))
        else:
            flash(str(account_or_message), "error")

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
        form_data = request.form.to_dict()
        account_type = form_data.get('account_type', '') # Get account type from form
        success, message = auth_service.register(form_data, account_type)

        flash(message, "success" if success else "error")
        if success:
            session.pop('registration_data', None) # Clean up session data
            return redirect(url_for('login_page'))
        else:
            return redirect(url_for('register_page'))

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
        session['registration_data'] = request.form.to_dict()
        session['account_type'] = 'user'
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
        session['account_type'] = 'merchant'
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
    # Ensure there's data from the first step
    if 'registration_data' not in session:
        flash("Please complete the first step of registration.", "error")
        return redirect(url_for('register_user_page')) # Or a generic start page

    if request.method == 'POST':
        full_form_data = session.get('registration_data', {}).copy()
        full_form_data.update(request.form.to_dict())
        account_type = session.get('account_type', '')
        success, message = auth_service.register(full_form_data, account_type)

        if success:
            session.pop('registration_data', None)
            flash(message, "success")
            return redirect(url_for('login_page'))
        else:
            session.pop('registration_data', None)
            flash(message, "error")
            return redirect(url_for('register_page'))

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

    user = user_repository.get_by_username(session['username'])
    if not user:
        flash("User not found. Please log in again.", "error")
        session.pop('username', None)
        return redirect(url_for('login_page'))

    success, orders_or_none = order_service.get_orders_for_user(user.id)
    if not success:
        flash("Could not retrieve your orders at this time.", "error")
        orders = []
    else:
        orders = orders_or_none or []

    status_filter_str = request.args.get('status')
    if status_filter_str:
        try:
            status_filter = Status[status_filter_str.upper()]
            orders = [o for o in orders if o.status == status_filter]
        except KeyError:
            # Handle invalid status string
            flash("Invalid status filter.", "error")
    for order in orders:
        for item in order.items:
            _, product_entry = product_service.get_product_for_display(item.product_id)

            # Attach the whole product object (already done)
            setattr(item, 'product', product_entry)

            # ALSO attach the thumbnail directly to the item
            setattr(item, 'thumbnail', product_entry.thumbnail) # type: ignore

    
    # Pass the selected status to the template to highlight the active button
    return render_template('orders.html', orders=orders, Status=Status, selected_status=status_filter_str)

@app.route('/cancel-order/<int:order_id>', methods=['POST'])
def cancel_order(order_id: int):
    """Cancels a user's order."""
    if 'username' not in session:
        flash("Please log in to cancel an order.", "error")
        return redirect(url_for('login_page'))

    user = user_repository.get_by_username(session['username'])
    if not user:
        flash("User not found. Please log in again.", "error")
        session.pop('username', None)
        return redirect(url_for('login_page'))

    success, message = order_service.cancel_order(order_id=order_id, user_id=user.id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('orders_page'))

@app.route('/confirm-delivery/<int:order_id>', methods=['POST'])
def confirm_delivery(order_id: int):
    """Confirms that an order has been delivered."""
    if 'username' not in session:
        flash("Please log in to confirm an order delivery.", "error")
        return redirect(url_for('login_page'))

    user = user_repository.get_by_username(session['username'])
    if not user:
        flash("User not found. Please log in again.", "error")
        session.pop('username', None)
        return redirect(url_for('login_page'))

    success, message = order_service.confirm_delivery(order_id=order_id, user_id=user.id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('orders_page'))

@app.route('/invoice/<int:order_id>')
def invoice_page(order_id: int):
    """Renders the invoice page for a specific order."""
    if 'username' not in session:
        flash("Please log in to view this page.", "error")
        return redirect(url_for('login_page'))

    user = user_repository.get_by_username(session['username'])
    if not user:
        flash("User not found. Please log in again.", "error")
        session.pop('username', None)
        return redirect(url_for('login_page'))

    success, result = order_service.get_order_details(order_id=order_id, user_id=user.id)

    if not success:
        flash(str(result), "error")
        return redirect(url_for('orders_page'))
    
    order, invoice = cast(tuple, result)
    if not invoice:
        flash("Invoice for this order could not be found.", "error")
        return redirect(url_for('orders_page'))

    address = product_service.get_address_by_id(invoice.address_id) if invoice.address_id else None
    
    for item in order.items:
        _, product_entry = product_service.get_product_for_display(item.product_id)
        setattr(item, 'product', product_entry)

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
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return redirect(url_for('change_password_page'))

        success, message = auth_service.change_password(username, old_password, new_password)
        flash(message, 'success' if success else 'error')
        
        if success:
            return redirect(url_for('login_security_page'))
        else:
            return redirect(url_for('change_password_page'))

    return render_template('change-password.html')

@app.route('/user-addresses')
def user_addresses_page():
    """Renders the page that displays the client's saved addresses."""
    if 'username' not in session:
        flash("Please log in to view this page.", "error")
        return redirect(url_for('login_page'))
    
    client = None
    if session['role'] == 'user':
        client = user_repository.get_by_username(session['username'])
    elif session['role'] == 'merchant':
        client = merchant_repository.get_by_username(session['username'])
    if not client:
        flash("User not found. Please log in again.", "error")
        return redirect(url_for('login_page'))

    if session['role'] == 'user':
        success, result = address_service.get_user_addresses(client.id)
    elif session['role'] == 'merchant':
        success, result = address_service.get_merchant_addresses(client.id)
    else:
        success, result = False, "Invalid account role."

    addresses = result if success else []
    if not success:
        flash(str(result), "error")

    return render_template('user-addresses.html', addresses=addresses)

@app.route('/add-address', methods=['POST'])
def add_address():
    """Handles adding a new address for the current user."""
    if 'username' not in session:
        flash("Please log in to add an address.", "error")
        return redirect(url_for('login_page'))

    client = None
    if session['role'] == 'user':
        client = user_repository.get_by_username(session['username'])
    elif session['role'] == 'merchant':
        client = merchant_repository.get_by_username(session['username'])

    if not client:
        flash("User not found. Please log in again.", "error")
        return redirect(url_for('login_page'))

    address_data = request.form.to_dict()
    if session['role'] == 'user':
        success, message = address_service.add_address_for_user(client.id, address_data)
    elif session['role'] == 'merchant':
        success, message = address_service.add_address_for_merchant(client.id, address_data)
    else:
        success, message = False, "Invalid account role."

    flash(message, 'success' if success else 'error')
    return redirect(url_for('user_addresses_page'))

@app.route('/edit-address/<int:address_id>', methods=['POST'])
def edit_address(address_id: int):
    """Handles editing an existing address."""
    if 'username' not in session:
        flash("Please log in to edit an address.", "error")
        return redirect(url_for('login_page'))

    client = None
    if session['role'] == 'user':
        client = user_repository.get_by_username(session['username'])
    elif session['role'] == 'merchant':
        client = merchant_repository.get_by_username(session['username'])

    if not client:
        flash("User not found. Please log in again.", "error")
        return redirect(url_for('login_page'))

    if session['role'] == 'user':
        success, message = address_service.update_user_address(client.id, address_id, request.form.to_dict())
    elif session['role'] == 'merchant':
        success, message = address_service.update_merchant_address(client.id, address_id, request.form.to_dict())
    else:
        success, message = False, "Invalid account role."

    flash(message, 'success' if success else 'error')
    return redirect(url_for('user_addresses_page'))

@app.route('/delete-address/<int:address_id>', methods=['POST'])
def delete_address(address_id: int):
    """Handles deleting an address."""
    if 'username' not in session:
        flash("Please log in to delete an address.", "error")
        return redirect(url_for('login_page'))

    client = None
    if session['role'] == 'user':
        client = user_repository.get_by_username(session['username'])
    elif session['role'] == 'merchant':
        client = merchant_repository.get_by_username(session['username'])

    if not client:
        flash("User not found. Please log in again.", "error")
        return redirect(url_for('login_page'))

    if session['role'] == 'user':
        success, message = address_service.delete_user_address(client.id, address_id)
    elif session['role'] == 'merchant':
        success, message = address_service.delete_merchant_address(client.id, address_id)
    else:
        success, message = False, "Invalid account role."

    flash(message, 'success' if success else 'error')
    return redirect(url_for('user_addresses_page'))

@app.route('/merchant-dashboard')
def merchant_dashboard_page():
    """Renders the merchant dashboard page."""
    if 'username' not in session:
        flash("Please log in to view this page.", "error")
        return redirect(url_for('login_page'))
    
    user = merchant_repository.get_by_username(session['username'])
    if not user or user.role != 'merchant':
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for('index'))

    products = product_service.get_product_entries_by_merchant_id(user.id)

    if not products:
        flash("You don't have any products yet, start selling!", "error")
        products = []
    return render_template('merchant-dashboard.html', products=products)

@app.route('/merchant-orders')
def merchant_orders_page():
    """Renders the page for merchants to manage their orders."""
    if 'username' not in session:
        flash("Please log in to view this page.", "error")
        return redirect(url_for('login_page'))
    
    user = merchant_repository.get_by_username(session['username'])
    if not user or user.role != 'merchant':
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for('index'))

    success, orders_or_message = order_service.get_orders_for_merchant(user.id)
    if not success:
        flash(str(orders_or_message), "error")
        orders = []
    else:
        orders = orders_or_message or []

    for order in orders:
        customer = user_repository.read(order.user_id)
        setattr(order, 'customer_name', f"{customer.first_name} {customer.last_name}" if customer else "Unknown User")

        for item in order.items:
            _, product_entry = product_service.get_product_for_display(item.product_id)
            setattr(item, 'product', product_entry)

    return render_template('merchant-orders.html', orders=orders, Status=Status)

@app.route('/merchant-ship-order/<int:order_id>', methods=['POST'])
def merchant_ship_order(order_id: int):
    """Allows a merchant to mark an order as shipped."""
    if 'username' not in session:
        flash("Please log in to perform this action.", "error")
        return redirect(url_for('login_page'))
    
    user = merchant_repository.get_by_username(session['username'])
    if not user or user.role != 'merchant':
        flash("You do not have permission to perform this action.", "error")
        return redirect(url_for('index'))

    success, message = order_service.ship_order(order_id=order_id, merchant_id=user.id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('merchant_orders_page'))

@app.route('/merchant-cancel-order/<int:order_id>', methods=['POST'])
def merchant_cancel_order(order_id: int):
    """Allows a merchant to cancel a pending order."""
    if 'username' not in session:
        flash("Please log in to perform this action.", "error")
        return redirect(url_for('login_page'))
    
    user = merchant_repository.get_by_username(session['username'])
    if not user or user.role != 'merchant':
        flash("You do not have permission to perform this action.", "error")
        return redirect(url_for('index'))

    success, message = order_service.merchant_cancel_order(order_id=order_id, merchant_id=user.id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('merchant_orders_page'))


@app.route('/add-product', methods=['GET', 'POST'])
def add_product_page():
    """Renders the page for adding a new product and handles form submission."""
    if 'username' not in session:
        flash("Please log in to add a product.", "error")
        return redirect(url_for('login_page'))

    user = merchant_repository.get_by_username(session['username'])
    if not user or user.role != 'merchant':
        flash("You do not have permission to perform this action.", "error")
        return redirect(url_for('index'))

    merchant_addresses = address_repository.get_addresses_for_merchant(user.id)
    if request.method == 'POST':
        if not merchant_addresses:
            flash("You must have a saved address to add a product.", "error")
            return redirect(url_for('user_addresses_page'))
        
        # Image Processing: Save files and get their URLs
        upload_folder = os.path.join(cast(str, app.static_folder), 'img', 'uploads')
        form_data = request.form.to_dict()
        image_files = request.files.getlist('images')
        image_urls = []
        address_id = request.form.get('address_id', type=int)

        os.makedirs(upload_folder, exist_ok=True)

        for image_file in image_files:
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                unique_filename = f"{os.urandom(8).hex()}_{filename}"
                save_path = os.path.join(upload_folder, unique_filename)
                try:
                    img = Image.open(image_file.stream)
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    img.save(save_path, 'jpeg', quality=85, optimize=True)
                    # Construct the web-accessible URL for the saved image
                    web_path = f'img/uploads/{unique_filename}'
                    image_urls.append(url_for('static', filename=web_path))
                except Exception as e:
                    flash(f"Error processing image {filename}: {e}", "error")
                    return redirect(url_for('add_product_page'))


        try:
            # Create the ProductCreate object
            product_data = ProductCreate(
                name=form_data.get('name', 'Unnamed Product'),
                brand=form_data.get('brand', 'Unbranded'),
                category_id=int(form_data.get('category_id', 0)),
                description=form_data.get('description', ''),
                price=float(form_data.get('price', 0)),
                quantity_available=int(form_data.get('quantity_available', 0)),
                merchant_id=user.id,
                address_id=address_id # type: ignore
            )
        except (ValueError, TypeError) as e:
            flash(f"Invalid data provided: {e}", "error")
            return redirect(url_for('add_product_page'))

        new_product_id, message = product_service.create_product(product_data, image_urls)

        flash(message, 'success' if new_product_id else 'error')
        return redirect(url_for('merchant_dashboard_page') if new_product_id else url_for('add_product_page'))

    # For GET request, use the mock backend
    categories = product_service.get_all_categories()
    return render_template('add-product.html', categories=categories or [], addresses=merchant_addresses)

@app.route('/edit-product/<int:product_id>', methods=['GET', 'POST'])
def edit_product_page(product_id: int):
    """Renders the page for editing an existing product and handles updates."""
    if 'username' not in session:
        flash("Please log in to edit a product.", "error")
        return redirect(url_for('login_page'))

    user = merchant_repository.get_by_username(session['username'])
    if not user or user.role != 'merchant':
        flash("You do not have permission to perform this action.", "error")
        return redirect(url_for('index'))

    # Fetch the product for both GET and POST to ensure it exists and is owned by the merchant
    success, product_or_none = product_service.get_product(product_id)
    if not success or not product_or_none:
        flash("Product not found.", "error")
        return redirect(url_for('merchant_dashboard_page'))

    product = product_or_none
    if product.merchant_id != user.id:
        flash("Product not found or you do not have permission to edit it.", "error")
        return redirect(url_for('merchant_dashboard_page'))

    merchant_addresses = address_repository.get_addresses_for_merchant(user.id)
    if request.method == 'POST':
            if not merchant_addresses:
                flash("You must have a saved address to edit this product.", "error")
                return redirect(url_for('user_addresses_page'))
            
            form_data = request.form.to_dict()
            
            # Convert types
            form_data['price'] = float(form_data.get('price', 0))  # type: ignore
            form_data['quantity_available'] = int(form_data.get('quantity_available', 0)) # type: ignore
            form_data['category_id'] = int(form_data.get('category_id')) # type: ignore
            address_id = request.form.get('address_id', type=int)

            # Data Validation for address
            if not address_id or not any(addr.id == address_id for addr in merchant_addresses):
                flash("Please select a valid address for the product.", "error")
                return redirect(url_for('edit_product_page', product_id=product_id))

            # Handle image uploads and existing images
            upload_folder = os.path.join(cast(str, app.static_folder), 'img', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)

            # Get existing images from the hidden input
            existing_images = [img.strip() for img in request.form.get('images', '').split(',') if img.strip()]
            
            new_image_files = request.files.getlist('new_images')
            new_image_urls = []

            for image_file in new_image_files:
                if image_file and image_file.filename:
                    filename = secure_filename(image_file.filename)
                    unique_filename = f"{os.urandom(8).hex()}_{filename}"
                    save_path = os.path.join(upload_folder, unique_filename)
                    try:
                        img = Image.open(image_file.stream)
                        if img.mode in ('RGBA', 'P'):
                            img = img.convert('RGB')
                        img.save(save_path, 'jpeg', quality=85, optimize=True)
                        web_path = f'img/uploads/{unique_filename}'
                        new_image_urls.append(f'/static/{web_path}')
                    except Exception as e:
                        flash(f"Error processing image {filename}: {e}", "error")
                        return redirect(url_for('edit_product_page', product_id=product_id))

            # Combine existing and new images
            all_images = existing_images + new_image_urls
            form_data.pop('images', None)  # Remove from form_data if it exists
            result, message = product_repository.update(product_id, form_data, all_images)
            result, message = product_repository.update(product_id, form_data)
            flash(message, 'success' if result else 'error')
            return redirect(url_for('merchant_dashboard_page'))

    # For GET request
    categories = product_service.get_all_categories()
    return render_template('edit-product.html', product=product, categories=categories, addresses=merchant_addresses)


@app.route('/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id: int):
    """Handles deleting a product for a merchant."""
    if 'username' not in session:
        flash("Please log in to delete a product.", "error")
        return redirect(url_for('login_page'))

    user = merchant_repository.get_by_username(session['username'])
    if not user or user.role != 'merchant':
        flash("You do not have permission to perform this action.", "error")
        return redirect(url_for('index'))

    status, product = product_service.get_product(product_id)

    # Ensure the product belongs to the logged-in merchant
    if not product or product.merchant_id != user.id:
        flash("Product not found or you do not have permission to delete it.", "error")
        return redirect(url_for('merchant_dashboard_page'))

    success, result = product_service.delete_product(product_id, user.id)
    flash(result, 'success' if success else 'error')
    return redirect(url_for('merchant_dashboard_page'))

@app.route('/payments')
def payments_page():
    """Renders the user's payments page, showing virtual card and history."""
    if 'username' not in session:
        flash("Please log in to view your payment information.", "error")
        return redirect(url_for('login_page'))

    # Get the current logged-in user (can be a user or merchant)
    client = None
    if session.get('role') == 'user':
        client = user_repository.get_by_username(session['username'])
    elif session.get('role') == 'merchant':
        client = merchant_repository.get_by_username(session['username'])
    if not client:
        flash("Could not find your account. Please log in again.", "error")
        session.pop('username', None)
        return redirect(url_for('login_page'))

    if client.role == 'user':
        result = transaction_service.get_user_payment_history(client.id)
        virtual_card = virtual_card_repository.get_by_user_id(client.id)
    elif client.role == 'merchant':
        result = transaction_service.get_merchant_payment_history(client.id)
        virtual_card = virtual_card_repository.get_by_merchant_id(client.id)

    if not result:
        return render_template('payments.html', virtual_card=virtual_card, payment_history=[])

    return render_template('payments.html', virtual_card=virtual_card, payment_history=result)

@app.route('/activate-card', methods=['POST'])
def activate_card():
    """Activates a virtual card for the current user."""
    if 'username' not in session:
        flash("Please log in to activate a card.", "error")
        return redirect(url_for('login_page'))

    owner = None
    if session['role'] == 'user':
        owner = user_repository.get_by_username(session['username'])
        account_type = 'user'
    elif session['role'] == 'merchant':
        owner = merchant_repository.get_by_username(session['username'])
        account_type = 'merchant'
    if not owner:
        flash("Could not identify your account. Please log in again.", "error")
        session.pop('username', None)
        return redirect(url_for('login_page'))

    success, message = transaction_service.create_virtual_card(owner.id, account_type)
    flash(message, 'success' if success else 'error')

    if account_type == 'merchant':
        return redirect(url_for('merchant_dashboard_page'))
    else:
        return redirect(url_for('payments_page'))

@app.route('/deposit-to-card', methods=['POST'])
def deposit_to_card():
    """Handles deposits to the user's virtual card."""
    if 'username' not in session:
        flash("Please log in to make a deposit.", "error")
        return redirect(url_for('login_page'))

    owner = None
    if session['role'] == 'user':
        owner = user_repository.get_by_username(session['username'])
        account_type = 'user'
    elif session['role'] == 'merchant':
        owner = merchant_repository.get_by_username(session['username'])
        account_type = 'merchant'
    if not owner:
        flash("Could not identify your account. Please log in again.", "error")
        session.pop('username', None)
        return redirect(url_for('login_page'))

    if account_type == 'user':
        virtual_card = virtual_card_repository.get_by_user_id(owner.id)
    else:
        virtual_card = virtual_card_repository.get_by_merchant_id(owner.id)

    if not virtual_card:
        flash("You don't have an active virtual card.", "error")
        return redirect(url_for('payments_page'))

    try:
        amount = float(request.form.get('amount', '0'))
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
    except (ValueError, TypeError):
        flash("Please enter a valid, positive deposit amount.", "error")
        return redirect(url_for('payments_page'))

    success, message = transaction_service.cash_in(card_id=virtual_card.id, amount=amount)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('payments_page'))

@app.route('/cart')
def cart_page():
    """Renders the shopping cart page for the current user."""
    if 'username' not in session:
        flash("Please log in to view your cart.", "error")
        return redirect(url_for('login_page'))

    user = user_repository.get_by_username(session['username'])
    if not user:
        flash("User not found. Please log in again.", "error")
        session.pop('username', None)
        return redirect(url_for('login_page'))

    cart = cart_repository.get_cart(user.id)
    if not cart:
        flash(str("Failed to get cart!"), "error")
        cart_items = []
    else:
        cart_items = cart.items

    total_price = sum(item.total_price for item in cart_items) # type: ignore

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout_page():
    """Handles the checkout process."""
    if 'username' not in session:
        flash("Please log in to proceed to checkout.", "error")
        return redirect(url_for('login_page'))

    user = user_repository.get_by_username(session['username'])
    if not user:
        flash("User not found. Please log in again.", "error")
        return redirect(url_for('login_page'))

    # Fetch cart contents for both GET and POST
    cart = cart_repository.get_cart(user.id)
    if not cart:
        flash("Your cart is empty.", "error")
        return redirect(url_for('cart_page'))
    
    cart_items = cart.items

    if request.method == 'POST':
        address_id = request.form.get('address_id', type=int)
        if not address_id:
            flash("Please select a shipping address.", "error")
            return redirect(url_for('checkout_page'))

        # The service layer now handles the entire checkout process
        order_id, message = order_service.create_order_from_cart(user.id, address_id)

        if order_id:
            flash(message, "success")
            return redirect(url_for('orders_page'))
        else:
            flash(message, "error")
            return redirect(url_for('checkout_page'))

    # For GET request
    addr_success, addr_result = address_service.get_user_addresses(user.id)
    if not addr_success:
        flash(str(addr_result), "error")
    addresses = addr_result if addr_success else []

    virtual_card = virtual_card_repository.get_by_user_id(user.id)
    if not virtual_card:
        flash(str("You have no card!"), "error")

    total_price = sum(item.total_price for item in cart_items) # type: ignore

    return render_template('checkout.html', cart_items=cart_items, total_price=total_price, addresses=addresses, virtual_card=virtual_card)

@app.route('/products-page')
def products_page(): 
    """Renders the page that displays all products.

    Returns:
        str: The rendered HTML of the products page with a list of all
        products.
    """
    PRODUCTS_PER_PAGE = 12

    # Capturing all user input
    search_criteria = {
        'query': request.args.get('query'),
        'category': request.args.get('category', type=int),
        'min_price': request.args.get('min_price', type=float, default=None),
        'max_price': request.args.get('max_price', type=float, default=None),
        'min_rating': request.args.get('min_rating', type=float, default=None),
        'sort_by': request.args.get('sort_by'),
        'page': request.args.get('page', 1, type=int)
    }

    categories = product_service.get_all_categories()
    if categories is None:
        flash("Could not load categories.", "error")
        categories = []

    # Use product_service to get filtered, sorted, and paginated products
    success, result = product_service.search_products(
        filters=search_criteria,
        page=search_criteria['page'],
        per_page=PRODUCTS_PER_PAGE
    )

    if not success:
        flash(str(result), "error")
        paginated_products = []
        total_products = 0
    else:
        paginated_products, total_products = result

    # Pagination logic
    total_pages = (int(total_products) + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE
    page = search_criteria['page']

    selected_category = product_service.get_product_category(search_criteria['category']) if search_criteria['category'] else None

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
    # Fetch main product data
    success, product_or_none = product_service.get_product(product_id)
    if not success or not product_or_none:
        flash("Product not found.", "error")
        return redirect(url_for('products_page'))
    product = product_or_none

    # Fetch reviews for the product
    review_success, reviews_or_none = review_service.get_reviews_for_product(product_id)
    reviews = reviews_or_none if review_success and reviews_or_none else []

    # Fetch merchant details
    merchant = None
    if product.merchant_id:
        merchant = merchant_repository.read(product.merchant_id)

    can_review = False
    is_liked = False

    if 'username' in session:
        user = user_repository.get_by_username(session['username'])
        if user:
            # Check if the user has purchased this product to allow reviewing
            can_review = order_repository.has_user_purchased_product(user.id, product_id)
            
            # Check if the user has liked this product
            is_liked = interaction_service.is_product_liked_by_user(user.id, product_id)

    if product:
        # Attach merchant store name to the product object for easy access in the template
        setattr(product, 'store_name', merchant.store_name if merchant else "Unknown Store")

        # Fetch and attach metadata to the product object
        _, metadata = product_service.get_product_metadata(product.id)
        setattr(product, 'sold_count', metadata.sold_count if metadata else 0)

        if product.rating_score and product.rating_count:
            average = product.rating_score / product.rating_count
        else:
            average = 0

    return render_template('product_detail.html', product=product, average=average, reviews=reviews, merchant=merchant, can_review=can_review, is_liked=is_liked)

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

    user = user_repository.get_by_username(session['username'])
    if not user:
        flash("User not found. Please log in again.", "error")
        session.pop('username', None)
        return redirect(url_for('login_page'))

    try:
        product_id = int(request.form.get('product_id') or 0)
        quantity = int(request.form.get('quantity', '1'))
    except (ValueError, TypeError):
        flash("Invalid product or quantity.", "error")
        return redirect(request.referrer or url_for('index'))

    success, message = interaction_service.add_to_cart(user.id, product_id, quantity)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('product_page', product_id=product_id))

@app.route('/update-cart-item/<int:item_id>', methods=['POST'])
def update_cart_item(item_id: int):
    """Updates the quantity of an item in the user's cart."""
    if 'username' not in session:
        flash("Please log in to update your cart.", "error")
        return redirect(url_for('cart_page'))

    user = user_repository.get_by_username(session['username'])
    if not user:
        flash("User not found. Please log in again.", "error")
        session.pop('username', None)
        return redirect(url_for('login_page'))

    try:
        quantity = int(request.form.get('quantity') or 0)
    except (ValueError, TypeError):
        flash("Invalid quantity specified.", "error")
        return redirect(url_for('cart_page'))

    success, message = interaction_service.update_cart_item(user.id, item_id, quantity)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('cart_page'))

@app.route('/remove-from-cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id: int):
    """Removes an item from the user's cart."""
    if 'username' not in session:
        flash("Please log in to update your cart.", "error")
        return redirect(url_for('login_page'))

    user = user_repository.get_by_username(session['username'])
    if not user:
        flash("User not found. Please log in again.", "error")
        return redirect(url_for('login_page'))

    success, message = interaction_service.remove_cart_item(user.id, item_id)
    flash(message, 'success' if success else 'error')
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

    user = user_repository.get_by_username(session['username'])
    if not user:
        flash("User not found. Please log in again.", "error")
        session.pop('username', None)
        return redirect(url_for('login_page'))

    try:
        rating = float(request.form.get('rating', 0))
        description = request.form.get('description', '')
        images = request.files.getlist('images')
    except (ValueError, TypeError):
        flash("Invalid review data submitted.", "error")
        return redirect(url_for('product_page', product_id=product_id))

    success, message = review_service.create_review(
        user_id=user.id, product_id=product_id, rating=rating, description=description
    )
    flash(message, 'success' if success else 'error')

    return redirect(url_for('product_page', product_id=product_id))

@app.route('/like-product/<int:product_id>', methods=['POST'])
def like_product(product_id: int):
    """Toggles a product in the user's liked list."""
    if 'username' not in session:
        flash("Please log in to like products.", "error")
        return redirect(url_for('login_page'))

    user = user_repository.get_by_username(session['username'])
    if not user:
        flash("User not found. Please log in again.", "error")
        session.pop('username', None)
        return redirect(url_for('login_page'))

    success, message = interaction_service.toggle_wishlist_status(user.id, product_id)
    flash(message, 'success' if success else 'error')
    return redirect(request.referrer or url_for('product_page', product_id=product_id))

@app.route('/liked-products')
def liked_products_page():
    """Renders the page showing the user's liked products."""
    if 'username' not in session:
        flash("Please log in to view your liked products.", "error")
        return redirect(url_for('login_page'))

    user = user_repository.get_by_username(session['username'])
    if not user:
        flash("User not found. Please log in again.", "error")
        session.pop('username', None)
        return redirect(url_for('login_page'))

    wishlist_product_ids = user_repository.get_wishlist(user.id)
    liked_products = []
    if wishlist_product_ids:
        for product_id in wishlist_product_ids:
            product_entry = product_repository.get_product_entry(product_id)
            if product_entry:
                liked_products.append(product_entry)

    return render_template('liked-products.html', products=liked_products)

if __name__ == '__main__':
    app.run(debug=True)