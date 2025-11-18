from datetime import datetime
from dataclasses import asdict

from models.accounts import User, UserCreate
from models.products import (Product, ProductCreate, Category, CategoryCreate, 
                              Inventory, InventoryCreate)
from models.orders import (Cart, CartItem, Order, OrderItem, Invoice, Status)
from models.addresses import Address, AddressCreate
from models.payments import VirtualCard, Payment, Voucher
from models.reviews import Review
from models.logs import Interaction, AdminLog

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
        price=65000.00,
        original_price=70000.00,
        discount_rate=0.07,
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
        discount_rate=0.0,
        quantity_available=5
    )
]

mock_users = {
    "testuser": User(
        id=1,
        role="user",
        username="testuser",
        hash="password",
        first_name="Blanca",
        last_name="Evangelista",
        phone_number="676767676767",
        email="blancaevangelista@gmail.com",
        gender="Female",
        age=30,
        created_at=datetime.now()
    )
}

mock_categories = [
    Category(id=1, name="Laptops", parent_id=None, description="Portable computers for work and play."),
    Category(id=2, name="Gaming Laptops", parent_id=1, description="High-performance laptops for gaming."),
]

mock_inventories = [
    Inventory(id=1, product_id=1, quantity_available=5, quantity_reserved=0, locations=[1]),
    Inventory(id=2, product_id=2, quantity_available=5, quantity_reserved=0, locations=[1]),
]

mock_carts = [
    Cart(id=1, user_id=1, items=[
        CartItem(id=1, product_id=1, product_quantity=1, product_price=65000.00, added_at=datetime.now())
    ])
]

mock_orders = [
    Order(id=1, user_id=1, status=Status.DELIVERED, order_created=datetime.now(), payment_type="COD", orders=(
        OrderItem(id=1, product_id=1, product_quantity=1, product_price=65000.00, applied_discounts=[], total_price=65000.00),
    ))
]

mock_invoices = [
    Invoice(id=1, order_id=1, address_id=1, issue_date=datetime.now(), status=Status.PAID, payment_summary="Paid via COD")
]

mock_addresses = [
    Address(id=1, house_no="123", street="Maple Street", city="Springfield", postal_code="12345", additional_notes="N/A")
]

mock_virtual_cards = [
    VirtualCard(id=1, owner_id=1, balance=5000.00)
]

mock_payments = [
    Payment(id=1, sender_id=1, receiver_id=1, type="ORDER", amount=65000.00, created_at=datetime.now())
]

mock_vouchers = [
    Voucher(id=1, merchant_id=1, type="DISCOUNT", active_until=datetime(2026, 12, 31), cashback=0.0, created_at=datetime.now())
]

mock_reviews = [
    Review(id=1, user_id=1, product_id=1, rating=5.0, description="Excellent laptop!", attached=[], likes=10)
]

mock_interactions = [
    Interaction(id=1, user_id=1, interaction_type="VIEW", created_at=datetime.now(), product_id=1)
]

mock_admin_logs = [
    AdminLog(id=1, user_id=1, interaction_type="CREATE", created_at=datetime.now(), target_type="PRODUCT", target_id=1, details="Admin created new product", status="SUCCESS")
]


# Account Management

def mock_login(username: str, password: str) -> dict: 
    user = mock_users.get(username)
    if user and user.hash == password:
        return {
            "status": True, 
            "message": f"Welcome back, {username}!"}   
    return {
        "status": False, 
        "message": "Invalid username or password."}

def mock_register(form_data: dict) -> dict:
    username = form_data.get("username")
    if not username:
        return {"status": False, "message": "Username is required."}
    if username in mock_users:
        return {"status": False, "message": f"Username '{username}' already exists."}

    try:
        user_create_data = UserCreate(**form_data)
        new_id = max(u.id for u in mock_users.values()) + 1 if mock_users else 1
        new_user = User(
            id=new_id,
            role="user",
            created_at=datetime.now(),
            **asdict(user_create_data)
        )
        mock_users[username] = new_user
        return {"status": True, "message": "Registration successful! Please log in."}
    except TypeError as e:
        return {"status": False, "message": f"Invalid registration data: {e}"}

def mock_get_user_by_username(username: str) -> User | None:
    return mock_users.get(username)

def mock_update_user(username: str, form_data: dict) -> dict:
    user_to_update = mock_users.get(username)
    if not user_to_update:
        return {"status": False, "message": "User not found."}

    for key, value in form_data.items():
        if hasattr(user_to_update, key):
            setattr(user_to_update, key, value)
        else:
            return {"status": False, "message": f"Invalid field: {key}"}

    return {"status": True, "message": f"User '{username}' updated successfully."}

