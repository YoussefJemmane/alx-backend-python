#!/usr/bin/env python3
"""Module for logging database queries using a decorator."""
import sqlite3
import functools


def log_queries():
    """
    Decorator that logs SQL queries before they are executed.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(query):
            print(f"Query: {query}")
            return func(query)
        return wrapper
    return decorator


@log_queries()
def fetch_all_users(query):
    """
    Fetch all users from the database using the provided query.
    
    Args:
        query (str): SQL query to execute
        
    Returns:
        list: Results of the query
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


if __name__ == "__main__":
    users = fetch_all_users(query="SELECT * FROM users")

