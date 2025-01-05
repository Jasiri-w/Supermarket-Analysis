from datetime import datetime, date
from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex, Document, Settings, SimpleDirectoryReader
import matplotlib.pyplot as plt
import openai
import pandas as pd
import streamlit as st
from utils.auth import get_authenticator
from utils.database import fetch_data

## Page Configurations must come first
st.set_page_config(
    page_title="AI: Chatting...",
    page_icon=st.secrets["FAVICON"],
    layout="wide",
)
# Initialize session state for date inputs
if 'start_date' not in st.session_state:
    st.session_state.start_date = datetime.strptime("2000-01-01", "%Y-%m-%d").date()
if 'end_date' not in st.session_state:
    st.session_state.end_date = datetime.now().date()

from pages.Customer_Relationship_Manager import (
    get_all_customer_data,
    get_customer_by_phone,
    get_top_10_items,
    get_top_10_items_by_phone,
    get_purchase_history_by_phone,
    get_payment_history_by_phone,
    get_products,
    get_top_product,
)
from pages.Sales_Trend_Analysis import (
    load_sales_data,
    plot_sales_trend,
    plot_weekly_sales,
    plot_daily_sales,
    plot_monthly_sales_with_rolling_avg,
    get_purchases_within_range,
    get_invoice_info,
    format_date,
)
from pages.Product_Analysis import (
    get_credit_account_most_purchased,
    get_daily_customer_most_purchased,
    get_highest_daily_customers,
    get_items_purchased_less_than_20,
    get_least_purchased_items,
    get_longest_buying_customers,
)

st.title("AI Chat Bot")
st.logo(
    st.secrets["LOGO"],
    icon_image=st.secrets["ICON"],
)
st.write('This chatbot is created using ChatGPT.')
debug_mode = st.secrets["DEBUG_MODE"]
## LlamaIndex Auxiliary Functions

@st.cache_resource(show_spinner=True)
def load_data():
    """
    Loads data from multiple sources, including database data, 
    and prepares the index for the LlamaIndex-powered chat engine.
    """
    # Placeholder for dynamically fetched database data
    @st.cache_data
    def fetch_dynamic_data():
        """
        Fetches data dynamically from the database and converts it into LlamaIndex-compatible Documents.
        Includes default foundational queries and specific queries for later use.
        """
        # Default foundational queries to provide breadth for the chatbot
        foundational_queries = {
            "customer_data": "SELECT * FROM public.customers LIMIT 100",
            "product_data": "SELECT * FROM public.product LIMIT 100",
            "transaction_data": "SELECT * FROM public.transactions LIMIT 100",
            "transaction_details": "SELECT * FROM public.transactiondetails LIMIT 100",
            "payment_data": "SELECT * FROM public.payment LIMIT 100",
            "inventory_data": "SELECT * FROM public.inventory LIMIT 100"
        }

        # Execute foundational queries
        documents = []
        for query_name, query in foundational_queries.items():
            try:
                df = fetch_data(query)
                documents.append(
                    Document(
                        text=df.to_string(index=False),
                        metadata={"source": query_name},
                    )
                )
            except Exception as e:
                print(f"Error fetching {query_name}: {e}")

        if debug_mode:
            print(f"Foundational Documents: {documents}")
        return documents

    # Fetch static documents (e.g., text files in the "data" folder)
    reader = SimpleDirectoryReader(input_dir="./data", recursive=True)
    static_docs = reader.load_data()

    # Combine static and dynamic documents
    dynamic_docs = fetch_dynamic_data()
    all_documents = static_docs + dynamic_docs

    if debug_mode:
        print(f"Static Documents: {static_docs}")
        print(f"Dynamic Documents: {dynamic_docs}")

    # Set LlamaIndex's LLM settings
    Settings.llm = OpenAI(
        model="gpt-4o-mini",
        temperature=0.0,  # Ensure deterministic, fact-based responses
        system_prompt="""
            You are a highly reliable and conversational personal data analytics assistant specializing in analyzing sales, product, and marketing information. Your responses must adhere to the following structured format to ensure compatibility with the rendering function:
            Key Response Format Instructions:
            1. **Structure**:
            - All responses must be provided as a JSON object.
            - The JSON object must include the following keys:
                - `"text"`: A string summarizing the response in plain language.
                - `"visualization"` (optional): An object containing details for rendering visualizations.

            2. **Visualization Object**:
            - If the response involves a visualization, include the `"visualization"` key with the following structure:
                ```json
                {
                "type": "<visualization_type>",
                "data_params": {
                    "<param_name>": "<param_value>"
                }
                }
                ```
            - Examples of visualization types: `"sales_trend"`, `"top_10_items"`, `"purchase_history"`.
            - `data_params` should contain any parameters needed to generate the visualization, such as dates or customer IDs.

            3. **Unavailable Data**:
            - If specific data is unavailable, the response should only include the `"text"` key with a message like: "I cannot answer this question based on the provided data."

            4. **Transparency**:
            - If asked about your role, explain clearly that you are a data analytics assistant based on OpenAI's GPT models.

            Example Response:
            User Input: "Show me the sales trend for the past month."
            LLM Response:
            ```json
            {
            "text": "Here is the sales trend for the past month:",
            "visualization": {
                "type": "sales_trend",
                "data_params": {
                "start_date": "2024-12-01",
                "end_date": "2024-12-31"
                }
            }
            }"""
    )

    # Build and return the index
    index = VectorStoreIndex.from_documents(all_documents)
    return index


