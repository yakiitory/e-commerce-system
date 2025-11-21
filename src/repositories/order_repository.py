from typing import override, Any
from models.orders import Order, OrderCreate, OrderItem, OrderItemCreate
from models.payments import VirtualCard
from repositories.base_repository import BaseRepository
from database.database import Database
from models.status import Status

class OrderRepository(BaseRepository):
    def __init__(self, db: Database):
        self.db = db
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

        # Prepare data for _create_record, converting Status enum to its value
        order_data_for_db = data.__dict__.copy()
        order_data_for_db['status'] = data.status.value

        # Create the order record
        new_order_id, message = self._create_record(
            data=order_data_for_db,
            fields=order_fields,
            table_name=self.table_name,
            db=self.db
        )

        if not new_order_id:
            return (None, message)

        if data.items:
            for item_data in data.items:
                item_fields = [
                    "order_id",
                    "product_id",
                    "quantity",
                    "price_at_purchase",
                ]
                # Manually set order_id for each item
                item_data.order_id = new_order_id
                item_id, item_message = self._create_record(
                    data=item_data,
                    fields=item_fields,
                    table_name=self.order_items_table_name,
                    db=self.db
                )
                if not item_id:
                    # Rollback: Delete the order that was just created
                    self._delete_by_id(new_order_id, self.table_name, self.db)
                    return (None, f"Failed to create order item, order creation rolled back. Reason: {item_message}")

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

        # Fetch associated order items
        items_query = f"SELECT * FROM {self.order_items_table_name} WHERE order_id = %s"
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
            SELECT vc.* FROM virtual_cards vc
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
            # Fetch associated order items for each order
            items_query = f"SELECT * FROM {self.order_items_table_name} WHERE order_id = %s"
            item_rows = self.db.fetch_all(items_query, (order_id,))
            
            order_items = [OrderItem(**item_row) for item_row in item_rows] if item_rows else []
            order = self._map_to_order(order_row, order_items)
            if order:
                orders.append(order)
        return orders

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
            # Fetch associated order items for each order
            items_query = f"SELECT * FROM {self.order_items_table_name} WHERE order_id = %s"
            item_rows = self.db.fetch_all(items_query, (order_id,))
            
            order_items = [OrderItem(**item_row) for item_row in item_rows] if item_rows else []
            order = self._map_to_order(order_row, order_items)
            if order:
                orders.append(order)
        return orders
