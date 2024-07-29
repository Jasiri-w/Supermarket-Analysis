import streamlit as st

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
        st.markdown("Interact with the AI chatbot for understanding your data.")

#st.sidebar.title("Navigation")
#page = st.sidebar.selectbox("Choose a Dashboard", ["Sales Trend Analysis"])

#if page == "Sales Trend Analysis":
#    import pages.sales_trend_analysis
