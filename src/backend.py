from datetime import datetime
from dataclasses import asdict

from models.accounts import User, UserCreate, Merchant, MerchantCreate, UserMetadata
from models.products import (Product, ProductCreate, ProductMetadata, Category, CategoryCreate, 
                              Inventory, InventoryCreate)
from models.orders import (Cart, CartItem, Order, OrderItem, Invoice, Status) # Make sure AddressCreate has user_id: int | None = None
from models.addresses import Address, AddressCreate # Make sure Address has user_id: int | None = None
from models.payments import VirtualCard, Payment, Voucher # Make sure AddressCreate has user_id: int | None = None
from models.reviews import Review
from models.logs import Interaction, AdminLog

mock_products = [
    Product(
        id=1,
        name="Thinkbook 14+",
        merchant_id=1,
        brand="Lenovo",
        category_id=2,
        description="Operating System: Windows 11 Home Chinese Edition Display: 14.5 16:10 3K (3072x1920) IPS 120Hz 100% DCI-P3 500nits Anti-glare Storage: 1TB M.2 2242 PCIe Gen4 SSD Right: 1x RJ45, USB 3.2 Gen1, SD Card reader (SD/SDHC/SDXC), USB 2.0 (Hidden) Left: USB 3.2 Gen2 (10Gb/s), USB 3.2 Gen1, HDMI 2.1 TMDS, USB-C 4 (Thunderbolt 4, 100W) Features: MIL-STD 810H certified Keyboard and Touchpad: Full-size backlit keyboard, 1.5mm key travel, precision touchpad Audio & Mic: Stereo speakers, 2W x2, Dual microphone array",
        address_id=1,
        images=["/static/img/product1.jpg", "/static/img/product1-no1.jpg"],
        price=65000.00,
        original_price=70000.00,
        quantity_available=5,
    ),
    Product(
        id=2,
        name="Loq ksdfjksdhjfkjhsdfjkhskdfhk jdhfjsdfhsdkfh",
        merchant_id=1,
        brand="Lenovo",
        category_id=2,
        description="AMD Ryzen 7 7435HS (8C / 16T, 3.1 / 4.5GHz, 4MB L2 / 16MB L3)2x 12GB SODIMM DDR5-4800 1TB SSD M.2 2242 PCIe 4.0x4 NVMe NVIDIA GeForce RTX 4070 8GB GDDR6, Boost Clock 2175MHz, TGP 115W Windows 11 Home, Portuguese / English 3-year, Courier or Carry-in",
        address_id=1,
        images=["/static/img/product2.jpg", "/static/img/product2-no1.jpg"],
        price=80000.00,
        original_price=80000.00,
        quantity_available=5
    )
]

mock_product_metadata = [
    ProductMetadata(product_id=1, sold_count=25, rating_avg=4.5, rating_count=1),
    ProductMetadata(product_id=2, sold_count=10, rating_avg=5.0, rating_count=0),
]

mock_user_metadata = [
    UserMetadata(id=1, user_id=2, liked_products=(1,)) # User 2 likes product 1
]

mock_users = {
    "testmerchant": Merchant(
        id=1,
        role="merchant",
        username="testmerchant",
        hash="password",
        first_name="Steven",
        last_name="Universe",
        phone_number="1234567890",
        email="contact@lenovo.com",
        store_name="Lenovo Official",
        created_at=datetime.now()
    ),
    "testuser": User(
        id=2,
        role="user",
        username="testuser",
        hash="password",
        first_name="Juan",
        last_name="Dela Cruz",
        phone_number="09123456789",
        email="juan@example.com",
        gender="Male",
        age=25,
        created_at=datetime.now()
    ),
    "fayefaye": User(
        id=2,
        role="user",
        username="fayefaye",
        hash="password",
        first_name="Faye",
        last_name="Peteros",
        phone_number="09123456789",
        email="juan@example.com",
        gender="Female",
        age=25,
        created_at=datetime.now()
    )
}

