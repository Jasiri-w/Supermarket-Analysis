# Supermarket-Analysis

This Web App is a comprehensive data analysis dashboard designed for analyzing Supermarket sales. It offers detailed views for Customer Relationship Management (CRM), Sales Trends Analysis, and Product Analysis. Additionally, a fine-tuned LLM-based AI chat feature is in the works and will be available soon.

View the live application at: [Supermarket Analytics Dashboard](https://supermarket-analytics-dashboard.streamlit.app/)

This aims to help sales and management answer questions such as _who_ are our quality customers, _what_ are they buying and _how_ can we get them to buy more and build a relationship with our customers?

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

### 5. **AI Chat (Coming Soon)**
   - A fine-tuned language model (LLM) will be integrated into the app, providing an AI-powered chat feature. This AI assistant will specialize in sales data analysis and provide insightful responses related to customer trends, product performance, and overall supermarket analytics.

Data is based on real supermarket data courtesy of a supermarket in Kenya, personal information has been randomized for preview.

## Preview

![image](https://github.com/user-attachments/assets/60a3d512-af36-4150-89e2-d9077d817bb3)

![image](https://github.com/user-attachments/assets/b8d1480a-949a-45e3-84b6-9d973b41c8d4)

![image](https://github.com/user-attachments/assets/09f0bec2-ebc8-4318-9463-90c3a46a4e33)

... View more at [Supermarket Analytics Dashboard](https://supermarket-analytics-dashboard.streamlit.app/)

## Icons and Visuals
Icons used in this project are courtesy of [geticon](https://github.com/get-icon/geticon).
