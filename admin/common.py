# common.py
import streamlit as st

def redirect(page_name):
    st.session_state.current_page = page_name
    st.experimental_rerun()

def logged_in():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    return st.session_state.logged_in

def login():
    st.session_state.logged_in = True
    st.experimental_rerun()

def logout():
    st.session_state.logged_in = False
    st.experimental_rerun()

def manage_session_state():
    # Check to make sure the user is logged in
    if 'admin_password' not in st.secrets:
            st.write("No admin password set. Please set the admin password in the secrets.")
            st.stop()
    else:
        admin_password = st.secrets["admin_password"]['password']

    if logged_in() is False:
        # Log in the user by setting the session state variable
        # Get the password from the secrets and compare it to the user input
        # Make a login form
        password = st.text_input("Enter password", type="password")
        if st.button("Log in"):
            if password == admin_password:
                login()
            else:
                st.write("Incorrect password :", password, admin_password)
        st.stop()
        
    # Log out the user by setting the session state variable   
    if st.button("Log out"):
        logout()