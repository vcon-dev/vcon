import streamlit as st
import pymongo
import json
import redis
import boto3

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    url = st.secrets["mongo_db"]["url"]
    return pymongo.MongoClient(url)

client = init_connection()

st.title("IMPORT VCONS")

tab_names= ["UPLOAD ONE", "UPLOAD JSONL", "URL", "TEXT", "REDIS", "S3"]
upload_tab, jsonl_tab, url_tab, text_tab, redis_tab, s3_tab = st.tabs(tab_names)

with upload_tab:
    "**UPLOAD A SINGLE VCON FILE**"

    # Allow the user to upload a single JSON file
    uploaded_file = st.file_uploader("UPLOAD", type=["json", "vcon"])
    if uploaded_file is not None:
        if st.button("UPLOAD AND INSERT"):
            db = client[st.secrets["mongo_db"]['db']]
            collection = db[st.secrets["mongo_db"]['collection']]
            try:
                document = json.load(uploaded_file)
                collection.replace_one({'_id': document['uuid']}, document, upsert=True)
                st.success("INSERTED SUCCESSFULLY!")
            except json.JSONDecodeError as e:
                st.warning("INVALID JSON")
                st.error(e)

with jsonl_tab:
    "**UPLOAD BULK VCON**"

    uploaded_file = st.file_uploader("UPLOAD JSONL", type="jsonl, vconl")

    if uploaded_file is not None:
        if st.button("UPLOAD AND INSERT"):
            db = client[st.secrets["mongo_db"]['db']]
            collection = db[st.secrets["mongo_db"]['collection']]
            for i, line in enumerate(uploaded_file):
                try:
                    document = json.loads(line)
                    collection.replace_one({'_id': document['uuid']}, document, upsert=True)
                except json.JSONDecodeError as e:
                    st.warning(f"SKIPPED INVALID JSON, INDEX {i}")
                    continue
            st.success("INSERTED SUCCESSFULLY!")

with url_tab:
    # Import from a URL
    "**IMPORT FROM URL**"
    url = st.text_input("ENTER URL")
    if url:
        if st.button("IMPORT"):
            db = client[st.secrets["mongo_db"]['db']]
            collection = db[st.secrets["mongo_db"]['collection']]
            try:
                document = json.load(url)
                collection.replace_one({'_id': document['uuid']}, document, upsert=True)
                st.success("INSERTED SUCCESSFULLY!")
            except json.JSONDecodeError as e:
                st.warning("INVALID JSON")
                st.error(e)

with text_tab:
    # Import from a URL
    "**IMPORT FROM TEXT**"
    text = st.text_area("ENTER TEXT")
    if text:
        if st.button("IMPORT"):
            db = client[st.secrets["mongo_db"]['db']]
            collection = db[st.secrets["mongo_db"]['collection']]
            try:
                document = json.loads(text)
                collection.replace_one({'_id': document['uuid']}, document, upsert=True)
                st.success("INSERTED SUCCESSFULLY!")
            except json.JSONDecodeError as e:
                st.warning("INVALID JSON")
                st.error(e)

with redis_tab:
    # Import from REDIS
    "**IMPORT FROM REDIS**"
    redis_url= st.text_input("ENTER REDIS URL")
    if redis_url:
        if st.button("IMPORT"):
            db = client[st.secrets["mongo_db"]['db']]
            collection = db[st.secrets["mongo_db"]['collection']]

            # Connect to the REDIS server, and find all the keys with the pattern "vcon:*"
            
            redis_client = redis.Redis.from_url(redis_url)
            keys = redis_client.keys("vcon:*")
            for key in keys:
                vcon = redis_client.json().get(key)
                try:
                    collection.replace_one({'_id': vcon['uuid']}, vcon, upsert=True)
                except json.JSONDecodeError as e:
                    st.warning("INVALID JSON")
                    st.error(e)

with s3_tab:
    "**IMPORT S3 BUCKET**"
    # For inputs, use the 
    AWS_ACCESS_KEY_ID = st.secrets['aws']["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY = st.secrets['aws']["AWS_SECRET_ACCESS_KEY"]
    AWS_DEFAULT_REGION = st.secrets['aws']["AWS_DEFAULT_REGION"]
    s3_bucket = st.text_input("ENTER S3 BUCKET")
    s3_path = st.text_input("ENTER S3 PATH")
    if s3_bucket:
        if st.button("IMPORT"):
            db = client[st.secrets["mongo_db"]['db']]
            collection = db[st.secrets["mongo_db"]['collection']]
            s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_DEFAULT_REGION)

            # Connect to the S3 bucket and find all the keys with the pattern "vcon:*"
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=s3_bucket, Prefix=s3_path)

            # Count the number of vCons we're importing overall
            count = 0
            for index, page in enumerate(pages):
                for obj in page['Contents']:
                    key = obj['Key']
                    if key.endswith(".vcon"):
                        count += 1
            st.write(f"IMPORTING {count} VCONS")
            # Show progress
            progress_bar = st.progress(0)
            upload_count = 0
            for index, page in enumerate(pages):
                for obj in page['Contents']:
                    # increment the progress bar
                    key = obj['Key']
                    if key.endswith(".vcon"):
                        try:
                            vcon = s3_client.get_object(Bucket=s3_bucket, Key=key)
                            vcon = json.loads(vcon['Body'].read())
                            result = collection.replace_one({'_id': vcon['uuid']}, vcon, upsert=True)
                            upload_count += 1
                            progress_bar.progress(upload_count / count)
                        except json.JSONDecodeError as e:
                            st.warning("INVALID JSON")
                            st.error(e)
                    else:
                        st.warning(f"SKIPPING {key}")
            st.success("COMPLETE")