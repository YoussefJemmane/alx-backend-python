# Python Generators - MySQL Database Seeder

This project demonstrates how to use Python to interact with a MySQL database, and specifically how Python generators can be used to stream data efficiently.

## Project Overview

The `seed.py` script sets up and populates a MySQL database with user data from a CSV file. It creates a database called `ALX_prodev` with a table `user_data` that has the following structure:

- `user_id` - Primary Key, UUID, Indexed
- `name` - VARCHAR, NOT NULL
- `email` - VARCHAR, NOT NULL
- `age` - DECIMAL, NOT NULL

## Dependencies

- Python 3.x
- mysql-connector-python
- pandas

You can install the required packages using pip:

```bash
pip install mysql-connector-python pandas
```

## Usage

1. Make sure MySQL server is running on your machine
2. Place the `user_data.csv` file in the same directory as the script
3. Run the script:

```bash
python3 seed.py
```

Or use the test script:

```bash
python3 0-main.py
```

## Function Overview

- `connect_db()`: Establishes a connection to the MySQL server
- `create_database(connection)`: Creates the `ALX_prodev` database if it doesn't exist
- `connect_to_prodev()`: Connects specifically to the `ALX_prodev` database
- `create_table(connection)`: Creates the `user_data` table with the required schema
- `insert_data(connection, data)`: Inserts data from a CSV file into the database

## Notes on Python Generators

Python generators are functions that can be used to create iterators. They use the `yield` statement to return values one at a time, which makes them memory efficient for handling large data sets.

In this project, while we're not explicitly defining a generator function with `yield`, we are using the iterator functionality of pandas DataFrames when processing the CSV data row by row, which demonstrates the concept of streaming data rather than loading it all into memory at once.

For larger datasets, you could implement a true generator function to stream rows from the database one by one.

