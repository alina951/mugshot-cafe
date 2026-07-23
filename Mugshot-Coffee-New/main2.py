```python
# ==========================================================
# IMPORTS
# ==========================================================

import csv              # Used to read CSV files.
import pprint           # Used to print Python objects in a readable format (not used in this script).
import connect          # Custom module that creates the database connection.
import pandas as pd     # Used to create and manipulate DataFrames.


# ==========================================================
# EXTRACT STAGE - READ CSV FILE
# ==========================================================

# Path to the Mugshot Coffee sales CSV file.
filename = 'Data/leeds_09-05-2023_09-00-00.csv'

# Define the column names because the CSV file does not contain headers.
keys = (
    'Date and time',
    'Location',
    'Name',
    'Order',
    'Total',
    'Payment Type',
    'Card Number'
)

# Open the CSV file in read mode.
with open(filename, 'r') as data:

    # Read each row as a dictionary.
    reader = csv.DictReader(data, keys)

    # Create an empty list to store transaction records.
    mugshot = list()

    # Add every row from the CSV into the list.
    for row in reader:
        mugshot.append(row)


# ==========================================================
# ALTERNATIVE METHOD USING PANDAS (COMMENTED OUT)
# ==========================================================

# filename = 'Data/leeds_09-05-2023_09-00-00.csv'
# keys = ('Date and time', 'Location','Name', 'Order', 'Total', 'Payment Type', 'Card Number')
# mugshot = pd.read_csv(filename,names = keys)
# print(mugshot)

# ==========================================================
# PANDAS TRANSFORMATION EXAMPLES (COMMENTED OUT)
# ==========================================================

# Remove sensitive information.
# mugshot = mugshot.drop(columns=['Name', 'Card Number'])

# print(mugshot)

# Split Date and Time into separate columns.
# mugshot['Date'] = pd.to_datetime(mugshot['Date and time']).dt.date
# mugshot['Time'] = pd.to_datetime(mugshot['Date and time']).dt.time

# Remove the original Date and Time column.
# mugshot = mugshot.drop(columns=['Date and time'])

# print(mugshot)


# ==========================================================
# REMOVE SENSITIVE DATA
# ==========================================================

def remove_sens_data(input_data_list: list, sens_data_keys: list):
    """
    Removes sensitive information such as customer
    names and card numbers before storing the data.
    """

    for dicts in input_data_list:
        for key in sens_data_keys:

            # Delete the field if it exists.
            if key in dicts:
                del dicts[key]


# ==========================================================
# SPLIT DATE AND TIME
# ==========================================================

def split_date_time(input_data_list: list):
    """
    Splits the combined Date and time field into
    separate Date and Time columns.
    """

    for dicts in input_data_list:

        # Store the original datetime value.
        dt_temp = dicts["Date and time"]

        # Extract the date.
        date = dt_temp[0:10]

        # Extract the time.
        time = dt_temp[11:16]

        # Create new fields.
        dicts["Date"] = date
        dicts["Time"] = time

        # Remove the original combined field.
        del dicts["Date and time"]


# ==========================================================
# SPLIT ORDER INTO PRODUCTS
# ==========================================================

def split_order(input_data_list: list):
    """
    Splits an order into individual products and
    calculates their quantities.
    """

    for dicts in input_data_list:

        # Flag used to detect duplicate products.
        product_dupe_tag = 0

        # Stores all products in one transaction.
        order_dicts_list = []

        # Split each product in the order.
        split_order_list = dicts["Order"].split(", ")

        for orders in split_order_list:

            product_dupe_tag = 0

            # Split product name from price.
            templist = orders.split(" - ")

            # Handle products whose names contain hyphens.
            if len(templist) > 2:

                # Last item is always the price.
                price = templist[len(templist) - 1]

                name = ""

                for items in templist:

                    if items != price:
                        name += items

                    name += " "
                    name.rstrip()

            else:

                # Standard product format.
                name = templist[0]
                price = templist[1]

            # Check if product already exists.
            for products in order_dicts_list:

                if products["Name"] == name:

                    # Increase quantity if duplicate.
                    products["Quantity"] += 1
                    product_dupe_tag = 1

            # Add new product if not already stored.
            if product_dupe_tag != 1:

                quantity = 1

                order_dicts_list.append({
                    "Name": name,
                    "Price": price,
                    "Quantity": quantity
                })

                product_dupe_tag = 0

        # Store transformed order.
        dicts["Order_dict"] = order_dicts_list

        # Remove original order string.
        del dicts["Order"]


# ==========================================================
# LOAD DATA INTO DATABASE
# ==========================================================

def insert_data_into_db(connection, transactions_data):
    """
    Inserts transaction, product and order item
    information into the relational database.
    """

    with connection.cursor() as cursor:

        # Loop through every transaction.
        for index, transaction in transactions_data.iterrows():

            # ==================================================
            # Insert transaction
            # ==================================================

            insert_transaction_sql = """
            INSERT INTO transactions
            (date, time, city, total_cost, payment_method)
            VALUES (%s, %s, %s, %s, %s)
            """

            cursor.execute(
                insert_transaction_sql,
                (
                    transaction.get('Date'),
                    transaction.get('Time'),
                    transaction.get('Location'),
                    transaction.get('Total'),
                    transaction.get('Payment Type')
                )
            )

            # ==================================================
            # Get transaction ID
            # ==================================================

            select_transaction_sql = """
            SELECT transaction_id
            FROM transactions
            WHERE date = %s and time = %s
            """

            cursor.execute(
                select_transaction_sql,
                (
                    transaction.get("Date"),
                    transaction.get('Time')
                )
            )

            transaction_id = cursor.fetchone()

            # ==================================================
            # Process every product in the transaction
            # ==================================================

            for product in transaction.get('Order_dict'):

                product_name = product.get('Name')
                product_price = product.get('Price')
                product_quantity = product.get('Quantity')

                # Check whether the product already exists.
                select_product_sql = """
                SELECT product_id
                FROM products
                WHERE product_name = %s
                """

                try:

                    cursor.execute(select_product_sql, (product_name,))
                    result = cursor.fetchone()

                except Exception as e:

                    print(f'Error {e}')
                    print('error here')
                    connection.rollback()

                # Product already exists.
                if result:

                    product_id = result[0]

                else:

                    # Insert new product.
                    insert_product_sql = """
                    INSERT INTO products
                    (product_name, product_price)
                    VALUES (%s, %s)
                    """

                    cursor.execute(
                        insert_product_sql,
                        (product_name, product_price)
                    )

                    # Retrieve new product ID.
                    select_product_id_sql = """
                    SELECT product_id
                    FROM products
                    WHERE product_name = %s
                    and product_price = %s
                    """

                    cursor.execute(
                        select_product_id_sql,
                        (product_name, product_price)
                    )

                    product_id = cursor.fetchone()

                # ==================================================
                # Insert Order Item
                # ==================================================

                insert_order_item_sql = """
                INSERT INTO order_items
                (transaction_id, product_id, product_quantity)
                VALUES (%s, %s, %s)
                """

                try:

                    cursor.execute(
                        insert_order_item_sql,
                        [transaction_id, product_id, product_quantity]
                    )

                except:

                    # Ignore duplicate primary keys.
                    print("key already exists")

            # Save all inserts to the database.
            connection.commit()

            print(f"Transaction {transaction_id} successfully inserted into database.")


# ==========================================================
# MAIN PROGRAM
# ==========================================================

# Create a connection to the database.
connection = connect.connect()

# Continue only if the connection succeeds.
if connection:

    # Remove personal information.
    remove_sens_data(mugshot, ['Name', 'Card Number'])

    # Split datetime into separate columns.
    split_date_time(mugshot)

    # Split orders into products.
    split_order(mugshot)

    # Convert the transformed data into a Pandas DataFrame.
    df = pd.DataFrame(mugshot)

    # Display the Date column.
    print(df[["Date"]])

    # Display the first transaction date.
    print(df.loc[0][["Date"]])

    # Load the transformed data into the database.
    insert_data_into_db(connection, df)

    # Close the database connection.
    connection.close()
```

This version keeps your code unchanged while adding comments that explain each section, function, loop, and SQL operation. It's suitable for learning, revision, or submitting as a documented project.
