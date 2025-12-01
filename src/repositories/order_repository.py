from typing import override, Any
from types import SimpleNamespace
from models.orders import Order, OrderCreate, OrderItem, OrderItemCreate, Invoice, InvoiceCreate
from models.payments import VirtualCard
from repositories.base_repository import BaseRepository
from database.database import Database
from models.status import Status
from repositories.cart_repository import CartRepository


class OrderRepository(BaseRepository):
    def __init__(self, db: Database, cart_repository: CartRepository):
        self.db = db
        self.cart_repository = cart_repository
        self.table_name = "orders"
        self.order_items_table_name = "order_items"

    @override
    def create(self, data: OrderCreate) -> tuple[int | None, str]:
        """
        Creates a new order and its associated order items.
        Args:
            data (OrderCreate): The OrderCreate object containing the new order's data
                                and a list of OrderItemCreate objects.
        Returns:
            tuple[int | None, str]: A tuple indicating the new order's ID if successful,
                                    `None` otherwise, and a message.
        """
        order_fields = [
            "user_id",
            "merchant_id",
            "order_date",
            "total_amount",
            "status",
            "shipping_address_id",
            "billing_address_id",
        ]

        # Use a SimpleNamespace to create a mutable object from the dataclass
        order_data_for_db = SimpleNamespace(**data.__dict__)
        order_data_for_db.status = data.status.value

        # Create the order record
        new_order_id, message = self._create_record(
            data=order_data_for_db,
            fields=order_fields,
            table_name=self.table_name,
            db=self.db
        )

        if not new_order_id:
            return (None, message)
        
        # Create item records from the OrderItemCreate data and link them to this order
        if data.items:
            for item_data in data.items:
                # Step 1: Create an item record with the correct columns
                item_insert_query = """
                    INSERT INTO items (product_id, product_quantity, product_price, applied_discounts, total_price)
                    VALUES (%s, %s, %s, %s, %s)
                """
                try:
                    total_price = item_data.product_price * item_data.product_quantity
                    
                    # execute_query returns the lastrowid for INSERT statements
                    item_id = self.db.execute_query(
                        item_insert_query,
                        (
                            item_data.product_id,
                            item_data.product_quantity,
                            item_data.product_price,
                            0,  # applied_discounts - default to 0
                            total_price
                        )
                    )
                    
                    if not item_id:
                        error_message = f"Failed to create item record for product {item_data.product_id}"
                        print(f"[OrderRepository ERROR] {error_message}")
                        return (None, error_message)
                    
                    # Step 2: Link the item to this order
                    order_item_insert_query = f"""
                        INSERT INTO {self.order_items_table_name} (order_id, item_id)
                        VALUES (%s, %s)
                    """
                    self.db.execute_query(order_item_insert_query, (new_order_id, item_id))
                    print(f"[OrderRepository] Successfully linked order {new_order_id} to item {item_id} (product {item_data.product_id})")
                    
                except Exception as e:
                    error_message = f"Failed to create order item for order {new_order_id}, product {item_data.product_id}: {e}"
                    print(f"[OrderRepository ERROR] {error_message}")
                    return (None, error_message)
        
        return (new_order_id, f"Order created successfully with ID {new_order_id}.")

    @override
    def read(self, identifier: int) -> Order | None:
        """
        Reads an order and its items by the order ID.

        Args:
            identifier (int): The ID of the order to retrieve.

        Returns:
            Order | None: The Order object with its items if found, otherwise `None`.
        """
        # Fetch the main order details
        order_query = f"SELECT * FROM {self.table_name} WHERE id = %s"
        order_row = self.db.fetch_one(order_query, (identifier,))

        if not order_row:
            print(f"[OrderRepository] No order found with id = {identifier}")
            return None

        # Fetch associated order items by joining order_items with items table
        items_query = f"""
            SELECT i.* 
            FROM items i
            JOIN {self.order_items_table_name} oi ON i.id = oi.item_id
            WHERE oi.order_id = %s
        """
        item_rows = self.db.fetch_all(items_query, (identifier,))

        # Map to dataclasses
        order_items = [OrderItem(**item_row) for item_row in item_rows] if item_rows else []

        return self._map_to_order(order_row, order_items)

    @override
    def update(self, identifier: int, data: dict[str, Any]) -> bool:
        """
        Updates an existing order record. Typically used for changing order status.
        Note: This does not update order items.

        Args:
            identifier (int): The ID of the order to update.
            data (dict): A dictionary of fields to update.
 
        Returns:
            bool: `True` if the update was successful, `False` otherwise.
        """
        allowed_fields = [
            "status",
            "shipping_address_id",
            "billing_address_id",
        ]
        
        update_data = data.copy()
        # Convert Status enum to its integer value if present
        if 'status' in update_data and isinstance(update_data['status'], Status):
            update_data['status'] = update_data['status'].value

        return self._update_by_id(
            identifier=identifier, data=update_data, table_name=self.table_name, db=self.db, allowed_fields=allowed_fields
        )

    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        """
        Deletes an order and its associated order items.
        This should be used with caution.

        Args:
            identifier (int): The ID of the order to delete.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        return self._delete_by_id(identifier, table_name=self.table_name, db=self.db)

    def has_user_purchased_product(self, user_id: int, product_id: int) -> bool:
        """
        Checks if a user has a completed order containing a specific product.

        Args:
            user_id (int): The ID of the user.
            product_id (int): The ID of the product.

        Returns:
            bool: True if a completed purchase exists, False otherwise.
        """
        query = """
            SELECT 1 FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE o.user_id = %s AND oi.product_id = %s AND o.status = %s
            LIMIT 1
        """
        result = self.db.fetch_one(query, (user_id, product_id, Status.DELIVERED.value))
        return result is not None

    def _map_to_order(self, row: dict, items: list[OrderItem]) -> Order | None:
        """
        Maps a database row and a list of items to an Order dataclass object.

        Args:
            row (dict): A dictionary representing a row from the 'orders' table.
            items (list[OrderItem]): A list of OrderItem objects associated with the order.

        Returns:
            Order | None: An Order object if the row is not empty, otherwise `None`.
        """
        if not row:
            return None
        
        # Create a copy of the row to avoid modifying the original dict
        order_data = row.copy()
        # Convert integer status from DB back to Status enum
        if 'status' in order_data:
            order_data['status'] = Status(order_data['status'])

        # Add the items list to the data
        order_data['items'] = items
        
        return Order(**order_data)

    def update_status(self, order_id: int, status: Status) -> tuple[bool, str]:
        """
        Updates the status of a specific order.

        Args:
            order_id (int): The ID of the order to update.
            status (Status): The new status for the order.

        Returns:
            tuple[bool, str]: A tuple indicating success and a message.
        """
        success = self.update(order_id, {'status': status})
        if success:
            return (True, f"Order {order_id} status updated to {status.name}.")
        return (False, f"Failed to update status for order {order_id}.")

    def get_user_card_for_order(self, order_id: int) -> VirtualCard | None:
        """
        Retrieves the user's virtual card used for a specific order payment.

        Args:
            order_id (int): The ID of the order.

        Returns:
            VirtualCard | None: The user's VirtualCard object if found, otherwise None.
        """
        query = """
            SELECT vc.* FROM virtualcards vc
            JOIN payments p ON vc.id = p.sender_id
            WHERE p.order_id = %s AND p.type = 'ORDER_PAYMENT'
        """
        card_row = self.db.fetch_one(query, (order_id,))
        if not card_row:
            print(f"[OrderRepository WARN] Could not find user card for order {order_id}")
            return None
        return VirtualCard(**card_row)

    def get_merchant_card_for_order(self, order_id: int) -> VirtualCard | None:
        """
        Retrieves the merchant's virtual card that received payment for a specific order.

        Args:
            order_id (int): The ID of the order.

        Returns:
            VirtualCard | None: The merchant's VirtualCard object if found, otherwise None.
        """
        query = """
            SELECT vc.* FROM virtual_cards vc
            JOIN payments p ON vc.id = p.receiver_id
            WHERE p.order_id = %s AND p.type = 'ORDER_PAYMENT'
        """
        card_row = self.db.fetch_one(query, (order_id,))
        if not card_row:
            print(f"[OrderRepository WARN] Could not find merchant card for order {order_id}")
            return None
        return VirtualCard(**card_row)

    def read_all_by_user_id(self, user_id: int) -> list[Order]:
        """
        Reads all orders and their items for a specific user.

        Args:
            user_id (int): The ID of the user whose orders to retrieve.

        Returns:
            list[Order]: A list of Order objects with their items, ordered by most recent.
        """
        # Fetch all orders for the user
        orders_query = f"SELECT * FROM {self.table_name} WHERE user_id = %s ORDER BY order_date DESC"
        order_rows = self.db.fetch_all(orders_query, (user_id,))

        if not order_rows:
            return []

        orders = []
        for order_row in order_rows:
            order_id = order_row['id']
            # Fetch associated order items by joining with items table
            items_query = f"""
                SELECT i.* 
                FROM items i
                JOIN {self.order_items_table_name} oi ON i.id = oi.item_id
                WHERE oi.order_id = %s
            """
            item_rows = self.db.fetch_all(items_query, (order_id,))
            
            order_items = [OrderItem(**item_row) for item_row in item_rows] if item_rows else []
            order = self._map_to_order(order_row, order_items)
            if order:
                orders.append(order)
        return orders

    def get_invoice_by_order_id(self, order_id: int) -> Invoice | None:
        """
        Retrieves an invoice by its associated order ID.

        Args:
            order_id (int): The ID of the order.

        Returns:
            Invoice | None: The Invoice object if found, otherwise None.
        """
        query = "SELECT * FROM invoices WHERE order_id = %s"
        invoice_row = self.db.fetch_one(query, (order_id,))
        if not invoice_row:
            return None
        
        invoice_row['status'] = Status(invoice_row['status'])
        return Invoice(**invoice_row)

    def create_invoice(self, data: InvoiceCreate, order_id: int) -> tuple[int | None, str]:
        """
        Creates a new invoice for a given order.

        Args:
            data (InvoiceCreate): The data for the new invoice.
            order_id (int): The ID of the order this invoice belongs to.

        Returns:
            tuple[int | None, str]: A tuple with the new invoice ID and a message.
        """
        invoice_fields = [
            "order_id",
            "address_id",
            "issue_date",
            "status",
            "payment_summary"
        ]

        # Use SimpleNamespace to create an object that _create_record can use
        invoice_data_for_db = SimpleNamespace(**data.__dict__)
        setattr(invoice_data_for_db, 'order_id', order_id)
        setattr(invoice_data_for_db, 'status', data.status.value)

        new_invoice_id, message = self._create_record(
            data=invoice_data_for_db, fields=invoice_fields, table_name="invoices", db=self.db
        )
        
        return (new_invoice_id, message)

    def read_all_by_merchant_id(self, merchant_id: int) -> list[Order]:
        """
        Reads all orders and their items for a specific merchant.

        Args:
            merchant_id (int): The ID of the merchant whose orders to retrieve.

        Returns:
            list[Order]: A list of Order objects with their items, ordered by most recent.
        """
        # Fetch all orders for the merchant
        orders_query = f"SELECT * FROM {self.table_name} WHERE merchant_id = %s ORDER BY order_date DESC"
        order_rows = self.db.fetch_all(orders_query, (merchant_id,))

        if not order_rows:
            return []

        orders = []
        for order_row in order_rows:
            order_id = order_row['id']
            # Fetch associated order items by joining with items table
            items_query = f"""
                SELECT i.* 
                FROM items i
                JOIN {self.order_items_table_name} oi ON i.id = oi.item_id
                WHERE oi.order_id = %s
            """
            item_rows = self.db.fetch_all(items_query, (order_id,))
            
            order_items = [OrderItem(**item_row) for item_row in item_rows] if item_rows else []
            order = self._map_to_order(order_row, order_items)
            if order:
                orders.append(order)
        return orders
