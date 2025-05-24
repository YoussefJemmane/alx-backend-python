#!/usr/bin/env python3
"""Module for database transaction management using decorators."""
import sqlite3
import functools


def with_db_connection(func):
    """Decorator that handles database connection lifecycle."""
    @functools.wraps(func)
    def wrapper(user_id, *args, **kwargs):
        conn = sqlite3.connect('users.db')
        try:
            return func(conn, user_id, *args, **kwargs)
        finally:
            conn.close()
    return wrapper


def transactional(func):
    """Decorator that manages database transactions."""
    @functools.wraps(func)
    def wrapper(conn, *args, **kwargs):
        try:
            result = func(conn, *args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            raise e
    return wrapper


@with_db_connection
@transactional
def update_user_email(conn, user_id, new_email):
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user_id))


if __name__ == "__main__":
    update_user_email(user_id=1, new_email='Crawford_Cartwright@hotmail.com')

