from typing import override, Any
from repositories.base_repository import BaseRepository
from database.database import Database
from models.payments import VirtualCard, VirtualCardCreate, Payment, PaymentCreate
from models.status import Status


class VirtualCardRepository(BaseRepository):
    def __init__(self, db: Database):
        """Initializes the VirtualCardRepository."""
        self.db = db
        self.table_name = "virtualcards"

    @override   
    def create(self, data: VirtualCardCreate) -> tuple[int | None, str]:
        """
        Creates a new virtual card record.
        Args:
            data (VirtualCardCreate): The data for the new virtual card.
            account_type (str): User or merchant.

        Returns:
            tuple[int | None, str]: A tuple with the new ID and a message.
        """
        fields = ["balance"]
        new_id, message = self._create_record(data, fields, self.table_name, self.db)
        return (new_id, message)

    @override
    def read(self, identifier: int) -> VirtualCard | None:
        """
        Reads a virtual card record by its ID.

        Args:
            identifier (int): The ID of the virtual card to retrieve.

        Returns:
            VirtualCard | None: The VirtualCard object if found, otherwise None.
        """
        return self._id_to_dataclass(
            identifier=identifier,
            table_name=self.table_name,
            db=self.db,
            map_func=lambda row: VirtualCard(**row) if row else None
        )

    @override
    def update(self, identifier: int, data: dict[str, Any]) -> bool:
        """This method is not supported for direct updates. Use adjust_balance instead."""
        raise NotImplementedError("Direct balance updates are unsafe. Use `adjust_balance` for atomic operations.")

    def adjust_balance(self, identifier: int, amount: float) -> bool:
        """
        Atomically adjusts the balance of a virtual card.
        A positive amount adds to the balance, a negative amount subtracts.

        Args:
            identifier (int): The ID of the virtual card.
            amount (float): The amount to adjust the balance by.

        Returns:
            bool: True if successful, False otherwise.
        """
        # This query atomically updates the balance only if the resulting balance is non-negative.
        query = f"UPDATE {self.table_name} SET balance = balance + %s WHERE id = %s AND balance + %s >= 0"
        params = (amount, identifier, amount)

        try:
            # We need to check the number of affected rows to confirm the update happened.
            # Assuming execute_query returns the number of affected rows for UPDATE statements.
            affected_rows = self.db.execute_query(query, params)

            if affected_rows is not None and affected_rows > 0:
                print(f"[{self.__class__.__name__}] Adjusted balance for card ID {identifier} by {amount}.")
                return True
            else:
                # This means the update was blocked, likely due to insufficient funds.
                print(f"[{self.__class__.__name__} INFO] Balance adjustment for card ID {identifier} failed. Insufficient funds or card not found.")
                return False
        except Exception as e:
            print(f"[{self.__class__.__name__} ERROR] Failed to adjust balance for card ID {identifier}: {e}") # pragma: no cover
            return False



    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        """
        Deletes a virtual card record by its ID.

        Args:
            identifier (int): The ID of the virtual card to delete.

        Returns:
            tuple[bool, str]: A tuple indicating success and a message.
        """
        return self._delete_by_id(identifier, self.table_name, self.db)

    def get_by_user_id(self, user_id: int) -> VirtualCard | None:
        query = """
            SELECT vc.*
            FROM virtualcards vc
            JOIN user_virtualcards uvc ON vc.id = uvc.virtualcard_id
            WHERE uvc.user_id = %s
        """
        result = self.db.fetch_one(query, (user_id,))
        return VirtualCard(**result) if result else None
    
    def get_by_merchant_id(self, merchant_id: int) -> VirtualCard | None:
        query = """
            SELECT vc.*
            FROM virtualcards vc
            JOIN merchant_virtualcards mvc ON vc.id = mvc.virtualcard_id
            WHERE mvc.merchant_id = %s
        """
        result = self.db.fetch_one(query, (merchant_id,))
        return VirtualCard(**result) if result else None



