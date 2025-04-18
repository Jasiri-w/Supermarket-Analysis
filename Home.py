import streamlit as st
import streamlit_authenticator as stauth

import os
from llama_index.core import Settings

# Environment-level protection
os.environ["LLAMA_INDEX_CACHE_DIR"] = "/tmp/llamaindex_cache"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# LlamaIndex-level protection
Settings.tokenizer_cache_dir = "/tmp/llamaindex_cache"

from utils.auth import get_authenticator

st.set_page_config(
    page_title="Supermarket Analysis Dashboard",
    page_icon=st.secrets["FAVICON"],
    layout="centered",
)
st.title("Supermarket Analysis Dashboard")
st.sidebar.markdown("# Home")
st.logo(
    st.secrets["LOGO"],
    icon_image=st.secrets["ICON"],
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
    st.sidebar.success("You are logged in.")

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True, height=140):
            st.page_link("pages/Customer_Relationship_Manager.py", label="Customer Relationship Manager", icon="🙍", use_container_width=True)
            st.markdown("Monitor customer interactions and manage relationships.")
        
        with st.container(border=True, height=140):
            st.page_link("pages/Product_Analysis.py", label="Product Analysis Dashboard", icon="🛍️", use_container_width=True)
            st.markdown("Analyze product performance and sales metrics.")

    # Column 2
    with col2:
        with st.container(border=True, height=140):
            st.page_link("pages/Sales_Trend_Analysis.py", label="Sales Trends Dashboard", icon="📈", use_container_width=True)
            st.markdown("Track and analyze sales trends over time.")
        
        with st.container(border=True, height=140):
            st.page_link("pages/AI_Chat_Bot.py", label="AI Chat Bot", icon="🤖", use_container_width=True)
            st.markdown("TUpdated! Interact with the AI chatbot for better understanding of your data.")

elif authentication_status is False:
    st.error("Invalid username or password.")
elif authentication_status is None:
    st.warning("Please enter your login credentials.")

#st.sidebar.title("Navigation")
#page = st.sidebar.selectbox("Choose a Dashboard", ["Sales Trend Analysis"])

#if page == "Sales Trend Analysis":
#    import pages.sales_trend_analysis