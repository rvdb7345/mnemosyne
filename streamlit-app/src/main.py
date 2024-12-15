# src/main.py

import streamlit as st
import pandas as pd
import json
import traceback
import random
import os

from utils.helpers import create_dir
from utils.file_paths import add_project_to_path, ProjectPaths
from streamlit_cookies_manager import EncryptedCookieManager
from sections.practice_session import PracticeSession
from sections import practice
from sections import components  # Assuming components might be used in main as well
from utils.google_drive import GoogleDriveManager
import dotenv

dotenv.load_dotenv(".env")

# Initialize project paths
pp = ProjectPaths()
add_project_to_path(pp)

# Initialize cookie manager
cookies = EncryptedCookieManager(
    prefix="vocabulary_app",
    password="YourSecretKey",  # Replace with your secure secret key
)

if not cookies.ready():
    st.stop()

# Initialize base directory (locally)
EXERCISES_DIR = 'exercises'
create_dir(EXERCISES_DIR)

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

# Dynamically create the PREDEFINED_EXERCISES mapping from registered subclasses
import standard_exercises.standard_exercise_definition
from standard_exercises.standard_exercise_definition import VocabList
PREDEFINED_EXERCISES = {
    vocab_class().exercise_name: vocab_class
    for vocab_class in VocabList.__subclasses__()
}

def initialize_practice_session():
    if 'practice_session' not in st.session_state:
        st.session_state['practice_session'] = PracticeSession()

def main():
    initialize_practice_session()
    practice_session = st.session_state['practice_session']

    # Sidebar navigation
    st.sidebar.title("Navigation")

    # User enters username
    username = st.text_input("Enter your username", key='user_name_input')
    st.session_state['username'] = username.strip()

    # Initialize Google Drive Manager
    # Make sure your environment has GDRIVE_CREDENTIALS and MAIN_PROGRESS_FOLDER_ID set
    drive_manager = GoogleDriveManager()
    if 'drive_manager' not in st.session_state:
        st.session_state['drive_manager'] = GoogleDriveManager()

    main_progress_folder_id =  st.secrets['other_variables']["MAIN_PROGRESS_FOLDER_ID"]
    if not main_progress_folder_id:
        st.error("MAIN_PROGRESS_FOLDER_ID not set in environment.")
        return

    user_folder_id = None
    if username:
        # Check if user folder exists
        user_folder_id = get_or_create_user_folder(drive_manager, main_progress_folder_id, username)
        st.session_state['user_folder_id'] = user_folder_id

    # Prepare main menu options
    options = ["Main Menu", "Practice", "Mistakes"]
    if 'page' not in st.session_state:
        st.session_state['page'] = 'Main Menu'
    st.session_state['page'] = st.sidebar.radio("Go to", options, index=options.index(st.session_state['page']))

    # Main Page Navigation
    if st.session_state['page'] == 'Main Menu':
        show_main_page(practice_session, cookies, drive_manager)
    elif st.session_state['page'] == 'Practice':
        practice.show_practice(practice_session, cookies, mode='practice')
    elif st.session_state['page'] == 'Mistakes':
        practice.show_practice(practice_session, cookies, mode='mistakes')

def show_main_page(practice_session, cookies, drive_manager):
    st.title("Vocabulary Practice App")
    st.write("Please select an option:")

    # Default options
    options = ["Upload Progress", "Start New Exercise", "Select a Predefined Exercise"]

    username = st.session_state.get('username', '').strip()
    user_folder_id = st.session_state.get('user_folder_id', None)

    # If we have a username and corresponding folder on Drive
    # Check if there are any progress files for this user
    if username and user_folder_id:
        progress_files = drive_manager.list_files_in_directory(user_folder_id)
        # Filter to .json files that might represent progress files
        progress_json_files = [f for f in progress_files if f['name'].endswith('.json')]

        # If progress files exist, add "Continue where you left off" as an option
        if progress_json_files:
            options = ["Continue where you left off"] + options

    choice = st.selectbox("Select an option", options, key='main_choice_selectbox')

    if choice == "Continue where you left off":
        # Let user choose from their existing progress files on Drive
        selected_file = st.selectbox("Select progress file to continue", [f['name'] for f in progress_json_files])
        if st.button("Load Progress", key='load_progress_button'):
            # Download the selected file from Drive
            file_id = None
            for f in progress_json_files:
                if f['name'] == selected_file:
                    file_id = f['id']
                    break

            if file_id:
                local_download_path = f"temp_downloads/{selected_file}"
                drive_manager.download_file(file_id, local_download_path)
                with open(local_download_path, 'r') as f:
                    progress_data = json.load(f)
                practice_session.load_from_progress(progress_data)

                # Navigate to Practice page
                st.session_state['page'] = 'Practice'
                st.rerun()

    elif choice == "Upload Progress":
        upload_progress(practice_session, cookies)
    elif choice == "Start New Exercise":
        start_new_exercise(practice_session, cookies)
    elif choice == "Select a Predefined Exercise":
        select_predefined_exercise(practice_session, cookies)

def load_progress(practice_session, cookies):
    progress_content = cookies.get('progress_data')
    if progress_content:
        progress_data = json.loads(progress_content)
        # Load necessary session state variables
        practice_session.load_from_progress(progress_data)
        # Navigate to Practice page
        st.session_state['page'] = 'Practice'
        st.rerun()
    else:
        st.error("No progress data found in cookies.")

