import streamlit as st
import pymongo
import openai
import json

# Title and page layout
st.title("VCON INSPECTOR")

# Function to initialize the MongoDB connection
def get_mongo_client():
    return pymongo.MongoClient(**st.secrets["mongo_host"])

# Functin to return the summary of a vCon if it's available
def get_vcon_summary(vcon):
    if vcon:
        analysis = vcon.get('analysis', [])
        for a in analysis:
            if a.get('type') == 'summary':
                return a.get('body')
    return None

    
# Get the query parameter (uuid) from the URL
q = st.experimental_get_query_params()
uuid = q.get('uuid', [''])[0]

if uuid:
    st.write(f"INSPECTING VCON {uuid}")
    client = get_mongo_client()
    db = client[st.secrets["mongo_db"]["db"]]
    vcon = db[st.secrets["mongo_db"]["collection"]].find_one({'uuid': uuid})

    # ADD A BUTTON FOR DOWNLOADING THE VCON as JSON
    download = st.download_button(
        label="DOWNLOAD VCON",
        data=json.dumps(vcon),
        file_name=f"{uuid}.json",
        mime="application/json"
    )

    # ADD A BUTTON FOR ADDING THE UUID TO THE WORKBENCH
    if st.button("ADD TO INPUTS"):
        if 'vcon_uuids' not in st.session_state:
            st.session_state.vcon_uuids = []
        vcon_uuids = st.session_state.vcon_uuids
        vcon_uuids.append(uuid)
        st.session_state.vcon_uuids = vcon_uuids
        st.success(f"ADDED {uuid} TO WORKBENCH.")

    if vcon:
        try:
            created_at = vcon['created_at']
            updated_at = vcon.get("updated_at", "vCon has not been updated")

            # Make sure we don't throw errors here.
            parties = vcon.get("parties", [])
            dialog = vcon.get("dialog", [])
            attachments = vcon.get("attachments", [])
            analysis = vcon.get("analysis", [])

            # Display the summary of the vCon
            summary = get_vcon_summary(vcon)
            if summary:
                st.header("Summary")
                st.write(summary)

            # Create tabs for different sections
            tabs = st.tabs(['COMPLETE', 'ANALYSIS', 'DIALOG', 'PARTIES', 'ATTACHMENTS'])

            # Display content in respective tabs
            with tabs[1]:
                if analysis:
                    st.json(analysis)

            with tabs[2]:
                if dialog:
                    st.json(dialog)

            with tabs[3]:
                if parties:
                    st.json(parties)

            with tabs[4]:
                if attachments:
                    st.json(attachments)

            with tabs[0]:
                st.json(vcon)

        except KeyError:
            st.error("Invalid vCon, both created_at and uuid are required.")
    else:
        st.error(f"No vCon found with uuid: {uuid}")
else:
    st.write("PLEASE ENTER A VCON ID TO INSPECT")
    uuid = st.text_input("ENTER A VCON ID")
    if uuid:
        st.experimental_set_query_params(uuid=uuid)
