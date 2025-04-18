from datetime import datetime, date
import inspect
import json
from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex, Document, Settings, SimpleDirectoryReader, get_response_synthesizer
import matplotlib.pyplot as plt
import os
import openai
import pandas as pd
import streamlit as st
import time
from utils.auth import get_authenticator
from utils.database import fetch_data
from utils.auxiliary import IdentityStatus, stream_generator


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

print(f"Temp File Location in Settings: {Settings.tokenizer_cache_dir}")
print(f"Temp File Location in OS ENV: {os.getenv('LLAMA_INDEX_CACHE_DIR')}")

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

from utils.models import get_recommendations

st.title("AI Chat Bot")
st.logo(
    st.secrets["LOGO"],
    icon_image=st.secrets["ICON"],
)
st.write('This chatbot is created using ChatGPT.')
debug_mode = st.secrets["DEBUG_MODE"]
sales_data_frame, _ = load_sales_data()
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
    "get_recommendations": get_recommendations,
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
            #"Customer Information": "SELECT * FROM public.customers",
            #"Product Inventory": "SELECT * FROM public.product LIMIT 100",
            #"Transactions": "SELECT * FROM public.transactions LIMIT 100",
            #"transaction_details": "SELECT * FROM public.transactiondetails LIMIT 100",
            #"payment_data": "SELECT * FROM public.payment LIMIT 100",
        }

        query_descriptions = {
           "Customer Information": (
                "This data represents detailed the cumulative information about each of our customers from the database, not individual transactions, including the following fields: "
                "- phone: The customer's phone number. "
                "- customer_name: Name of the customer. If the name of the customer is 'Cash Sale' then they are an anonymous customer without a credit account."
                "- total_payments: The total number of payments made by the customer since being with the company. "
                "- total_paid: The total amount paid by the customer over the course of their history with us. "
                "- first_payment_date: Date of the first payment they ever made at the business. "
                "- last_payment_date: Date of the last payment they ever made at the business. "
                "- total_purchases: Total number of purchases made by the customer over the course of their time with us. "
                "- first_purchase_date: Date of the first recorded purchase. "
                "- last_purchase_date: Date of the last recorded purchase. "
                "- most_purchased_item: Name of the most frequently purchased item. "
                "- most_purchased_item_count: The number of times the purchased their most purchased item at our business. "
                "- purchase_duration_days: The number of days between their first and last purchase, in otherwords, their longevity with us. "
                "- customer_email: Email of the customer. "
                "- customer_address: Address of the customer."
            ),
            "Product Inventory": (
                "This data represents detailed information about the product inventory from the database, including the following fields: "
                "- productno: This is the product number, a unique identifier for each product. "
                "- description: Name or description of the product. "
                "- saleprice: The price at which the product is sold to customers. "
                "- buyprice: The cost incurred by the company to purchase the product. "
                "- purchase_count: The total number of times the product has been purchased by customers."
            ),            
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

        product_info = get_all_customer_data()
        documents.append(
            Document(
                text=product_info.to_string(index=False),
                metadata={"Source": "Customer Information", "Description": query_descriptions["Product Inventory"], "Type": "Database Data"},
            )
        )

        product_info = get_products()
        documents.append(
            Document(
                text=product_info.to_string(index=False),
                metadata={"Source": "Product Inventory", "Description": query_descriptions["Product Inventory"], "Type": "Database Data"},
            )
        )
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
    all_documents = static_docs + dynamic_docs + function_registry_docs

    # Set LlamaIndex's LLM settings
    Settings.llm = OpenAI(
        model="ft:gpt-4o-mini-2024-07-18:uncle-suave:analytics-helper:AqFcIXps",
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
    # LlamaIndex-level protection
    Settings.tokenizer_cache_dir = "/tmp/llamaindex_cache"

    # Build and return the index
    index = VectorStoreIndex.from_documents(all_documents)
    return index

def render_visualization(llm_response):
    """
    Render visualizations based on the LLM response. Utilizes all imported functions.
    :param llm_response: Dictionary with keys 'text' and optional 'visualization'.
    """
    # Auxiliary function to cast parameters to their respective types
    def cast_params_to_types(func, data_params):
        sig = inspect.signature(func)
        type_hints = {
            name: param.annotation
            for name, param in sig.parameters.items()
            if param.annotation is not inspect.Parameter.empty
        }

        filtered_params = {
            k: type_hints[k](v) if k in type_hints else v
            for k, v in data_params.items()
        }

        return filtered_params

    visualization = llm_response.get("visualization", {})

    # Handle visualizations
    if visualization:
        vis_type = visualization.get("type")
        data_params = visualization.get("data_params", {})

        # Find and execute the function
        visualization_function = function_registry.get(vis_type)
        if visualization_function:
            if "df" in visualization_function.__code__.co_varnames:
                try:
                    st.session_state.start_date = data_params.get("start_date") if "start_date" in data_params else sales_data_frame.index.min().date()
                    st.session_state.end_date = data_params.get("end_date") if "end_date" in data_params else sales_data_frame.index.max().date()
                    
                    filtered_params = {k: v for k, v in data_params.items() if k not in ["start_date", "end_date"]}
                    if filtered_params:
                        if visualization_function == get_recommendations:
                            filtered_params = cast_params_to_types(visualization_function, filtered_params)
                            output = visualization_function(**filtered_params, df=get_products())
                            print(f"Output: {output}")
                        return (st.dataframe, output)
                    else:
                        output = visualization_function(sales_data_frame)
                        # Needs to be implemented and tested for all relevant functions
                    return (st.dataframe, sales_data_frame[(sales_data_frame.index >= pd.to_datetime(st.session_state.start_date)) & (sales_data_frame.index <= pd.to_datetime(st.session_state.end_date))])
                except Exception as e:
                    #st.error(f"Error executing {vis_type}: {e} \n {llm_response}")
                    return None
            elif visualization_function.__code__.co_varnames[0] == "phone":
                try:
                    if data_params.get("phone") is None:
                        #st.error(f"Phone number not provided for visualization {vis_type}.")
                        return None
                    output = visualization_function(data_params.get("phone"))
                    return (st.dataframe, output)
                except Exception as e:
                    print(f"Error executing {vis_type}: {e} \n {llm_response}")
                    return None
            else:
                try:
                    output = visualization_function(**data_params)
                    print(f"Data Parameters - {data_params}")
                    if isinstance(output, pd.DataFrame):
                        return (st.dataframe, output)
                    elif isinstance(output, plt.Figure):
                        return (st.pyplot, output)
                    else:
                        return (st.write, output)
                except Exception as e:
                    #st.error(f"Error executing {vis_type}: {e} \n {llm_response}")
                    print(f"Error executing {vis_type}: {e} \n {llm_response}")
                    return None
        else:
            print(f"Visualization type '{vis_type}' not recognized. \n {llm_response}")
            return None
    else:
        st.write(f"No visualization requested.")
        return None



# Load the index for use in the chat engine
index = load_data()
response_synthesizer_refine = get_response_synthesizer(response_mode="refine", structured_answer_filtering=False) # This is used to ensure that it is true to the context i.e. it is based on our RAGged stuff information
response_synthesizer_compact = get_response_synthesizer(response_mode="compact", structured_answer_filtering=False) # This is used to ensure that it is true to the context i.e. it is based on our RAGged stuff information

if "chat_engine" not in st.session_state.keys():  # Initialize the chat engine
    st.session_state.chat_engine = index.as_chat_engine(
        chat_mode="condense_plus_context", verbose=True, streaming=True
    )

# Authenticate user
authenticator = get_authenticator()
if authenticator:
    authenticator.login(key='Login1',location= 'main')

# Safely access session state keys with default values
authentication_status = st.session_state.get('authentication_status', None)
name = st.session_state.get('name', "Guest")
username = st.session_state.get('username', "guest")

if authentication_status:
    st.success(f"Welcome, {name}!")
    st.write(f"Temp File Location: {Settings.tokenizer_cache_dir}")
    st.write(f"Temp File Location: {os.getenv('LLAMA_INDEX_CACHE_DIR')}")
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

        StatusHandler = st.status if debug_mode else IdentityStatus
        # Use LlamaIndex to generate a response
        with st.chat_message("assistant"):
            st.toast("Polling the LLM ...")
            
            response = st.session_state.chat_engine.chat(prompt)
            print(f"LLM  Final Response: {response}")
            st.session_state.json_responses.append(json.loads(response.response))
            response_text = json.loads(response.response)["text"]
            st.toast("Done thinking!")
            
            st.write_stream(stream_generator(response_text))

            st.toast("Rendering any visualizations")
            visualization = render_visualization(json.loads(response.response))

            if visualization:
                visualization[0](*visualization[1:])

                # Adding the functions retrieved data to the index so the LLM can learn
                # This was a really cool idea to have the LLM learn from the structured data progressively
                # However without Tight Knit Ingestion Control via Lamma Index, I fear this could become an
                # efficiency bottleneck (nightmare)
                
                # output = visualization[1:]
                # if isinstance(*visualization[1:], pd.DataFrame):
                #     print("Learning from dataframe")
                #     vis_type = json.loads(response.response)["visualization"]["type"]
                #     if not ("plot" in vis_type or "phone" in vis_type or "recommendations" in vis_type or "product" in vis_type):
                #         for i in output:
                #             index.insert(
                #                 Document(
                #                     text=i.to_string(index=False),
                #                     metadata={"source": json.loads(response.response)["visualization"]["type"]},
                #                 )
                #             )
                # elif isinstance(*visualization[1:], plt.Figure):
                #     print("Learning from plot")
                #     pass
                # else:
                #     print("Learning from other formats")
                #     index.insert(Document(text=output))

            # Append the assistant's response to the chat history
            message = {"role": "assistant", "content": response_text, "visualization": visualization}
            st.session_state.messages.append(message)
        
elif authentication_status is False:
    st.error("Invalid username or password.")
elif authentication_status is None:
    st.warning("Please enter your login credentials to access the AI Chat Bot.")