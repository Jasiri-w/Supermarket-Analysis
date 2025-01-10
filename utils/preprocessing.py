import pandas as pd
from datetime import datetime
import streamlit as st

def preprocess_data(df):
    """
    Preprocesses the input DataFrame by performing the following steps:
    1. Logs the initial DataFrame.
    2. Creates a copy of the DataFrame.
    3. Ensures the 'datein' column exists and converts it to datetime format.
    4. Removes rows where 'datein' is null.
    5. Filters out rows with 'datein' earlier than 2019-01-01.
    6. Sets 'datein' as the index of the DataFrame.
    Args:
        df (pd.DataFrame): The input DataFrame to preprocess.
    Returns:
        pd.DataFrame: The preprocessed DataFrame with 'datein' as the index.
                      If an error occurs, returns the original DataFrame.
    Raises:
        KeyError: If the 'datein' column is missing from the DataFrame."""
 
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
