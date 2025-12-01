from __future__ import annotations
from decimal import Decimal
from typing import TYPE_CHECKING

from models.orders import Order, OrderCreate, OrderItemCreate, Invoice, InvoiceCreate
from models.status import Status

if TYPE_CHECKING:
    from repositories.order_repository import OrderRepository
    from repositories.product_repository import ProductRepository
    from services.transaction_service import TransactionService
    from repositories.cart_repository import CartRepository
    from database.database import Database


class OrderService:
    """
    Handles the business logic for creating and managing orders.
    """

    def __init__(self, db: Database, order_repo: OrderRepository, product_repo: ProductRepository, transaction_service: TransactionService, cart_repo: CartRepository):
        self.db = db
        self.order_repo = order_repo
        self.product_repo = product_repo
        self.transaction_service = transaction_service
        self.cart_repo = cart_repo

    def create_order(
        self,
        user_id: int,
        merchant_id: int,
        shipping_address_id: int,
        billing_address_id: int,
        items: list[OrderItemCreate],
        user_card_id: int,
        merchant_card_id: int
    ) -> tuple[int | None, str]:
        """
        Creates a new order by orchestrating product validation, payment,
        order creation, and invoice generation.
        """
        if not items:
            return (None, "Cannot create an order with no items.")

        # --- 1. Validate items and calculate total amount ---
        total_amount = Decimal(0.0)
        validated_items = []
        for item in items:
            product = self.product_repo.read(item.product_id)
            if not product:
                return (None, f"Validation failed: Product with ID {item.product_id} not found.")
            item.product_price = product.price
            total_amount += Decimal(item.product_price * item.product_quantity)
            validated_items.append(item)

        if total_amount <= 0:
            return (None, "Total amount must be positive.")

        transaction_committed = False
        try:
            self.db.begin_transaction()

            # --- 2. Process Payment ---
            payment_success, payment_message = self.transaction_service.transfer_funds(
                sender_card_id=user_card_id,
                receiver_card_id=merchant_card_id,
                amount=float(total_amount),
                payment_type="ORDER_PAYMENT",
                in_transaction=True
            )
            if not payment_success:
                return (None, f"Order creation failed: {payment_message}")

            # --- 3. Create the Order record ---
            order_to_create = OrderCreate(
                user_id=user_id, 
                merchant_id=merchant_id,
                shipping_address_id=shipping_address_id, 
                billing_address_id=billing_address_id,
                total_amount=float(total_amount), 
                items=validated_items, 
                status=Status.PAID
            )
            new_order_id, order_message = self.order_repo.create(order_to_create)
            if not new_order_id:
                return (None, f"CRITICAL: Payment succeeded but order creation failed. Transaction rolled back. Reason: {order_message}")

            # --- 4. Create Invoice ---
            invoice_to_create = InvoiceCreate(
                address_id=shipping_address_id,
                order_id=new_order_id,
                status=Status.PAID,
                payment_summary=f"Paid via Virtual Card (User Card ID: {user_card_id} → Merchant Card ID: {merchant_card_id})"
            )
            new_invoice_id, invoice_message = self.order_repo.create_invoice(invoice_to_create, new_order_id)
            if not new_invoice_id:
                return (None, f"CRITICAL: Order created but invoice creation failed. Transaction rolled back. Reason: {invoice_message}")

            # --- 5. Update Product Metadata ---
            for item in validated_items:
                self.product_repo.metadata_repo.increment_field(item.product_id, 'sold_count')
                self.product_repo.update_quantity(item.product_id, item.product_quantity)

            # --- 6. Commit Transaction ---
            self.db.commit()
            transaction_committed = True
            return (new_order_id, f"Order created successfully with ID {new_order_id}.")

        except Exception as e:
            print(f"[OrderService ERROR] An unexpected error occurred during order creation: {e}")
            return (None, "An unexpected error occurred during order creation. The transaction has been rolled back.")
        finally:
            if not transaction_committed:
                self.db.rollback()

    def get_orders_for_user(self, user_id: int) -> tuple[bool, list[Order] | None]:
        """
        Retrieves all orders placed by a specific user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            tuple[bool, list[Order] | None]: A tuple containing a boolean for success,
                                             and either a list of orders or `None` on failure.
        """
        try:
            orders = self.order_repo.read_all_by_user_id(user_id)
            return (True, orders)
        except Exception as e:
            print(f"[OrderService ERROR] An unexpected error occurred while fetching orders for user {user_id}: {e}")
            return (False, None)

    def get_orders_for_merchant(self, merchant_id: int) -> tuple[bool, list[Order] | None]:
        """
        Retrieves all orders for a specific merchant.

        Args:
            merchant_id (int): The ID of the merchant.

        Returns:
            tuple[bool, list[Order] | None]: A tuple containing a boolean for success,
                                             and either a list of orders or `None` on failure.
        """
        try:
            orders = self.order_repo.read_all_by_merchant_id(merchant_id)
            return (True, orders)
        except Exception as e:
            print(f"[OrderService ERROR] An unexpected error occurred while fetching orders for merchant {merchant_id}: {e}")
            return (False, None)

    def cancel_order(self, order_id: int, user_id: int) -> tuple[bool, str]:
        """
        Cancels an existing order, refunds the payment, and reverts product metadata.
        FIXED: Allow cancellation for PENDING and PAID statuses, and restore product inventory.

        Args:
            order_id (int): The ID of the order to cancel.
            user_id (int): The ID of the user requesting the cancellation.

        Returns:
            tuple[bool, str]: A tuple containing a boolean for success and a message.
        """
        transaction_committed = False
        try:
            self.db.begin_transaction()

            # --- 1. Fetch the order and perform validations ---
            order = self.order_repo.read(order_id)
            if not order:
                return (False, f"Order with ID {order_id} not found.")

            if order.user_id != user_id:
                return (False, "You are not authorized to cancel this order.")

            if order.status not in [Status.PENDING, Status.PAID]:
                return (False, f"Order cannot be canceled. Current status: {order.status.name}.")

            # --- 2. Get Virtual Cards ---
            user_card = self.transaction_service.virtual_card_repo.get_by_user_id(order.user_id)
            merchant_card = self.transaction_service.virtual_card_repo.get_by_merchant_id(order.merchant_id)

            if not user_card or not merchant_card:
                return (False, "CRITICAL: Could not retrieve card details for refund. Cannot cancel order.")

            # --- 3. Process Refund ---
            refund_success, refund_message = self.transaction_service.transfer_funds(
                sender_card_id=merchant_card.id,
                receiver_card_id=user_card.id,
                amount=order.total_amount,
                payment_type="REFUND",
                in_transaction=True
            )
            if not refund_success:
                return (False, f"Order cancellation failed: {refund_message}")

            # --- 4. Update Order Status ---
            update_success, update_message = self.order_repo.update_status(order_id, Status.CANCELLED)
            if not update_success:
                return (False, f"CRITICAL: Refund succeeded but order status update failed. Transaction rolled back. Reason: {update_message}")

            # --- 5. Revert Product Metadata AND Restore Inventory ---
            for item in order.items:
                # Decrement sold count
                self.product_repo.metadata_repo.decrement_field(item.product_id, 'sold_count', item.product_quantity)
                
                product = self.product_repo.read(item.product_id)
                if product:
                    self.product_repo.update(
                        item.product_id, 
                        {'quantity_available': product.quantity_available + item.product_quantity}
                    )

            # --- 6. Commit Transaction ---
            self.db.commit()
            transaction_committed = True
            return (True, f"Order {order_id} has been successfully canceled and refunded.")

        except Exception as e:
            print(f"[OrderService ERROR] An unexpected error occurred during order cancellation: {e}")
            return (False, "An unexpected error occurred during order cancellation. The transaction has been rolled back.")
        finally:
            if not transaction_committed:
                self.db.rollback()


    def confirm_delivery(self, order_id: int, user_id: int) -> tuple[bool, str]:
        """
        Confirms that an order has been delivered by the user.

        Args:
            order_id (int): The ID of the order to confirm.
            user_id (int): The ID of the user confirming the delivery.

        Returns:
            tuple[bool, str]: A tuple containing a boolean for success and a message.
        """
        # 1. Fetch the order and perform validations
        order = self.order_repo.read(order_id)
        if not order:
            return (False, f"Order with ID {order_id} not found.")

        if order.user_id != user_id:
            return (False, "You are not authorized to confirm delivery for this order.")

        if order.status != Status.SHIPPED:
            return (False, f"Cannot confirm delivery. Order status is '{order.status.name}', not 'SHIPPED'.")

        # 2. Update Order Status
        success, message = self.order_repo.update_status(order_id, Status.DELIVERED)
        return (success, "Delivery confirmed successfully! You can now review the product." if success else message)


    def get_order_details(self, order_id: int, user_id: int) -> tuple[bool, str | tuple[Order, Invoice | None]]:
        """
        Retrieves the full details for an order, including the invoice,
        and verifies user ownership.

        Args:
            order_id (int): The ID of the order to retrieve.
            user_id (int): The ID of the user making the request.

        Returns:
            tuple[bool, str | tuple[Order, Invoice | None]]: A tuple containing success status,
                and either an error message or a tuple of (Order, Invoice).
        """
        order = self.order_repo.read(order_id)
        if not order:
            return (False, f"Order with ID {order_id} not found.")

        if order.user_id != user_id:
            return (False, "You are not authorized to view this order.")

        invoice = self.order_repo.get_invoice_by_order_id(order_id)
        if not invoice:
            # This is not a critical failure, an order might exist without an invoice yet.
            print(f"[OrderService WARN] No invoice found for order {order_id}")

        return (True, (order, invoice))

    def ship_order(self, order_id: int, merchant_id: int) -> tuple[bool, str]:
        """
        Allows a merchant to mark an order as shipped.

        Args:
            order_id (int): The ID of the order to ship.
            merchant_id (int): The ID of the merchant performing the action.

        Returns:
            tuple[bool, str]: A tuple containing a boolean for success and a message.
        """
        # 1. Fetch the order and perform validations
        order = self.order_repo.read(order_id)
        if not order:
            return (False, f"Order with ID {order_id} not found.")

        if order.merchant_id != merchant_id:
            return (False, "You are not authorized to ship this order.")

        if order.status != Status.PAID:
            return (False, f"Order cannot be shipped. Current status: '{order.status.name}'.")

        # 2. Update Order Status
        success, message = self.order_repo.update_status(order_id, Status.SHIPPED)
        return (success, "Order marked as shipped successfully." if success else message)

    def merchant_cancel_order(self, order_id: int, merchant_id: int) -> tuple[bool, str]:
        """
        Allows a merchant to cancel an order, which refunds the customer.
        FIXED: Use correct card retrieval and restore inventory.

        Args:
            order_id (int): The ID of the order to cancel.
            merchant_id (int): The ID of the merchant performing the action.

        Returns:
            tuple[bool, str]: A tuple containing a boolean for success and a message.
        """
        transaction_committed = False
        try:
            self.db.begin_transaction()

            # 1. Fetch the order and perform validations
            order = self.order_repo.read(order_id)
            if not order:
                return (False, f"Order with ID {order_id} not found.")

            if order.merchant_id != merchant_id:
                return (False, "You are not authorized to cancel this order.")

            # Only allow cancellation for PENDING and PAID orders (not SHIPPED)
            if order.status not in [Status.PENDING, Status.PAID]:
                return (False, f"Only pending or paid orders can be canceled. Current status: {order.status.name}.")

            # 2. Get Virtual Cards - FIXED: Use correct method
            user_card = self.transaction_service.virtual_card_repo.get_by_user_id(order.user_id)
            merchant_card = self.transaction_service.virtual_card_repo.get_by_merchant_id(order.merchant_id)

            if not user_card or not merchant_card:
                return (False, "CRITICAL: Could not retrieve card details for refund. Cannot cancel order.")

            # 3. Process Refund
            refund_success, refund_message = self.transaction_service.transfer_funds(
                sender_card_id=merchant_card.id, 
                receiver_card_id=user_card.id,
                amount=order.total_amount, 
                payment_type="REFUND", 
                in_transaction=True
            )
            if not refund_success:
                return (False, f"Order cancellation failed: {refund_message}")

            # 4. Update Order Status
            self.order_repo.update_status(order_id, Status.CANCELLED)
            
            # 5. Revert Product Metadata AND Restore Inventory - FIXED
            for item in order.items:
                # Decrement sold count
                self.product_repo.metadata_repo.decrement_field(item.product_id, 'sold_count', item.product_quantity)
                
                # Restore product quantity back to inventory
                product = self.product_repo.read(item.product_id)
                if product:
                    self.product_repo.update(
                        item.product_id, 
                        {'quantity_available': product.quantity_available + item.product_quantity}
                    )
            
            # 6. Commit Transaction
            self.db.commit()
            transaction_committed = True
            return (True, f"Order {order_id} has been successfully canceled and refunded.")
        finally:
            if not transaction_committed:
                self.db.rollback()

    def create_order_from_cart(self, user_id: int, address_id: int) -> tuple[list[int] | None, str]:
        """
        Orchestrates the entire checkout process from a user's cart.
        Supports multiple merchants by creating separate orders for each.
        This is a transactional operation.
        
        Args:
            user_id (int): The ID of the user checking out.
            address_id (int): The selected shipping and billing address ID.
        
        Returns:
            tuple[list[int] | None, str]: A tuple containing a list of new order IDs and a message.
        """
        transaction_committed = False
        created_order_ids = []
        
        try:
            self.db.begin_transaction()
            
            # 1. Get cart contents
            cart_items = self.cart_repo.get_cart_contents(user_id)
            if not cart_items:
                return (None, "Your cart is empty.")
            
            # 2. Group cart items by merchant
            merchant_groups = {}
            for item in cart_items:
                product = self.product_repo.read(item.product_id)
                if not product:
                    raise Exception(f"Product '{item.product_name}' is no longer available.")
                
                if product.quantity_available < item.quantity:
                    raise Exception(
                        f"Not enough stock for '{item.product_name}'. "
                        f"Only {product.quantity_available} left."
                    )
                
                merchant_id = product.merchant_id
                if merchant_id not in merchant_groups:
                    merchant_groups[merchant_id] = {
                        'items': [],
                        'total_amount': 0.0
                    }
                
                merchant_groups[merchant_id]['items'].append(OrderItemCreate(
                    product_id=item.product_id,
                    product_quantity=item.quantity,
                    product_price=item.price
                ))
                merchant_groups[merchant_id]['total_amount'] += item.total_price
            
            # 3. Get user's card (needed for all orders)
            user_card = self.transaction_service.virtual_card_repo.get_by_user_id(user_id)
            if not user_card:
                raise Exception("Could not find your payment card.")
            
            # 4. Create an order for each merchant
            for merchant_id, group_data in merchant_groups.items():
                # Get merchant's card
                merchant_card = self.transaction_service.virtual_card_repo.get_by_merchant_id(merchant_id)
                if not merchant_card:
                    raise Exception(f"Could not find payment card for merchant {merchant_id}.")
                
                # Create order for this merchant
                new_order_id, message = self.create_order(
                    user_id=user_id,
                    merchant_id=merchant_id,
                    shipping_address_id=address_id,
                    billing_address_id=address_id,
                    items=group_data['items'],
                    user_card_id=user_card.id,
                    merchant_card_id=merchant_card.id
                )
                
                if not new_order_id:
                    # If any order fails, the exception will trigger rollback of all orders
                    raise Exception(f"Failed to create order for merchant {merchant_id}: {message}")
                
                created_order_ids.append(new_order_id)
            
            # 5. Clear the user's cart only after ALL orders succeed
            self.cart_repo.clear_cart(user_id)
            
            # 6. Commit the entire transaction
            self.db.commit()
            transaction_committed = True
            
            # Build success message
            if len(created_order_ids) == 1:
                return (created_order_ids, "Order placed successfully!")
            else:
                return (
                    created_order_ids,
                    f"Successfully placed {len(created_order_ids)} orders from {len(created_order_ids)} merchants!"
                )
        
        except Exception as e:
            print(f"[OrderService ERROR] Checkout failed for user {user_id}: {e}")
            if not transaction_committed:
                self.db.rollback()
            return (None, f"Checkout failed: {e}")