def mock_delete_user(username: str) -> dict: 
    if username in mock_users:
        del mock_users[username]
        return {"status": True, "message": f"User '{username}' deleted successfully."}
    return {"status": False, "message": "User not found."}

# Product Management

def mock_get_all_products() -> list[Product]:
    return mock_products

def mock_get_product_by_id(product_id: int) -> Product | None:
    product = next((p for p in mock_products if p.id == product_id), None)
    return product

def mock_create_product(form_data: dict) -> dict: 
    try:
        new_id = max(p.id for p in mock_products) + 1 if mock_products else 1
        product_create = ProductCreate(**form_data)
        new_product = Product(id=new_id, **asdict(product_create))
        mock_products.append(new_product)
        return {"status": True, "message": "Product created successfully.", "product_id": new_id}
    except TypeError as e:
        return {"status": False, "message": f"Invalid product data: {e}"}

def mock_update_product(product_id: int, form_data: dict) -> dict:
    product_to_update = next((p for p in mock_products if p.id == product_id), None)
    if not product_to_update:
        return {"status": False, "message": "Product not found."}

    for key, value in form_data.items():
        if hasattr(product_to_update, key):
            setattr(product_to_update, key, value)
        else:
            return {"status": False, "message": f"Invalid field: {key}"}
            
    return {"status": True, "message": f"Product {product_id} updated successfully."}

def mock_delete_product(product_id: int) -> dict:
    global mock_products
    initial_len = len(mock_products)
    mock_products = [p for p in mock_products if p.id != product_id]
    
    if len(mock_products) < initial_len:
        return {"status": True, "message": f"Product {product_id} deleted successfully."}
    else:
        return {"status": False, "message": "Product not found."}

# Category Management

def mock_get_all_categories() -> list[Category]:
    return mock_categories

def mock_get_category_by_id(category_id: int) -> Category | None:
    return next((c for c in mock_categories if c.id == category_id), None)

def mock_create_category(form_data: dict) -> dict:
    try:
        new_id = max(c.id for c in mock_categories) + 1 if mock_categories else 1
        category_create = CategoryCreate(**form_data)
        new_category = Category(id=new_id, **asdict(category_create))
        mock_categories.append(new_category)
        return {"status": True, "message": "Category created successfully.", "category_id": new_id}
    except TypeError as e:
        return {"status": False, "message": f"Invalid category data: {e}"}

def mock_update_category(category_id: int, form_data: dict) -> dict:
    category_to_update = next((c for c in mock_categories if c.id == category_id), None)
    if not category_to_update:
        return {"status": False, "message": "Category not found."}

    for key, value in form_data.items():
        if hasattr(category_to_update, key):
            setattr(category_to_update, key, value)
        else:
            return {"status": False, "message": f"Invalid field: {key}"}
            
    return {"status": True, "message": f"Category {category_id} updated successfully."}

def mock_delete_category(category_id: int) -> dict:
    global mock_categories
    initial_len = len(mock_categories)
    mock_categories = [c for c in mock_categories if c.id != category_id]
    
    if len(mock_categories) < initial_len:
        return {"status": True, "message": f"Category {category_id} deleted successfully."}
    else:
        return {"status": False, "message": "Category not found."}

# Inventory Management

def mock_get_inventory_by_product_id(product_id: int) -> Inventory | None:
    return next((i for i in mock_inventories if i.product_id == product_id), None)

def mock_update_inventory(inventory_id: int, form_data: dict) -> dict:
    inventory_to_update = next((i for i in mock_inventories if i.id == inventory_id), None)
    if not inventory_to_update:
        return {"status": False, "message": "Inventory not found."}

    for key, value in form_data.items():
        if hasattr(inventory_to_update, key):
            setattr(inventory_to_update, key, value)
        else:
            return {"status": False, "message": f"Invalid field: {key}"}
            
    return {"status": True, "message": f"Inventory {inventory_id} updated successfully."}

def mock_create_inventory(form_data: dict) -> dict:
    try:
        new_id = max(i.id for i in mock_inventories) + 1 if mock_inventories else 1
        inventory_create = InventoryCreate(**form_data)
        new_inventory = Inventory(id=new_id, **asdict(inventory_create))
        mock_inventories.append(new_inventory)
        return {"status": True, "message": "Inventory created successfully.", "inventory_id": new_id}
    except TypeError as e:
        return {"status": False, "message": f"Invalid inventory data: {e}"}

