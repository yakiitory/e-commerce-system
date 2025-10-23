from abc import ABC, abstractmethod
from database.database import Database

class BaseController(ABC):
    """Contract for every controller to follow"""

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
