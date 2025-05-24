#!/usr/bin/env python3
"""Module for handling database connections using a decorator."""
import sqlite3
import functools


def with_db_connection(func):
    """Decorator that handles database connection lifecycle."""
    @functools.wraps(func)
    def wrapper(user_id):
        conn = sqlite3.connect('users.db')
        try:
            return func(conn, user_id)
        finally:
            conn.close()
    return wrapper


@with_db_connection
def get_user_by_id(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()


if __name__ == "__main__":
    user = get_user_by_id(user_id=1)
    print(user)

#!/usr/bin/env python3
"""Module for handling database connections using a decorator."""
import sqlite3
import functools


def with_db_connection(func):
    """
    Decorator that handles database connection lifecycle.
    Opens a connection, passes it to the function, and ensures proper closure.
    """
    @functools.wraps(func)
    def wrapper(user_id):
        conn = sqlite3.connect('users.db')
        try:
            result = func(conn, user_id)
            return result
        finally:
            conn.close()
    return wrapper


@with_db_connection
def get_user_by_id(conn, user_id):
    """
    Fetch a user from the database by their ID.
    
    Args:
        conn: SQLite database connection
        user_id: ID of the user to fetch
        
    Returns:
        tuple: User record or None if not found
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()


if __name__ == "__main__":
    user = get_user_by_id(user_id=1)
    print(user)

