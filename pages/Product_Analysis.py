import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils.database import fetch_data

# Function to fetch credit account most purchased items
@st.cache_data
def get_credit_account_most_purchased():
    query = """
    WITH customer_purchases AS (
        SELECT
            c.custid,
            c.cname,
            c.phone,
            td.productno,
            p.description,
            COUNT(td.productno) AS purchase_count
        FROM
            public.customers c
        JOIN
            public.transactiondetails td ON c.custid = td.customerid
        JOIN
            public.product p ON td.productno = p.productno
        GROUP BY
            c.custid, c.cname, td.productno, p.description, c.phone
    ),
    ranked_purchases AS (
        SELECT
            cp.*,
            ROW_NUMBER() OVER (PARTITION BY cp.custid ORDER BY cp.purchase_count DESC) AS rank
        FROM
            customer_purchases cp
    )
    SELECT
        custid,
        cname,
        phone,
        description,
        purchase_count,
        productno
    FROM
        ranked_purchases
    WHERE
        rank = 1
    ORDER BY
        custid;
    """
    return fetch_data(query)

# Function to fetch daily customer most purchased items
@st.cache_data
def get_daily_customer_most_purchased():
    query = """
    WITH customer_purchases AS (
        SELECT
            pay.phone,
            td.productno,
            p.description,
            COUNT(td.productno) AS purchase_count,
            c.cname AS customer_name,
            c.address,
            c.email,
            c.creditlimit,
            c.balance,
            c.loyaltypoints,
            c.loyalty_number,
            c.autodiscount
        FROM
            public.transactiondetails td
        JOIN
            public.transactions t ON td.transactionid = t.id
        JOIN
            public.payment pay ON t.invoiceno = pay.invoiceno::text
        JOIN
            public.customers c ON pay.custid = c.custid
        JOIN
            public.product p ON td.productno = p.productno
        WHERE
            pay.phone IS NOT NULL AND pay.phone <> ''
        GROUP BY
            pay.phone, td.productno, p.description, c.cname, c.address, c.email, c.creditlimit, c.balance, c.loyaltypoints, c.loyalty_number, c.autodiscount
    ),
    most_purchased AS (
        SELECT
            phone,
            productno,
            description,
            purchase_count,
            customer_name,
            address,
            email,
            creditlimit,
            balance,
            loyaltypoints,
            loyalty_number,
            autodiscount,
            ROW_NUMBER() OVER (PARTITION BY phone ORDER BY purchase_count DESC) AS rn
        FROM
            customer_purchases
    )
    SELECT
        phone,
        productno,
        description AS most_purchased_item,
        purchase_count,
        customer_name,
        address,
        email,
        creditlimit,
        balance,
        loyaltypoints,
        loyalty_number,
        autodiscount
    FROM
        most_purchased
    WHERE
        rn = 1
    ORDER BY
        purchase_count DESC;
    """
    return fetch_data(query)

# Function to fetch highest daily customers
@st.cache_data
def get_highest_daily_customers():
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
    )
    SELECT
        cpc.phone,
        cpc.customer_name,
        cpc.total_purchases,
        cpc.first_purchase_date,
        cpc.last_purchase_date,
        cpc.total_spent,
        ri.product_description AS most_purchased_item
    FROM
        customer_purchase_counts cpc
    LEFT JOIN
        ranked_items ri ON cpc.phone = ri.phone AND ri.rn = 1
    ORDER BY
        cpc.total_purchases DESC;
    """
    return fetch_data(query)

# Function to fetch items purchased less than 20 times
@st.cache_data
def get_items_purchased_less_than_20():
    query = """
    WITH product_purchases AS (
        SELECT
            td.productno,
            p.description,
            COUNT(td.productno) AS purchase_count
        FROM
            public.transactiondetails td
        JOIN
            public.product p ON td.productno = p.productno
        GROUP BY
            td.productno, p.description
    )
    SELECT
        productno,
        description,
        purchase_count
    FROM
        product_purchases
    WHERE
        purchase_count < 20
    ORDER BY
        purchase_count;
    """
    return fetch_data(query)

# Function to fetch least purchased items
@st.cache_data
def get_least_purchased_items():
    query = """
    WITH product_purchases AS (
        SELECT
            td.productno,
            p.description,
            COUNT(td.productno) AS purchase_count
        FROM
            public.transactiondetails td
        JOIN
            public.product p ON td.productno = p.productno
        GROUP BY
            td.productno, p.description
    )
    SELECT
        productno,
        description,
        purchase_count
    FROM
        product_purchases
    ORDER BY
        purchase_count ASC
    LIMIT 100;
    """
    return fetch_data(query)

# Function to fetch longest buying customers
@st.cache_data
def get_longest_buying_customers():
    query = """
    WITH customer_purchase_details AS (
        SELECT
            pay.phone,
            c.cname AS customer_name,
            MIN(t.datein) AS first_purchase_date,
            MAX(t.datein) AS last_purchase_date,
            SUM(t.totalamount) AS total_spent,
            COUNT(td.productno) AS total_purchases
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
        cpd.phone,
        cpd.customer_name,
        cpd.first_purchase_date,
        cpd.last_purchase_date,
        cpd.total_spent,
        mpi.most_purchased_item,
        mpi.most_purchased_item_count,
        cpd.total_purchases
    FROM
        customer_purchase_details cpd
    LEFT JOIN
        most_purchased_items_with_count mpi ON cpd.phone = mpi.phone
    ORDER BY
        cpd.first_purchase_date;
    """
    return fetch_data(query)

# Streamlit Page
st.set_page_config(
    page_title="Product Performance Analysis",
    page_icon=st.secrets["FAVICON"],
    layout="wide",
)
st.title("Product Performance Analysis")
st.logo(
    st.secrets["LOGO"],
    icon_image=st.secrets["ICON"],
)
st.sidebar.markdown("# Product Analysis Dashboard")

# Example for expanders with headers and data


# Most Purchased Items
with st.expander("Credit Account Most Purchased Items"):
    credit_account_data = get_credit_account_most_purchased()
    st.dataframe(credit_account_data)

# Daily Customer Most Purchased Items
with st.expander("Daily Customer Most Purchased Items"):
    daily_customer_data = get_daily_customer_most_purchased()
    st.dataframe(daily_customer_data)

# Items Purchased Less than 20 Times
with st.expander("Items Purchased Less than 20 Times"):
    items_less_than_20_data = get_items_purchased_less_than_20()
    st.dataframe(items_less_than_20_data)

# Least Purchased Items
with st.expander("Least Purchased Items"):
    least_purchased_items_data = get_least_purchased_items()
    st.dataframe(least_purchased_items_data)

# Longest Buying Customers
with st.expander("Longest Buying Customers"):
    longest_buying_customers_data = get_longest_buying_customers()
    st.dataframe(longest_buying_customers_data)

