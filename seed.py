#!/usr/bin/python3
"""
This module contains functions to set up and seed a MySQL database with user data.
"""
import mysql.connector
import pandas as pd
import uuid
import os


def connect_db():
    """
    Connects to the MySQL database server.
    
    Returns:
        connection: MySQL connection object if successful, None otherwise
    """
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root"
        )
        print("Successfully connected to MySQL")
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None


def create_database(connection):
    """
    Creates the ALX_prodev database if it doesn't exist.
    
    Args:
        connection: MySQL connection object
    """
    try:
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS ALX_prodev")
        print("Database ALX_prodev created or already exists")
        cursor.close()
    except mysql.connector.Error as err:
        print(f"Error creating database: {err}")


def connect_to_prodev():
    """
    Connects to the ALX_prodev database in MySQL.
    
    Returns:
        connection: MySQL connection object to ALX_prodev if successful, None otherwise
    """
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="ALX_prodev"
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to ALX_prodev: {err}")
        return None


def create_table(connection):
    """
    Creates a table user_data if it doesn't exist with the required fields.
    
    Args:
        connection: MySQL connection object to ALX_prodev
    """
    try:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_data (
                user_id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                age DECIMAL NOT NULL,
                INDEX (user_id)
            )
        """)
        print("Table user_data created successfully")
        cursor.close()
    except mysql.connector.Error as err:
        print(f"Error creating table: {err}")


def insert_data(connection, csv_file):
    """
    Inserts data from a CSV file into the user_data table if it doesn't exist.
    
    Args:
        connection: MySQL connection object to ALX_prodev
        csv_file: Path to the CSV file containing user data
    """
    try:
        # Check if file exists
        if not os.path.exists(csv_file):
            print(f"Error: File {csv_file} does not exist")
            return
        
        # Read CSV file
        df = pd.read_csv(csv_file)
        
        cursor = connection.cursor()
        
        # Prepare query to check if record exists
        check_query = "SELECT 1 FROM user_data WHERE user_id = %s LIMIT 1"
        
        # Prepare insert query
        insert_query = """
            INSERT INTO user_data (user_id, name, email, age)
            VALUES (%s, %s, %s, %s)
        """
        
        # Insert data row by row (to implement generator concept)
        for i, row in df.iterrows():
            # If user_id is not provided or is invalid, generate a new one
            user_id = row.get('user_id', str(uuid.uuid4()))
            
            # Check if record already exists
            cursor.execute(check_query, (user_id,))
            exists = cursor.fetchone()
            
            if not exists:
                # Extract data from the row
                name = row.get('name', '')
                email = row.get('email', '')
                age = row.get('age', 0)
                
                # Insert data
                cursor.execute(insert_query, (user_id, name, email, age))
        
        # Commit changes
        connection.commit()
        print(f"Data from {csv_file} inserted successfully")
        
        cursor.close()
    except pd.errors.EmptyDataError:
        print(f"Error: The CSV file {csv_file} is empty")
    except pd.errors.ParserError:
        print(f"Error: Could not parse the CSV file {csv_file}")
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    # For testing purposes
    conn = connect_db()
    if conn:
        create_database(conn)
        conn.close()
        
        conn = connect_to_prodev()
        if conn:
            create_table(conn)
            insert_data(conn, 'user_data.csv')
            conn.close()