mock_categories = [
    Category(id=1, name="Electronics", parent_id=None, description="Gadgets and devices."),
    Category(id=2, name="Laptops", parent_id=1, description="Portable computers for work and play."),
    Category(id=3, name="Smartphones", parent_id=1, description="Mobile phones with advanced features."),
    Category(id=4, name="Clothing", parent_id=None, description="Apparel and accessories."),
    Category(id=5, name="Men's", parent_id=4, description="Clothing for men."),
    Category(id=6, name="Women's", parent_id=4, description="Clothing for women."),
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
    Order(id=1, user_id=2, status=Status.DELIVERED, order_created=datetime.now(), payment_type="COD", orders=(
        OrderItem(id=1, product_id=1, product_quantity=1, product_price=65000.00, applied_discounts=[], total_price=65000.00),
    ))
    # Order(id=2, user_id=2, status=Status.DELIVERED, order_created=datetime.now(), payment_type="COD", orders=(
    #     OrderItem(id=2, product_id=2, product_quantity=1, product_price=80000.00, applied_discounts=[], total_price=80000.00),
    # ))
]

mock_invoices = [
    Invoice(id=1, order_id=1, address_id=1, issue_date=datetime.now(), status=Status.PAID, payment_summary="Paid via Virtual Card")
]

mock_addresses = [
    Address(id=1, house_no="123", street="Maple Street", city="Springfield", postal_code="12345", additional_notes="N/A")
]

# Mock junction tables to represent the many-to-many relationship
mock_user_addresses = [
    # (user_id, address_id)
    (2, 1) 
]
mock_merchant_addresses = [
    # (merchant_id, address_id) - Assuming merchant with id=1 has an address
    (1, 1)
]
mock_virtual_cards = [
    # Merchant's card, with funds received from the mock payment
    VirtualCard(id=1, owner_id=1, balance=70000.00),
    # User's card, with funds spent on the mock payment
    VirtualCard(id=2, owner_id=2, balance=10000.00)
]

mock_payments = [
    Payment(id=1, sender_id=2, receiver_id=1, type="ORDER", amount=65000.00, created_at=datetime.now())
]

mock_reviews = [
    Review(id=1, user_id=2, product_id=1, rating=5.0, description="Excellent laptop!", attached=[], likes=10)
]

mock_interactions = [
    Interaction(id=1, user_id=1, interaction_type="VIEW", created_at=datetime.now(), product_id=1)
]

mock_admin_logs = [
    AdminLog(id=1, user_id=1, interaction_type="CREATE", created_at=datetime.now(), target_type="PRODUCT", target_id=1, details="Admin created new product", status="SUCCESS")
]


# Account Management

def mock_login(username: str, password: str) -> dict: 
    """Authenticates a user based on username and password.

    Args:
        username (str): The user's username.
        password (str): The user's password.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
    user = mock_users.get(username)
    if user and user.hash == password:
        return {
            "status": True, 
            "message": f"Welcome back, {username}!"}   
    return {
        "status": False, 
        "message": "Invalid username or password."}

def mock_register(form_data: dict) -> dict:
    """Registers a new user or merchant.

    The function determines whether to create a user or a merchant based on
    the presence of a 'store_name' in the form data.

    Args:
        form_data (dict): A dictionary containing user or merchant registration details.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
    username = form_data.get("username")
    if not username:
        return {"status": False, "message": "Username is required."}
    if username in mock_users:
        return {"status": False, "message": f"Username '{username}' already exists."}

    try:
        new_id = max(u.id for u in mock_users.values()) + 1 if mock_users else 1

        if 'store_name' in form_data:
            # Merchant Registration
            if 'password' in form_data:
                form_data['hash'] = form_data.pop('password', None)
                form_data.pop('re_password', None)
            
            address_fields = ['house_number', 'street', 'city', 'postal', 'additional_notes']
            address_data = {key: form_data.pop(key) for key in address_fields if key in form_data}
            if 'house_number' in address_data:
                address_data['house_no'] = address_data.pop('house_number')
            if 'postal' in address_data:
                address_data['postal_code'] = address_data.pop('postal')

            address_result = mock_create_address(address_data)
            if not address_result['status']:
                return {"status": False, "message": f"Failed to create address: {address_result['message']}"}
            
            # Link address to merchant in the junction table
            mock_merchant_addresses.append((new_id, address_result['address_id']))
            
            merchant_create_data = MerchantCreate(**form_data)
            
            new_account = Merchant(
                id=new_id,
                role="merchant",
                created_at=datetime.now(),
                **asdict(merchant_create_data)
            )
        else:
            # User Registration
            if 'password' in form_data:
                form_data['hash'] = form_data.pop('password', None)
                form_data.pop('re_password', None)

            address_fields = ['house_number', 'street', 'city', 'postal', 'additional_notes']
            address_data = {key: form_data.pop(key) for key in address_fields if key in form_data}
            if 'house_number' in address_data:
                address_data['house_no'] = address_data.pop('house_number')
            if 'postal' in address_data:
                address_data['postal_code'] = address_data.pop('postal')

            address_result = mock_create_address(address_data)
            if not address_result['status']:
                return {"status": False, "message": f"Failed to create address: {address_result['message']}"}

            # Link address to user in the junction table
            mock_user_addresses.append((new_id, address_result['address_id']))

            user_create_fields = [
                'username', 'hash', 'first_name', 'last_name', 
                'phone_number', 'email', 'gender', 'age'
            ]
            user_create_dict = {key: form_data[key] for key in user_create_fields if key in form_data}

            user_create_data = UserCreate(**user_create_dict)
            
            new_account = User(
                id=new_id,
                role="user",
                created_at=datetime.now(),
                **asdict(user_create_data)
            )

        mock_users[username] = new_account
        return {"status": True, "message": "Registration successful! Please log in."}
    except (TypeError, KeyError) as e:
        return {"status": False, "message": f"Invalid registration data: {e}"}

