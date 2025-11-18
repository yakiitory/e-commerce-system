from __future__ import annotations
from typing import TYPE_CHECKING

from models.payments import PaymentCreate
from models.status import Status

if TYPE_CHECKING:
    from repositories.transaction_repository import VirtualCardRepository, PaymentRepository
    from database.database import Database


class TransactionService:
    """
    Handles the business logic for financial transactions like payments.
    """

    def __init__(self, db: Database, virtual_card_repo: VirtualCardRepository, payment_repo: PaymentRepository):
        self.db = db
        self.virtual_card_repo = virtual_card_repo
        self.payment_repo = payment_repo

    def transfer_funds(self, sender_card_id: int, receiver_card_id: int, amount: float, payment_type: str, in_transaction: bool = False) -> tuple[bool, str]:
        """
        Transfers a specified amount from a sender's virtual card to a receiver's.
        This entire operation is performed within a database transaction to ensure atomicity.

        Args:
            sender_card_id (int): The ID of the sender's virtual card.
            receiver_card_id (int): The ID of the receiver's virtual card.
            amount (float): The amount to transfer. Must be positive.
            payment_type (str): The type of payment (e.g., 'ORDER_PAYMENT', 'REFUND').
            in_transaction (bool): If True, assumes a transaction is already active and does not manage it.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        if amount <= 0:
            return (False, "Transfer amount must be positive.")

        # Create a payment record first with a PENDING status
        payment_create = PaymentCreate(
            sender_id=sender_card_id,
            receiver_id=receiver_card_id,
            type=payment_type,
            amount=amount,
        )
        payment_id, _ = self.payment_repo.create(payment_create)

        if not payment_id:
            return (False, "Failed to create initial payment record.")

        transaction_committed = False
        try:
            if not in_transaction:
                self.db.begin_transaction()

            # 1. Debit the sender. The repository method ensures balance >= 0.
            debit_success = self.virtual_card_repo.adjust_balance(sender_card_id, -amount)
            if not debit_success:
                self.payment_repo.update(payment_id, {'status': Status.CANCELLED})
                return (False, "Transfer failed: Insufficient funds.")

            # 2. Credit the receiver.
            credit_success = self.virtual_card_repo.adjust_balance(receiver_card_id, amount)
            if not credit_success:
                self.payment_repo.update(payment_id, {'status': Status.CANCELLED})
                return (False, "Transfer failed: Could not credit receiver. Transaction rolled back.")

            # 3. If both succeed, finalize the payment status.
            self.payment_repo.update(payment_id, {'status': Status.PAID})
            if not in_transaction:
                self.db.commit()
                transaction_committed = True
            return (True, f"Transfer of {amount} successful. Payment ID: {payment_id}")

        except Exception as e:
            print(f"[TransactionService ERROR] An unexpected error occurred during fund transfer: {e}")
            self.payment_repo.update(payment_id, {'status': Status.CANCELLED})
            return (False, "An unexpected error occurred. The transaction has been cancelled.")
        finally:
            # Ensure the transaction is always closed.
            # If the commit was successful, this does nothing.
            # If there was an error or early return, this rolls back the transaction.
            if not in_transaction and not transaction_committed:
                self.db.rollback()