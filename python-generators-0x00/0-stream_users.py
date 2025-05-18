#!/usr/bin/python3
"""
Module containing a generator function to stream user data from MySQL database
"""
import mysql.connector


def stream_users():
    """
    Generator function that yields rows from the user_data table one by one.
    Each row is returned as a dictionary with keys corresponding to column names.
    
    Returns:
        Generator yielding dictionaries containing user data
    """
    # Set up database connection
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="ALX_prodev"
        )
        
        # Create cursor and execute query
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_data")
        
        # Yield rows one by one
        for row in cursor:
            yield row
            
        # Clean up
        cursor.close()
        connection.close()
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        yield {}  # Yield empty dictionary in case of error


if __name__ == "__main__":
    # Example usage
    for i, user in enumerate(stream_users()):
        print(user)
        if i >= 5:  # Print only first 6 users as example
            break