# Placeholder for dynamically called specific queries
def fetch_specific_data_by_phone(phone):
    """
    Fetches specific customer-related data by phone number.
    """
    customer_query = f"""
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
        pay.phone = '{phone}'
    GROUP BY
        pay.phone, c.cname;
    """

    payment_history_query = f"""
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
        payment_date DESC;
    """

    purchase_history_query = f"""
    SELECT
        td.productno,
        p.description AS product_description,
        td.saleprice AS sold_price,
        td.quantity AS purchase_quantity,
        (td.saleprice * td.quantity) AS total,
        t.datein AS purchase_date
    FROM
        public.transactiondetails td
    JOIN public.transactions t ON td.transactionid = t.id
    JOIN public.payment pay ON t.invoiceno = pay.invoiceno::TEXT
    JOIN public.product p ON td.productno = p.productno
    WHERE
        pay.phone = '{phone}'
    ORDER BY
        purchase_date DESC;
    """

    results = {
        "customer_summary": fetch_data(customer_query),
        "payment_history": fetch_data(payment_history_query),
        "purchase_history": fetch_data(purchase_history_query)
    }

    return results

def render_visualization(llm_response):
    """
    Render visualizations based on the LLM response. Utilizes all imported functions.
    :param llm_response: Dictionary with keys 'text' and optional 'visualization'.
    """
    response_text = llm_response.get("text", "").lower()
    visualization = llm_response.get("visualization", {})

    # Helper function to display Streamlit visualizations or outputs
    def display_output(output, title="Result"):
        if isinstance(output, pd.DataFrame):
            st.write(title)
            st.dataframe(output)
        elif isinstance(output, str):
            st.write(title)
            st.text(output)
        elif isinstance(output, plt.Figure):
            st.write(title)
            st.pyplot(output)
        else:
            st.write(f"{title}: {output}")

    # Handle visualization rendering
    if visualization:
        vis_type = visualization.get("type")
        data_params = visualization.get("data_params", {})

        if vis_type == "sales_trend":
            start_date = data_params.get("start_date")
            end_date = data_params.get("end_date")
            output = plot_sales_trend(start_date=start_date, end_date=end_date)
            display_output(output, "Sales Trend")

        elif vis_type == "top_10_items":
            output = get_top_10_items()
            display_output(output, "Top 10 Items")

        elif vis_type == "customer_data":
            phone = data_params.get("phone")
            output = get_customer_by_phone(phone)
            display_output(output, f"Customer Data for Phone: {phone}")

        elif vis_type == "purchase_history":
            phone = data_params.get("phone")
            output = get_purchase_history_by_phone(phone)
            display_output(output, f"Purchase History for Phone: {phone}")

        elif vis_type == "payment_history":
            phone = data_params.get("phone")
            output = get_payment_history_by_phone(phone)
            display_output(output, f"Payment History for Phone: {phone}")

        elif vis_type == "weekly_sales":
            output = plot_weekly_sales()
            display_output(output, "Weekly Sales")

        elif vis_type == "daily_sales":
            output = plot_daily_sales()
            display_output(output, "Daily Sales")

        elif vis_type == "monthly_sales":
            output = plot_monthly_sales_with_rolling_avg()
            display_output(output, "Monthly Sales with Rolling Average")

        elif vis_type == "invoice_info":
            output = get_invoice_info()
            display_output(output, "Invoice Info")

        elif vis_type == "credit_account_most_purchased":
            output = get_credit_account_most_purchased()
            display_output(output, "Credit Account Most Purchased Items")

        elif vis_type == "items_purchased_less_than_20":
            output = get_items_purchased_less_than_20()
            display_output(output, "Items Purchased Less than 20")

        elif vis_type == "least_purchased_items":
            output = get_least_purchased_items()
            display_output(output, "Least Purchased Items")

        elif vis_type == "longest_buying_customers":
            output = get_longest_buying_customers()
            display_output(output, "Longest Buying Customers")

        elif vis_type == "highest_daily_customers":
            output = get_highest_daily_customers()
            display_output(output, "Highest Daily Customers")

        elif vis_type == "daily_customer_most_purchased":
            output = get_daily_customer_most_purchased()
            display_output(output, "Daily Customer Most Purchased Items")

        else:
            st.write(f"Unknown visualization type: {vis_type}")

    else:
        # Process response_text for keyword-based triggers
        if "all customer data" in response_text:
            output = get_all_customer_data()
            display_output(output, "All Customer Data")

        elif "customer by phone" in response_text:
            phone = llm_response.get("metadata", {}).get("phone", "1234567890")
            output = get_customer_by_phone(phone)
            display_output(output, f"Customer Data for Phone: {phone}")

        elif "top 10 items by phone" in response_text:
            phone = llm_response.get("metadata", {}).get("phone", "1234567890")
            output = get_top_10_items_by_phone(phone)
            display_output(output, f"Top 10 Items for Phone: {phone}")

        elif "top product" in response_text:
            output = get_top_product()
            display_output(output, "Top Product")

        elif "sales trend" in response_text:
            output = plot_sales_trend()
            display_output(output, "Sales Trend")

        elif "weekly sales" in response_text:
            output = plot_weekly_sales()
            display_output(output, "Weekly Sales")

        elif "daily sales" in response_text:
            output = plot_daily_sales()
            display_output(output, "Daily Sales")

        elif "monthly sales" in response_text:
            output = plot_monthly_sales_with_rolling_avg()
            display_output(output, "Monthly Sales with Rolling Average")

        elif "purchases within range" in response_text:
            start_date, end_date = "2024-01-01", "2024-12-31"  # Example date range
            output = get_purchases_within_range(start_date, end_date)
            display_output(output, f"Purchases from {start_date} to {end_date}")

        elif "invoice info" in response_text:
            output = get_invoice_info()
            display_output(output, "Invoice Info")

        elif "format date" in response_text:
            date_to_format = "2024-12-31"  # Example date
            output = format_date(date_to_format)
            display_output(output, f"Formatted Date: {output}")

        else:
            st.write("No recognized visualization or text command in the response.")

