import streamlit as st
import os
from utils.helpers import handle_exercise_upload

def show():
    st.header("Upload a New Exercise")
    st.write("Please upload a TXT file (tab-separated) or a CSV file with two columns: 'Turkish' and 'English'.")

    uploaded_file = st.file_uploader("Choose a file", type=['txt', 'csv'])
    custom_exercise_name = st.text_input("Custom Exercise Name")
    
    if st.button("Upload Exercise"):
        username = st.session_state.get('username')
        EXERCISES_DIR = "exercises"
        handle_exercise_upload(uploaded_file, custom_exercise_name, username, EXERCISES_DIR)
        
show()