import streamlit as st
import os
from utils.helpers import handle_exercise_upload


# Language options with codes for gTTS compatibility
LANGUAGE_OPTIONS = {
    "English": "en",
    "Turkish": "tr",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Dutch": "nl",
    "Russian": "ru",
    "Portuguese": "pt",
    # Add more languages as needed
}

def show():
    st.header("Upload a New Exercise")
    st.write("Please upload a TXT file (tab-separated) or a CSV file with two columns: Source and Target languages.")

    uploaded_file = st.file_uploader("Choose a file", type=['txt', 'csv'])
    custom_exercise_name = st.text_input("Custom Exercise Name")

    # Dropdowns for selecting languages with default values
    source_language_name = st.selectbox("Source Language", list(LANGUAGE_OPTIONS.keys()), index=1)  # Default to Turkish
    target_language_name = st.selectbox("Target Language", list(LANGUAGE_OPTIONS.keys()), index=0)  # Default to English
    source_language_code = LANGUAGE_OPTIONS[source_language_name]
    target_language_code = LANGUAGE_OPTIONS[target_language_name]

    if st.button("Upload Exercise"):
        username = st.session_state.get('username')
        EXERCISES_DIR = "exercises"
        handle_exercise_upload(uploaded_file, custom_exercise_name, username, EXERCISES_DIR, source_language_name, target_language_name)

show()

