from datetime import datetime, date
import io
import json
from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex, Document, Settings, SimpleDirectoryReader, get_response_synthesizer
import matplotlib.pyplot as plt
import openai
import pandas as pd
import streamlit as st
import time
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
            You are a highly reliable and conversational personal data analytics assistant specializing in the company's sales, product, and marketing information. Your role is to analyze and provide technical, fact-based answers based on the company's data and context provided.

            ### Key Capabilities:
            - **Conversational Tone**: Speak conversationally and engagingly, like a friendly and professional assistant. Speak in the first person and use a friendly, approachable tone.
            - **Avoid Hallucination**: DO NOT fabricate data or make assumptions. Provide responses strictly based on the available data.
            - **Unavailable Data**: If specific information is unavailable, clearly state: "I cannot answer this question based on the provided data."
            - **General Insights**: You may offer general advice, industry best practices, or relevant tips based on your expertise, provided they align with the context.
            - **Transparent Role**: If asked about your nature, training, or background, you may clarify and explain your role liberally, including mentioning you are based on OpenAI's GPT models.
            - **Response Format**: All responses are JSON objects containing a `"text"` field summarizing the response and an optional `"visualization"` field if visualization is applicable.
            - **Consistency**: Always ensure the data format, tone, and style match the structured requirements provided.

            ### Function: `get_daily_customer_most_purchased`
            **Purpose**: This function identifies the most frequently purchased product for each daily customer in the database. Daily customers are individuals without a credit account but with a purchase history identified by the phone number used during transactions. The function ranks products by purchase frequency for each phone number and returns the top item along with relevant customer details.

            **Inputs**: None explicitly required by the function. However, the dataset includes:
            - Customer phone numbers for identification.
            - Product purchase records with counts aggregated for each customer.

            **Outputs**:
            - A table containing:
            - `phone`: The customer's phone number.
            - `productno`: The product ID of the most purchased item.
            - `most_purchased_item`: Description of the top product.
            - `purchase_count`: Number of times the product was purchased.
            - Additional customer information, including name, address, email, credit limit, balance, loyalty points, and other attributes.

            **Usage Example**:
            User Input: "What is the most purchased product for daily customers?"
            LLM Response:
            {
                "text": "Here are the most purchased products for daily customers:",
                "visualization": {
                    "type": "daily_customer_most_purchased",
                    "data_params": {}
                }
            }

            ### General Guidelines:
            1. **Structure**: All responses must follow the JSON format with `text` and optional `visualization` keys.
            2. **Visualization Requirements**: Include `data_params` with relevant filters (e.g., date range, customer phone).
            3. **Unavailable Data**: Respond clearly if data cannot be determined or accessed.
            4. **Accuracy First**: Strictly base answers on the data provided or generated by the defined functions.

            ### Mission:
            Your mission is to deliver actionable insights, technical accuracy, and a user-friendly conversational experience to empower decision-making within the company.

            """
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
    # Function registry
    function_registry = {
        "sales_trend": plot_sales_trend,
        "top_10_items": get_top_10_items,
        "customer_data": get_customer_by_phone,
        "purchase_history": get_purchase_history_by_phone,
        "payment_history": get_payment_history_by_phone,
        "weekly_sales": plot_weekly_sales,
        "daily_sales": plot_daily_sales,
        "monthly_sales": plot_monthly_sales_with_rolling_avg,
        "invoice_info": get_invoice_info,
        "credit_account_most_purchased": get_credit_account_most_purchased,
        "items_purchased_less_than_20": get_items_purchased_less_than_20,
        "least_purchased_items": get_least_purchased_items,
        "longest_buying_customers": get_longest_buying_customers,
        "highest_daily_customers": get_highest_daily_customers,
        "daily_customer_most_purchased": get_daily_customer_most_purchased,
        "purchases_within_range": get_purchases_within_range,
        "all_customer_data": get_all_customer_data,
        "top_10_items_by_phone": get_top_10_items_by_phone,
        "products": get_products,
        "top_product": get_top_product,
    }

    response_text = llm_response.get("text", "")
    visualization = llm_response.get("visualization", {})

    # Display text response
    st.write(response_text)

    # Handle visualizations
    if visualization:
        vis_type = visualization.get("type")
        data_params = visualization.get("data_params", {})

        # Find and execute the function
        visualization_function = function_registry.get(vis_type)
        if visualization_function:
            try:
                output = visualization_function(**data_params)
                if isinstance(output, pd.DataFrame):
                    st.dataframe(output)
                elif isinstance(output, plt.Figure):
                    st.pyplot(output)
                else:
                    st.write(output)
            except Exception as e:
                st.error(f"Error executing {vis_type}: {e}")
        else:
            st.error(f"Visualization type '{vis_type}' not recognized.")
    else:
        st.write("No visualization requested.")



# Load the index for use in the chat engine
index = load_data()
response_synthesizer_refine = get_response_synthesizer(response_mode="refine", structured_answer_filtering=False) # This is used to ensure that it is true to the context i.e. it is based on our RAGged stuff information
response_synthesizer_compact = get_response_synthesizer(response_mode="compact", structured_answer_filtering=False) # This is used to ensure that it is true to the context i.e. it is based on our RAGged stuff information

if "chat_engine" not in st.session_state.keys():  # Initialize the chat engine
    st.session_state.chat_engine = index.as_chat_engine(
        chat_mode="condense_question", verbose=True, streaming=True, response_synthesizer=response_synthesizer_refine
    )

# Authenticate user
authenticator = get_authenticator()
authenticator.login(key='LoginCRM',location= 'main')
authentication_status = st.session_state['authentication_status']
name = st.session_state['name']
username = st.session_state['username']

if authentication_status:
    st.success(f"Welcome, {name}!")
    st.sidebar.success("You are logged in.")

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
            response = st.session_state.chat_engine.chat(prompt)
            response_text = json.loads(response.response)["text"]
            response_generator = lambda: (time.sleep(0.05) or chunk for chunk in response_text.split('\n'))
            st.write_stream(response_generator())

            # Append the assistant's response to the chat history
            message = {"role": "assistant", "content": response_text}
            st.session_state.messages.append(message)

        # Pass the response to render_visualization for future enhancements
        try:
            vis = json.loads(response.response)["visualization"]
        except Exception:
            vis = None

        render_visualization({
            "text": response_text,
            "visualization": vis
        })
        
elif authentication_status is False:
    st.error("Invalid username or password.")
elif authentication_status is None:
    st.warning("Please enter your login credentials to access the AI Chat Bot.")