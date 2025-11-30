from __future__ import annotations
from typing import TYPE_CHECKING, Any

from models.payments import PaymentCreate, VirtualCardCreate
from models.status import Status

if TYPE_CHECKING:
    from repositories.transaction_repository import VirtualCardRepository, PaymentRepository
    from repositories.account_repository import UserRepository, MerchantRepository
    from models.payments import VirtualCard, Payment
    from database.database import Database


class TransactionService:
    """
    Handles the business logic for financial transactions like payments.
    """

    def __init__(self, db: Database, virtual_card_repo: VirtualCardRepository, payment_repo: PaymentRepository, user_repo: UserRepository, merchant_repo: MerchantRepository):
        self.db = db
        self.virtual_card_repo = virtual_card_repo
        self.payment_repo = payment_repo
        self.user_repo = user_repo
        self.merchant_repo = merchant_repo

    def cash_in(self, card_id: int, amount: float) -> tuple[bool, str]:
        """
        Adds funds to a user's virtual card, simulating a "cash in" from an external source.

        Args:
            card_id (int): The ID of the virtual card to fund.
            amount (float): The amount to add. Must be positive.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        if amount <= 0:
            return (False, "Cash-in amount must be positive.")

        # Create a payment record to log the cash-in.
        # id of 0 should represent the system, instead of a user or an external body
        payment_create = PaymentCreate(
            sender_id=0,
            sender_type="SYSTEM",
            receiver_id=card_id,
            receiver_type="VIRTUAL_CARD",
            amount=amount
        )

        transaction_committed = False
        try:
            self.db.begin_transaction()
            payment_id, _ = self.payment_repo.create(payment_create)
            if not payment_id:
                return (False, "Failed to create payment record for cash-in.")

            self.virtual_card_repo.adjust_balance(card_id, amount)
            self.db.commit()
            transaction_committed = True
            return (True, f"Successfully cashed in {amount} to card {card_id}.")
        finally:
            if not transaction_committed:
                self.db.rollback()

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

    def get_user_payment_history(self, user_id: int) -> list[Payment] | None:
        """
        Retrieves a user's enriched payment history.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list[Payment] | None: A list of annotated Payment objects, or None on error.
        """
        try:
            user_card = self.virtual_card_repo.get_by_user_id(user_id)
            if not user_card:
                return [] # No card means no history

            payment_history = self.payment_repo.get_payments_for_user(user_card.id)

            for payment in payment_history:
                if payment.sender_id == user_card.id:
                    transaction_type = "Sent"
                    other_party = f"{payment.receiver_type.capitalize()}"
                else:
                    transaction_type = "Received"
                    other_party = f"{payment.sender_type.capitalize()}"

                setattr(payment, 'transaction_type', transaction_type)
                setattr(payment, 'other_party', other_party)

            return payment_history

        except Exception as e:
            print(f"[TransactionService ERROR] Failed to get payment details for user {user_id}: {e}")
            return None
        

    def get_merchant_payment_history(self, merchant_id: int) -> list[Payment] | None:
        """
        Retrieves a user's enriched payment history.

        Args:
            merchant_id (int): The ID of the merchant.

        Returns:
            A tuple containing success status, and either a tuple of (VirtualCard, list[Payment])
            or an error message string.
        """
        try:
            merchant_card = self.virtual_card_repo.get_by_merchant_id(merchant_id)
            if not merchant_card:
                return [] # No card means no history

            payment_history = self.payment_repo.get_payments_for_user(merchant_card.id)

            for payment in payment_history:
                if payment.sender_id == merchant_card.id:
                    transaction_type = "Sent"
                    other_party = f"{payment.receiver_type.capitalize()}"
                else:
                    transaction_type = "Received"
                    other_party = f"{payment.sender_type.capitalize()}"

                setattr(payment, 'transaction_type', transaction_type)
                setattr(payment, 'other_party', other_party)

            return payment_history

        except Exception as e:
            print(f"[TransactionService ERROR] Failed to get payment details for merchant {merchant_id}: {e}")
            return None

    def create_virtual_card(self, owner_id: int, account_type: str) -> tuple[bool, str]:
        """
        Creates a new virtual card for a user or merchant if they don't already have one.

        Args:
            owner_id (int): The ID of the user or merchant who will own the card.
            account_type (str): The type of account ('user' or 'merchant').

        Returns:
            tuple[bool, str]: A tuple indicating success and a message.
        """
        # 1. Check if a card already exists for this owner based on account type
        if account_type == 'user':
            if self.virtual_card_repo.get_by_user_id(owner_id):
                return (False, "A virtual card already exists for this account.")
            new_card_id, message = self.virtual_card_repo.create(VirtualCardCreate(balance=0))
            self.db.execute_query("INSERT INTO user_virtualcards (user_id, virtualcard_id) VALUES (%s, %s)", (owner_id, new_card_id))
        elif account_type == 'merchant':
            if self.virtual_card_repo.get_by_merchant_id(owner_id):
                return (False, "A virtual card already exists for this account.")
            new_card_id, message = self.virtual_card_repo.create(VirtualCardCreate(balance=0))
            self.db.execute_query("INSERT INTO merchant_virtualcards (merchant_id, virtualcard_id) VALUES (%s, %s)", (owner_id, new_card_id))
        else:
            return (False, "Invalid account type specified.")

        if new_card_id:
            return (True, "Virtual card activated successfully!")
        else:
            return (False, f"Failed to activate virtual card: {message}")