def upload_progress(practice_session, cookies):
    st.write("Upload your progress file to continue.")
    progress_file = st.file_uploader("Upload Progress File", type=['json'], key='progress_file_uploader')
    if progress_file is not None:
        try:
            progress_content = progress_file.getvalue().decode("utf-8")
            progress_data = json.loads(progress_content)
            practice_session.load_from_progress(progress_data)

            # Save progress data back to cookies
            practice_session.save_progress_data(cookies, drive_manager=st.session_state['drive_manager'], user_folder_id=st.session_state['user_folder_id'])

            # Navigate to Practice page
            st.session_state['page'] = 'Practice'
            st.rerun()
        except json.JSONDecodeError:
            st.error("Failed to decode progress file. Please upload a valid JSON file.")
        except Exception as e:
            st.error(f"An error occurred while uploading progress: {e}: \n {traceback.format_exc()}")

def start_new_exercise(practice_session, cookies):
    st.write("Upload a new exercise file (CSV or TXT).")
    uploaded_file = st.file_uploader("Choose a file", type=['txt', 'csv'], key='exercise_file_uploader')
    custom_exercise_name = st.text_input("Custom Exercise Name", key='custom_exercise_name_input')

    source_language_name = st.selectbox(
        "Source Language",
        list(LANGUAGE_OPTIONS.keys()),
        index=1,
        key='source_language_selectbox'
    )
    target_language_name = st.selectbox(
        "Target Language",
        list(LANGUAGE_OPTIONS.keys()),
        index=0,
        key='target_language_selectbox'
    )

    if st.button("Upload Exercise", key='upload_exercise_button'):
        if uploaded_file is not None and custom_exercise_name:
            try:
                source_language_code = LANGUAGE_OPTIONS[source_language_name]
                target_language_code = LANGUAGE_OPTIONS[target_language_name]
                if uploaded_file.name.endswith('.txt'):
                    cleaned_lines = []
                    for line in uploaded_file:
                        line = line.decode('utf-8').rstrip()
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            cleaned_lines.append('\t'.join(parts[:2]))
                        else:
                            st.warning(f"Ignored improperly formatted line: {line}")

                    from io import StringIO
                    cleaned_content = StringIO('\n'.join(cleaned_lines))
                    df = pd.read_csv(
                        cleaned_content,
                        sep='\t',
                        header=None,
                        names=[source_language_name, target_language_name]
                    )

                elif uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(
                        uploaded_file,
                        header=None,
                        names=[source_language_name, target_language_name]
                    ).applymap(str.strip)
                else:
                    st.error("Unsupported file format.")
                    return

                # Validate DataFrame
                if df.empty or df.isnull().values.any():
                    st.error("Uploaded exercise file is empty or contains invalid data.")
                    return

                # Save the exercise data to practice_session
                practice_session.setup_new_exercise(
                    df=df,
                    source_language=source_language_name,
                    target_language=target_language_name,
                    exercise_name=custom_exercise_name
                )

                # Save progress data
                practice_session.save_progress_data(cookies, drive_manager=st.session_state['drive_manager'], user_folder_id=st.session_state['user_folder_id'])

                # Navigate to Practice page
                st.session_state['page'] = 'Practice'
                st.rerun()
            except Exception as e:
                st.error(f"Error uploading exercise: {e} \n {traceback.format_exc()}")
        else:
            st.error("Please provide both a file and a custom exercise name.")

def select_predefined_exercise(practice_session, cookies):
    options = ["Select list"] + list(PREDEFINED_EXERCISES.keys())
    prefab_exercise_choice = st.selectbox("Select an option", options, key='prefab_exercise_selectbox')

    if prefab_exercise_choice != "Select list":
        vocab_class = PREDEFINED_EXERCISES.get(prefab_exercise_choice)
        if vocab_class is None:
            st.error("Selected list is not available.")
            return

        vocab_list = vocab_class()
        with st.spinner('Loading exercise...'):
            df = vocab_list.load_exercise()
        if df.empty:
            st.error("The selected exercise file is empty or improperly formatted.")
            return

        # Save the exercise data to practice_session
        practice_session.setup_new_exercise(
            df=df,
            source_language=vocab_list.source_language_name,
            target_language=vocab_list.target_language_name,
            exercise_name=vocab_list.exercise_name
        )

        # Save progress data
        practice_session.save_progress_data(cookies, drive_manager=st.session_state['drive_manager'], user_folder_id=st.session_state['user_folder_id'])

        # Navigate to Practice page
        st.session_state['page'] = 'Practice'
        st.rerun()

def get_or_create_user_folder(drive_manager, main_folder_id, username):
    # Check if folder with username already exists in main_folder_id
    files = drive_manager.list_files_in_directory(main_folder_id)
    for f in files:
        if f['name'] == username and f['mimeType'] == 'application/vnd.google-apps.folder':
            return f['id']

    # If not found, create a new folder for this user
    user_folder_id = drive_manager.create_directory(username, parent_folder_id=main_folder_id)
    return user_folder_id

if __name__ == "__main__":
    main()
