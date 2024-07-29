import streamlit as st
import pandas as pd
from utils.database import fetch_data

# Function to fetch all customer data including total amount spent and top purchases
@st.cache_data
def get_all_customer_data():
    query = """
    WITH customer_payment_totals AS (
        SELECT
            pay.phone,
            c.cname AS customer_name,
            COUNT(DISTINCT pay.paymentid) AS total_payments,
            SUM(pay.amount) AS total_paid,
            MIN(pay.datein) AS first_payment_date,
            MAX(pay.datein) AS last_payment_date
        FROM
            public.payment pay
        JOIN
            public.customers c ON pay.custid = c.custid
        WHERE
            pay.phone IS NOT NULL AND pay.phone <> ''
        GROUP BY
            pay.phone, c.cname
    ),
    customer_purchase_counts AS (
        SELECT
            pay.phone,
            COUNT(td.productno) AS total_purchases,
            MIN(t.datein) AS first_purchase_date,
            MAX(t.datein) AS last_purchase_date
        FROM
            public.transactiondetails td
        JOIN
            public.transactions t ON td.transactionid = t.id
        JOIN
            public.payment pay ON t.invoiceno = pay.invoiceno::text
        WHERE
            pay.phone IS NOT NULL AND pay.phone <> ''
        GROUP BY
            pay.phone
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
        cpt.phone,
        cpt.customer_name,
        cpc.total_purchases,
        cpt.total_payments,
        cpt.total_paid,
        cpc.first_purchase_date,
        cpc.last_purchase_date,
        mpi.most_purchased_item,
        mpi.most_purchased_item_count,
        DATE_PART('day', cpc.last_purchase_date - cpc.first_purchase_date) AS purchase_duration_days
    FROM
        customer_payment_totals cpt
    LEFT JOIN
        customer_purchase_counts cpc ON cpt.phone = cpc.phone
    LEFT JOIN
        most_purchased_items_with_count mpi ON cpt.phone = mpi.phone
    ORDER BY
        cpt.total_paid DESC;
    """
    return fetch_data(query)


# Function to fetch specific customer data by phone number
@st.cache_data
def get_customer_by_phone(phone):
    query = f"""
    WITH
    customer_payments AS (
        SELECT
        phone,
        COUNT(DISTINCT paymentid) AS total_payments,
        SUM(amount) AS total_spent,
        MIN(datein) AS first_payment_date,
        MAX(datein) AS last_payment_date
        FROM
        public.payment
        WHERE
        phone = '{phone}'
        GROUP BY
        phone
    )
    SELECT
        phone,
        total_payments,
        total_spent,
        first_payment_date,
        last_payment_date,
        DATE_PART('day', last_payment_date - first_payment_date) AS payment_duration
    FROM
        customer_payments;
    """
    return fetch_data(query)

# Function to fetch top 10 most purchased items
@st.cache_data
def get_top_10_items():
    query = """
    SELECT
        p.description AS product_description,
        COUNT(td.productno) AS purchase_count
    FROM
        public.transactiondetails td
    JOIN
        public.product p ON td.productno = p.productno
    GROUP BY
        p.description
    ORDER BY
        purchase_count DESC
    LIMIT 10;
    """
    return fetch_data(query)

# Function to fetch top 10 most purchased items for a specific customer by phone number
@st.cache_data
def get_top_10_items_by_phone(phone):
    query = f"""
    SELECT
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
        pay.phone = '{phone}'
    GROUP BY
        p.description
    ORDER BY
        purchase_count DESC
    LIMIT 10;
    """
    return fetch_data(query)

# Function to fetch purchase history for a specific customer by phone number
@st.cache_data
def get_purchase_history_by_phone(phone):
    query = f"""
    SELECT
        td.productno,
        p.description AS product_description,
        td.saleprice AS sold_price,
        p.saleprice AS current_item_price,
        td.quantity AS purchase_quantity,
        (td.saleprice * td.quantity) AS total,
        t.datein AS purchase_date
    FROM
        public.transactiondetails td
        JOIN public.transactions t ON td.transactionid = t.id
        JOIN public.payment pay ON t.invoiceno = pay.invoiceno::TEXT
        JOIN public.product p ON td.productno = p.productno
        JOIN public.customers c ON pay.custid = c.custid
    WHERE
        pay.phone = '{phone}';
    """
    return fetch_data(query)

# Function to fetch payment history for a specific customer by phone number
@st.cache_data
def get_payment_history_by_phone(phone):
    query = f"""
    SELECT
        invoiceno,
        SUM(amount) AS total_paid,
        MIN(datein) AS payment_date
    FROM
        public.payment
    WHERE
        phone = '{phone}'
    GROUP BY
        invoiceno
    ORDER BY
        invoiceno;
    """
    return fetch_data(query)

# Main function to render the Streamlit page
def main():
    st.set_page_config(
        page_title="CRM",
        page_icon=st.secrets["FAVICON"],
        layout="wide",
    )
    st.title("Customer Relationship Dashboard")
    st.sidebar.markdown('# Home') 
    st.logo(
        st.secrets["LOGO"],
        icon_image=st.secrets["ICON"],
    )  

    tab1, tab2 = st.tabs(["📈 All Customers Overview", "🔍 Search for Customer Information"])

    # Display all customer data
    all_customer_data = get_all_customer_data()

    if not all_customer_data.empty:
        with tab1:
            st.subheader("All Customers Overview")
            st.dataframe(all_customer_data)

            # Top 10 Most Purchased Items by Total Purchases
            top_items = get_top_10_items()
            st.subheader("Top 10 Most Purchased Items")
            st.bar_chart(top_items.set_index('product_description')['purchase_count'])
    else:
        with tab1:
            st.write("No data available.")

    # Search for specific customer information
    with tab2:
        st.subheader("Search for Customer Information")
        phone_number = st.text_input("Enter Customer Phone Number:", "")

        if phone_number:
            # Fetch and display specific customer data
            customer_data = get_customer_by_phone(phone_number)
            
            if not customer_data.empty:
                st.subheader(f"Customer Data for Phone Number: {phone_number}")

                # Extract metrics
                total_spent = customer_data['total_spent'].iloc[0]
                total_payments = customer_data['total_payments'].iloc[0]
                payment_duration_days = customer_data['payment_duration'].iloc[0]

                # Display metrics in columns
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Spent", f"KES {total_spent:,.2f}")
                col2.metric("Total Payments", f"{total_payments}")
                col3.metric("Days With Us", f"{payment_duration_days}")

                # Display customer payment history
                payment_history = get_payment_history_by_phone(phone_number)
                st.subheader("Payment History")
                st.dataframe(payment_history)

                # Display customer purchase history
                purchase_history = get_purchase_history_by_phone(phone_number)
                st.subheader("Purchase History")
                st.dataframe(purchase_history)

                # Display top 10 most purchased items for this customer
                top_customer_items = get_top_10_items_by_phone(phone_number)
                st.subheader("Top 10 Most Purchased Items")
                st.bar_chart(top_customer_items.set_index('product_description')['purchase_count'])

            else:
                st.write("No customer data found for the provided phone number.")

if __name__ == "__main__":
    main()
