import streamlit as st
import redis
import pandas as pd
import pymongo
import json

"""

## Admin Portal

This is the admin portal for the system. It allows you to view the current configuration, and to make changes to it.

"""
# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(**st.secrets["mongo_host"])

client = init_connection()

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