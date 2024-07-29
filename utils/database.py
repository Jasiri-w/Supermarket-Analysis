from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime
import time
import streamlit as st

# Load environment variables
DB_HOST = st.secrets['DB_HOST']
DB_PORT = st.secrets['DB_PORT']
DB_NAME = st.secrets['DB_NAME']
DB_USER = st.secrets['DB_USER']
DB_PASSWORD = st.secrets['DB_PASSWORD']
SSL_CERT_PATH = st.secrets['SSL_CERT_PATH']

# Create connection string
DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require'
print(f"\n\n{datetime.now()}:  DATABASE_URL = {DATABASE_URL}\n\n")

def connect_to_db():
    print(f"{datetime.now()}: Connecting to the Database and creating Engine")
    return create_engine(DATABASE_URL, 
                         connect_args={
                             'connect_timeout': 10,  # Increase timeout
                             'sslrootcert': SSL_CERT_PATH
                         })

def fetch_data(query, retries=5, delay=5):
    print(f"{datetime.now()}: Running Query:{query}")
    connection = connect_to_db()
    for attempt in range(retries):
        try:
            df = pd.read_sql(query, connection)
            return df
        except Exception as e:  # Catch all exceptions
            print(f"Attempt {attempt + 1} failed with error: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise  # Re-raise the last exception if retries are exhausted

def fetch_sales_data():
    query = """
    WITH customer_purchase_counts AS (
        SELECT
            pay.phone,
            c.cname AS customer_name,
            COUNT(td.productno) AS total_purchases,
            MIN(t.datein) AS first_purchase_date,
            MAX(t.datein) AS last_purchase_date,
            SUM(t.totalamount) AS total_spent
        FROM
            public.transactiondetails td
        JOIN
            public.transactions t ON td.transactionid = t.id
        JOIN
            public.payment pay ON t.invoiceno = pay.invoiceno::text
        JOIN
            public.customers c ON pay.custid = c.custid
        WHERE
            pay.phone IS NOT NULL AND pay.phone <> ''
        GROUP BY
            pay.phone, c.cname
    ),
    most_purchased_items AS (
        SELECT
            pay.phone,
            td.productno,
            p.description AS product_description,
            COUNT(td.productno) AS purchase_count
        FROM
            public.transactiondetails td
        JOIN
            public.transactions t ON td.transactionid = t.id
        JOIN
            public.payment pay ON t.invoiceno = pay.invoiceno::text
        JOIN
            public.product p ON td.productno = p.productno
        WHERE
            pay.phone IS NOT NULL AND pay.phone <> ''
        GROUP BY
            pay.phone, td.productno, p.description
    ),
    ranked_items AS (
        SELECT
            phone,
            productno,
            product_description,
            purchase_count,
            ROW_NUMBER() OVER (PARTITION BY phone ORDER BY purchase_count DESC) AS rn
        FROM
            most_purchased_items
    ),
    most_purchased_items_with_count AS (
        SELECT
            ri.phone,
            ri.product_description AS most_purchased_item,
            ri.purchase_count AS most_purchased_item_count
        FROM
            ranked_items ri
        WHERE
            ri.rn = 1
    )
    SELECT
        cpc.phone,
        cpc.customer_name,
        cpc.total_purchases,
        cpc.first_purchase_date,
        cpc.last_purchase_date,
        cpc.total_spent,
        mpi.most_purchased_item,
        mpi.most_purchased_item_count,
        DATE_PART('day', cpc.last_purchase_date - cpc.first_purchase_date) AS purchase_duration_days
    FROM
        customer_purchase_counts cpc
    LEFT JOIN
        most_purchased_items_with_count mpi ON cpc.phone = mpi.phone
    ORDER BY
        cpc.total_spent DESC;
    """
    df = fetch_data(query)
    print("\nData Queried:\n")
    print(df)
    return df
