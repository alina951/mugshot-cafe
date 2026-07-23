# ======================================================
# MUGSHOT COFFEE ETL PIPELINE
# ======================================================
# This script performs an ETL (Extract, Transform, Load)
# process:
# 1. Extracts raw sales data from a CSV file.
# 2. Transforms the data by cleaning and restructuring it.
# 3. Loads the cleaned data into a PostgreSQL database.
# ======================================================

# ======================================================
# IMPORT REQUIRED LIBRARIES
# ======================================================
# These libraries are used to read CSV files, manipulate
# data, connect to PostgreSQL and perform bulk inserts.
# ======================================================

import csv
import pprint
import pandas
import psycopg2.extras
import connect
import psycopg2
from sqlalchemy import create_engine


#Discarded attempt at sorting the key.
#        print(row['Name'], row['Colour'], row['Age'])

# ======================================================
# EXTRACT STAGE
# ======================================================
# Read the raw Mugshot Coffee sales CSV file and store
# each row as a dictionary inside a Python list.
# ======================================================

#Loading data from data source and printing
filename = 'Data/leeds_09-05-2023_09-00-00.csv'
keys = ('Date and time', 'Location','Name', 'Order', 'Total', 'Payment Type', 'Card Number')
with open (filename, 'r') as data:
    reader = csv.DictReader(data,keys)
    mugshot = list()
    for row in reader:
        mugshot.append(row)
#pprint.pprint(mugshot)

# ======================================================
# TRANSFORM STAGE
# ======================================================
# Clean and prepare the raw data before loading it into
# PostgreSQL.
# ======================================================

###Transform stage - defining functions###
# ------------------------------------------------------
# Remove Sensitive Customer Information
# Removes customer names and card numbers before loading.
# ------------------------------------------------------
def remove_sens_data(input_data_list : list,sens_data_keys:list):
    for dicts in input_data_list:
        for key in sens_data_keys:
            if key in dicts:
                del dicts[key]

# ------------------------------------------------------
# Split Date and Time
# Separates the combined datetime column into Date and Time.
# ------------------------------------------------------
def split_date_time(input_data_list : list):
    for dicts in input_data_list:
        dt_temp = dicts["Date and time"]
        date = dt_temp[0:10]
        time = dt_temp[11:16]
        dicts["Date"] = date
        dicts["Time"] = time
        del dicts["Date and time"]

# ------------------------------------------------------
# Split Customer Orders
# Splits each order into individual products and counts
# duplicate items to create quantities.
# ------------------------------------------------------
def split_order(input_data_list : list):
    for dicts in input_data_list:
        product_dupe_tag = 0
        order_dicts_list=[]
        split_order_list = dicts["Order"].split(", ")
        for orders in split_order_list:
            product_dupe_tag = 0
            #order_list.append(orders.split(" - "))
            templist = orders.split(" - ")
            if len(templist)>2:
                price = templist[len(templist)-1]
                name = ""
                for items in templist:  
                    if items != price:
                        name += items
                    name +=" "
                    name.rstrip()
            else:
                name = templist[0]
                price = templist[1]
            for products in order_dicts_list:
                if products["Name"] == name:
                    products["Quantity"] = products["Quantity"] + 1
                    product_dupe_tag=1
            if product_dupe_tag !=1:
                quantity = 1
                order_dicts_list.append({"Name":name,"Price":price,"Quantity":quantity})
                product_dupe_tag = 0

        dicts["Order_dict"] = order_dicts_list
        del dicts["Order"]

# ======================================================
# LOAD STAGE
# ======================================================
# Insert the transformed data into PostgreSQL.
# ======================================================

### load stage - functions ###

# Function to create the sales table (if necessary)
# ------------------------------------------------------
# Create Database Tables
# Reads database.sql and creates the required tables.
# ------------------------------------------------------
def create_sales_table(connection):
    sql_file_path = 'database.sql'
    try:
        with open(sql_file_path, 'r') as file:
            sql_commands = file.read()

        with connection.cursor() as cursor:
            for command in sql_commands.split(';'):
                if command.strip():
                    cursor.execute(command)
        
        # Save all changes to the database
    connection.commit()
        print("Tables successfully created from the SQL file.")

    except FileNotFoundError:
        print(f"Error: The file '{sql_file_path}' was not found.")
    #except pymysql.Error as e:
    #    print(f"Error creating tables: {e}")

