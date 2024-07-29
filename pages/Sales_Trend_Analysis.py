import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils.database import fetch_data
from utils.preprocessing import preprocess_data
from datetime import datetime

st.set_page_config(
    page_title="Sales Trends",
    page_icon=st.secrets["FAVICON"],
    layout="wide",
)



@st.cache_data
def load_data():
    payment_query = "SELECT datein, amount, custid as customer_id FROM payment;"
    df = fetch_data(payment_query)
    df = preprocess_data(df)
    customers_query = "SELECT custid as customer_id, cname FROM customers;"
    customers_df = fetch_data(customers_query)
    return df, customers_df

# Load and preprocess data
df, customers_df = load_data()
# Initialize session state for date inputs
if 'start_date' not in st.session_state:
    st.session_state.start_date = datetime.strptime("2000-01-01", "%Y-%m-%d").date()
if 'end_date' not in st.session_state:
    st.session_state.end_date = datetime.now().date()

# Ensure session state dates are valid
if pd.isna(st.session_state.start_date) or not isinstance(st.session_state.start_date, datetime.date):
    st.session_state.start_date = df.index.min().date()
if pd.isna(st.session_state.end_date) or not isinstance(st.session_state.end_date, datetime.date):
    st.session_state.end_date = df.index.max().date()

# Function to plot sales trend with interactivity
def plot_sales_trend(df):
    df = df[(df.index >= pd.to_datetime(st.session_state.start_date)) & (df.index <= pd.to_datetime(st.session_state.end_date))]
    st.subheader("Monthly Sales Trend")
    df_monthly = df[['amount']].resample('MS').sum()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df_monthly.index, df_monthly['amount'], marker='o')
    ax.set_title('Monthly Sales Trend')
    ax.set_xlabel('Date')
    ax.set_ylabel('Total Sales')
    ax.grid(True)
    st.pyplot(fig)

# Function to plot weekly sales trend with interactivity
def plot_weekly_sales(df):
    df = df[(df.index >= pd.to_datetime(st.session_state.start_date)) & (df.index <= pd.to_datetime(st.session_state.end_date))]

    st.subheader("Weekly Sales Trend")
    df_weekly = df[['amount']].resample('W-MON').sum()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df_weekly.index, df_weekly['amount'], marker='o', color='orange')
    ax.set_title('Weekly Sales Trend')
    ax.set_xlabel('Date')
    ax.set_ylabel('Total Sales')
    ax.grid(True)
    st.pyplot(fig)

# Function to plot daily sales trend with interactivity
def plot_daily_sales(df):
    df = df[(df.index >= pd.to_datetime(st.session_state.start_date)) & (df.index <= pd.to_datetime(st.session_state.end_date))]

    st.subheader("Daily Sales Trend")
    df_daily = df[['amount']].resample('D').sum()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df_daily.index, df_daily['amount'], marker='o', color='red')
    ax.set_title('Daily Sales Trend')
    ax.set_xlabel('Date')
    ax.set_ylabel('Total Sales')
    ax.grid(True)
    st.pyplot(fig)

# Function to plot monthly sales with rolling average with interactivity
def plot_monthly_sales_with_rolling_avg(df):
    df = df[(df.index >= pd.to_datetime(st.session_state.start_date)) & (df.index <= pd.to_datetime(st.session_state.end_date))]

    st.subheader("Monthly Sales with Rolling Average")
    df_monthly = df[['amount']].resample('MS').sum()
    df_monthly['rolling_avg'] = df_monthly['amount'].rolling(window=3).mean()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df_monthly.index, df_monthly['amount'], label='Monthly Sales', marker='o')
    ax.plot(df_monthly.index, df_monthly['rolling_avg'], label='Rolling Average', color='red')
    ax.set_title('Monthly Sales with Rolling Average')
    ax.set_xlabel('Date')
    ax.set_ylabel('Total Sales')
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

@st.cache_data
def get_purchases_within_range(start_date=st.session_state.start_date, end_date=st.session_state.end_date):
    query = f'''
    SELECT
        p.paymentid,
        p.amount,
        p.datein,
        p.invoiceno,
        p.phone,
        c.cname AS customer_name,
        p.custid,
        p.paymenttype
    FROM
        payment p
    JOIN customers c ON p.custid = c.custid
    WHERE
        p.datein BETWEEN \'{st.session_state.start_date}\' AND \'{st.session_state.end_date}\';
    
    '''

    return fetch_data(query)

@st.cache_data
def get_invoice_info(invoice_number):
    query = f'''
    SELECT
        (td.saleprice * td.quantity) AS total,
        ti.custid,
        ti.datein,
        p.description AS product_description,
        td.productno,
        td.saleprice,
        td.quantity,
        ti.invoiceno,
        p.barcode AS product_barcode
    FROM
        transactions ti
        JOIN transactiondetails td ON ti.id = td.transactionid
        JOIN product p ON td.productno = p.productno
    WHERE
     ti.invoiceno = \'{invoice_number}\';
    
    '''

    return fetch_data(query)

def format_date(date):
    return date.strftime("%B %d, %Y")





st.title("Sales Trend Analysis")
st.sidebar.markdown("# Sales Analysis Dashboard")
st.logo(
    st.secrets["LOGO"],
    icon_image=st.secrets["ICON"],
)  



# Adding interactive date inputs to the sidebar
st.sidebar.markdown("## Date Range")
start_date = st.sidebar.date_input("Start Date", st.session_state.start_date)
end_date = st.sidebar.date_input("End Date", st.session_state.end_date)

# Update session state on button click
if st.sidebar.button('Apply Date Range'):
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date
    #st.rerun()

# Adding a filter for credit accounts (customers)
st.sidebar.markdown("## Filter by Customers")
customer_filter = st.sidebar.multiselect(
    "Select Customers to Exclude",
    options=customers_df['cname'].tolist()
)

if customer_filter:
    customer_ids_to_exclude = customers_df[customers_df['cname'].isin(customer_filter)]['customer_id'].values
    df = df[~df['customer_id'].isin(customer_ids_to_exclude)]

# Filter the data based on the selected date range
df = df[(df.index >= pd.to_datetime(st.session_state.start_date)) & (df.index <= pd.to_datetime(st.session_state.end_date))]

# Adding interactive options to the sidebar
st.sidebar.markdown("## Plot Selection")
options = st.sidebar.multiselect(
    'Scope',
    ['Monthly', 'Weekly', 'Daily', 'Monthly with Rolling Average'],
    default=['Monthly', 'Weekly', 'Daily', 'Monthly with Rolling Average']
)


# Main Layout

tab1, tab2 = st.tabs(["Charts", "Table"])

with tab1:
    if 'Monthly' in options:
        plot_sales_trend(df)
    if 'Weekly' in options:
        plot_weekly_sales(df)
    if 'Daily' in options:
        plot_daily_sales(df)
    if 'Monthly with Rolling Average' in options:
        plot_monthly_sales_with_rolling_avg(df)
with tab2:
    st.subheader(f"Purchases from :green[{format_date(st.session_state.start_date)}] to :green[{format_date(st.session_state.end_date)}]")
    st.dataframe(get_purchases_within_range(), use_container_width=True)

    with st.container(border=True):
        st.subheader("Search for Invoice information")
        invoice_number = st.text_input("Enter Invoice Number: (invoiceno)", "")
        st.dataframe(get_invoice_info(invoice_number))