def mock_get_user_by_username(username: str) -> User | None:
    """Retrieves a user object by their username.

    Args:
        username (str): The username of the user to retrieve.

    Returns:
        User | None: The User object if found, otherwise None.
    """
    return mock_users.get(username)

def mock_update_user(username: str, form_data: dict) -> dict:
    """Updates a user's information.

    Args:
        username (str): The username of the user to update.
        form_data (dict): A dictionary with the fields to update.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
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
    """Deletes a user from the mock database.

    Args:
        username (str): The username of the user to delete.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
    if username in mock_users:
        del mock_users[username]
        return {"status": True, "message": f"User '{username}' deleted successfully."}
    return {"status": False, "message": "User not found."}

def mock_change_password(username: str, old_password: str, new_password: str) -> dict:
    """Changes a user's password after verifying the old one.

    Args:
        username (str): The username of the user.
        old_password (str): The user's current password.
        new_password (str): The new password to set.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
    user = mock_users.get(username)
    if not user:
        return {"status": False, "message": "User not found."}

    if user.hash != old_password:
        return {"status": False, "message": "Incorrect current password."}

    if len(new_password) < 6:
        return {"status": False, "message": "New password must be at least 6 characters long."}

    user.hash = new_password
    return {"status": True, "message": "Password changed successfully."}

# Product Management

def mock_get_all_products() -> list[Product]:
    """Retrieves all products from the mock database.

    Returns:
        list[Product]: A list of all Product objects.
    """
    return mock_products

def mock_get_products_by_category_id(category_id: int) -> list[Product]:
    """Retrieves all products belonging to a specific category.

    Args:
        category_id (int): The ID of the category.

    Returns:
        list[Product]: A list of Product objects in that category.
    """
    if not category_id:
        return mock_get_all_products()
    return [p for p in mock_products if p.category_id == category_id]

def mock_get_products_by_merchant_id(merchant_id: int) -> list[Product]:
    """Retrieves all products for a specific merchant.

    Args:
        merchant_id (int): The ID of the merchant.

    Returns:
        list[Product]: A list of Product objects.
    """
    return [p for p in mock_products if p.merchant_id == merchant_id]


def mock_get_product_by_id(product_id: int) -> Product | None:
    """Retrieves a single product by its ID.

    Args:
        product_id (int): The ID of the product to retrieve.

    Returns:
        Product | None: The Product object if found, otherwise None.
    """
    product = next((p for p in mock_products if p.id == product_id), None)
    return product

def mock_create_product(product_data: ProductCreate) -> dict:
    """Creates a new product.

    This mock function is designed to accept a ProductCreate object,
    mirroring the behavior of the real product_service. This allows it
    to correctly handle complex data like the list of image URLs.

    Args:
        product_data (ProductCreate): A dataclass object containing the product details.

    Returns:
        dict: A dictionary with status, message, and the new product's ID.
    """
    try:
        new_id = max(p.id for p in mock_products) + 1 if mock_products else 1
        # Convert the ProductCreate object to a dictionary to create the full Product
        new_product = Product(id=new_id, **asdict(product_data))
        mock_products.append(new_product)
        # Also create a corresponding metadata entry for the new product
        mock_product_metadata.append(ProductMetadata(product_id=new_id))
        return {"status": True, "message": "Product created successfully.", "product_id": new_id}
    except TypeError as e:
        return {"status": False, "message": f"Invalid product data: {e}"}

def mock_update_product(product_id: int, form_data: dict) -> dict:
    """Updates a product's information.

    Args:
        product_id (int): The ID of the product to update.
        form_data (dict): A dictionary with the fields to update.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
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
    """Deletes a product from the mock database.

    Args:
        product_id (int): The ID of the product to delete.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
    global mock_products
    initial_len = len(mock_products)
    mock_products = [p for p in mock_products if p.id != product_id]
    
    if len(mock_products) < initial_len:
        return {"status": True, "message": f"Product {product_id} deleted successfully."}
    else:
        return {"status": False, "message": "Product not found."}

def mock_get_product_metadata(product_id: int) -> ProductMetadata | None:
    """Retrieves the metadata for a specific product.

    Args:
        product_id (int): The ID of the product.

    Returns:
        ProductMetadata | None: The ProductMetadata object if found, otherwise None.
    """
    return next((meta for meta in mock_product_metadata if meta.product_id == product_id), None)

def mock_get_user_metadata(user_id: int) -> UserMetadata | None:
    """Retrieves the metadata for a specific user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        UserMetadata | None: The UserMetadata object if found, otherwise None.
    """
    return next((meta for meta in mock_user_metadata if meta.user_id == user_id), None)

# Category Management

def mock_get_all_categories() -> list[Category]:
    """Retrieves all categories.

    Returns:
        list[Category]: A list of all Category objects.
    """
    return mock_categories

def mock_get_category_by_id(category_id: int) -> Category | None:
    """Retrieves a single category by its ID.

    Args:
        category_id (int): The ID of the category to retrieve.

    Returns:
        Category | None: The Category object if found, otherwise None.
    """
    return next((c for c in mock_categories if c.id == category_id), None)

def mock_create_category(form_data: dict) -> dict:
    """Creates a new category.

    Args:
        form_data (dict): A dictionary containing the category details.

    Returns:
        dict: A dictionary with status, message, and the new category's ID.
    """
    try:
        new_id = max(c.id for c in mock_categories) + 1 if mock_categories else 1
        category_create = CategoryCreate(**form_data)
        new_category = Category(id=new_id, **asdict(category_create))
        mock_categories.append(new_category)
        return {"status": True, "message": "Category created successfully.", "category_id": new_id}
    except TypeError as e:
        return {"status": False, "message": f"Invalid category data: {e}"}

def mock_update_category(category_id: int, form_data: dict) -> dict:
    """Updates a category's information.

    Args:
        category_id (int): The ID of the category to update.
        form_data (dict): A dictionary with the fields to update.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
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
    """Deletes a category from the mock database.

    Args:
        category_id (int): The ID of the category to delete.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
    global mock_categories
    initial_len = len(mock_categories)
    mock_categories = [c for c in mock_categories if c.id != category_id]
    
    if len(mock_categories) < initial_len:
        return {"status": True, "message": f"Category {category_id} deleted successfully."}
    else:
        return {"status": False, "message": "Category not found."}

# Inventory Management

def mock_get_inventory_by_product_id(product_id: int) -> Inventory | None:
    """Retrieves the inventory for a specific product.

    Args:
        product_id (int): The ID of the product.

    Returns:
        Inventory | None: The Inventory object if found, otherwise None.
    """
    return next((i for i in mock_inventories if i.product_id == product_id), None)

def mock_update_inventory(inventory_id: int, form_data: dict) -> dict:
    """Updates an inventory's information.

    Args:
        inventory_id (int): The ID of the inventory to update.
        form_data (dict): A dictionary with the fields to update.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
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
    """Creates a new inventory record.

    Args:
        form_data (dict): A dictionary containing inventory details.

    Returns:
        dict: A dictionary with status, message, and the new inventory's ID.
    """
    try:
        new_id = max(i.id for i in mock_inventories) + 1 if mock_inventories else 1
        inventory_create = InventoryCreate(**form_data)
        new_inventory = Inventory(id=new_id, **asdict(inventory_create))
        mock_inventories.append(new_inventory)
        return {"status": True, "message": "Inventory created successfully.", "inventory_id": new_id}
    except TypeError as e:
        return {"status": False, "message": f"Invalid inventory data: {e}"}

