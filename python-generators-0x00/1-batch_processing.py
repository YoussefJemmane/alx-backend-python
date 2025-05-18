#!/usr/bin/python3
"""
Module containing generator functions to stream and process user data in batches
"""
import mysql.connector


def stream_users_in_batches(batch_size):
    """
    Generator function that yields batches of rows from the user_data table.
    Each batch is a list of dictionaries with keys corresponding to column names.
    
    Args:
        batch_size (int): Number of rows to fetch in each batch
        
    Returns:
        Generator yielding lists of dictionaries containing user data
    """
    # Set up database connection
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="ALX_prodev"
        )
        
        cursor = connection.cursor(dictionary=True)
        
        # Set up batch processing with LIMIT and OFFSET
        offset = 0
        while True:
            # Create query with LIMIT and OFFSET for batch processing
            query = f"SELECT * FROM user_data LIMIT {batch_size} OFFSET {offset}"
            cursor.execute(query)
            
            # Fetch the current batch of rows
            batch = cursor.fetchall()
            
            # If no rows were fetched, we've reached the end
            if not batch:
                break
                
            # Yield the batch of rows
            yield batch
            
            # Move to the next batch
            offset += batch_size
        
        # Clean up
        cursor.close()
        connection.close()
        
        return  # Explicit return in generator function (optional but included as required)

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        yield []  # Yield empty list in case of error
        return  # Explicit return after yielding empty batch


def batch_processing(batch_size):
    """
    Generator function that processes batches of user data, filtering for users over 25.
    It prints each filtered user record.
    
    Args:
        batch_size (int): Number of rows to fetch in each batch
    """
    # Get batches from the stream_users_in_batches generator
    for batch in stream_users_in_batches(batch_size):
        # Process each row in the batch
        for user in batch:
            # Filter for users over age 25
            if user.get('age', 0) > 25:
                # Print the user record
                print(user)
                print()  # Empty line for readability

    return  # Explicit return at the end of the function


if __name__ == "__main__":
    # Example usage
    batch_processing(10)  # Process users in batches of 10
