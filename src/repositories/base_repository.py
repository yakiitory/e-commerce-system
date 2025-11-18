from abc import ABC, abstractmethod
from database.database import Database

class BaseRepository(ABC):
    """Contract for every repository to follow"""

    @abstractmethod
    def create(self, data): ...

    @abstractmethod
    def read(self, identifier): ...

    @abstractmethod
    def update(self, identifier, data): ...

    @abstractmethod
    def delete(self, identifier): ...

    def _create_record(self, data, fields: list[str], table_name: str, db: Database) -> tuple[int | None, str]:
        """Generic create method for any table.

        Args:
            data: An object containing the record data, expected to have attributes
                corresponding to `fields`.
            fields (list[str]): A list of field names to insert into the database.
            table_name (str): The name of the database table to insert into.
            db (Database): The database instance.

        Returns:
            tuple[int | None, str]: A tuple where the first element is the new record's ID
                if successful, `None` otherwise. The second element is a message.
        """
        caller_name = self.__class__.__name__

        # Build dynamic query
        placeholders = ", ".join(["%s"] * len(fields))
        columns = ", ".join(fields)
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        params = [getattr(data, f) for f in fields]

        try:
            last_id = db.execute_query(query, tuple(params))
            print(f"[{caller_name}] {table_name} record created with ID: {last_id}.")
            return (last_id, f"{caller_name} record created!")
        except Exception as e:
            print(f"[{caller_name} ERROR] Create failed: {e}")
            return (None, f"Failed to create {caller_name.lower()} record.")
        
    def _id_to_dataclass(self, identifier: int, table_name: str, db: Database, map_func, id_field: str = "id"):
        """Generic map method for any table by its ID.
        Automatically logs using the caller's class name.

        Args:
            identifier (int): The ID of the record to retrieve.
            map_func (callable): A function to map the database row (dict) to a
                specific model object (e.g., User, Merchant).
            id_field (str, optional): The name of the ID column in the table.
                Defaults to "id".

        Returns:
            Any | None: The mapped model object if found, otherwise `None`.

        Raises:
            Exception: If a database error occurs during the read operation.
        """

        caller_name = self.__class__.__name__
        query = f"SELECT * FROM {table_name} WHERE {id_field} = %s"
        params = (identifier,)

        try:
            result = db.fetch_one(query, params)
            if result:
                return map_func(result)
            else:
                print(f"[{caller_name}] No record found with {id_field} = {identifier}")
                return None
        except Exception as e:
            print(f"[{caller_name} ERROR] Read failed: {e}")
            return None 

    def _update_by_id(self, identifier: int, data, table_name: str, db: Database, allowed_fields: list[str], id_field: str = "id") -> bool:
        """Generic update method for any table by its ID.

        Args:
            identifier (int): The ID of the record to update.
            data: An object containing the record data, expected to have attributes
                corresponding to `fields`.
            allowed_fields (list[str]): A list of field names that are permitted
                to be updated.
            id_field (str, optional): The name of the ID column in the table.
                Defaults to "id".

        Returns:
            bool: `True` if the update was successful, `False` otherwise.

        Raises:
            Exception: If a database error occurs during the update operation.
        """
        caller_name = self.__class__.__name__
        # Filter only valid fields
        fields_to_update = {k: v for k, v in data.items() if k in allowed_fields}
        if not fields_to_update:
            print(f"[{caller_name}] No valid fields provided for update.")
            return False

        # Build SQL dynamically
        set_clause = ", ".join(f"{key} = %s" for key in fields_to_update.keys())
        values = list(fields_to_update.values())
        values.append(identifier)

        query = f"UPDATE {table_name} SET {set_clause} WHERE {id_field} = %s"

        try:
            db.execute_query(query, tuple(values))
            print(f"[{caller_name}] {table_name} ID {identifier} updated successfully.")
            return True
        except Exception as e:
            print(f"[{caller_name} ERROR] Failed to update {table_name}: {e}")
            return False
        
    def _delete_by_id(self, identifier: int, table_name: str, db: Database, id_field: str = "id") -> tuple[bool, str]:
        """Generic delete method for any table by its ID.

        Automatically logs using the caller's class name.

        Args:
            identifier (int): The ID of the record to delete.
            id_field (str, optional): The name of the ID column in the table.
                Defaults to "id".

        Returns:
            tuple[bool, str]: A tuple where the first element is `True` if deletion
                was successful, `False` otherwise. The second element is a message.

        Raises:
            Exception: If a database error occurs during the delete operation.
        """
        caller_name = self.__class__.__name__
        query = f"DELETE FROM {table_name} WHERE {id_field} = %s"
        params = (identifier,)

        try:
            db.execute_query(query, params)
            print(f"[{caller_name}] Record deleted from {table_name} (ID={identifier})")
            return (True, f"{caller_name} record deleted successfully.")
        except Exception as e:
            print(f"[{caller_name} ERROR] Delete failed: {e}")
            return (False, f"Failed to delete {caller_name.lower()} record.")
