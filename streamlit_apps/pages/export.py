import streamlit as st
import pymongo
import json


# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(**st.secrets["mongo_host"])

client = init_connection()
# Title of the app
st.title('vCon Exporter')
"""
Exports vCons from the database to either a 
single JSONL file or individual JSON files.
"""
output_format = st.radio("Export Format", ("JSONL", "JSON"))
DEFAULT_PATH = "/Users/thomashowe/Downloads/"
path = st.text_input("Enter the directory path", value=DEFAULT_PATH)
exporting = st.button("Export vCons")

if exporting: 
    # streamlit_app.py
    with st.spinner("Exporting vCons"):
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
    st.success("Complete!")