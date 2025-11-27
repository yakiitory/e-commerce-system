from __future__ import annotations
from typing import TYPE_CHECKING

from models.orders import Order, OrderCreate, OrderItemCreate
from models.status import Status

if TYPE_CHECKING:
    from repositories.order_repository import OrderRepository
    from repositories.product_repository import ProductRepository
    from services.transaction_service import TransactionService
    from database.database import Database


class OrderService:
    """
    Handles the business logic for creating and managing orders.
    """

    def __init__(self, db: Database, order_repo: OrderRepository, product_repo: ProductRepository, transaction_service: TransactionService):
        self.db = db
        self.order_repo = order_repo
        self.product_repo = product_repo
        self.transaction_service = transaction_service

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
        order creation updates.

        Args:
            user_id (int): The ID of the user placing the order.
            merchant_id (int): The ID of the merchant fulfilling the order.
            shipping_address_id (int): The shipping address ID.
            billing_address_id (int): The billing address ID.
            items (list[OrderItemCreate]): A list of items to be included in the order.
            user_card_id (int): The virtual card ID of the user for payment.
            merchant_card_id (int): The virtual card ID of the merchant to receive payment.

        Returns:
            tuple[int | None, str]: A tuple containing the new order ID and a message.
        """
        if not items:
            return (None, "Cannot create an order with no items.")

        # --- 1. Validate items and calculate total amount ---
        total_amount = 0.0
        validated_items = []
        for item in items:
            product = self.product_repo.read(item.product_id)
            if not product:
                return (None, f"Validation failed: Product with ID {item.product_id} not found.")
            # Use the current product price for the order
            item.price_at_purchase = product.price
            total_amount += item.price_at_purchase * item.quantity
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
                amount=total_amount,
                payment_type="ORDER_PAYMENT",
                in_transaction=True
            )
            if not payment_success:
                # transfer_funds already rolled back its own sub-steps, but we return here
                # and the finally block will ensure the outer transaction is also rolled back.
                return (None, f"Order creation failed: {payment_message}")

            # --- 3. Create the Order record ---
            order_to_create = OrderCreate(
                user_id=user_id, merchant_id=merchant_id,
                shipping_address_id=shipping_address_id, billing_address_id=billing_address_id,
                total_amount=total_amount, items=validated_items, status=Status.PAID
            )
            new_order_id, order_message = self.order_repo.create(order_to_create)
            if not new_order_id:
                # This is a critical failure. The transaction will be rolled back.
                return (None, f"CRITICAL: Payment succeeded but order creation failed. Transaction rolled back. Reason: {order_message}")

            # --- 4. Update Product Metadata ---
            for item in validated_items:
                self.product_repo.metadata_repo.increment_field(item.product_id, 'sold_count', item.quantity)

            # --- 5. Commit Transaction ---
            self.db.commit()
            transaction_committed = True
            return (new_order_id, f"Order created successfully with ID {new_order_id}.")

        except Exception as e:
            print(f"[OrderService ERROR] An unexpected error occurred during order creation: {e}")
            return (None, "An unexpected error occurred during order creation. The transaction has been rolled back.")
        finally:
            if not transaction_committed:
                self.db.rollback()

    def get_orders_for_user(self, user_id: int) -> tuple[bool, str | list[Order]]:
        """
        Retrieves all orders placed by a specific user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            tuple[bool, str | list[Order]]: A tuple containing a boolean for success,
                                            and either a list of orders or an error message.
        """
        try:
            orders = self.order_repo.read_all_by_user_id(user_id)
            return (True, orders)
        except Exception as e:
            print(f"[OrderService ERROR] An unexpected error occurred while fetching orders for user {user_id}: {e}")
            return (False, "An unexpected error occurred while fetching orders.")

    def get_orders_for_merchant(self, merchant_id: int) -> tuple[bool, str | list[Order]]:
        """
        Retrieves all orders for a specific merchant.

        Args:
            merchant_id (int): The ID of the merchant.

        Returns:
            tuple[bool, str | list[Order]]: A tuple containing a boolean for success,
                                            and either a list of orders or an error message.
        """
        try:
            orders = self.order_repo.read_all_by_merchant_id(merchant_id)
            return (True, orders)
        except Exception as e:
            print(f"[OrderService ERROR] An unexpected error occurred while fetching orders for merchant {merchant_id}: {e}")
            return (False, "An unexpected error occurred while fetching orders.")

    def cancel_order(self, order_id: int, user_id: int) -> tuple[bool, str]:
        """
        Cancels an existing order, refunds the payment, and reverts product metadata.

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

            if order.status != Status.PAID:
                return (False, f"Order cannot be canceled. Current status: {order.status.value}.")

            # --- 2. Process Refund ---
            # We need the virtual card IDs for the refund.
            user_card = self.order_repo.get_user_card_for_order(order_id)
            merchant_card = self.order_repo.get_merchant_card_for_order(order_id)

            if not user_card or not merchant_card:
                return (False, "CRITICAL: Could not retrieve card details for refund. Cannot cancel order.")

            refund_success, refund_message = self.transaction_service.transfer_funds(
                sender_card_id=merchant_card.id,
                receiver_card_id=user_card.id,
                amount=order.total_amount,
                payment_type="REFUND",
                in_transaction=True
            )
            if not refund_success:
                return (False, f"Order cancellation failed: {refund_message}")

            # --- 3. Update Order Status ---
            update_success, update_message = self.order_repo.update_status(order_id, Status.CANCELLED)
            if not update_success:
                return (False, f"CRITICAL: Refund succeeded but order status update failed. Transaction rolled back. Reason: {update_message}")

            # --- 4. Revert Product Metadata ---
            for item in order.items:
                self.product_repo.metadata_repo.decrement_field(item.product_id, 'sold_count', item.quantity)

            # --- 5. Commit Transaction ---
            self.db.commit()
            transaction_committed = True
            return (True, f"Order {order_id} has been successfully canceled and refunded.")

        except Exception as e:
            print(f"[OrderService ERROR] An unexpected error occurred during order cancellation: {e}")
            return (False, "An unexpected error occurred during order cancellation. The transaction has been rolled back.")
        finally:
            if not transaction_committed:
                self.db.rollback()