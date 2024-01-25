import streamlit as st
import pymongo
import json
import redis


# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    url = st.secrets["mongo_db"]["url"]
    return pymongo.MongoClient(url)

client = init_connection()
# Title of the app
st.title('EXPORT VCONS')
"""
Exports vCons from the database to either a 
single JSONL file or individual JSON files.
"""
output_format = st.radio("EXPORT FORMAT", ("JSONL", "JSON"))
DEFAULT_PATH = ""
path = st.text_input("ENTER THE DIRECTORY PATH", value=DEFAULT_PATH)
exporting = st.button("EXPORT VCONS", key="export")

if exporting: 
    # streamlit_app.py
    with st.spinner("EXPORTING VCONS"):
        db = client[str(st.secrets["mongo_db"]["db"])]
        vcons = db[st.secrets["mongo_db"]["collection"]].find()
        if output_format == "JSONL":
            # Open a file for writing in JSONL format
            with open(f"{path}output.jsonl", "w") as file:
                # Iterate through each JSON object in the array
                for vcon in vcons:
                    # Convert the JSON object to a string and write it to the file
                    json_line = json.dumps(vcon)
                    file.write(json_line + "\n")
        else:
            for vcon in vcons:
                uuid = vcon['uuid']
                filename = path + uuid + ".vcon.json"
                with open(filename, "w") as f:
                    f.write(json.dumps(vcon))
                    f.close()
    st.success("COMPLETE")

st.divider()
"***EXPORT TO REDIS***"

# Get the URL for the Redis instance
redis_url = st.text_input("ENTER THE REDIS URL", value="redis://redis:6379", key="redis_url_export")
if redis_url:
    if st.button("EXPORT VCONS", key="export_redis"):
        # Connect to Redis
        redis_client = redis.Redis.from_url(redis_url)
        db = client[str(st.secrets["mongo_db"]["db"])]
        vcons = db[st.secrets["mongo_db"]["collection"]].find()

        # So we can show progress, count the number of vCons
        count = db[st.secrets["mongo_db"]["collection"]].count_documents({})
        st.write(f"EXPORTING {count} VCONS")
        # Show progress
        progress_bar = st.progress(0)
        for index, vcon in enumerate(vcons):
            uuid = vcon['uuid']
            redis_client.json().set(f"vcon:{uuid}", "$", json.dumps(vcon))
            progress_bar.progress((index + 1) / count)

        st.success("COMPLETE")