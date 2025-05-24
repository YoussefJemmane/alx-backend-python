#!/usr/bin/env python3
"""Module for caching database query results."""
import time
import sqlite3
import functools


query_cache = {}


def with_db_connection(func):
    """Decorator that handles database connection lifecycle."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect('users.db')
        try:
            return func(conn, *args, **kwargs)
        finally:
            conn.close()
    return wrapper


def cache_query(func):
    """Decorator that caches query results."""
    @functools.wraps(func)
    def wrapper(conn, query):
        if query in query_cache:
            return query_cache[query]
        result = func(conn, query)
        query_cache[query] = result
        return result
    return wrapper


@with_db_connection
@cache_query
def fetch_users_with_cache(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()


if __name__ == "__main__":
    # First call will cache the result
    users = fetch_users_with_cache(query="SELECT * FROM users")
    
    # Second call will use the cached result
    users_again = fetch_users_with_cache(query="SELECT * FROM users")

