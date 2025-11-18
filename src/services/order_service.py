from __future__ import annotations
from typing import TYPE_CHECKING

from models.orders import OrderCreate, OrderItemCreate
from models.status import Status

if TYPE_CHECKING:
    from repositories.order_repository import OrderRepository
    from repositories.product_repository import ProductRepository
    from repositories.inventory_repository import InventoryRepository
    from services.transaction_service import TransactionService


class OrderService:
    """
    Handles the business logic for creating and managing orders.
    """

    def __init__(self, order_repo: OrderRepository, product_repo: ProductRepository, inventory_repo: InventoryRepository, transaction_service: TransactionService):
        self.order_repo = order_repo
        self.product_repo = product_repo
        self.inventory_repo = inventory_repo
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
        order creation, and inventory updates.

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
            inventory = self.inventory_repo.read(item.product_id)
            if not product:
                return (None, f"Validation failed: Product with ID {item.product_id} not found.")
            if not inventory or inventory.quantity_available < item.quantity:
                available = inventory.quantity_available if inventory else 0
                return (None, f"Validation failed: Insufficient stock for '{product.name}'. Requested: {item.quantity}, Available: {available}.")

            # Use the current product price for the order
            item.price_at_purchase = product.price
            total_amount += item.price_at_purchase * item.quantity
            validated_items.append(item)

        if total_amount <= 0:
            return (None, "Total amount must be positive.")

        # --- 2. Process Payment ---
        payment_success, payment_message = self.transaction_service.transfer_funds(
            sender_card_id=user_card_id,
            receiver_card_id=merchant_card_id,
            amount=total_amount,
            payment_type="ORDER_PAYMENT"
        )

        if not payment_success:
            return (None, f"Order creation failed: {payment_message}")

        # --- 3. Create the Order record ---
        order_to_create = OrderCreate(
            user_id=user_id,
            merchant_id=merchant_id,
            shipping_address_id=shipping_address_id,
            billing_address_id=billing_address_id,
            total_amount=total_amount,
            items=validated_items,
            status=Status.PAID  # Set status to PAID since payment was successful
        )

        new_order_id, order_message = self.order_repo.create(order_to_create)

        if not new_order_id:
            # This is a critical failure. Payment was made, but order creation failed.
            # We must attempt to refund the user.
            self.transaction_service.transfer_funds(
                sender_card_id=merchant_card_id,
                receiver_card_id=user_card_id,
                amount=total_amount,
                payment_type="CRITICAL_REFUND"
            )
            return (None, f"CRITICAL: Payment succeeded but order creation failed. A refund has been issued. Reason: {order_message}")

        # --- 4. Update Product Inventory and Metadata ---
        for item in validated_items:
            # Atomically decrease inventory and update sold count
            self.inventory_repo.adjust_quantity(item.product_id, -item.quantity)
            self.product_repo.metadata_repo.increment_field(item.product_id, 'sold_count', item.quantity)

        return (new_order_id, f"Order created successfully with ID {new_order_id}.")