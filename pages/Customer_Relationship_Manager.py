import streamlit as st
import pandas as pd
from utils.database import fetch_data
from utils.models import get_recommendations
from utils.auth import get_authenticator
import joblib

@st.cache_data
def get_all_customer_data():
    """
    Fetch all customer data, including total payments, total paid amounts, and purchase information.
    
    Inputs:
        None required.

    Returns:
        pd.DataFrame: A DataFrame where each row represents a customer, containing:
            - phone: Customer's phone number.
            - customer_name: Name of the customer.
            - total_payments: Total number of payments made by the customer.
            - total_paid: Total amount paid by the customer.
            - first_payment_date: Date of the first payment.
            - last_payment_date: Date of the last payment.
            - total_purchases: Total number of purchases made by the customer.
            - first_purchase_date: Date of the first recorded purchase.
            - last_purchase_date: Date of the last recorded purchase.
            - most_purchased_item: Name of the most frequently purchased item.
            - most_purchased_item_count: How many times this most purchased item was bought.
            - purchase_duration_days: The number of days between the first and last purchase.
            - customer_email: Email of the customer.
            - customer_address: Address of the customer.
    """
    query = """
    WITH customer_payment_totals AS (
        SELECT
            pay.phone,
            c.cname AS customer_name,
            COUNT(DISTINCT pay.paymentid) AS total_payments,
            SUM(pay.amount) AS total_paid,
            MIN(pay.datein) AS first_payment_date,
            MAX(pay.datein) AS last_payment_date,
            MIN(c.email) AS customer_email,
            MIN(c.address) AS customer_address
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

@st.cache_data
def get_customer_by_phone(phone):
    """
    Fetch detailed payment and purchase info for a single customer by phone number.
    
    Inputs:
        phone (str): The customer's phone number.

    Returns:
        pd.DataFrame: Contains columns such as:
            - phone: The queried customer's phone.
            - total_payments: How many payments the customer has made.
            - total_spent: Total amount spent by the customer.
            - first_payment_date: Date of the first payment.
            - last_payment_date: Date of the last payment.
            - payment_duration: Duration between the first and last payment in days.
    """
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

@st.cache_data
def get_top_10_items():
    """
    Fetch the top 10 most purchased items across all customers.
    
    Inputs:
        None required.

    Returns:
        pd.DataFrame: Contains columns such as:
            - product_description: Description of the product.
            - purchase_count: Number of times the product was purchased.
    """
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

@st.cache_data
def get_top_10_items_by_phone(phone):
    """
    Fetch the top 10 most purchased items for a specific customer by phone number.
    
    Inputs:
        phone (str): The customer's phone number.

    Returns:
        pd.DataFrame: Contains columns such as:
            - product_description: Description of the product.
            - purchase_count: Number of times the product was purchased.
    """
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

@st.cache_data
def get_purchase_history_by_phone(phone):
    """
    Fetch the purchase history for a specific customer by phone number.
    
    Inputs:
        phone (str): The customer's phone number.

    Returns:
        pd.DataFrame: Contains columns such as:
            - productno: Product number.
            - product_description: Description of the product.
            - sold_price: Price at which the product was sold.
            - current_item_price: Current price of the product.
            - purchase_quantity: Quantity of the product purchased.
            - total: Total amount spent on the product.
            - purchase_date: Date of the purchase.
    """
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

@st.cache_data
def get_payment_history_by_phone(phone):
    """
    Fetch the payment history for a specific customer by phone number.
    
    Inputs:
        phone (str): The customer's phone number.

    Returns:
        pd.DataFrame: Contains columns such as:
            - invoiceno: Invoice number.
            - total_paid: Total amount paid.
            - payment_date: Date of the payment.
    """
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

@st.cache_data
def get_products():
    """
    Fetch all products with their details and purchase counts.
    
    Inputs:
        None required.

    Returns:
        pd.DataFrame: Contains columns such as:
            - productno: Product number.
            - description: Description of the product.
            - saleprice: Sale price of the product.
            - buyprice: Buy price of the product.
            - purchase_count: Number of times the product was purchased.
    """
    products_query = """
        SELECT
        p.productno,
        p.description,
        p.saleprice,
        p.buyprice,
        COUNT(td.productno) AS purchase_count
        FROM
        product p
        LEFT JOIN transactiondetails td ON p.productno = td.productno
        GROUP BY
        p.productno,
        p.description,
        p.saleprice,
        p.buyprice
        ORDER BY
        p.productno;
    """
    return fetch_data(products_query)

@st.cache_data
def get_top_product(phone):
    """
    Fetch the top purchased product for a specific customer by phone number.
    
    Inputs:
        phone (str): The customer's phone number.

    Returns:
        pd.DataFrame: Contains columns such as:
            - productno: Product number.
            - product_description: Description of the product.
            - total_amount: Total amount spent on the product.
            - purchase_count: Number of times the product was purchased.
    """
    query = f"""
    SELECT
        td.productno,
        p.description AS product_description,
        SUM(td.saleprice * td.quantity) AS total_amount,
        COUNT(td.productno) AS purchase_count
    FROM
        public.transactiondetails td
        JOIN public.transactions t ON td.transactionid = t.id
        JOIN public.payment pay ON t.invoiceno = pay.invoiceno::TEXT
        JOIN public.product p ON td.productno = p.productno
        JOIN public.customers c ON pay.custid = c.custid
    WHERE
        pay.phone = '{phone}'
    GROUP BY    
        td.productno,
        p.description
    ORDER BY
         purchase_count DESC;
    """
    results = fetch_data(query)
    
    return results

def main():
    """
    Main function to render the Streamlit page for Customer Relationship Management (CRM).
    
    Inputs:
        None required.

    Returns:
        None: Renders the Streamlit page with customer data and analysis.
    """
    st.set_page_config(
        page_title="CRM",
        page_icon=st.secrets["FAVICON"],
        layout="wide",
    )
    st.title("Customer Relationship Dashboard")
    st.sidebar.markdown('# Home') 
    st.sidebar.markdown('Manage your top customers, ranked by their total purchase contribution in "📈 Overview: All Customers".')
    st.sidebar.markdown('Copy a phone number and search up their data in the 2nd tab named "🔍 Search for a Customer" and recommend your products.')
    st.logo(
        st.secrets["LOGO"],
        icon_image=st.secrets["ICON"],
    )  

    # Authenticate user
    authenticator = get_authenticator()
    if authenticator: # Checks if authentication is disabled via environment variable
        authenticator.login(key='LoginProductAnalysis', location='main') # This displays the authentication form

    # Safely access session state keys with default values
    authentication_status = st.session_state.get('authentication_status', None)
    name = st.session_state.get('name', "Guest")

    # Main Layout
    if authentication_status: # Display content only if authenticated
        tab1, tab2 = st.tabs(["📈 Overview: All Customers", "🔍 Search for a Customer"])

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

                    with st.container():
                        st.subheader("Other Product Recommendations")
                    
                        if st.button('Get Recommendations'):
                            top_prod = get_top_product(phone_number)
                            recommendations = get_recommendations(top_prod.iloc[0]['productno'], get_products())
                            st.write(f"Because they liked {top_prod.iloc[0]['product_description']}")
                            st.metric(label="Top Recommendation", value=f"{recommendations.iloc[0]['description']}", delta=f"{recommendations.iloc[0]['saleprice']}")
                            st.write("Other recommendations")
                            st.write(recommendations[['productno', 'description', 'saleprice']])

                else:
                    st.write("No customer data found for the provided phone number.")
    elif authentication_status is False:
        st.error("Invalid username or password.") 
    elif authentication_status is None:
        st.warning("Please enter your login credentials.")
if __name__ == "__main__":
    main()