# Load the index for use in the chat engine
index = load_data()


if "chat_engine" not in st.session_state.keys():  # Initialize the chat engine
    st.session_state.chat_engine = index.as_chat_engine(
        chat_mode="condense_question", verbose=True, streaming=True
    )

# User Authentication Check
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False

if not st.session_state['authentication_status']:
    get_authenticator().login(key='LoginCRM', location='main')
    st.warning("Please enter your login credentials to access the CRM.")
else:
    # OpenAI Chat Bot
    openai.api_key = st.secrets["OPENAI_API_KEY"]

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = Settings.llm.model

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    debug_mode = st.sidebar.checkbox("Enable Debug Mode", value=st.secrets["DEBUG_MODE"])

    with st.sidebar:
        def reset_conversation():
            # Clear the existing list of messages
            if "messages" in st.session_state:
                st.session_state.messages.clear()
        st.button('Reset Chat', on_click=reset_conversation)

    if debug_mode:
        with st.sidebar:
            # Cache clearing button
            if st.sidebar.button("Reset Session State"):
                st.cache_data.clear()
                st.cache_resource.clear()
                st.sidebar.success("Cache cleared successfully.")
            st.write("Session State:", st.session_state)
            st.write("Model System Prompt:", Settings.llm.system_prompt)

    # Handle user input
    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Use LlamaIndex to generate a response
        with st.chat_message("assistant"):
            response_stream = st.session_state.chat_engine.stream_chat(prompt)
            st.write_stream(response_stream.response_gen)

            # Append the assistant's response to the chat history
            message = {"role": "assistant", "content": response_stream.response}
            st.session_state.messages.append(message)

        # Pass the response to render_visualization for future enhancements
        render_visualization({
            "text": response_stream.response["text"],
            "visualization": response_stream.response.get("visualization")
        })
