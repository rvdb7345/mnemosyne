# src/pages/1_Main_Menu.py

import streamlit as st
import os
import json
import traceback
import pandas as pd

from sections.practice_session import PracticeSession
from utils.google_drive import GoogleDriveManager
from utils.story_translation import create_word_list_from_story
from standard_exercises.standard_exercise_definition import VocabList

# If you want the same PREDEFINED_EXERCISES logic from main, just replicate or import them
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
}

def app():
    """
    The main menu page, shown under "1 Main Menu" in the sidebar.
    """
    st.title("Main Menu")

    # Access the practice_session from session_state
    practice_session = st.session_state.get('practice_session', None)
    if not practice_session:
        st.error("Practice session not found. Please go back to the home page.")
        return

    drive_manager = st.session_state.get('drive_manager', None)
    if not drive_manager:
        st.warning("Drive manager not found. Some functionality may be limited.")

    username = st.session_state.get('username', '').strip()
    user_folder_id = st.session_state.get('user_folder_id', None)

    st.write("Please select an option:")
    options = ["Continue where you left off (if any)", 
               "Upload Progress", 
               "Start New Exercise", 
               "Select a Predefined Exercise",
               "Create Word List from Story"]

    choice = st.selectbox("Select an option", options)

    if choice == "Continue where you left off (if any)":
        if username and user_folder_id and drive_manager:
            progress_files = drive_manager.list_files_in_directory(user_folder_id)
            progress_json_files = [f for f in progress_files if f['name'].endswith('.json')]
            if not progress_json_files:
                st.info("No progress files found.")
            else:
                selected_file = st.selectbox("Select progress file", [f['name'] for f in progress_json_files])
                if st.button("Load Progress"):
                    file_id = next((f['id'] for f in progress_json_files if f['name'] == selected_file), None)
                    if file_id:
                        local_download_path = f"temp_downloads/{selected_file}"
                        drive_manager.download_file(file_id, local_download_path)
                        with open(local_download_path, 'r') as f:
                            progress_data = json.load(f)
                        practice_session.load_from_progress(progress_data)
                        st.success("Progress loaded successfully!")
        else:
            st.warning("Username or Drive Manager is not set, cannot continue where you left off.")

    elif choice == "Upload Progress":
        upload_progress(practice_session)

    elif choice == "Start New Exercise":
        start_new_exercise(practice_session)

    elif choice == "Select a Predefined Exercise":
        select_predefined_exercise(practice_session)

    elif choice == "Create Word List from Story":
        create_word_list_from_story()

    # Show generated word list options if present
    if 'generated_word_list' in st.session_state:
        st.markdown("---")
        st.subheader("Generated Word List Options")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Practice This Word List"):
                df_exercise = st.session_state['generated_word_list'].rename(columns={
                    "Original Word": st.session_state['word_list_source_language'],
                    f"Translation ({st.session_state['word_list_target_language']})": st.session_state['word_list_target_language']
                })

                # Setup the exercise
                practice_session.setup_new_exercise(
                    df=df_exercise,
                    source_language=st.session_state['word_list_source_language'],
                    target_language=st.session_state['word_list_target_language'],
                    exercise_name=f"{st.session_state['story_name']}"
                )

                # (Optional) Save progress to Google Drive
                if drive_manager and user_folder_id:
                    practice_session.save_progress_data(
                        drive_manager=drive_manager,
                        user_folder_id=user_folder_id
                    )
                st.success("New word list is ready to practice!")
        with col2:
            if st.button("Clear Word List"):
                del st.session_state['generated_word_list']
                del st.session_state['word_list_source_language']
                del st.session_state['word_list_target_language']
                del st.session_state['story_name']
                st.success("Word list cleared.")

def upload_progress(practice_session):
    st.write("Upload your progress file to continue.")
    progress_file = st.file_uploader("Upload Progress File", type=['json'])
    if progress_file is not None:
        try:
            progress_content = progress_file.getvalue().decode("utf-8")
            progress_data = json.loads(progress_content)
            practice_session.load_from_progress(progress_data)
            st.success("Progress file uploaded and loaded successfully!")
        except json.JSONDecodeError:
            st.error("Failed to decode progress file. Please upload a valid JSON file.")
        except Exception as e:
            st.error(f"An error occurred while uploading progress: {e}\n{traceback.format_exc()}")

def start_new_exercise(practice_session):
    st.write("Upload a new exercise file (CSV or TXT).")
    uploaded_file = st.file_uploader("Choose a file", type=['txt', 'csv'])
    custom_exercise_name = st.text_input("Custom Exercise Name")

    source_language_name = st.selectbox(
        "Source Language",
        list(LANGUAGE_OPTIONS.keys()),
        index=1
    )
    target_language_name = st.selectbox(
        "Target Language",
        list(LANGUAGE_OPTIONS.keys()),
        index=0
    )

    if st.button("Upload Exercise"):
        if uploaded_file is not None and custom_exercise_name:
            try:
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

                if df.empty or df.isnull().values.any():
                    st.error("Uploaded exercise file is empty or contains invalid data.")
                    return

                practice_session.setup_new_exercise(
                    df=df,
                    source_language=source_language_name,
                    target_language=target_language_name,
                    exercise_name=custom_exercise_name
                )
                st.success("New exercise started successfully!")

            except Exception as e:
                st.error(f"Error uploading exercise: {e} \n {traceback.format_exc()}")
        else:
            st.error("Please provide both a file and a custom exercise name.")

def select_predefined_exercise(practice_session):
    # In your original code, you create PREDEFINED_EXERCISES in main.py
    # If you need that, you can do something like:
    from main import PREDEFINED_EXERCISES

    options = ["Select list"] + list(PREDEFINED_EXERCISES.keys())
    prefab_choice = st.selectbox("Select a predefined exercise", options)

    if prefab_choice != "Select list":
        vocab_class = PREDEFINED_EXERCISES.get(prefab_choice)
        if vocab_class is None:
            st.error("Selected list is not available.")
            return

        vocab_list_obj = vocab_class()
        with st.spinner('Loading predefined exercise...'):
            df = vocab_list_obj.load_exercise()
        if df.empty:
            st.error("The selected exercise file is empty or improperly formatted.")
            return

        practice_session.setup_new_exercise(
            df=df,
            source_language=vocab_list_obj.source_language_name,
            target_language=vocab_list_obj.target_language_name,
            exercise_name=vocab_list_obj.exercise_name
        )
        st.success("Predefined exercise loaded and ready to practice!")


# Required by Streamlit: the function name must be `app()` in multipage usage
# so that Streamlit can run it when the user selects this page.
app()

# If you prefer the simpler approach (0.90+), you can also just rename `app()` to
# `write()` or keep it as is. What matters is that the file is in pages folder
# with a numeric prefix in the filename.
