import streamlit as st
import pymongo
import json

# Enable large files
st.set_option('deprecation.showfileUploaderEncoding', False)

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(**st.secrets["mongo_host"])

client = init_connection()

st.title("Import vCons from a JSONl File")

uploaded_file = st.file_uploader("Upload a JSONL file")
overwrite_data = st.checkbox("Overwrite all existing data")

if uploaded_file is not None:
    if st.button("Upload and Insert"):
        db = client[st.secrets["mongo_db"]['db']]
        collection = db[st.secrets["mongo_db"]['collection']]
        if overwrite_data:
            collection.drop()
        for i, line in enumerate(uploaded_file):
            try:
                document = json.loads(line)
                collection.replace_one({'_id': document['uuid']}, document, upsert=True)
            except json.JSONDecodeError as e:
                st.warning(f"Skipped invalid JSON, index {i}")
                continue
        st.success("Data inserted successfully!")
