import os
import sqlparse
from mysql.connector import pooling, Error
from dotenv import load_dotenv


class Database:
    """
    Handles MariaDB/MySQL database connection pooling and queries.
    Reads credentials from environment variables.
    Attemps to read an existing file called "schema.sql" in the same directory.
    """

    def __init__(self):
        load_dotenv()
        self._pool = None
        self._transaction_connection = None 
        self._create_pool()
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if os.path.exists(schema_path):
            self.initialize_schema(schema_path)
        else:
            print(f"[DB] Schema file not found at {schema_path}, skipping initialization.")

    def initialize_schema(self, sql_file_path: str) -> bool:
        """
        Safely executes all SQL statements from a .sql file.
        Handles multi-line statements, triggers, foreign keys, and comments.
        """
        connection = None
        cursor = None

        try:
            connection = self.get_connection()
            cursor = connection.cursor()

            with open(sql_file_path, "r", encoding="utf-8") as f:
                sql_script = f.read()

            # Parse SQL into executable statements
            statements = sqlparse.split(sql_script)

            print(f"[DB] Executing {len(statements)} SQL statements from {sql_file_path}...")

            for statement in statements:
                stmt = statement.strip()
                if stmt and not stmt.startswith("--"):  # Skip comments
                    cursor.execute(stmt)

            connection.commit()
            print("[DB] Schema initialized successfully!")
            return True

        except Exception as e:
            print(f"[DB ERROR] Failed to initialize schema: {e}")
            if connection:
                connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def _create_pool(self):
        """
        Initialize the connection pool if not already created.
        """
        try:
            dbconfig = {
                "host": os.environ["DB_HOST"],
                "port": int(os.environ["DB_PORT"]),
                "user": os.environ["DB_USER"],
                "password": os.environ["DB_PASSWORD"],
                "database": os.environ["DB_NAME"],
            }

            self._pool = pooling.MySQLConnectionPool(
                pool_name="ecommerce_pool",
                pool_size=int(os.getenv("DB_POOL_SIZE", 5)),
                **dbconfig
            )
            print("[DB] Connection pool created successfully.")
        except Error as e:
            print(f"[DB ERROR] Failed to create connection pool: {e}")
            raise

    def get_connection(self):
        """
        Retrieve a connection from the pool.
        """
        try:
            if self._pool:
                return self._pool.get_connection()
        except Error as e:
            print(f"[DB ERROR] Failed to get connection: {e}")
            raise

    def begin_transaction(self):
        """
        Starts a new database transaction by getting a connection and holding it.
        """
        if self._transaction_connection:
            print("[DB WARN] Transaction already in progress.")
            return
        try:
            self._transaction_connection = self.get_connection()
            self._transaction_connection.start_transaction()
            print("[DB] Transaction started.")
        except Error as e:
            print(f"[DB ERROR] Failed to start transaction: {e}")
            self._transaction_connection = None # Ensure cleanup on failure
            raise

    def commit(self):
        """
        Commits the current transaction and releases the connection.
        """
        if not self._transaction_connection:
            print("[DB WARN] Commit called but no transaction is active.")
            return
        try:
            self._transaction_connection.commit()
            print("[DB] Transaction committed.")
        finally:
            self._transaction_connection.close()
            self._transaction_connection = None

    def rollback(self):
        """
        Rolls back the current transaction and releases the connection.
        """
        if not self._transaction_connection:
            print("[DB WARN] Rollback called but no transaction is active.")
            return
        try:
            self._transaction_connection.rollback()
            print("[DB] Transaction rolled back.")
        finally:
            self._transaction_connection.close()
            self._transaction_connection = None

    def execute_query(self, query: str, params: tuple | None = None) -> int | None:
        """
        Execute an INSERT, UPDATE, or DELETE query.
        Returns the last inserted row ID for INSERT statements, or None otherwise.
        """
        connection = None
        cursor = None
        last_id = None
        try:
            # Use the transaction connection if available, otherwise get a new one.
            connection = self._transaction_connection or self.get_connection()
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            # Only commit if not in a transaction. The final commit() call will handle it.
            if not self._transaction_connection:
                connection.commit()
            last_id = cursor.lastrowid # Capture the last inserted ID
        except Error as e:
            print(f"[DB ERROR] Query failed: {e}")
            # Only rollback if not in a transaction. The final rollback() call will handle it.
            if connection and not self._transaction_connection:
                connection.rollback()
        finally:
            if cursor:
                cursor.close()
            # Only close the connection if it's not part of a transaction.
            if connection and not self._transaction_connection:
                connection.close()
        return last_id

    def fetch_one(self, query: str, params: tuple | None = None):
        """
        Execute a SELECT query and return a single row.
        """
        connection = None
        cursor = None
        try:
            # Use the transaction connection if available, otherwise get a new one.
            connection = self._transaction_connection or self.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchone()
        except Error as e:
            print(f"[DB ERROR] Fetch one failed: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            # Only close the connection if it's not part of a transaction.
            if connection and not self._transaction_connection:
                connection.close()

    def fetch_all(self, query: str, params: tuple | None = None):
        """
        Execute a SELECT query and return all rows.
        """
        connection = None
        cursor = None
        try:
            # Use the transaction connection if available, otherwise get a new one.
            connection = self._transaction_connection or self.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Error as e:
            print(f"[DB ERROR] Fetch all failed: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            # Only close the connection if it's not part of a transaction.
            if connection and not self._transaction_connection:
                connection.close()
