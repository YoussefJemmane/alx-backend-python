#!/usr/bin/env python3
"""Module implementing a custom context manager for database connections."""
import sqlite3


class DatabaseConnection:
    """A context manager for handling database connections."""
    
    def __init__(self, database_name='users.db'):
        """Initialize with database name."""
        self.database_name = database_name
        self.connection = None
    
    def __enter__(self):
        """Establish database connection when entering context."""
        self.connection = sqlite3.connect(self.database_name)
        return self.connection
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Close database connection when exiting context."""
        if self.connection:
            self.connection.close()


if __name__ == "__main__":
    # Using the context manager
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        print(results)