def mock_delete_inventory(inventory_id: int) -> dict:
    """Deletes an inventory record.

    Args:
        inventory_id (int): The ID of the inventory to delete.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
    global mock_inventories
    initial_len = len(mock_inventories)
    mock_inventories = [i for i in mock_inventories if i.id != inventory_id]
    if len(mock_inventories) < initial_len:
        return {"status": True, "message": f"Inventory {inventory_id} deleted successfully."}
    return {"status": False, "message": "Inventory not found."}

# Cart & Order Management

def mock_get_cart_by_user_id(user_id: int) -> Cart | None: 
    """Retrieves a user's cart, creating one if it doesn't exist.

    Args:
        user_id (int): The ID of the user.

    Returns:
        Cart | None: The user's Cart object.
    """
    cart = next((c for c in mock_carts if c.user_id == user_id), None)
    if not cart:
        new_id = max(c.id for c in mock_carts) + 1 if mock_carts else 1
        cart = Cart(id=new_id, user_id=user_id, items=[])
        mock_carts.append(cart)
    return cart

def mock_add_item_to_cart(cart_id: int, form_data: dict) -> dict:
    """Adds an item to a specified cart.

    If the item already exists in the cart, its quantity is updated.

    Args:
        cart_id (int): The ID of the cart.
        form_data (dict): Dictionary with 'product_id' and 'product_quantity'.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
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

