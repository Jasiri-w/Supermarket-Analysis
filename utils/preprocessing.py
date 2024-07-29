import pandas as pd
from datetime import datetime
import streamlit as st

def preprocess_data(df):
    print(f"{datetime.now()} Preprocessing:\n{df}")
    df2 = df.copy()
    print("df2 copied")
    # Ensure 'datein' column exists and is converted to datetime
    try:
        if 'datein' in df.columns:
            df2['datein'] = pd.to_datetime(df2['datein'], errors='coerce')
            print("df2 datetimed")
            df2 = df2[df2['datein'].notnull()]  # Remove rows where 'datein' is null
            print("df2 unnulled")
            df2 = df2[df2['datein'] >= pd.to_datetime('2019-01-01')]  # Filter out dates earlier than 2019-01-01
            print("df2 filtered past 2019")
            df2.set_index('datein', inplace=True)  # Set 'datein' as the index
            print("df2 date indexed")
        else:
            raise KeyError("The 'datein' column is missing from the DataFrame.")
    except Exception as e:
        st.cache_data.clear()
        return df
    
    return df2
