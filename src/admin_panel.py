"""
E-Commerce Admin Panel - CLI Interface
A comprehensive command-line tool for system administrators
"""

import os
import sys
from datetime import datetime
from getpass import getpass
from typing import Optional


# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.database import Database
from repositories import (
    AdminRepository,
    UserRepository,
    MerchantRepository,
    ProductRepository,
    ProductMetadataRepository,
    OrderRepository,
    CategoryRepository,
    CartRepository
)
from services import AuthService
from models.accounts import Admin, AdminCreate
from models.status import Status


class AdminPanel:
    """Main admin panel controller"""
    
    def __init__(self):
        """Initialize the admin panel with database and repositories"""
        self.db = Database()
        
        # Initialize repositories
        self.admin_repo = AdminRepository(self.db)
        self.user_repo = UserRepository(self.db)
        self.merchant_repo = MerchantRepository(self.db)
        self.product_repo = ProductRepository(self.db)
        self.product_meta_repo = ProductMetadataRepository(self.db)
        self.cart_repo = CartRepository(self.db, self.product_meta_repo)
        self.order_repo = OrderRepository(self.db, self.cart_repo)
        self.category_repo = CategoryRepository(self.db)
        
        # Initialize services
        self.auth_service = AuthService(
            user_repo=self.user_repo,
            merchant_repo=self.merchant_repo,
            admin_repo=self.admin_repo
        )
        
        self.current_admin: Optional[Admin] = None
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str):
        """Print a formatted header"""
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)
    
    def print_menu(self, options: dict):
        """Print a menu with numbered options"""
        print()
        for key, value in options.items():
            print(f"  [{key}] {value}")
        print()
    
    def get_input(self, prompt: str, required: bool = True) -> str:
        """Get user input with optional validation"""
        while True:
            value = input(f"  {prompt}: ").strip()
            if value or not required:
                return value
            print("  [!] This field is required. Please try again.")
    
    def confirm_action(self, message: str) -> bool:
        """Ask for confirmation before proceeding"""
        response = input(f"  {message} (yes/no): ").strip().lower()
        return response in ['yes', 'y']
    
    def pause(self):
        """Pause and wait for user input"""
        input("\n  Press Enter to continue...")
    
    # ========== AUTHENTICATION ==========
    
    def login(self) -> bool:
        """Admin login screen"""
        self.clear_screen()
        self.print_header("ADMIN LOGIN")
        
        print("\n  Please enter your admin credentials\n")
        
        username = self.get_input("Username")
        password = getpass("  Password: ")
        
        print("\n  Authenticating...")
        success, admin = self.auth_service.login_admin(username, password)
        
        if success and admin:
            self.current_admin = admin
            print(f"\n  [OK] Welcome, {username}!")
            print(f"  Role: {admin.role.upper()}")
            self.pause()
            return True
        else:
            print("\n  [ERROR] Authentication failed. Invalid credentials.")
            self.pause()
            return False
    
    def create_first_admin(self):
        """Create the first admin account if none exists"""
        self.clear_screen()
        self.print_header("INITIAL SETUP - CREATE ADMIN ACCOUNT")
        
        print("\n  No admin accounts found. Let's create the first one.\n")
        
        username = self.get_input("Admin Username")
        password = getpass("  Password: ")
        confirm_password = getpass("  Confirm Password: ")
        
        if password != confirm_password:
            print("\n  [ERROR] Passwords do not match!")
            self.pause()
            return False
        
        if len(password) < 6:
            print("\n  [ERROR] Password must be at least 6 characters long!")
            self.pause()
            return False
        
        admin_data = AdminCreate(
            username=username,
            hash=password,
            role="superadmin"
        )
        
        success, message = self.auth_service.register_admin(admin_data)
        
        if success:
            print(f"\n  [OK] {message}")
            print("  You can now log in with your credentials.")
        else:
            print(f"\n  [ERROR] {message}")
        
        self.pause()
        return success
    
    # ========== MAIN MENU ==========
    
    def main_menu(self):
        """Display the main admin menu"""
        while True:
            self.clear_screen()
            self.print_header(f"ADMIN PANEL - {self.current_admin.username}")
            
            print(f"\n  Logged in as: {self.current_admin.username}")
            print(f"  Role: {self.current_admin.role.upper()}")
            print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            options = {
                "1": "User Management",
                "2": "Merchant Management",
                "3": "Product Management",
                "4": "Order Management",
                "5": "Category Management",
                "6": "System Statistics",
                "7": "Admin Management",
                "8": "Change Password",
                "0": "Logout"
            }
            
            self.print_menu(options)
            choice = self.get_input("Select an option")
            
            if choice == "1":
                self.user_management_menu()
            elif choice == "2":
                self.merchant_management_menu()
            elif choice == "3":
                self.product_management_menu()
            elif choice == "4":
                self.order_management_menu()
            elif choice == "5":
                self.category_management_menu()
            elif choice == "6":
                self.system_statistics()
            elif choice == "7":
                if self.current_admin.role == "superadmin":
                    self.admin_management_menu()
                else:
                    print("\n  [ERROR] Access denied. Superadmin only.")
                    self.pause()
            elif choice == "8":
                self.change_password()
            elif choice == "0":
                if self.confirm_action("Are you sure you want to logout?"):
                    print("\n  Logging out...")
                    self.current_admin = None
                    return
            else:
                print("\n  [ERROR] Invalid option. Please try again.")
                self.pause()
    
    # ========== USER MANAGEMENT ==========
    
    def user_management_menu(self):
        """User management submenu"""
        while True:
            self.clear_screen()
            self.print_header("USER MANAGEMENT")
            
            options = {
                "1": "List All Users",
                "2": "Search User by Username",
                "3": "View User Details",
                "4": "Suspend User Account",
                "5": "Delete User Account",
                "0": "Back to Main Menu"
            }
            
            self.print_menu(options)
            choice = self.get_input("Select an option")
            
            if choice == "1":
                self.list_all_users()
            elif choice == "2":
                self.search_user()
            elif choice == "3":
                self.view_user_details()
            elif choice == "4":
                self.suspend_user()
            elif choice == "5":
                self.delete_user()
            elif choice == "0":
                return
            else:
                print("\n  [ERROR] Invalid option. Please try again.")
                self.pause()
    
    def list_all_users(self):
        """List all registered users"""
        self.clear_screen()
        self.print_header("ALL USERS")
        
        query = "SELECT id, username, email, first_name, last_name, created_at FROM users ORDER BY id"
        users = self.db.fetch_all(query)
        
        if not users:
            print("\n  No users found in the system.")
        else:
            print(f"\n  Total Users: {len(users)}\n")
            print(f"  {'ID':<6} {'Username':<20} {'Name':<30} {'Email':<30} {'Joined':<12}")
            print("  " + "-" * 98)
            
            for user in users:
                full_name = f"{user['first_name']} {user['last_name']}"
                joined = user['created_at'].strftime('%Y-%m-%d') if user['created_at'] else 'N/A'
                print(f"  {user['id']:<6} {user['username']:<20} {full_name:<30} {user['email']:<30} {joined:<12}")
        
        self.pause()
    
    def search_user(self):
        """Search for a user by username"""
        self.clear_screen()
        self.print_header("SEARCH USER")
        
        username = self.get_input("Enter username to search")
        user = self.user_repo.get_by_username(username)
        
        if user:
            print("\n  [OK] User found!")
            self._display_user_info(user)
        else:
            print(f"\n  [ERROR] No user found with username: {username}")
        
        self.pause()
    
    def view_user_details(self):
        """View detailed information about a user"""
        self.clear_screen()
        self.print_header("VIEW USER DETAILS")
        
        try:
            user_id = int(self.get_input("Enter User ID"))
            user = self.user_repo.read(user_id)
            
            if user:
                self._display_user_info(user)
                
                # Get additional statistics
                orders_query = "SELECT COUNT(*) as count FROM orders WHERE user_id = %s"
                order_count = self.db.fetch_one(orders_query, (user_id,))
                
                print(f"\n  Statistics:")
                print(f"    - Total Orders: {order_count['count'] if order_count else 0}")
            else:
                print(f"\n  [ERROR] No user found with ID: {user_id}")
        except ValueError:
            print("\n  [ERROR] Invalid user ID. Please enter a number.")
        
        self.pause()
    
    def _display_user_info(self, user):
        """Display user information"""
        print(f"\n  User Information:")
        print(f"    - ID: {user.id}")
        print(f"    - Username: {user.username}")
        print(f"    - Name: {user.first_name} {user.last_name}")
        print(f"    - Email: {user.email}")
        print(f"    - Phone: {user.phone_number}")
        print(f"    - Gender: {user.gender}")
        print(f"    - Age: {user.age}")
        print(f"    - Joined: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def suspend_user(self):
        """Suspend a user account"""
        self.clear_screen()
        self.print_header("SUSPEND USER ACCOUNT")
        
        print("\n  [WARNING]  Warning: Suspended users cannot access their accounts.")
        print("  This action can be reversed by updating the is_active flag.\n")
        
        try:
            user_id = int(self.get_input("Enter User ID to suspend"))
            user = self.user_repo.read(user_id)
            
            if not user:
                print(f"\n  [ERROR] No user found with ID: {user_id}")
                self.pause()
                return
            
            print(f"\n  User: {user.username} ({user.first_name} {user.last_name})")
            
            if self.confirm_action("Are you sure you want to suspend this account?"):
                query = "UPDATE users SET is_active = FALSE WHERE id = %s"
                self.db.execute_query(query, (user_id,))
                print("\n  [OK] User account suspended successfully.")
            else:
                print("\n  Operation cancelled.")
        except ValueError:
            print("\n  [ERROR] Invalid user ID. Please enter a number.")
        
        self.pause()
    
    def delete_user(self):
        """Delete a user account permanently"""
        self.clear_screen()
        self.print_header("DELETE USER ACCOUNT")
        
        print("\n  [WARNING]  DANGER: This will permanently delete the user and all associated data!")
        print("  This action CANNOT be undone.\n")
        
        try:
            user_id = int(self.get_input("Enter User ID to delete"))
            user = self.user_repo.read(user_id)
            
            if not user:
                print(f"\n  [ERROR] No user found with ID: {user_id}")
                self.pause()
                return
            
            print(f"\n  User: {user.username} ({user.first_name} {user.last_name})")
            print(f"  Email: {user.email}")
            
            if self.confirm_action("Type 'DELETE' to confirm deletion") and \
               input("  ").strip() == "DELETE":
                success, message = self.user_repo.delete(user_id)
                if success:
                    print(f"\n  [OK] {message}")
                else:
                    print(f"\n  [ERROR] {message}")
            else:
                print("\n  Operation cancelled.")
        except ValueError:
            print("\n  [ERROR] Invalid user ID. Please enter a number.")
        
        self.pause()
    
    # ========== MERCHANT MANAGEMENT ==========
    
    def merchant_management_menu(self):
        """Merchant management submenu"""
        while True:
            self.clear_screen()
            self.print_header("MERCHANT MANAGEMENT")
            
            options = {
                "1": "List All Merchants",
                "2": "Search Merchant by Username",
                "3": "View Merchant Details",
                "4": "Suspend Merchant Account",
                "5": "Delete Merchant Account",
                "0": "Back to Main Menu"
            }
            
            self.print_menu(options)
            choice = self.get_input("Select an option")
            
            if choice == "1":
                self.list_all_merchants()
            elif choice == "2":
                self.search_merchant()
            elif choice == "3":
                self.view_merchant_details()
            elif choice == "4":
                self.suspend_merchant()
            elif choice == "5":
                self.delete_merchant()
            elif choice == "0":
                return
            else:
                print("\n  [ERROR] Invalid option. Please try again.")
                self.pause()
    
    def list_all_merchants(self):
        """List all registered merchants"""
        self.clear_screen()
        self.print_header("ALL MERCHANTS")
        
        query = "SELECT id, username, store_name, email, created_at FROM merchants ORDER BY id"
        merchants = self.db.fetch_all(query)
        
        if not merchants:
            print("\n  No merchants found in the system.")
        else:
            print(f"\n  Total Merchants: {len(merchants)}\n")
            print(f"  {'ID':<6} {'Username':<20} {'Store Name':<30} {'Email':<30} {'Joined':<12}")
            print("  " + "-" * 98)
            
            for merchant in merchants:
                joined = merchant['created_at'].strftime('%Y-%m-%d') if merchant['created_at'] else 'N/A'
                print(f"  {merchant['id']:<6} {merchant['username']:<20} {merchant['store_name']:<30} {merchant['email']:<30} {joined:<12}")
        
        self.pause()
    
    def search_merchant(self):
        """Search for a merchant by username"""
        self.clear_screen()
        self.print_header("SEARCH MERCHANT")
        
        username = self.get_input("Enter username to search")
        merchant = self.merchant_repo.get_by_username(username)
        
        if merchant:
            print("\n  [OK] Merchant found!")
            self._display_merchant_info(merchant)
        else:
            print(f"\n  [ERROR] No merchant found with username: {username}")
        
        self.pause()
    
    def view_merchant_details(self):
        """View detailed information about a merchant"""
        self.clear_screen()
        self.print_header("VIEW MERCHANT DETAILS")
        
        try:
            merchant_id = int(self.get_input("Enter Merchant ID"))
            merchant = self.merchant_repo.read(merchant_id)
            
            if merchant:
                self._display_merchant_info(merchant)
                
                # Get additional statistics
                products_query = "SELECT COUNT(*) as count FROM products WHERE merchant_id = %s"
                product_count = self.db.fetch_one(products_query, (merchant_id,))
                
                orders_query = "SELECT COUNT(*) as count FROM orders WHERE merchant_id = %s"
                order_count = self.db.fetch_one(orders_query, (merchant_id,))
                
                print(f"\n  Statistics:")
                print(f"    - Total Products: {product_count['count'] if product_count else 0}")
                print(f"    - Total Orders: {order_count['count'] if order_count else 0}")
            else:
                print(f"\n  [ERROR] No merchant found with ID: {merchant_id}")
        except ValueError:
            print("\n  [ERROR] Invalid merchant ID. Please enter a number.")
        
        self.pause()
    
    def _display_merchant_info(self, merchant):
        """Display merchant information"""
        print(f"\n  Merchant Information:")
        print(f"    - ID: {merchant.id}")
        print(f"    - Username: {merchant.username}")
        print(f"    - Store Name: {merchant.store_name}")
        print(f"    - Owner: {merchant.first_name} {merchant.last_name}")
        print(f"    - Email: {merchant.email}")
        print(f"    - Phone: {merchant.phone_number}")
        print(f"    - Joined: {merchant.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def suspend_merchant(self):
        """Suspend a merchant account"""
        self.clear_screen()
        self.print_header("SUSPEND MERCHANT ACCOUNT")
        
        print("\n  [WARNING]  Warning: Suspended merchants cannot access their accounts.")
        print("  Their products will remain visible but they cannot manage them.\n")
        
        try:
            merchant_id = int(self.get_input("Enter Merchant ID to suspend"))
            merchant = self.merchant_repo.read(merchant_id)
            
            if not merchant:
                print(f"\n  [ERROR] No merchant found with ID: {merchant_id}")
                self.pause()
                return
            
            print(f"\n  Store: {merchant.store_name}")
            print(f"  Owner: {merchant.first_name} {merchant.last_name}")
            
            if self.confirm_action("Are you sure you want to suspend this merchant?"):
                query = "UPDATE merchants SET is_active = FALSE WHERE id = %s"
                self.db.execute_query(query, (merchant_id,))
                print("\n  [OK] Merchant account suspended successfully.")
            else:
                print("\n  Operation cancelled.")
        except ValueError:
            print("\n  [ERROR] Invalid merchant ID. Please enter a number.")
        
        self.pause()
    
    def delete_merchant(self):
        """Delete a merchant account permanently"""
        self.clear_screen()
        self.print_header("DELETE MERCHANT ACCOUNT")
        
        print("\n  [WARNING]  DANGER: This will permanently delete the merchant and all their products!")
        print("  This action CANNOT be undone.\n")
        
        try:
            merchant_id = int(self.get_input("Enter Merchant ID to delete"))
            merchant = self.merchant_repo.read(merchant_id)
            
            if not merchant:
                print(f"\n  [ERROR] No merchant found with ID: {merchant_id}")
                self.pause()
                return
            
            print(f"\n  Store: {merchant.store_name}")
            print(f"  Owner: {merchant.first_name} {merchant.last_name}")
            
            if self.confirm_action("Type 'DELETE' to confirm deletion") and \
               input("  ").strip() == "DELETE":
                success, message = self.merchant_repo.delete(merchant_id)
                if success:
                    print(f"\n  [OK] {message}")
                else:
                    print(f"\n  [ERROR] {message}")
            else:
                print("\n  Operation cancelled.")
        except ValueError:
            print("\n  [ERROR] Invalid merchant ID. Please enter a number.")
        
        self.pause()
    
    # ========== PRODUCT MANAGEMENT ==========
    
    def product_management_menu(self):
        """Product management submenu"""
        while True:
            self.clear_screen()
            self.print_header("PRODUCT MANAGEMENT")
            
            options = {
                "1": "List All Products",
                "2": "Search Products by Name",
                "3": "View Product Details",
                "4": "Delete Product",
                "5": "Products by Category",
                "0": "Back to Main Menu"
            }
            
            self.print_menu(options)
            choice = self.get_input("Select an option")
            
            if choice == "1":
                self.list_all_products()
            elif choice == "2":
                self.search_products()
            elif choice == "3":
                self.view_product_details()
            elif choice == "4":
                self.delete_product()
            elif choice == "5":
                self.products_by_category()
            elif choice == "0":
                return
            else:
                print("\n  [ERROR] Invalid option. Please try again.")
                self.pause()
    
    def list_all_products(self, limit: int = 50):
        """List all products"""
        self.clear_screen()
        self.print_header("ALL PRODUCTS")
        
        query = """
            SELECT p.id, p.name, p.brand, p.price, p.quantity_available, 
                   m.store_name, c.name as category_name
            FROM products p
            JOIN merchants m ON p.merchant_id = m.id
            JOIN categories c ON p.category_id = c.id
            ORDER BY p.id DESC
            LIMIT %s
        """
        products = self.db.fetch_all(query, (limit,))
        
        if not products:
            print("\n  No products found in the system.")
        else:
            print(f"\n  Showing {len(products)} most recent products\n")
            print(f"  {'ID':<6} {'Name':<30} {'Brand':<20} {'Price':<12} {'Stock':<8} {'Merchant':<20}")
            print("  " + "-" * 96)
            
            for product in products:
                price = f"₱{product['price']:,.2f}"
                print(f"  {product['id']:<6} {product['name'][:29]:<30} {product['brand'][:19]:<20} {price:<12} {product['quantity_available']:<8} {product['store_name'][:19]:<20}")
        
        self.pause()
    
    def search_products(self):
        """Search for products by name"""
        self.clear_screen()
        self.print_header("SEARCH PRODUCTS")
        
        search_term = self.get_input("Enter product name to search")
        
        query = """
            SELECT p.id, p.name, p.brand, p.price, p.quantity_available, 
                   m.store_name
            FROM products p
            JOIN merchants m ON p.merchant_id = m.id
            WHERE p.name LIKE %s OR p.brand LIKE %s
            ORDER BY p.id
        """
        products = self.db.fetch_all(query, (f"%{search_term}%", f"%{search_term}%"))
        
        if not products:
            print(f"\n  No products found matching: {search_term}")
        else:
            print(f"\n  Found {len(products)} product(s)\n")
            print(f"  {'ID':<6} {'Name':<35} {'Brand':<20} {'Price':<12} {'Stock':<8}")
            print("  " + "-" * 81)
            
            for product in products:
                price = f"₱{product['price']:,.2f}"
                print(f"  {product['id']:<6} {product['name'][:34]:<35} {product['brand'][:19]:<20} {price:<12} {product['quantity_available']:<8}")
        
        self.pause()
    
    def view_product_details(self):
        """View detailed information about a product"""
        self.clear_screen()
        self.print_header("VIEW PRODUCT DETAILS")
        
        try:
            product_id = int(self.get_input("Enter Product ID"))
            product = self.product_repo.read(product_id)
            
            if product:
                merchant = self.merchant_repo.read(product.merchant_id)
                category = self.category_repo.read(product.category_id)
                
                print(f"\n  Product Information:")
                print(f"    - ID: {product.id}")
                print(f"    - Name: {product.name}")
                print(f"    - Brand: {product.brand}")
                print(f"    - Price: ₱{product.price:,.2f}")
                print(f"    - Stock: {product.quantity_available}")
                print(f"    - Rating: {product.rating_score / product.rating_count if product.rating_count > 0 else 0:.1f} ({product.rating_count} reviews)")
                print(f"    - Category: {category.name if category else 'N/A'}")
                print(f"    - Merchant: {merchant.store_name if merchant else 'N/A'}")
                print(f"    - Description: {product.description[:100]}...")
            else:
                print(f"\n  [ERROR] No product found with ID: {product_id}")
        except ValueError:
            print("\n  [ERROR] Invalid product ID. Please enter a number.")
        
        self.pause()
    
    def delete_product(self):
        """Delete a product"""
        self.clear_screen()
        self.print_header("DELETE PRODUCT")
        
        print("\n  [WARNING]  Warning: This will permanently delete the product.")
        print("  Associated orders will remain but point to deleted product.\n")
        
        try:
            product_id = int(self.get_input("Enter Product ID to delete"))
            product = self.product_repo.read(product_id)
            
            if not product:
                print(f"\n  [ERROR] No product found with ID: {product_id}")
                self.pause()
                return
            
            print(f"\n  Product: {product.brand} - {product.name}")
            print(f"  Price: ₱{product.price:,.2f}")
            
            if self.confirm_action("Are you sure you want to delete this product?"):
                success, message = self.product_repo.delete(product_id)
                if success:
                    print(f"\n  [OK] {message}")
                else:
                    print(f"\n  [ERROR] {message}")
            else:
                print("\n  Operation cancelled.")
        except ValueError:
            print("\n  [ERROR] Invalid product ID. Please enter a number.")
        
        self.pause()
    
    def products_by_category(self):
        """View products organized by category"""
        self.clear_screen()
        self.print_header("PRODUCTS BY CATEGORY")
        
        query = """
            SELECT c.id, c.name, COUNT(p.id) as product_count
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id
            GROUP BY c.id, c.name
            ORDER BY c.name
        """
        categories = self.db.fetch_all(query)
        
        if not categories:
            print("\n  No categories found.")
        else:
            print(f"\n  {'ID':<6} {'Category Name':<40} {'Products':<10}")
            print("  " + "-" * 56)
            
            for cat in categories:
                print(f"  {cat['id']:<6} {cat['name']:<40} {cat['product_count']:<10}")
        
        self.pause()
    
    # ========== ORDER MANAGEMENT ==========
    
    def order_management_menu(self):
        """Order management submenu"""
        while True:
            self.clear_screen()
            self.print_header("ORDER MANAGEMENT")
            
            options = {
                "1": "List Recent Orders",
                "2": "Search Order by ID",
                "3": "View Order Details",
                "4": "Orders by Status",
                "5": "Cancel Order (Refund)",
                "0": "Back to Main Menu"
            }
            
            self.print_menu(options)
            choice = self.get_input("Select an option")
            
            if choice == "1":
                self.list_recent_orders()
            elif choice == "2":
                self.search_order()
            elif choice == "3":
                self.view_order_details()
            elif choice == "4":
                self.orders_by_status()
            elif choice == "5":
                self.admin_cancel_order()
            elif choice == "0":
                return
            else:
                print("\n  [ERROR] Invalid option. Please try again.")
                self.pause()
    
    def list_recent_orders(self, limit: int = 30):
        """List recent orders"""
        self.clear_screen()
        self.print_header("RECENT ORDERS")
        
        query = """
            SELECT o.id, o.user_id, o.merchant_id, o.total_amount, o.status, o.order_date,
                   u.username as buyer, m.store_name as seller
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN merchants m ON o.merchant_id = m.id
            ORDER BY o.order_date DESC
            LIMIT %s
        """
        orders = self.db.fetch_all(query, (limit,))
        
        if not orders:
            print("\n  No orders found.")
        else:
            print(f"\n  Showing {len(orders)} most recent orders\n")
            print(f"  {'ID':<6} {'Buyer':<20} {'Seller':<20} {'Amount':<12} {'Status':<12} {'Date':<12}")
            print("  " + "-" * 82)
            
            for order in orders:
                status = Status(order['status']).name
                amount = f"₱{order['total_amount']:,.2f}"
                date = order['order_date'].strftime('%Y-%m-%d')
                print(f"  {order['id']:<6} {order['buyer'][:19]:<20} {order['seller'][:19]:<20} {amount:<12} {status:<12} {date:<12}")
        
        self.pause()
    
    def search_order(self):
        """Search for an order by ID"""
        self.clear_screen()
        self.print_header("SEARCH ORDER")
        
        try:
            order_id = int(self.get_input("Enter Order ID"))
            order = self.order_repo.read(order_id)
            
            if order:
                print("\n  [OK] Order found!")
                self._display_order_summary(order)
            else:
                print(f"\n  [ERROR] No order found with ID: {order_id}")
        except ValueError:
            print("\n  [ERROR] Invalid order ID. Please enter a number.")
        
        self.pause()
    
    def view_order_details(self):
        """View detailed order information"""
        self.clear_screen()
        self.print_header("VIEW ORDER DETAILS")
        
        try:
            order_id = int(self.get_input("Enter Order ID"))
            order = self.order_repo.read(order_id)
            
            if order:
                self._display_order_summary(order)
                
                # Get items
                print(f"\n  Order Items:")
                for item in order.items:
                    product = self.product_repo.read(item.product_id)
                    product_name = product.name if product else "Unknown Product"
                    print(f"    - {product_name}")
                    print(f"      Quantity: {item.product_quantity} × ₱{item.product_price:,.2f} = ₱{item.total_price:,.2f}")
            else:
                print(f"\n  [ERROR] No order found with ID: {order_id}")
        except ValueError:
            print("\n  [ERROR] Invalid order ID. Please enter a number.")
        
        self.pause()
    
    def _display_order_summary(self, order):
        """Display order summary"""
        user = self.user_repo.read(order.user_id)
        merchant = self.merchant_repo.read(order.merchant_id)
        
        print(f"\n  Order Information:")
        print(f"    - Order ID: {order.id}")
        print(f"    - Buyer: {user.username if user else 'Unknown'}")
        print(f"    - Seller: {merchant.store_name if merchant else 'Unknown'}")
        print(f"    - Total Amount: ₱{order.total_amount:,.2f}")
        print(f"    - Status: {order.status.name}")
        print(f"    - Order Date: {order.order_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def orders_by_status(self):
        """View orders filtered by status"""
        self.clear_screen()
        self.print_header("ORDERS BY STATUS")
        
        print("\n  Select status:")
        print("    [1] Pending")
        print("    [2] Paid")
        print("    [3] Shipped")
        print("    [4] Delivered")
        print("    [5] Cancelled")
        
        choice = self.get_input("\n  Select status")
        
        status_map = {
            "1": Status.PENDING,
            "2": Status.PAID,
            "3": Status.SHIPPED,
            "4": Status.DELIVERED,
            "5": Status.CANCELLED
        }
        
        if choice not in status_map:
            print("\n  [ERROR] Invalid status selection.")
            self.pause()
            return
        
        status = status_map[choice]
        
        query = """
            SELECT o.id, o.user_id, o.total_amount, o.order_date,
                   u.username as buyer, m.store_name as seller
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN merchants m ON o.merchant_id = m.id
            WHERE o.status = %s
            ORDER BY o.order_date DESC
        """
        orders = self.db.fetch_all(query, (status.value,))
        
        if not orders:
            print(f"\n  No {status.name} orders found.")
        else:
            print(f"\n  {status.name} Orders: {len(orders)}\n")
            print(f"  {'ID':<6} {'Buyer':<20} {'Seller':<20} {'Amount':<12} {'Date':<12}")
            print("  " + "-" * 70)
            
            for order in orders:
                amount = f"₱{order['total_amount']:,.2f}"
                date = order['order_date'].strftime('%Y-%m-%d')
                print(f"  {order['id']:<6} {order['buyer'][:19]:<20} {order['seller'][:19]:<20} {amount:<12} {date:<12}")
        
        self.pause()
    
    def admin_cancel_order(self):
        """Cancel an order as admin (with refund)"""
        self.clear_screen()
        self.print_header("CANCEL ORDER (ADMIN)")
        
        print("\n  [WARNING]  This will cancel the order and process a refund if applicable.\n")
        
        try:
            order_id = int(self.get_input("Enter Order ID to cancel"))
            order = self.order_repo.read(order_id)
            
            if not order:
                print(f"\n  [ERROR] No order found with ID: {order_id}")
                self.pause()
                return
            
            self._display_order_summary(order)
            
            if order.status == Status.CANCELLED:
                print("\n  [INFO]  This order is already cancelled.")
                self.pause()
                return
            
            if order.status == Status.DELIVERED:
                print("\n  [WARNING]  Cannot cancel a delivered order.")
                self.pause()
                return
            
            reason = self.get_input("Cancellation reason", required=False)
            
            if self.confirm_action("Are you sure you want to cancel this order?"):
                # Update order status
                success = self.order_repo.update(order_id, {'status': Status.CANCELLED})
                
                if success:
                    print("\n  [OK] Order cancelled successfully.")
                    if reason:
                        print(f"  Reason: {reason}")
                else:
                    print("\n  [ERROR] Failed to cancel order.")
            else:
                print("\n  Operation cancelled.")
        except ValueError:
            print("\n  [ERROR] Invalid order ID. Please enter a number.")
        
        self.pause()
    
    # ========== CATEGORY MANAGEMENT ==========
    
    def category_management_menu(self):
        """Category management submenu"""
        while True:
            self.clear_screen()
            self.print_header("CATEGORY MANAGEMENT")
            
            options = {
                "1": "List All Categories",
                "2": "View Category Details",
                "0": "Back to Main Menu"
            }
            
            self.print_menu(options)
            choice = self.get_input("Select an option")
            
            if choice == "1":
                self.list_all_categories()
            elif choice == "2":
                self.view_category_details()
            elif choice == "0":
                return
            else:
                print("\n  [ERROR] Invalid option. Please try again.")
                self.pause()
    
    def list_all_categories(self):
        """List all categories"""
        self.clear_screen()
        self.print_header("ALL CATEGORIES")
        
        query = """
            SELECT c1.id, c1.name, c1.parent_id, c2.name as parent_name,
                   (SELECT COUNT(*) FROM products WHERE category_id = c1.id) as product_count
            FROM categories c1
            LEFT JOIN categories c2 ON c1.parent_id = c2.id
            ORDER BY c1.parent_id, c1.name
        """
        categories = self.db.fetch_all(query)
        
        if not categories:
            print("\n  No categories found.")
        else:
            print(f"\n  Total Categories: {len(categories)}\n")
            print(f"  {'ID':<6} {'Name':<35} {'Parent':<25} {'Products':<10}")
            print("  " + "-" * 76)
            
            for cat in categories:
                parent = cat['parent_name'] if cat['parent_name'] else "None (Root)"
                print(f"  {cat['id']:<6} {cat['name']:<35} {parent:<25} {cat['product_count']:<10}")
        
        self.pause()
    
    def view_category_details(self):
        """View category details"""
        self.clear_screen()
        self.print_header("VIEW CATEGORY DETAILS")
        
        try:
            category_id = int(self.get_input("Enter Category ID"))
            category = self.category_repo.read(category_id)
            
            if category:
                parent = None
                if category.parent_id:
                    parent = self.category_repo.read(category.parent_id)
                
                print(f"\n  Category Information:")
                print(f"    - ID: {category.id}")
                print(f"    - Name: {category.name}")
                print(f"    - Parent: {parent.name if parent else 'None (Root Category)'}")
                print(f"    - Description: {category.description}")
                
                # Get product count
                query = "SELECT COUNT(*) as count FROM products WHERE category_id = %s"
                result = self.db.fetch_one(query, (category_id,))
                print(f"    - Total Products: {result['count'] if result else 0}")
            else:
                print(f"\n  [ERROR] No category found with ID: {category_id}")
        except ValueError:
            print("\n  [ERROR] Invalid category ID. Please enter a number.")
        
        self.pause()
    
    # ========== SYSTEM STATISTICS ==========
    
    def system_statistics(self):
        """Display system-wide statistics"""
        self.clear_screen()
        self.print_header("SYSTEM STATISTICS")
        
        # Get counts
        user_count = self.db.fetch_one("SELECT COUNT(*) as count FROM users")
        merchant_count = self.db.fetch_one("SELECT COUNT(*) as count FROM merchants")
        product_count = self.db.fetch_one("SELECT COUNT(*) as count FROM products")
        order_count = self.db.fetch_one("SELECT COUNT(*) as count FROM orders")
        
        # Get total revenue
        revenue = self.db.fetch_one("SELECT SUM(total_amount) as total FROM orders WHERE status != %s", (Status.CANCELLED.value,))
        
        # Get recent activity
        recent_users = self.db.fetch_one("SELECT COUNT(*) as count FROM users WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
        recent_orders = self.db.fetch_one("SELECT COUNT(*) as count FROM orders WHERE order_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
        
        print(f"\n  Platform Overview:")
        print(f"    - Total Users: {user_count['count'] if user_count else 0:,}")
        print(f"    - Total Merchants: {merchant_count['count'] if merchant_count else 0:,}")
        print(f"    - Total Products: {product_count['count'] if product_count else 0:,}")
        print(f"    - Total Orders: {order_count['count'] if order_count else 0:,}")
        print(f"    - Total Revenue: ₱{revenue['total'] if revenue and revenue['total'] else 0:,.2f}")
        
        print(f"\n  Recent Activity (Last 7 Days):")
        print(f"    - New Users: {recent_users['count'] if recent_users else 0:,}")
        print(f"    - New Orders: {recent_orders['count'] if recent_orders else 0:,}")
        
        # Order status breakdown
        print(f"\n  Order Status Breakdown:")
        for status in [Status.PENDING, Status.PAID, Status.SHIPPED, Status.DELIVERED, Status.CANCELLED]:
            query = "SELECT COUNT(*) as count FROM orders WHERE status = %s"
            result = self.db.fetch_one(query, (status.value,))
            print(f"    - {status.name}: {result['count'] if result else 0:,}")
        
        self.pause()
    
    # ========== ADMIN MANAGEMENT ==========
    
    def admin_management_menu(self):
        """Admin management submenu (superadmin only)"""
        while True:
            self.clear_screen()
            self.print_header("ADMIN MANAGEMENT (SUPERADMIN ONLY)")
            
            options = {
                "1": "List All Admins",
                "2": "Create New Admin",
                "3": "Delete Admin",
                "0": "Back to Main Menu"
            }
            
            self.print_menu(options)
            choice = self.get_input("Select an option")
            
            if choice == "1":
                self.list_all_admins()
            elif choice == "2":
                self.create_admin()
            elif choice == "3":
                self.delete_admin()
            elif choice == "0":
                return
            else:
                print("\n  [ERROR] Invalid option. Please try again.")
                self.pause()
    
    def list_all_admins(self):
        """List all admin accounts"""
        self.clear_screen()
        self.print_header("ALL ADMINISTRATORS")
        
        query = "SELECT id, username, role, created_at FROM admins ORDER BY id"
        admins = self.db.fetch_all(query)
        
        if not admins:
            print("\n  No admin accounts found.")
        else:
            print(f"\n  Total Admins: {len(admins)}\n")
            print(f"  {'ID':<6} {'Username':<25} {'Role':<15} {'Created':<20}")
            print("  " + "-" * 66)
            
            for admin in admins:
                created = admin['created_at'].strftime('%Y-%m-%d %H:%M:%S') if admin['created_at'] else 'N/A'
                print(f"  {admin['id']:<6} {admin['username']:<25} {admin['role']:<15} {created:<20}")
        
        self.pause()
    
    def create_admin(self):
        """Create a new admin account"""
        self.clear_screen()
        self.print_header("CREATE NEW ADMIN")
        
        print("\n  Create a new administrator account.\n")
        
        username = self.get_input("Admin Username")
        
        # Check if username exists
        if self.admin_repo.get_by_username(username):
            print(f"\n  [ERROR] Username '{username}' already exists.")
            self.pause()
            return
        
        password = getpass("  Password: ")
        confirm_password = getpass("  Confirm Password: ")
        
        if password != confirm_password:
            print("\n  [ERROR] Passwords do not match.")
            self.pause()
            return
        
        if len(password) < 6:
            print("\n  [ERROR] Password must be at least 6 characters long.")
            self.pause()
            return
        
        print("\n  Select admin role:")
        print("    [1] admin - Standard administrator")
        print("    [2] superadmin - Full system access")
        
        role_choice = self.get_input("\n  Select role")
        role = "superadmin" if role_choice == "2" else "admin"
        
        admin_data = AdminCreate(
            username=username,
            hash=password,
            role=role
        )
        
        success, message = self.auth_service.register_admin(admin_data)
        
        if success:
            print(f"\n  [OK] {message}")
        else:
            print(f"\n  [ERROR] {message}")
        
        self.pause()
    
    def delete_admin(self):
        """Delete an admin account"""
        self.clear_screen()
        self.print_header("DELETE ADMIN ACCOUNT")
        
        print("\n  [WARNING]  Warning: This will permanently delete the admin account.\n")
        
        try:
            admin_id = int(self.get_input("Enter Admin ID to delete"))
            
            if admin_id == self.current_admin.id:
                print("\n  [ERROR] You cannot delete your own account!")
                self.pause()
                return
            
            admin = self.admin_repo.read(admin_id)
            
            if not admin:
                print(f"\n  [ERROR] No admin found with ID: {admin_id}")
                self.pause()
                return
            
            print(f"\n  Admin: {admin.username}")
            print(f"  Role: {admin.role}")
            
            if self.confirm_action("Are you sure you want to delete this admin?"):
                success, message = self.admin_repo.delete(admin_id)
                if success:
                    print(f"\n  [OK] {message}")
                else:
                    print(f"\n  [ERROR] {message}")
            else:
                print("\n  Operation cancelled.")
        except ValueError:
            print("\n  [ERROR] Invalid admin ID. Please enter a number.")
        
        self.pause()
    
    # ========== PASSWORD CHANGE ==========
    
    def change_password(self):
        """Change current admin's password"""
        self.clear_screen()
        self.print_header("CHANGE PASSWORD")
        
        print("\n  Change your admin password\n")
        
        old_password = getpass("  Current Password: ")
        new_password = getpass("  New Password: ")
        confirm_password = getpass("  Confirm New Password: ")
        
        if new_password != confirm_password:
            print("\n  [ERROR] New passwords do not match.")
            self.pause()
            return
        
        success, message = self.auth_service.change_password(
            self.current_admin.username,
            old_password,
            new_password
        )
        
        if success:
            print(f"\n  [OK] {message}")
        else:
            print(f"\n  [ERROR] {message}")
        
        self.pause()
    
    # ========== MAIN RUN METHOD ==========
    
    def run(self):
        """Main application loop"""
        self.clear_screen()
        
        # Check if any admin exists
        admin_count_query = "SELECT COUNT(*) as count FROM admins"
        admin_count = self.db.fetch_one(admin_count_query)
        
        if not admin_count or admin_count['count'] == 0:
            if not self.create_first_admin():
                return
        
        # Login loop
        while not self.current_admin:
            if not self.login():
                if not self.confirm_action("Try again?"):
                    return
        
        # Main menu loop
        try:
            self.main_menu()
        except KeyboardInterrupt:
            print("\n\n  Interrupted by user. Logging out...")
        except Exception as e:
            print(f"\n\n  [ERROR] An unexpected error occurred: {e}")
            self.pause()
        
        self.clear_screen()
        print("\n  Thank you for using the Admin Panel!\n")


def main():
    """Entry point for the admin panel"""
    try:
        panel = AdminPanel()
        panel.run()
    except KeyboardInterrupt:
        print("\n\n  Exiting...")
    except Exception as e:
        print(f"\n  FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
