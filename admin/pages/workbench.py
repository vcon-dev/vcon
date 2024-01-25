import streamlit as st
import pymongo
import json

# This code is for v1 of the openai package: pypi.org/project/openai
from openai import OpenAI
OPENAI_API_KEY="sk-xxxxxxxxxxx"
open_ai_client = OpenAI(
    api_key=OPENAI_API_KEY
)

# Title and page layout
st.title("VCON WORKBENCH")

# Function to initialize the MongoDB connection
def get_mongo_client():
    url = st.secrets["mongo_db"]["url"]
    return pymongo.MongoClient(url)

# Functin to return the summary of a vCon if it's available
def get_vcon_summary(vcon):
    if vcon:
        analysis = vcon.get('analysis', [])
        for a in analysis:
            if a.get('type') == 'summary':
                return a.get('body')
    return None

def get_vcon_transcript(vcon):
    if vcon:
        analysis = vcon.get('analysis', [])
        for a in analysis:
            if a.get('type') == 'transcript':
                return a.get('body')
    return None

# We are going to keep two different arrays of state.
# The first is a list of vCons that we are going to analyze.
# The second is a list of Prompts to give to OpenAI.
if 'vcon_uuids' not in st.session_state:
    st.session_state.vcon_uuids = []
if 'prompts' not in st.session_state:
    st.session_state.prompts = []

vcon_uuids = st.session_state.vcon_uuids
prompts = st.session_state.prompts

# Make three tabs, one for the vCons, one for the prompts, and one for the results
tab_names = ["ADD VCONS", "CONFIGURE PROMPTS", "RUN ANALYSIS"]
vcon_tab, prompt_tab, results_tab = st.tabs(tab_names)

with vcon_tab: 
    "**ADD INPUT BY ID**"
    uuid = st.text_input("ENTER A VCON ID")
    if st.button("ADD TO INPUTS", key=uuid):
        vcon_uuids.append(uuid)
        st.session_state.vcon_uuids = vcon_uuids
        st.rerun()
    st.divider()
    # Break the page into two columns
    col1, col2 = st.columns(2)
    with col1:
        pick_random = st.button("FIND RANDOM VCON")
        if pick_random:
            st.rerun()

        summary_only = st.checkbox("ONLY PICK VCONS WITH SUMMARIES")

        # Get a random vCon from the database
        mongo_client = get_mongo_client()
        db = mongo_client[st.secrets["mongo_db"]["db"]]
        if summary_only:
            vcon = db[st.secrets["mongo_db"]["collection"]].aggregate([{'$match': {'analysis.type': 'summary'}}, {'$sample': {'size': 1}}]) 
        else:
            vcon = db[st.secrets["mongo_db"]["collection"]].aggregate([{'$sample': {'size': 1}}])
        vcon = list(vcon)[0]

        # Show the summary of the vCon, if it's available.
        summary = get_vcon_summary(vcon)
        if summary:
            st.markdown(f"> {summary}")

    with col2:
        # Show the created_at and updated_at timestamps
        created_at = vcon['created_at']
        updated_at = vcon.get("updated_at", "vCon has not been updated")
        st.markdown(f"**UUID**: {vcon['uuid']}")
        st.markdown(f"**Created at**: {created_at}")
        st.markdown(f"**Updated at**: {updated_at}")


        # Show a link to the detail page
        st.markdown(f"[VCON DETAILS](/inspect?uuid={vcon['uuid']})")
        add_random = st.button("ADD TO INPUTS", key="random") 
        # Also show a link to the vCon 
        if add_random:
            vcon_uuids.append(vcon['uuid'])
            st.session_state.vcon_uuids = vcon_uuids
            st.success(f"ADDED {vcon['uuid']} TO WORKBENCH")



    st.divider()
    st.subheader(f"CURRENT VCON INPUTS ({len(vcon_uuids)})")

    mongo_client = get_mongo_client()
    db = mongo_client[st.secrets["mongo_db"]["db"]]

    for vcon_uuid in vcon_uuids:
        st.markdown(f"**vCon UUID**: {vcon_uuid}")
        vcon = db[st.secrets["mongo_db"]["collection"]].find_one({'uuid': vcon_uuid})
        # Show the summary of the vCon, if it's available.
        summary = get_vcon_summary(vcon)
        if summary:
            st.markdown(f"> {summary}")

        # display a link to the vCon
        st.markdown(f"[VCON DETAILS](/inspect?uuid={vcon_uuid})")
        
        # Make a delete button to take it out of the list
        if st.button("DELETE", key=vcon_uuid):
            vcon_uuids.remove(vcon_uuid)
            st.session_state.vcon_uuids = vcon_uuids
            st.success(f"DELETED {vcon_uuid} FROM WORKBENCH")
            st.rerun()


# Show the prompts tab
with prompt_tab:
    # Add a prompt, including system prompt, user prompt, model name and temperature
    system_prompt = st.text_area("SYSTEM PROMPT", "The following is a vCon conversation between two parties, captured in a JSON. The parties array is a list of participants; the dialog array are the recordings, emails and transcripts. The analysis array contains transcripts and summaries and other analysis types. The attachments array is a list of documents describing the context of the conversation.")
    user_prompt = st.text_area("USER PROMPT", "Summarize this conversation.")
    model_names = ["gpt-4-1106-preview", "gpt-4", "gpt-4-32k", "gpt-3.5-turbo-1106", "gpt-3.5-turbo"]
    model_name = st.selectbox("MODEL NAME", model_names)
    temperature = st.slider("TEMPERATURE", 0.0, 1.0, 0.5, 0.01)
    input_types = ["complete", "summary", "transcript"]
    input_type = st.selectbox("INPUT TYPE", input_types)

    prompt = {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "model_name": model_name,
        "temperature": temperature
    }
    prompts.append(prompt)
    st.session_state.prompts = prompts


# Show the results tab
with results_tab:
    if st.button(f"RUN ANALYSIS FOR {len(vcon_uuids)} VCONS"):
        if st.expander("Show Prompt"):
            st.code(f"""
                model_name = {model_name}
                temperature = {temperature}
                system_prompt = {system_prompt}
                user_prompt = {user_prompt}
                input_type = {input_type}
                """)
        for vcon_uuid in vcon_uuids:
            # Get the content, either the transcript or the summary or the dialog
            mongo_client = get_mongo_client()
            db = mongo_client[st.secrets["mongo_db"]["db"]]
            vcon = db[st.secrets["mongo_db"]["collection"]].find_one({'uuid': vcon_uuid})
            match input_type:
                case "complete":
                    content = json.dumps(vcon)
                case "summary":
                    content = get_vcon_summary(vcon)
                case "transcript":
                    content = get_vcon_transcript(vcon)

            # Call open AI to complete the prompt
            st.subheader(f"RESULTS FOR VCON {vcon_uuid}")
            # Show a button to see the vCon in detail
            st.markdown(f"[VCON DETAILS](/inspect?uuid={vcon_uuid})")

            response = open_ai_client.chat.completions.create(
                model=model_name,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": content}
                ]
            )
            # Display the response
            st.subheader("RESPONSE")
            choices = response.choices
            for choice in choices:
                st.write(choice.message.content)
   



