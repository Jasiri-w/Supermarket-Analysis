# Supermarket-Analysis

![image](https://github.com/user-attachments/assets/b8d1480a-949a-45e3-84b6-9d973b41c8d4)

View live: [Supermarket Analytics Dashboard](https://supermarket-analytics-dashboard.streamlit.app/)

This Web App is a comprehensive data analysis dashboard designed for analyzing Supermarket sales. It offers detailed views for Customer Relationship Management (CRM), Sales Trends Analysis, and Product Analysis. Additionally, a fine-tuned LLM-based AI chat feature is in the works and will be available soon.


An authentication system is modelled in the application, but turned off for the time being. The test users have username:*John* and password:*johnpass*

This aims to help sales and management answer questions such as _who_ are our quality customers, _what_ are they buying and _how_ can we get them to buy more and build a relationship with our customers?

Read the [code walkthrough here on Medium](https://medium.com/@jasiri.w/building-a-data-analysis-dashboard-with-python-9f4f35a8289f)

## Tech Stack

This project is developed using:
- <a href="https://www.python.org/" title="Python"><img src="https://github.com/get-icon/geticon/raw/master/icons/python.svg" alt="Python" width="21px" height="21px"></a> Python for scripting and data manipulation.
- <a href="https://dev.mysql.com/" title="MySQL"><img src="https://github.com/get-icon/geticon/raw/master/icons/mysql.svg" alt="MySQL" width="21px" height="21px"></a> MySQL and <a href="https://www.postgresql.org/" title="PostgreSQL"><img src="https://github.com/get-icon/geticon/raw/master/icons/postgresql.svg" alt="PostgreSQL" width="21px" height="21px"></a> PostgreSQL for relational database management.
- **Pandas** for data manipulation and analysis.
- **Seaborn** and **Matplotlib** for data visualization.
- **Scikit-learn** for implementing machine learning models.
- **Joblib** for model serialization and deployment.
- **Streamlit** for the backend and UI of the application.
- **Supabase** for handling database interactions.
- **Streamlit Community Cloud** for hosting the application.
- **LlamaIndex** for indexing data and enabling natural language queries over internal supermarket documents and reports.
- **OpenAI (GPT-3.5)** for generating intelligent responses grounded in indexed sales and customer data.


## Key Features

### 1. **Customer Relationship Management (CRM)**
   - **Daily Customer Insights:** View and analyze daily customer interactions, purchase behavior, and overall engagement.
   - **Customer Segmentation:** Easily segment customers based on their purchasing patterns and other criteria.

### 2. **Sales Trends Analysis**
   - **Sales Performance:** Track and visualize sales performance over time, identifying peaks, trends, and seasonal behaviors.
   - **Revenue Breakdown:** Get a clear view of revenue contributions from different product categories.

### 3. **Product Analysis**
   - **Top Products:** Identify and analyze the best-performing products in the supermarket.
   - **Product Segmentation:** View sales performance and other metrics for specific product segments.

### 4. **Product Recommendation System**
   - This app features a content-based filtering product recommendation system, leveraging data-driven insights to suggest products that customers are likely to purchase based on their past behaviors and preferences. The recommendation engine is built using:
     - **Pandas** for data processing.
     - **Scikit-learn** for implementing the content-based filtering algorithm.
     - **Joblib** for model persistence and fast retrieval.
     - View the notebook used to train this model [here](https://colab.research.google.com/drive/1-hjoyNgRj2KtlPsl87aTI0xqu0VTwx4M?usp=sharing)


### 5. **AI Chat Assistant (New in 2025!)**
An AI-powered assistant is integrated into the application to provide natural language querying capabilities for supermarket analytics. Powered by **OpenAI's GPT-3.5** and **LlamaIndex**, the assistant allows users to ask business questions such as:
- "What were our best-selling products last month?"
- "Who are our top customers this week?"
- "Which payment method brings the highest revenue?"

The assistant retrieves answers by:
- Indexing structured reports and insights from the supermarket dataset using **LlamaIndex** (vector-based search).
- Generating context-aware responses using **GPT-3.5** with a low-temperature setting to ensure accuracy and clarity.

This makes sales analytics more intuitive and accessible to non-technical users through a simple chat interface embedded in the Streamlit dashboard.
This assistant has been fine-tuned using a carefully curated dataset of supermarket-related queries and structured analytical tasks. It responds with both visual insights and concise text, formatted in a developer-friendly JSON format.


## Preview

![image](https://github.com/user-attachments/assets/60a3d512-af36-4150-89e2-d9077d817bb3)

![image](https://github.com/user-attachments/assets/b8d1480a-949a-45e3-84b6-9d973b41c8d4)

![image](https://github.com/user-attachments/assets/09f0bec2-ebc8-4318-9463-90c3a46a4e33)

... View more at [Supermarket Analytics Dashboard](https://supermarket-analytics-dashboard.streamlit.app/)

Example questions you can ask the AI Assistant:

- What are the top 10 best-selling items?
- Show me the sales trend over the last 3 months.
- What did the customer with phone number 0712345678 buy last week?
- Which product category brings in the most revenue?
- Show me all customers who have shopped more than 10 times.

## Icons and Visuals
Icons used in this project are courtesy of [geticon](https://github.com/get-icon/geticon).
