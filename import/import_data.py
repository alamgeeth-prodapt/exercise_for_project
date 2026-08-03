from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, engine
import csv
import os
from dotenv import load_dotenv
file_path="telecom_churn.csv"
load_dotenv()
url = os.getenv("DATABASE_URL")
if url is None:
    raise IOError

cursor = None
connection = None

try:
    engine = create_engine(url)
    connection = engine.raw_connection()
    cursor = connection.cursor()

    with open(file_path,"r") as f:
        reader = csv.reader(f)
        header = next(reader)
        # print(header)
        columns_with_types = [f"`{col}` TEXT" for col in header]
        table_query = f"CREATE TABLE IF NOT EXISTS telecom ({','.join(columns_with_types)})"
        # print(columns_with_types)
        # print(table_query)
        cursor.execute(table_query)

        placeholders = ','.join(['%s'] * len(header))
        # print(placeholders)
        columns = ','.join([f"`{col}`" for col in header])
        # print(columns)
        insert_query = f"INSERT INTO telecom ({columns}) VALUES ({placeholders})"

        for row in reader:
            cursor.execute(insert_query,row)
    connection.commit()

except FileNotFoundError as e:
    print(e)
finally:
    if cursor is not None:
        cursor.close()
    if connection is not None:
        connection.close()