# inserting data into tables
# ------------------------------------------------------
# Load Data into PostgreSQL
# Inserts transactions, products and order items.
# ------------------------------------------------------
def insert_data_into_db(connection, transactions_data):
    #try:
        with connection.cursor() as cursor:
            print("insert started")
            transaction_values = []
            product_values = []
            unique_prods=[]
            insert_prods=[]
            order_items_list = []
            insert_order_item_sql = """
                    INSERT INTO order_items (transaction_id, product_id, product_quantity)
                    VALUES (%s, %s, %s)
                    """
            select_product_sql = "SELECT * FROM products"
            insert_transaction_sql = """
                INSERT INTO transactions (date, time, city, total_cost, payment_method)
                VALUES (%s, %s, %s, %s, %s)
                """
            insert_products_sql ="""
                INSERT INTO products (product_name,product_price)
                VALUES (%s, %s)
                """
            
            select_transaction_sql = "select transaction_id,time FROM transactions where date = %s and city = %s"
            for transaction in transactions_data:
                # insert into transactions table
                transaction_values.append((transaction['Date'],
                    transaction['Time'],
                    transaction['Location'],
                    transaction['Total'],
                    transaction['Payment Type']))
            print("starting execute")
            df = pandas.DataFrame(transaction_values)
            df.columns =['date','time','city','total_cost','payment_method']
            print(df)
            df.to_sql("transactions",con=connection,index=False)
            cursor.commit()
        







            psycopg2.extras.execute_batch(cursor,insert_transaction_sql,transaction_values,page_size=100)
            #cursor.executemany(insert_transaction_sql,transaction_values)
            print("transactions complete")
            with open ("transactions_data.csv","w",newline='') as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow(["date","time","city","total_cost","payment_method"]) # write headers
                csv_writer.writerows(transaction_values)
            cursor.execute(select_transaction_sql, (transactions_data[0]["Date"],transactions_data[0]['Location'],))
            transaction_id_list = cursor.fetchall()
            for transaction in transactions_data:
                for items in transaction['Order_dict']:
                    product_values.append((items['Name'],items['Price'],items['Quantity']))
                    unique_prods.append((items['Name'],items['Price']))
            unique_prods = [t for t in (set(tuple(i) for i in unique_prods))]
            #cursor.executemany(insert_products_sql,unique_prods)
            cursor.execute(select_product_sql)
            product_id_list = cursor.fetchall()
            if len(product_id_list) >0:
                for x in unique_prods:
                    found_flag=0
                    for y in product_id_list:
                        if x[0] == y[1]:
                            found_flag = 1
                    if found_flag == 0:
                        insert_prods.append(x)
            else:
                insert_prods = unique_prods
            if len(insert_prods) > 0:
                psycopg2.extras.execute_batch(cursor,insert_products_sql,insert_prods,page_size=100)
            cursor.execute(select_product_sql)
            print("products complete")
            product_id_list = cursor.fetchall()
            for transaction in transactions_data:
                for orders in transaction['Order_dict']:
                    for items in transaction_id_list:
                        if transaction['Time'] == items[1]:
                            transaction_id = items[0]
                    for items in product_id_list:
                        if orders["Name"] == items[1]:
                            product_id = items[0]
                    product_quantity = orders["Quantity"]
                    order_items_list.append((transaction_id,product_id,product_quantity))
        
            psycopg2.extras.execute_batch(cursor,insert_order_item_sql,order_items_list,page_size=100)
            print("order items complete")
            







                    




                #cursor.execute(insert_transaction_sql, (
                #    transaction['Date'],
                #    transaction['Time'],
                #    transaction['Location'],
                #    transaction['Total'],
                #    transaction['Payment Type']
                #))
                ## Save all changes to the database
    connection.commit()
                # Retrieve the transaction_id of the newly inserted transaction
                #select_transaction_sql = "SELECT transaction_id FROM transactions WHERE date = %s and time = %s"
                #cursor.execute(select_transaction_sql, (transaction["Date"],transaction['Time'],))
                #
                #transaction_id = cursor.fetchone()
#
                #for product in transaction['Order_dict']:
                #    product_name = product['Name']
                #    product_price = product['Price']
                #    product_quantity = product['Quantity']
#
                #    # check if the product already exists in products table
                #    select_product_sql = "SELECT product_id FROM products WHERE product_name = %s"
                #    try: 
                #        cursor.execute(select_product_sql, (product_name,))
                #        result = cursor.fetchone()
                #    except Exception as e:
                #        print(f'Error {e}')
                #        print('error here')
                #        connection.rollback()
#
                #    if result:
                #        product_id = result[0]
                #        
