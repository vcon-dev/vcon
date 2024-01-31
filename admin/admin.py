import streamlit as st
import redis
import pandas as pd
import pymongo
import json
import os

"""

## Admin Portal

This is the admin portal for the system. It allows you to view the current configuration, and to make changes to it.

"""
# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    url = st.secrets["mongo_db"]["url"]
    return pymongo.MongoClient(url)

client = init_connection()

# Print the current directory to markdown
st.markdown(f"Current directory: {os.getcwd()}")

# Print the contents of the directory to markdown
st.markdown(f"Contents of the directory: {os.listdir()}")



# Current directory in the container is /app
# Check if the file exists
if os.path.isfile("custom_info.md"):
    # Open the file and read its contents
    with open("custom_info.md", "r") as file:
        contents = file.read()
else:
    contents = "No custom information available."

# Display the contents in the Streamlit app
st.markdown(contents)



col1, col2 = st.columns(2)
with col1:
    st.header("Current Configuration")
    st.write("The current configuration of the system is displayed below.")
    st.write("To make changes, click on the 'Edit Configuration' button.")
    if st.button("Edit Configuration"):
        st.write("You clicked the button!")
with col2:
    st.header("System Status")
    st.write("The current status of the system is displayed below.")
    st.write("To make changes, click on the 'Edit Status' button.")
    if st.button("Edit Status"):
        st.write("You clicked the button!")

# Add three tabs
st.header("Recent vCons")   

# Limit to vCons that have a summary
if st.checkbox("Show only vCons with summaries"):
    only_summary = {
        'analysis.type': 'summary'
    }
else:
    only_summary = {}

num_vcons = st.number_input("Number of vCons to display", min_value=1, max_value=1000, value=10)
db = client[str(st.secrets["mongo_db"]["db"])]
vcons = db[st.secrets["mongo_db"]["collection"]].find(only_summary).sort("created_at", -1).limit(num_vcons)
for v in vcons:
    # For each vCon, display the created_at timestamp, and a link to the vCon in the inspect page.
    # First, make a human readable timestamp
    created_at = pd.to_datetime(v['created_at'])
    st.write(f"{created_at} - [Inspect vCon](/inspect?uuid={v['uuid']})")