def mock_update_cart_item_quantity(cart_id: int, item_id: int, quantity: int) -> dict:
    """Updates the quantity of a specific item in a cart.

    Args:
        cart_id (int): The ID of the cart.
        item_id (int): The ID of the cart item to update.
        quantity (int): The new quantity for the item.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
    cart = next((c for c in mock_carts if c.id == cart_id), None)
    if not cart:
        return {"status": False, "message": "Cart not found."}

    item_to_update = next((item for item in cart.items if item.id == item_id), None)
    if not item_to_update:
        return {"status": False, "message": "Item not found in cart."}

    if quantity > 0:
        item_to_update.product_quantity = quantity
        return {"status": True, "message": "Cart updated successfully."}
    else:
        return mock_remove_item_from_cart(cart_id, item_id)

def mock_remove_item_from_cart(cart_id: int, item_id: int) -> dict:
    """Removes an item from a cart.

    Args:
        cart_id (int): The ID of the cart.
        item_id (int): The ID of the cart item to remove.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
    cart = next((c for c in mock_carts if c.id == cart_id), None)
    if not cart:
        return {"status": False, "message": "Cart not found."}
    
    initial_len = len(cart.items)
    cart.items = [item for item in cart.items if item.id != item_id]

    if len(cart.items) < initial_len:
        return {"status": True, "message": "Item removed from cart."}
    return {"status": False, "message": "Item not found in cart."}