def mock_delete_inventory(inventory_id: int) -> dict:
    global mock_inventories
    initial_len = len(mock_inventories)
    mock_inventories = [i for i in mock_inventories if i.id != inventory_id]
    if len(mock_inventories) < initial_len:
        return {"status": True, "message": f"Inventory {inventory_id} deleted successfully."}
    return {"status": False, "message": "Inventory not found."}

# Cart & Order Management

def mock_get_cart_by_user_id(user_id: int) -> Cart | None: 
    cart = next((c for c in mock_carts if c.user_id == user_id), None)
    if not cart:
        new_id = max(c.id for c in mock_carts) + 1 if mock_carts else 1
        cart = Cart(id=new_id, user_id=user_id, items=[])
        mock_carts.append(cart)
    return cart

def mock_add_item_to_cart(cart_id: int, form_data: dict) -> dict:
    cart = next((c for c in mock_carts if c.id == cart_id), None)
    if not cart:
        return {"status": False, "message": "Cart not found."}

    product_id = form_data.get('product_id')
    product = mock_get_product_by_id(product_id)
    if not product:
        return {"status": False, "message": "Product not found."}

    for item in cart.items:
        if item.product_id == product_id:
            item.product_quantity += form_data.get('product_quantity', 1)
            return {"status": True, "message": "Item quantity updated in cart."}

    new_item_id = max(i.id for c in mock_carts for i in c.items) + 1 if any(c.items for c in mock_carts) else 1
    new_item = CartItem(
        id=new_item_id,
        product_id=product.id,
        product_quantity=form_data.get('product_quantity', 1),
        product_price=product.price,
        added_at=datetime.now()
    )
    cart.items.append(new_item)
    return {"status": True, "message": "Item added to cart."}

def mock_remove_item_from_cart(cart_id: int, item_id: int) -> dict:
    cart = next((c for c in mock_carts if c.id == cart_id), None)
    if not cart:
        return {"status": False, "message": "Cart not found."}
    
    initial_len = len(cart.items)
    cart.items = [item for item in cart.items if item.id != item_id]

    if len(cart.items) < initial_len:
        return {"status": True, "message": "Item removed from cart."}
    return {"status": False, "message": "Item not found in cart."}

def mock_create_order_from_cart(cart_id: int, form_data: dict) -> dict:
    cart = next((c for c in mock_carts if c.id == cart_id), None)
    if not cart or not cart.items:
        return {"status": False, "message": "Cart not found or is empty."}

    new_order_id = max(o.id for o in mock_orders) + 1 if mock_orders else 1
    order_items = []
    for item in cart.items:
        order_item = OrderItem(
            id=item.id,
            product_id=item.product_id,
            product_quantity=item.product_quantity,
            product_price=item.product_price,
            applied_discounts=[],
            total_price=item.product_price * item.product_quantity
        )
        order_items.append(order_item)

    new_order = Order(
        id=new_order_id,
        user_id=cart.user_id,
        status=Status.PENDING,
        order_created=datetime.now(),
        payment_type=form_data.get("payment_type", "N/A"),
        orders=tuple(order_items)
    )
    mock_orders.append(new_order)
    cart.items = [] 
    return {"status": True, "message": "Order created successfully.", "order_id": new_order_id}

def mock_get_orders_by_user_id(user_id: int) -> list[Order]:
    return [o for o in mock_orders if o.user_id == user_id]

# Address Management

def mock_get_address_by_id(address_id: int) -> Address | None:
    return next((a for a in mock_addresses if a.id == address_id), None)

def mock_create_address(form_data: dict) -> dict:
    try:
        new_id = max(a.id for a in mock_addresses) + 1 if mock_addresses else 1
        address_create = AddressCreate(**form_data)
        new_address = Address(id=new_id, **asdict(address_create))
        mock_addresses.append(new_address)
        return {"status": True, "message": "Address created successfully.", "address_id": new_id}
    except TypeError as e:
        return {"status": False, "message": f"Invalid address data: {e}"}

def mock_update_address(address_id: int, form_data: dict) -> dict:
    address_to_update = next((a for a in mock_addresses if a.id == address_id), None)
    if not address_to_update:
        return {"status": False, "message": "Address not found."}

    for key, value in form_data.items():
        if hasattr(address_to_update, key):
            setattr(address_to_update, key, value)
        else:
            return {"status": False, "message": f"Invalid field: {key}"}
            
    return {"status": True, "message": f"Address {address_id} updated successfully."}

