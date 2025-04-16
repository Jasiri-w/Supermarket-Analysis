import pandas as pd
import joblib
import streamlit as st

cosine_sim = joblib.load(st.secrets["CBF_MODEL_PATH"])
                    
def get_recommendations(productno: int, df, cosine_sim=cosine_sim):
    '''
    Get product recommendations based on cosine similarity, purchase count, and sales margin.
    
    Parameters:
        productno (int): The Number ID of the product for which recommendations are to be generated.
        df (pd.DataFrame): DataFrame containing product data with columns 'productno', 'saleprice', 'buyprice', and 'purchase_count'.
        cosine_sim (np.ndarray): Precomputed cosine similarity matrix. Defaults to the matrix loaded from disk
    
    Returns:
        pd.DataFrame: DataFrame containing the top 10 recommended products, ranked by a weighted score of normalized purchase count and sales margin.
    '''

    try:
        idx = df[df['productno'] == productno].index[0]
    except IndexError:
        print(f"Product with ProductNo {productno} not found in the dataset.")
        return pd.DataFrame()

    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:11]  # Get top 10 recommendations
    
    product_indices = [i[0] for i in sim_scores]
    
    # Include purchase count and sales margin for ranking
    recommendations = df.iloc[product_indices].copy()
    
    # Calculate sales margin
    recommendations['sales_margin'] = recommendations['saleprice'] - recommendations['buyprice']
    
    # Normalize purchase_count and sales_margin
    recommendations['norm_purchase_count'] = (recommendations['purchase_count'] - recommendations['purchase_count'].min()) / (recommendations['purchase_count'].max() - recommendations['purchase_count'].min())
    recommendations['norm_sales_margin'] = (recommendations['sales_margin'] - recommendations['sales_margin'].min()) / (recommendations['sales_margin'].max() - recommendations['sales_margin'].min())
    
    # Calculate weighted score (you can adjust the weights as needed)
    recommendations['score'] = 0.6 * recommendations['norm_purchase_count'] + 0.4 * recommendations['norm_sales_margin']
    
    recommendations = recommendations.sort_values(by='score', ascending=False)
    
    return recommendations