def mock_clear_cart(cart_id: int) -> dict:
    """Removes all items from a cart.

    Args:
        cart_id (int): The ID of the cart to clear.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
    cart = next((c for c in mock_carts if c.id == cart_id), None)
    if not cart:
        return {"status": False, "message": "Cart not found."}
    cart.items = []
    return {"status": True, "message": "Cart cleared successfully."}

def mock_create_order_from_cart(cart_id: int, form_data: dict) -> dict:
    """Creates an order from all items in a cart and then empties the cart.

    Args:
        cart_id (int): The ID of the cart to convert into an order.
        form_data (dict): Dictionary containing order details like 'payment_type'.

    Returns:
        dict: A dictionary with status, message, and the new order's ID.
    """
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

        # --- Update Product Quantity ---
        product_to_update = mock_get_product_by_id(item.product_id)
        if product_to_update:
            if product_to_update.quantity_available >= item.product_quantity:
                product_to_update.quantity_available -= item.product_quantity
                # Update sold_count in metadata
                metadata = mock_get_product_metadata(item.product_id)
                if metadata:
                    metadata.sold_count += item.product_quantity
            else:
                # This is a failsafe. In a real app, this check should happen earlier.
                return {"status": False, "message": f"Not enough stock for {product_to_update.name}."}
        # -----------------------------

    new_order = Order(
        id=new_order_id,
        user_id=cart.user_id,
        status=Status.PENDING,
        order_created=datetime.now(),
        payment_type=form_data.get("payment_type", "N/A"),
        orders=tuple(order_items)
    )
    mock_orders.append(new_order)
    return {"status": True, "message": "Order created successfully.", "order_id": new_order_id}

def mock_get_orders_by_user_id(user_id: int) -> list[Order]:
    """Retrieves all orders for a specific user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        list[Order]: A list of Order objects belonging to the user.
    """
    return [o for o in mock_orders if o.user_id == user_id]

def mock_get_orders_by_merchant_id(merchant_id: int) -> list[Order]:
    """Retrieves all orders containing products from a specific merchant.

    Args:
        merchant_id (int): The ID of the merchant.

    Returns:
        list[Order]: A list of relevant Order objects.
    """
    merchant_orders = []
    merchant_product_ids = {p.id for p in mock_get_products_by_merchant_id(merchant_id)}
    
    for order in mock_orders:
        for item in order.orders:
            if item.product_id in merchant_product_ids:
                merchant_orders.append(order)
                break # Move to the next order once a match is found
    return merchant_orders

def mock_update_order_status(order_id: int, new_status: Status) -> dict:
    """Updates the status of a specific order.

    Args:
        order_id (int): The ID of the order to update.
        new_status (Status): The new status for the order.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
    order_to_update = next((o for o in mock_orders if o.id == order_id), None)
    if not order_to_update:
        return {"status": False, "message": "Order not found."}

    order_to_update.status = new_status
    return {"status": True, "message": f"Order status updated to {new_status.value}."}


def mock_create_invoice(order_id: int, address_id: int) -> dict:
    """Creates an invoice for a given order.

    Args:
        order_id (int): The ID of the order.
        address_id (int): The ID of the shipping address.

    Returns:
        dict: A dictionary with status, message, and the new invoice's ID.
    """
    try:
        new_id = max(i.id for i in mock_invoices) + 1 if mock_invoices else 1
        new_invoice = Invoice(id=new_id, order_id=order_id, address_id=address_id, issue_date=datetime.now(), status=Status.PAID, payment_summary="Paid via Virtual Card")
        mock_invoices.append(new_invoice)
        return {"status": True, "message": "Invoice created successfully.", "invoice_id": new_id}
    except Exception as e:
        return {"status": False, "message": f"Failed to create invoice: {e}"}

def mock_get_invoice_by_order_id(order_id: int) -> Invoice | None:
    """Retrieves an invoice by its associated order ID.

    Args:
        order_id (int): The ID of the order.

    Returns:
        Invoice | None: The Invoice object if found, otherwise None.
    """
    return next((i for i in mock_invoices if i.order_id == order_id), None)


def mock_get_addresses_by_user_id(user_id: int) -> list[Address]:
    """Retrieves all addresses associated with a user OR merchant.

    This function checks both user and merchant address link tables to
    find all addresses associated with a given ID.

    Args:
        user_id (int): The ID of the user or merchant.

    Returns:
        list[Address]: A list of the user's Address objects.
    """
    address_ids = [addr_id for u_id, addr_id in mock_user_addresses if u_id == user_id]
    address_ids.extend([addr_id for m_id, addr_id in mock_merchant_addresses if m_id == user_id])
    return [addr for addr in mock_addresses if addr.id in address_ids]

# Address Management

def mock_get_address_by_id(address_id: int) -> Address | None:
    """Retrieves a single address by its ID.

    Args:
        address_id (int): The ID of the address to retrieve.

    Returns:
        Address | None: The Address object if found, otherwise None.
    """
    return next((a for a in mock_addresses if a.id == address_id), None)

def mock_create_address(form_data: dict, user_id: int | None = None) -> dict:
    """Creates a new address.

    If a user_id is provided, it also links the new address to the user
    in the mock junction table.

    Args:
        form_data (dict): A dictionary containing address details.
        user_id (int | None): The ID of the user creating the address.

    Returns:
        dict: A dictionary with status, message, and the new address's ID.
    """
    try:
        new_id = max(a.id for a in mock_addresses) + 1 if mock_addresses else 1
        address_create = AddressCreate(**form_data)
        new_address = Address(id=new_id, **asdict(address_create))
        mock_addresses.append(new_address)

        if user_id:
            mock_user_addresses.append((user_id, new_id))

        return {"status": True, "message": "Address created successfully.", "address_id": new_id}
    except TypeError as e:
        return {"status": False, "message": f"Invalid address data: {e}"}

