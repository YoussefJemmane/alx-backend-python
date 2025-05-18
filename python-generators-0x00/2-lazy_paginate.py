#!/usr/bin/python3
"""
Lazy pagination of user data using a generator.
"""
seed = __import__('seed')


def paginate_users(page_size, offset):
    """
    Fetch a page of users from the database using the given offset and page size.
    """
    connection = seed.connect_to_prodev()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM user_data LIMIT {page_size} OFFSET {offset}")
    rows = cursor.fetchall()
    connection.close()
    return rows


def lazy_pagination(page_size):
    """
    Generator that lazily paginates through user data, one page at a time.
    
    Args:
        page_size (int): Number of users per page.
        
    Yields:
        list: A list of user records for each page.
    """
    offset = 0
    while True:
        page = paginate_users(page_size, offset)
        if not page:
            break
        yield page
        offset += page_size
