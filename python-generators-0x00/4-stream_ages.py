#!/usr/bin/python3
"""
Memory-efficient aggregation using generators to compute average age.
"""
seed = __import__('seed')


def stream_user_ages():
    """
    Generator that yields user ages one by one from the database.
    """
    connection = seed.connect_to_prodev()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT age FROM user_data")

    for row in cursor:
        yield row['age']

    cursor.close()
    connection.close()


def compute_average_age():
    """
    Compute the average age of users using the stream_user_ages generator.
    """
    total_age = 0
    count = 0

    for age in stream_user_ages():
        total_age += age
        count += 1

    if count == 0:
        print("Average age of users: 0")
    else:
        average_age = total_age / count
        print(f"Average age of users: {average_age}")


if __name__ == "__main__":
    compute_average_age()