def mock_update_address(address_id: int, form_data: dict) -> dict:
    """Updates an address's information.

    Args:
        address_id (int): The ID of the address to update.
        form_data (dict): A dictionary with the fields to update.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
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
    """Deletes an address from the mock database.

    Args:
        address_id (int): The ID of the address to delete.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
    global mock_addresses
    initial_len = len(mock_addresses)
    mock_addresses = [a for a in mock_addresses if a.id != address_id]

    # Also remove links from junction tables
    global mock_user_addresses
    mock_user_addresses = [(u_id, a_id) for u_id, a_id in mock_user_addresses if a_id != address_id]
    
    if len(mock_addresses) < initial_len:
        return {"status": True, "message": f"Address {address_id} deleted successfully."}
    else:
        return {"status": False, "message": "Address not found."}

# Payment & Voucher Management

def mock_get_virtual_card_by_owner_id(owner_id: int) -> VirtualCard | None:
    """Retrieves a virtual card by the owner's ID.

    Args:
        owner_id (int): The ID of the card owner.

    Returns:
        VirtualCard | None: The VirtualCard object if found, otherwise None.
    """
    return next((vc for vc in mock_virtual_cards if vc.owner_id == owner_id), None)

def mock_create_virtual_card(owner_id: int) -> dict:
    """Creates a new virtual card for a user.

    Args:
        owner_id (int): The ID of the user who will own the card.

    Returns:
        dict: A dictionary with status and message.
    """
    if mock_get_virtual_card_by_owner_id(owner_id):
        return {"status": False, "message": "User already has a virtual card."}

    new_id = max(vc.id for vc in mock_virtual_cards) + 1 if mock_virtual_cards else 1
    new_card = VirtualCard(id=new_id, owner_id=owner_id, balance=0.00)
    mock_virtual_cards.append(new_card)
    return {"status": True, "message": "Virtual card activated successfully!"}

def mock_deposit_to_virtual_card(card_id: int, amount: float) -> dict:
    """Deposits a specified amount into a virtual card.

    Args:
        card_id (int): The ID of the virtual card.
        amount (float): The amount to deposit.

    Returns:
        dict: A dictionary with status and message.
    """
    card = next((vc for vc in mock_virtual_cards if vc.id == card_id), None)
    if not card:
        return {"status": False, "message": "Virtual card not found."}
    card.balance += amount
    return {"status": True, "message": f"Successfully deposited ₱{amount:,.2f}."}

def mock_process_payment(form_data: dict) -> dict:
    """Processes a payment from a sender's virtual card.

    Args:
        form_data (dict): Dictionary with 'sender_id' and 'amount'.

    Returns:
        dict: A dictionary with status, message, and the new payment's ID.
    """
    sender_id = form_data.get("sender_id")
    receiver_id = form_data.get("receiver_id")
    amount = form_data.get("amount")

    sender_card = mock_get_virtual_card_by_owner_id(sender_id)
    if not sender_card:
        return {"status": False, "message": "Sender's virtual card not found."}
    if sender_card.balance < amount:
        return {"status": False, "message": "Insufficient balance."}

    receiver_card = mock_get_virtual_card_by_owner_id(receiver_id)
    if not receiver_card:
        return {"status": False, "message": "The merchant cannot accept payments at this time. Please try again later."}

    try:
        # Transfer funds
        sender_card.balance -= amount
        receiver_card.balance += amount

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
    """Retrieves all payments where the user was the sender or receiver.

    Args:
        user_id (int): The ID of the user.

    Returns:
        list[Payment]: A list of Payment objects.
    """
    return sorted([p for p in mock_payments if p.sender_id == user_id or p.receiver_id == user_id], key=lambda p: p.created_at, reverse=True)

# --- Reviews & Logging ---

