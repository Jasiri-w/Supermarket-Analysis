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
df = load_sales_data()
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
            "Customer Information": "SELECT * FROM public.customers",
            "Product Inventory": "SELECT * FROM public.product LIMIT 100",
            #"Transactions": "SELECT * FROM public.transactions LIMIT 100",
            #"transaction_details": "SELECT * FROM public.transactiondetails LIMIT 100",
            #"payment_data": "SELECT * FROM public.payment LIMIT 100",
        }

        query_descriptions = {
            "Customer Information": "This data represents customer information from the database including their name (cname), address (address), phone number (phone), email (email), and credit limit (creditlimit). The 'Cash Sale' customer represents all daily customers that buy items without an account while the rest are Credit Account holders.",
            "Product Inventory": "This data represents fetches the product inventory data from the database, including the product's name (description), how much it cost to purchase (purchasecost), how much it is sold for (saleprice), and the quantity available (quantity).",
            #"Transactions": "This query fetches the transaction data from the database.",
            #"transaction_details": "This query fetches the transaction details from the database.",
            #"payment_data": "This query fetches the payment data from the database.",

        }

        # Execute foundational queries
        documents = []
        for query_name, query in foundational_queries.items():
            try:
                df = fetch_data(query)
                documents.append(
                    Document(
                        text=df.to_string(index=False),
                        metadata={"Source": query_name,"Description": query_descriptions[query_name], "Type": "Database Data"},
                    )
                )
            except Exception as e:
                print(f"Error fetching {query_name}: {e}")

        return documents

    # Fetch static documents (e.g., text files in the "data" folder)
    reader = SimpleDirectoryReader(input_dir="./data", recursive=True)
    static_docs = reader.load_data()

    dynamic_docs = fetch_dynamic_data()

    function_registry_docs = [
        Document(
            text=f"Function Registry Name - {key}:\n"
                f"Description: {value.__doc__}\n",
            metadata={"Name": key, "Type": "Visualization Function", "Function Number": count},
        )
        for count, (key, value) in enumerate(function_registry.items(), start=1)
    ]
    st.write(f"Function Registry Documents: {function_registry_docs}")
    all_documents = static_docs + dynamic_docs + function_registry_docs

    # Set LlamaIndex's LLM settings
    Settings.llm = OpenAI(
        model="gpt-4o-mini",
        temperature=0.1,  # Ensure deterministic, fact-based responses
        system_prompt="""
            You are a highly reliable and conversational personal data analytics assistant specializing in the company's sales, product, and marketing information.
            Your role is to analyze and provide technical, fact-based answers based on the company's data and context provided. 
            You will answer any and all questions about the data you have been trained on. 
            You have been given the names and descriptions of tools for analytics called visualization functions, and these functions are in a list called the registry which you have been trained on. 
            You have also been trained on data with "type" database data so that you can answer questions about the company.
            You must share information on all the functions in your registry, including their names and descriptions, when asked so that the user can better interact with you.

            1. Interactive Questions:
            When a user asks about your nature, capabilities, how to interact with you, or seeks help on phrasing their inquiries, respond with a clear and engaging explanation. Be transparent about your capabilities, the data you can process, and how the user can interact with you for optimal results. You are based on OpenAI's GPT models, and you should explain this freely when asked. Provide a user-friendly guide to help users get the most out of their interactions with you. Always list every function in your function registry that you have been trained on.

            2. Analytical / Business Inquiries:
            When answering analytical or business-related inquiries, your response should be split into two components:
            - Text Response: Strictly provide factual information based on the available data. Avoid hallucination and give a clear, direct answer to the user's question. If the query involves a relevant function in the registry, always include the corresponding visualization, even if the query does not explicitly provide enough context for the function.
            - Visualization Response: If there is a function in the registry that relates to the user’s query, generate data for the visualization response. Even if the query does not provide complete details, assume the visualization function is capable of handling missing details. Use the exact function name from the registry in the "type" field of the visualization object, such as "plot_sales_trend." Always include the visualization object if it supports the analytical response.

            Example:
            User: "Can you provide me with a summary of the most purchased products by daily customers?"
            LLM Response:
            {
                "text": "Here you go, I found the relevant information based on your query:",
                "visualization": {
                    "type": "get_daily_customer_most_purchased",
                    "data_params": {}
                }
            }

            If the query does not match any function in the registry and no relevant data is available, respond as follows:
            {
                "text": "I cannot answer this question based on the provided data or available functions. Here is a list of the available functions: 1. get_daily_customer_most_purchased ..."
            }

            3. Handling Missing Data or Function Context:
            If the user’s query does not provide enough context for a direct answer, always refer to the visualization functions in your registry. Trust the visualizers to generate necessary data, even if the query lacks full details. You must:
            - Identify relevant functions from the function registry, even if the query wording differs slightly from the function's description.
            - Avoid hallucinating function names. Use exact matches from the registry, even if they have similar meanings to the user’s request.
            - If a function does not exist in the registry, omit the visualization feed. Instead, provide a clear response stating that no suitable visualization function is available.
            - State unavailability only if no relevant function exists in the registry and no relevant context is available.

            Example:
            User: "Can you tell me about the most recent marketing data?"
            LLM Response:
            {
                "text": "I cannot answer this question based on the provided data or available functions. You can ask me about the available functions in the registry, about products in the store and more"
            }

            4. Formatting and Tone:
            - Response Format: All responses should be formatted in JSON with "text" summarizing the answer or insight and "visualization" containing optional visualization data. Include "visualization" only when relevant to the user's request.
            - Do not create extra JSON fields or structures. Only use "text" and "visualization."
            - Do not hallucinate or invent function names. Use only the exact names from the registry.
            - Tone: Maintain a conversational, friendly, and professional tone. Be approachable, like a helpful assistant, while remaining consistent with the required structure and style.

            Emphasis on avoiding hallucinations:
            You must not invent or assume the existence of data or functions that are not explicitly provided in the registry or the database. Always use the exact function names and ensure all answers are based strictly on the provided data and context. If no valid match exists, clearly state that the query cannot be answered.
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
    visualization = llm_response.get("visualization", {})

    # Handle visualizations
    if visualization:
        vis_type = visualization.get("type")
        data_params = visualization.get("data_params", {})

        # Find and execute the function
        visualization_function = function_registry.get(vis_type)
        if visualization_function:
            if visualization_function.__code__.co_varnames[0] == "df":
                try:
                    sd = st.session_state.start_date
                    ed = st.session_state.end_date
                    if "start_date" in visualization.get("data_params"):
                        sd = visualization.get("data_params")["start_date"]
                    if "end_date" in visualization.get("data_params"):
                        ed = visualization.get("data_params")["end_date"]
                        
                    temp_df = df[(df.index >= pd.to_datetime(sd)) & (df.index <= pd.to_datetime(ed))]
                    output = visualization_function(temp_df)
                    return (st.pyplot, output)
                except Exception as e:
                    st.error(f"Error executing {vis_type}: {e} \n {llm_response}")
                    return None
            else:
                try:
                    output = visualization_function(**data_params)
                    if isinstance(output, pd.DataFrame):
                        return (st.dataframe, output)
                    elif isinstance(output, plt.Figure):
                        return (st.pyplot, output)
                    else:
                        return (st.write, output)
                except Exception as e:
                    st.error(f"Error executing {vis_type}: {e} \n {llm_response}")
                    return None
        else:
            st.error(f"Visualization type '{vis_type}' not recognized. \n {llm_response}")
            return None
    else:
        st.write(f"No visualization requested. \n {llm_response}")
        return None



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
            if "visualization" in message:
                visualization = message["visualization"]
                if visualization:
                    visualization[0](*visualization[1:])

    if(debug_mode):
        debug_mode = st.sidebar.checkbox("Enable Debug Mode", value=st.secrets["DEBUG_MODE"])

    with st.sidebar:
        with st.expander("Chat Settings", expanded=False):
            def reset_conversation():
                # Clear the existing list of messages
                if "messages" in st.session_state:
                    st.session_state.messages.clear()
            st.button('Reset Chat', on_click=reset_conversation)

    if debug_mode:
        with st.sidebar:
            # Cache clearing button
            with st.expander("Cache & Debugging", expanded=False):
                if st.sidebar.button("Reset Cache"):
                    st.cache_data.clear()
                    st.cache_resource.clear()
                    st.sidebar.success("Cache cleared successfully.")
                st.write("Session State:", st.session_state)
                st.write("Model System Prompt:", Settings.llm.system_prompt)
    # Handle user input
    if not "json_responses" in st.session_state:
        st.session_state.json_responses = []

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)


        # Use LlamaIndex to generate a response
        with st.chat_message("assistant"):
            with st.status("Thinking...", expanded=True) as status:
                st.write("Polling the LLM")
                response = st.session_state.chat_engine.chat(prompt)
                st.session_state.json_responses.append(json.loads(response.response))
                st.write("Loading the json")
                response_text = json.loads(response.response)["text"]
                st.write("Creating the response generator")
                response_generator = lambda: (time.sleep(0.05) or chunk for chunk in response_text.split('\n'))
                status.update(
                    label="Done Thinking!", state="complete", expanded=False
                )
            
            st.write_stream(response_generator())

            with st.status("Visualizing...", expanded=True) as status:
                st.write("Rendering the visualization")
                visualization = render_visualization(json.loads(response.response))
                status.update(
                    label="Done Visualizing!", state="complete", expanded=False
                )

            if visualization:
                visualization[0](*visualization[1:])

                # Adding the functions retrieved data to the index so the LLM can learn
                output = visualization[1:]
                if isinstance(*visualization[1:], pd.DataFrame):
                    for i in output:
                        index.insert(
                            Document(
                                text=i.to_string(index=False),
                                metadata={"source": json.loads(response.response)["visualization"]["type"]},
                            )
                        )
                elif isinstance(*visualization[1:], plt.Figure):
                    pass
                else:
                    index.insert(Document(text=output))

            # Append the assistant's response to the chat history
            message = {"role": "assistant", "content": response_text, "visualization": visualization}
            st.session_state.messages.append(message)
        
elif authentication_status is False:
    st.error("Invalid username or password.")
elif authentication_status is None:
    st.warning("Please enter your login credentials to access the AI Chat Bot.")