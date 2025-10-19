import os
import sqlparse
from mysql.connector import pooling, Error


class Database:
    """
    Handles MariaDB/MySQL database connection pooling and queries.
    Reads credentials from environment variables.
    """

    def __init__(self):
        self._pool = None
        self._create_pool()

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
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", 3306)),
                "user": os.getenv("DB_USER", "root"),
                "password": os.getenv("DB_PASSWORD", ""),
                "database": os.getenv("DB_NAME", "ecommerce"),
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
            return self._pool.get_connection()
        except Error as e:
            print(f"[DB ERROR] Failed to get connection: {e}")
            raise

    def execute_query(self, query: str, params: tuple | None = None) -> None:
        """
        Execute an INSERT, UPDATE, or DELETE query.
        """
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            connection.commit()
        except Error as e:
            print(f"[DB ERROR] Query failed: {e}")
            if connection:
                connection.rollback()
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def fetch_one(self, query: str, params: tuple | None = None):
        """
        Execute a SELECT query and return a single row.
        """
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchone()
        except Error as e:
            print(f"[DB ERROR] Fetch one failed: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def fetch_all(self, query: str, params: tuple | None = None):
        """
        Execute a SELECT query and return all rows.
        """
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Error as e:
            print(f"[DB ERROR] Fetch all failed: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
