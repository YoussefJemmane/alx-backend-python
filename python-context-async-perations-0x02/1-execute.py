#!/usr/bin/env python3
"""Module implementing a query execution context manager."""
import sqlite3


class ExecuteQuery:
    """A context manager for executing parameterized queries."""
    
    def __init__(self, query, params):
        """Initialize with query and parameters."""
        self.query = query
        self.params = params
        self.connection = None
        self.cursor = None
        self.results = None
    
    def __enter__(self):
        """Set up database connection and execute query."""
        self.connection = sqlite3.connect('users.db')
        self.cursor = self.connection.cursor()
        self.cursor.execute(self.query, self.params)
        self.results = self.cursor.fetchall()
        return self.results
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Clean up database resources."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


if __name__ == "__main__":
    # Using the context manager
    with ExecuteQuery("SELECT * FROM users WHERE age > ?", (25,)) as results:
        print(results)

