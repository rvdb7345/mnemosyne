# src/main.py

import streamlit as st
import os
import dotenv

from sections.practice_session import PracticeSession
from utils.google_drive import GoogleDriveManager
from utils.helpers import create_dir
from utils.file_paths import add_project_to_path, ProjectPaths

dotenv.load_dotenv(".env")

# Optional: Set page config
st.set_page_config(
    page_title="Vocabulary Practice App",
    page_icon=":books:",
    layout="centered",
)

# Initialize project paths (if you use them)
pp = ProjectPaths()
add_project_to_path(pp)

# Create exercises directory (if needed)
EXERCISES_DIR = 'exercises'
create_dir(EXERCISES_DIR)

# If you haven't already created a practice_session or drive_manager in session state
if 'practice_session' not in st.session_state:
    st.session_state['practice_session'] = PracticeSession()

if 'drive_manager' not in st.session_state:
    st.session_state['drive_manager'] = GoogleDriveManager()

def main():
    st.title("Vocabulary Practice App")

    # Ask the user for their username
    username = st.text_input("Enter your username:", key="user_name_input")


    # We'll load this from environment or .env
    main_progress_folder_id = os.getenv("MAIN_PROGRESS_FOLDER_ID", "")

    if not main_progress_folder_id:
        st.warning("Warning: MAIN_PROGRESS_FOLDER_ID is not set. Google Drive actions may fail.")

    # Only proceed once the user has typed something
    if username.strip():
        drive_manager = st.session_state['drive_manager']
        st.session_state['username'] = username

        # Check if user folder already exists
        existing_folder_id = find_user_folder_id(drive_manager, main_progress_folder_id, username.strip())

        if existing_folder_id:
            # We found an existing folder => recognized user
            st.success(f"Welcome back, **{username}**! Glad to see you again.")
            st.session_state['user_folder_id'] = existing_folder_id
        else:
            # Folder not found => new user => create folder
            new_folder_id = create_user_folder(drive_manager, main_progress_folder_id, username.strip())
            st.session_state['user_folder_id'] = new_folder_id
            st.info(f"Hello **{username}**, good to have you here. "
                    "We’ve created a new folder for you. Let's get started practicing!")
    else:
        st.write(
            "Please enter a username in the box above. "
            "We'll check Google Drive to see if you've visited before."
        )

def find_user_folder_id(drive_manager, parent_folder_id, username):
    """
    Look for a folder in 'parent_folder_id' matching 'username'.
    Returns the folder ID if found, otherwise None.
    """
    if not parent_folder_id:
        return None

    # List files in the main folder
    files = drive_manager.list_files_in_directory(parent_folder_id)
    for f in files:
        # Check if the item is a folder with the user's name
        if f['name'] == username and f['mimeType'] == 'application/vnd.google-apps.folder':
            return f['id']
    return None

def create_user_folder(drive_manager, parent_folder_id, username):
    """
    Create a new Google Drive folder for the user in 'parent_folder_id'.
    Returns the new folder ID.
    """
    if not parent_folder_id:
        return None
    return drive_manager.create_directory(username, parent_folder_id)

if __name__ == "__main__":
    main()
