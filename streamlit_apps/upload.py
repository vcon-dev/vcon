import streamlit as st
import redis
import pandas as pd

"""

## Admin Portal

This is the admin portal for the system. It allows you to view the current configuration, and to make changes to it.

"""
# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)
config = r.json().get("config")

# Title of the app
st.title('vCon Importer')

# Add a file uploader to allow users to upload CSV files
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Read the file with Pandas
    df = pd.read_csv(uploaded_file) 

    # Display the DataFrame
    st.write(df)