#
                #    else:
                #        # Insert product into products table
                #        insert_product_sql = "INSERT INTO products (product_name, product_price) VALUES (%s, %s)"
                #        cursor.execute(insert_product_sql, (product_name, product_price))
                #        select_product_id_sql = "SELECT product_id FROM products WHERE product_name = %s and product_price = %s"
                #        cursor.execute(select_product_id_sql, (product_name,product_price))
                #        product_id = cursor.fetchone()
                #        
#
                #    # Insert into order_items table
                #    insert_order_item_sql = """
                #    INSERT INTO order_items (transaction_id, product_id, product_quantity)
                #    VALUES (%s, %s, %s)
                #    """
                #    try:
                #        cursor.execute(insert_order_item_sql, [transaction_id, product_id, product_quantity])
                #    except:
                #        print("key already exists")
                #
                ## Save all changes to the database
    connection.commit()
                #print(f"Transaction successfully inserted into database.")
    #except:
    #print("error")
    #except pymysql.Error as e:
    #    connection.rollback()
    #    print(f"Error inserting data into database: {e}")


# Function to establish a database connection
#def get_database_connection():
#    try:
#        connection = pymysql.connect(
#            host='localhost',
#            user='postgres',
#            password='example',
#            db='mugshot_coffee',
#            charset='utf8mb4',  # Adjust charset if needed
#            cursorclass=pymysql.cursors.DictCursor  # Adjust cursor class if needed
#        )
#        return connection
#    except pymysql.Error as e:
#        print(f"Error connecting to the database: {e}")
#        return None


# Establish the database connection
# ======================================================
# EXECUTE THE ETL PIPELINE
# ======================================================
# Connect to PostgreSQL, execute the Transform and Load
# stages, commit the transaction and close the connection.
# ======================================================

connection = connect.connect()

if connection:

    # Remove sensitive customer information
    remove_sens_data(mugshot,['Name','Card Number'])
    # Split combined Date and Time column
    split_date_time(mugshot)
    # Split customer orders into individual products
    split_order(mugshot)
    #create_sales_table(connection)
    # Load transformed data into PostgreSQL
    insert_data_into_db(connection, mugshot)
    # Save all changes to the database
    connection.commit()
    # Close the database connection
    # Close the database connection
    connection.close()
#for items in mugshot:
#    print(items)
    
#for transaction in transactions_data:
#                # insert a single transaction  into transactions table # prepared sql statement with placeholders for values # it excute sql command 
#                insert_transaction_sql = """
#                INSERT INTO transactions (date, time, city, total_cost, payment_method) 
#                VALUES (%s, %s, %s, %s, %s)
#                """
#                cursor.execute(insert_transaction_sql, (
#                    transaction['Date'],
#                    transaction['Time'],
#                    transaction['Location'],
#                    transaction['Total'],
#                    transaction['Payment Type']
#                ))
#                ## Save all changes to the database
    connection.commit()
#                # Retrieve the transaction_id of the newly inserted transaction
#                select_transaction_sql = "SELECT transaction_id FROM transactions WHERE date = %s and time = %s"
#                cursor.execute(select_transaction_sql, (transaction["Date"],transaction['Time'],))
#                transaction_id = cursor.fetchone()
#
#                for product in transaction['Order_dict']:
#                    product_name = product['Name']
#                    product_price = product['Price']
#                    product_quantity = product['Quantity']
#
#                    # check if the product already exists in products table
#                    select_product_sql = "SELECT product_id FROM products WHERE product_name = %s"
#                    cursor.execute(select_product_sql, (product_name,))
#                    result = cursor.fetchone()
#
#                    if result:
#                        product_id = result[0]
#                        
#
#                    else:
#                        # Insert product into products table
#                        insert_product_sql = "INSERT INTO products (product_name, product_price) VALUES (%s, %s)"
#                        cursor.execute(insert_product_sql, (product_name, product_price))
#                        select_product_id_sql = "SELECT product_id FROM products WHERE product_name = %s and product_price = %s"
#                        cursor.execute(select_product_id_sql, (product_name,product_price))
#                        product_id = cursor.fetchone()
#                        
#
#                    # Insert into order_items table
#                    insert_order_item_sql = """
#                    INSERT INTO order_items (transaction_id, product_id, product_quantity)
#                    VALUES (%s, %s, %s)
#                    """
#                    try:
#                        cursor.execute(insert_order_item_sql, [transaction_id, product_id, product_quantity])
#                    except:
#                        print("key already exists")
#
#                print(f"Transaction {transaction_id} successfully inserted into database.")
