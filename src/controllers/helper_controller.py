from typing import override, TypeVar, Callable
from controllers.base_controller import BaseController
from database.database import Database

from models.addresses import Address, AddressCreate

class AddressController(BaseController):
    def __init__(self, db: Database):
        self.db = db
        self.table_name = "addresses"

    @override
    def create(self, data: AddressCreate) -> tuple[bool, str]:
        """Creates a new address record.

        Args:
            data (AddressCreate): An AddressCreate object containing the new address record data.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        fields = [
            "house_no",
            "street",
            "city",
            "postal_code",
            "additional_notes",
        ]
        new_id, message = self._create_record(data=data, fields=fields, table_name=self.table_name, db=self.db)
        return (new_id is not None, message)
    
    @override
    def read(self, identifier: int) -> Address | None:
        """Reads an address record by ID.
        
        Args:
            identifier (int): The ID of the address in database.
        
        Returns:
            Address | None: The Address object if found, otherwise `None`.
        """
        return self._id_to_dataclass(identifier=identifier, table_name=self.table_name, db=self.db, map_func=self._map_to_address)

    @override
    def update(self, identifier: int, data: dict) -> bool:
        """Updates an existing address record.

        Args:
            identifier (int): The ID of the address to update.
            data (dict): A dictionary of fields to update and their new values.

        Returns:
            bool: `True` if the update was successful, `False` otherwise.
        """

        fields = [
            "house_no",
            "street",
            "city",
            "postal_code",
            "additional_notes",
        ]
        return self._update_by_id(identifier=identifier, data=data, table_name=self.table_name, db=self.db, allowed_fields=fields)

    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        """Deletes an address record by its ID.
        
        Args:
            identifier (int): The ID of the address to delete.
        
        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        return self._delete_by_id(identifier, table_name=self.table_name, db=self.db, id_field="id")


    def _map_to_address(self, row: dict) -> Address | None:
        """Maps a database row (dictionary) to an Address dataclass object.

        Args:
            row (dict): A dictionary representing a row from the 'addresses' table.

        Returns:
            Address | None: An Address object if the row is not empty, otherwise `None`.
        """
        if not row:
            return None
        return Address(**row)
    