class PaymentRepository(BaseRepository):
    def __init__(self, db: Database):
        """Initializes the PaymentRepository."""
        self.db = db
        self.table_name = "payments"

    @override
    def create(self, data: PaymentCreate) -> tuple[int | None, str]:
        """
        Creates a new payment record.

        Args:
            data (PaymentCreate): The data for the new payment.

        Returns:
            tuple[int | None, str]: A tuple with the new ID and a message.
        """
        fields = ["sender_id", "sender_type", "receiver_id", "receiver_type", "amount"]

        new_id, message = self._create_record(data, fields, self.table_name, self.db)
        return (new_id, message)

    @override
    def read(self, identifier: int) -> Payment | None:
        """
        Reads a payment record by its ID.

        Args:
            identifier (int): The ID of the payment to retrieve.

        Returns:
            Payment | None: The Payment object if found, otherwise None.
        """
        return self._id_to_dataclass(
            identifier=identifier,
            table_name=self.table_name,
            db=self.db,
            map_func=self._map_to_payment
        )

    @override
    def update(self, identifier: int, data: dict[str, Any]) -> bool:
        """
        Updates the status of a payment record. This is the only recommended update operation.

        Args:
            identifier (int): The ID of the payment to update.
            data (dict[str, Any]): A dictionary containing the 'status' to update.

        Returns:
            bool: True if successful, False otherwise.
        """
        allowed_fields = ["status"]

        update_data = data.copy()
        # Convert Status enum to its integer value if present
        if 'status' in update_data and isinstance(update_data['status'], Status):
            update_data['status'] = update_data['status'].value

        return self._update_by_id(identifier, update_data, self.table_name, self.db, allowed_fields)

    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        """
        Hard-deleting financial records is disallowed.
        To void a payment, update its status to CANCELLED or REFUNDED.
        """
        raise NotImplementedError("Payments cannot be deleted. Update status to CANCELLED or REFUNDED instead.")

    def get_payments_for_user(self, user_id: int) -> list[Payment]:
        """
        Retrieves all payments where the user was the sender or receiver, sorted by creation date.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list[Payment]: A list of Payment objects.
        """
        query = f"SELECT * FROM {self.table_name} WHERE (sender_id = %s AND sender_type = 'VIRTUAL_CARD') OR (receiver_id = %s AND receiver_type = 'VIRTUAL_CARD')"
        rows = self.db.fetch_all(query, (user_id, user_id)) # user_id is now card_id
        if not rows:
            return []
        return [payment for row in rows if (payment := self._map_to_payment(row)) is not None]

    def get_payments_for_merchant(self, merchant_id: int) -> list[Payment]:
        """
        Retrieves all payments where the merchant was the sender or receiver, sorted by creation date.

        Args:
            merchant_id (int): The ID of the merchant.

        Returns:
            list[Payment]: A list of Payment objects.
        """
        query = f"SELECT * FROM {self.table_name} WHERE (sender_id = %s AND sender_type = 'VIRTUAL_CARD') OR (receiver_id = %s AND receiver_type = 'VIRTUAL_CARD')"
        rows = self.db.fetch_all(query, (merchant_id, merchant_id))
        if not rows:
            return []
        return [payment for row in rows if (payment := self._map_to_payment(row)) is not None]

    def _map_to_payment(self, row: dict) -> Payment | None:
        """
        Maps a database row to a Payment dataclass object, handling enum conversion.
        """
        if not row:
            return None

        payment_data = row.copy()
        # Convert integer status from DB back to Status enum
        if 'status' in payment_data:
            try:
                payment_data['status'] = Status(payment_data['status'])
            except ValueError:
                print(f"[{self.__class__.__name__} WARNING] Invalid status value '{payment_data['status']}' for payment ID {payment_data.get('id')}")

        return Payment(**payment_data)