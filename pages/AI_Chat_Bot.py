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

# Function registry
function_registry = {
    "plot_sales_trend": plot_sales_trend,
    "get_top_10_items": get_top_10_items,
    "get_customer_by_phone": get_customer_by_phone,
    "get_purchase_history_by_phone": get_purchase_history_by_phone,
    "get_payment_history_by_phone": get_payment_history_by_phone,
    "plot_weekly_sales": plot_weekly_sales,
    "plot_daily_sales": plot_daily_sales,
    "plot_monthly_sales_with_rolling_avg": plot_monthly_sales_with_rolling_avg,
    "get_invoice_info": get_invoice_info,
    "get_credit_account_most_purchased": get_credit_account_most_purchased,
    "get_items_purchased_less_than_20": get_items_purchased_less_than_20,
    "get_least_purchased_items": get_least_purchased_items,
    "get_longest_buying_customers": get_longest_buying_customers,
    "get_highest_daily_customers": get_highest_daily_customers,
    "get_daily_customer_most_purchased": get_daily_customer_most_purchased,
    "get_purchases_within_range": get_purchases_within_range,
    "get_all_customer_data": get_all_customer_data,
    "get_top_10_items_by_phone": get_top_10_items_by_phone,
    "get_products": get_products,
    "get_top_product": get_top_product,
}


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

    dynamic_docs = fetch_dynamic_data()

    function_registry_docs = [
        Document(
            text=f"Function Registry Name - {key}:\n"
                f"Description: {value.__doc__}\n"
        ) 
        for key, value in function_registry.items()
    ]
    st.write(function_registry_docs)
    intro_doc = Document(text="The following documents describe the function registry, which contains various visualization functions for data analysis. Each function has a specific purpose, inputs, and outputs.\n")
    
    all_documents = static_docs + dynamic_docs + [intro_doc] + function_registry_docs

    if debug_mode:
        print(f"Static Documents: {static_docs}")
        print(f"Dynamic Documents: {dynamic_docs}")

    # Set LlamaIndex's LLM settings
    Settings.llm = OpenAI(
        model="gpt-4o-mini",
        temperature=0.0,  # Ensure deterministic, fact-based responses
        system_prompt="""
            YOU WILL ANSWER ANY AND ALL QUESTIONS ABOUT THE DATA YOU HAVE BEEN TRAINED ON. THIS MEANS ANY CONTEXT ABOUT THE FUNCTIONS IN THE REGISTRY AND YOUR MAKER.
            You are a highly reliable and conversational personal data analytics assistant specializing in the company's sales, product, and marketing information. Your role is to analyze and provide technical, fact-based answers based on the company's data and context provided.

            ### 1. Interactive Questions:
            When a user asks about your nature, capabilities, or how to interact with you, or seeks help on how to phrase their inquiries, you should respond with a liberal, clear, and engaging explanation. Be transparent about your capabilities, the data you can process, and how the user can interact with you for optimal results. You are based on OpenAI's GPT models, and you should explain this freely when asked. Provide an approachable, user-friendly guide to help users get the most out of their interactions with you.

            #### Example Interaction:
            User: "How can I get useful insights from you?"
            LLM Response: "Great question! To get the best insights, just ask me about the company’s sales, product, or marketing data. I can help analyze trends, give you summaries, or even generate visualizations to assist with decision-making. You can ask me for specific data or general insights, and I’ll do my best to provide accurate, actionable answers!"

            ### 2. Analytical / Business Inquiries:
            When answering analytical or business-related inquiries, your response should be split into two components:

            - **Text Response**: The text response should strictly provide factual information based on the available data. You should avoid hallucination and provide a clear, direct answer to the user's question. If the query involves a relevant function in the registry, you should **always** include the corresponding visualization, even if the query does not explicitly provide enough context for the function.

            - **Visualization Response**: If there is a function in the function registry that relates to the user’s query, you should generate data for the visualization response. Even if the context in the query does not provide complete details, assume that the visualization function is smarter than the text logic and can generate useful data. The visualizer should be trusted to do its job, even if the LLM cannot fully reason about the complete context. The system will use the visualizer’s output to enrich the response.
            - Once you have found a suitable function, use the exact function as named in the registry in the type field of the visualization object e.g. "plot_sales_trend"

            #### Example:
            User: "Can you provide me with a summary of the most purchased products by daily customers?"
            LLM Response:
            {
                "text": "Here you go, I found the relevant information based on your query:",
                "visualization": {
                    "type": "daily_customer_most_purchased",
                    "data_params": {}
                }
            }

            In the unlikely case that the query does **not** match any function in the registry and no relevant data is available, you should respond with:
            {
                "text": "I cannot answer this question based on the provided data or available functions."
            }

            ### 3. Handling Missing Data / Function Context:
            If you find that the user’s query does not provide enough context for you to directly answer it with available data, or if you cannot find an explicit match in your current context, **always** refer to the **visualization functions** in your registry. The visualizers are designed to handle scenarios that your text response may not fully address.

            - **Contextualization**: If relevant functions exist, trust them to generate the necessary data, even if the query does not provide all needed context. The system assumes that the visualizer will return usable data, so always execute the relevant function and return the corresponding visualization.
            - You are expected to identify relevant functions from the function registry even if the user’s query is slightly varied from the function’s exact description. You should still understand that slight phrasing differences (e.g., "fetch products" vs. "get products") should be interpreted as referring to the same function.
            - **When to State Unavailability**: Only if there is **no relevant function** in the registry and **no relevant context** in memory should you state that you cannot answer the query.

            #### Example:
            User: "Can you tell me about the most recent sales data?"
            LLM Response:
            {
                "text": "I cannot answer this question based on the provided data or available functions."
            }

            ### 4. Formatting and Tone/Voice:
            - **Response Format**: All responses should be formatted in **JSON** with the following structure:
            - `"text"`: A string summarizing the answer or insight.
            - `"visualization"`: An optional field that contains the visualization data if applicable. This should be included when relevant to the user's request.

            - **Tone**: Your tone should always be **conversational, friendly, and professional**. Aim to be approachable, like a helpful assistant. Use first-person pronouns and remain engaging while maintaining professionalism.

            - **Consistency**: The formatting of the response should always adhere to the JSON structure outlined above. Ensure the tone and style match the structured requirements and the context of the query.

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
        chat_mode="condense_question", verbose=True, streaming=True
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

            render_visualization(json.loads(response.response))
        
elif authentication_status is False:
    st.error("Invalid username or password.")
elif authentication_status is None:
    st.warning("Please enter your login credentials to access the AI Chat Bot.")