def mock_delete_address(address_id: int) -> dict:
    global mock_addresses
    initial_len = len(mock_addresses)
    mock_addresses = [a for a in mock_addresses if a.id != address_id]
    
    if len(mock_addresses) < initial_len:
        return {"status": True, "message": f"Address {address_id} deleted successfully."}
    else:
        return {"status": False, "message": "Address not found."}

# Payment & Voucher Management

def mock_get_virtual_card_by_owner_id(owner_id: int) -> VirtualCard | None:
    return next((vc for vc in mock_virtual_cards if vc.owner_id == owner_id), None)

def mock_process_payment(form_data: dict) -> dict:
    sender_id = form_data.get("sender_id")
    amount = form_data.get("amount")

    card = mock_get_virtual_card_by_owner_id(sender_id)
    if not card:
        return {"status": False, "message": "Sender's virtual card not found."}
    if card.balance < amount:
        return {"status": False, "message": "Insufficient balance."}

    try:
        card.balance -= amount
        new_id = max(p.id for p in mock_payments) + 1 if mock_payments else 1
        new_payment = Payment(
            id=new_id,
            created_at=datetime.now(),
            **form_data
        )
        mock_payments.append(new_payment)
        return {"status": True, "message": "Payment successful.", "payment_id": new_id}
    except TypeError as e:
        return {"status": False, "message": f"Invalid payment data: {e}"}

def mock_get_user_payments(user_id: int) -> list[Payment]:
    return [p for p in mock_payments if p.sender_id == user_id or p.receiver_id == user_id]

def mock_create_voucher(form_data: dict) -> dict:
    try:
        new_id = max(v.id for v in mock_vouchers) + 1 if mock_vouchers else 1
        if isinstance(form_data.get("active_until"), str):
            form_data["active_until"] = datetime.fromisoformat(form_data["active_until"])
        
        new_voucher = Voucher(id=new_id, created_at=datetime.now(), **form_data)
        mock_vouchers.append(new_voucher)
        return {"status": True, "message": "Voucher created successfully.", "voucher_id": new_id}
    except (TypeError, ValueError) as e:
        return {"status": False, "message": f"Invalid voucher data: {e}"}

def mock_get_vouchers_by_merchant(merchant_id: int) -> list[Voucher]:
    now = datetime.now()
    return [v for v in mock_vouchers if v.merchant_id == merchant_id and v.active_until > now]

# --- Reviews & Logging ---

def mock_create_review(form_data: dict) -> dict:
    try:
        new_id = max(r.id for r in mock_reviews) + 1 if mock_reviews else 1
        new_review = Review(id=new_id, **form_data)
        mock_reviews.append(new_review)
        return {"status": True, "message": "Review submitted successfully.", "review_id": new_id}
    except TypeError as e:
        return {"status": False, "message": f"Invalid review data: {e}"}

def mock_get_reviews_by_product_id(product_id: int) -> list[Review]:
    return [r for r in mock_reviews if r.product_id == product_id]

def mock_like_review(review_id: int) -> dict:
    review = next((r for r in mock_reviews if r.id == review_id), None)
    if not review:
        return {"status": False, "message": "Review not found."}
    review.likes += 1
    return {"status": True, "message": "Review liked!"}

def mock_delete_review(review_id: int) -> dict:
    global mock_reviews
    initial_len = len(mock_reviews)
    mock_reviews = [r for r in mock_reviews if r.id != review_id]
    if len(mock_reviews) < initial_len:
        return {"status": True, "message": "Review deleted successfully."}
    return {"status": False, "message": "Review not found."}

def mock_log_user_interaction(form_data: dict) -> dict:   
    try:
        new_id = max(i.id for i in mock_interactions) + 1 if mock_interactions else 1
        new_interaction = Interaction(id=new_id, created_at=datetime.now(), **form_data)
        mock_interactions.append(new_interaction)
        return {"status": True, "message": "Interaction logged."}
    except TypeError as e:
        return {"status": False, "message": f"Invalid interaction data: {e}"}

def mock_get_user_interactions(user_id: int) -> list[Interaction]:
    return [i for i in mock_interactions if i.user_id == user_id]

def mock_log_admin_action(form_data: dict) -> dict:
    try:
        new_id = max(log.id for log in mock_admin_logs) + 1 if mock_admin_logs else 1
        new_log = AdminLog(id=new_id, created_at=datetime.now(), **form_data)
        mock_admin_logs.append(new_log)
        return {"status": True, "message": "Admin action logged."}
    except TypeError as e:
        return {"status": False, "message": f"Invalid log data: {e}"}

def mock_get_all_admin_logs() -> list[AdminLog]:
    return mock_admin_logs
