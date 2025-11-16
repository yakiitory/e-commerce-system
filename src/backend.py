from datetime import datetime
from dataclasses import asdict

from .models.products import Product
from .models.accounts import User


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
    username = form_data.get('username')
    print(f"Mock registration attempt for: {username}")
    return {
        "status": True, 
        "message": "Registration successful! Please log in."}

def mock_get_all_products() -> list[Product]:
    return mock_products

def mock_get_product_by_id(product_id: int) -> Product | None:
    product = next((p for p in mock_products if p.id == product_id), None)
    return product