def mock_create_review(form_data: dict) -> dict:
    """Creates a new product review.

    Args:
        form_data (dict): A dictionary containing review details like
                          'user_id', 'product_id', 'rating', etc.

    Returns:
        dict: A dictionary with status, message, and the new review's ID.
    """
    try:
        new_id = max(r.id for r in mock_reviews) + 1 if mock_reviews else 1
        new_review = Review(id=new_id, **form_data)
        mock_reviews.append(new_review)
        return {"status": True, "message": "Review submitted successfully.", "review_id": new_id}
    except TypeError as e:
        return {"status": False, "message": f"Invalid review data: {e}"}

def mock_get_reviews_by_product_id(product_id: int) -> list[Review]:
    """Retrieves all reviews for a specific product.

    Args:
        product_id (int): The ID of the product.

    Returns:
        list[Review]: A list of Review objects for the product.
    """
    return [r for r in mock_reviews if r.product_id == product_id]

def mock_like_review(review_id: int) -> dict:
    """Increments the 'likes' count of a review.

    Args:
        review_id (int): The ID of the review to like.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
    review = next((r for r in mock_reviews if r.id == review_id), None)
    if not review:
        return {"status": False, "message": "Review not found."}
    review.likes += 1
    return {"status": True, "message": "Review liked!"}

def mock_delete_review(review_id: int) -> dict:
    """Deletes a review from the mock database.

    Args:
        review_id (int): The ID of the review to delete.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
    global mock_reviews
    initial_len = len(mock_reviews)
    mock_reviews = [r for r in mock_reviews if r.id != review_id]
    if len(mock_reviews) < initial_len:
        return {"status": True, "message": "Review deleted successfully."}
    return {"status": False, "message": "Review not found."}

def mock_log_user_interaction(form_data: dict) -> dict:   
    """Logs a user interaction, such as a product view.

    Args:
        form_data (dict): Dictionary with interaction details like 'user_id',
                          'interaction_type', and 'product_id'.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
    try:
        new_id = max(i.id for i in mock_interactions) + 1 if mock_interactions else 1
        new_interaction = Interaction(id=new_id, created_at=datetime.now(), **form_data)
        mock_interactions.append(new_interaction)
        return {"status": True, "message": "Interaction logged."}
    except TypeError as e:
        return {"status": False, "message": f"Invalid interaction data: {e}"}

def mock_get_user_interactions(user_id: int) -> list[Interaction]:
    """Retrieves all interactions for a specific user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        list[Interaction]: A list of Interaction objects.
    """
    return [i for i in mock_interactions if i.user_id == user_id]

def mock_log_admin_action(form_data: dict) -> dict:
    """Logs an action performed by an administrator.

    Args:
        form_data (dict): Dictionary with log details like 'user_id',
                          'interaction_type', 'target_type', 'target_id',
                          'details', and 'status'.

    Returns:
        dict: A dictionary with a 'status' boolean and a 'message' string.
    """
    try:
        new_id = max(log.id for log in mock_admin_logs) + 1 if mock_admin_logs else 1
        new_log = AdminLog(id=new_id, created_at=datetime.now(), **form_data)
        mock_admin_logs.append(new_log)
        return {"status": True, "message": "Admin action logged."}
    except TypeError as e:
        return {"status": False, "message": f"Invalid log data: {e}"}

def mock_get_all_admin_logs() -> list[AdminLog]:
    """Retrieves all admin logs.

    Returns:
        list[AdminLog]: A list of all AdminLog objects.
    """
    return mock_admin_logs

def mock_like_unlike_product(user_id: int, product_id: int) -> dict:
    """Toggles a product in a user's liked list.

    Args:
        user_id (int): The ID of the user.
        product_id (int): The ID of the product.

    Returns:
        dict: A dictionary with status and message.
    """
    metadata = mock_get_user_metadata(user_id)
    if not metadata:
        return {"status": False, "message": "User metadata not found."}

    liked_list = list(metadata.liked_products)
    if product_id in liked_list:
        liked_list.remove(product_id)
        metadata.liked_products = tuple(liked_list)
        return {"status": True, "message": "Product removed from your likes."}
    else:
        liked_list.append(product_id)
        metadata.liked_products = tuple(liked_list)
        return {"status": True, "message": "Product added to your likes!"}

def mock_get_liked_products(user_id: int) -> list[Product]:
    """Retrieves all products liked by a user.
    """
    metadata = mock_get_user_metadata(user_id)
    if not metadata:
        return []
    return [p for p in mock_products if p.id in metadata.liked_products]
