# src/main.py

import streamlit as st
import pandas as pd
import json
import traceback
import random
import openai  # Added import for OpenAI API

from pydantic import BaseModel
from typing import List

# Import the standard_exercise_definition module to ensure all subclasses are loaded
import standard_exercises.standard_exercise_definition
from standard_exercises.standard_exercise_definition import VocabList
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

# Define Pydantic models for Structured Outputs

class WordExtractionResponse(BaseModel):
    words: List[str]

class TranslationItem(BaseModel):
    original: str
    translation: str

class TranslationResponse(BaseModel):
    translations: List[TranslationItem]

def initialize_practice_session():
    if 'practice_session' not in st.session_state:
        st.session_state['practice_session'] = PracticeSession()

def main():
    initialize_practice_session()
    practice_session = st.session_state['practice_session']

    # User enters username
    username = st.text_input("Enter your username", key='user_name_input')
    st.session_state['username'] = username.strip()

    # Initialize Google Drive Manager
    drive_manager = GoogleDriveManager()
    if 'drive_manager' not in st.session_state:
        st.session_state['drive_manager'] = GoogleDriveManager()

    main_progress_folder_id = st.secrets['other_variables']["MAIN_PROGRESS_FOLDER_ID"]
    if not main_progress_folder_id:
        st.error("MAIN_PROGRESS_FOLDER_ID not set in environment.")
        return

    user_folder_id = None
    if username:
        # Check if user folder exists
        user_folder_id = get_or_create_user_folder(drive_manager, main_progress_folder_id, username)
        st.session_state['user_folder_id'] = user_folder_id

    # Initialize the 'page' state if not already set
    if 'page' not in st.session_state:
        st.session_state['page'] = 'Main Menu'

    # Sidebar navigation
    st.sidebar.title("Navigation")
    sidebar_options = ["Main Menu", "Practice", "Mistakes"]

    # Sidebar radio selection
    selected_sidebar = st.sidebar.radio(
        "Go to",
        sidebar_options,
        index=sidebar_options.index(st.session_state['page']) if st.session_state['page'] in sidebar_options else 0,
        key='sidebar_radio'
    )

    # Update 'page' based on sidebar selection only if it's different
    if selected_sidebar != st.session_state['page']:
        st.session_state['page'] = selected_sidebar
        st.rerun()

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

    username = st.session_state.get('username', '').strip()
    user_folder_id = st.session_state.get('user_folder_id', None)

    # Default options
    options = ["Upload Progress", "Start New Exercise", "Select a Predefined Exercise", "Create Word List from Story"]

    # If we have existing progress files, add "Continue where you left off"
    if username and user_folder_id:
        progress_files = drive_manager.list_files_in_directory(user_folder_id)
        progress_json_files = [f for f in progress_files if f['name'].endswith('.json')]
        if progress_json_files:
            options = ["Continue where you left off"] + options

    choice = st.selectbox("Select an option", options, key='main_choice_selectbox')

    if choice == "Continue where you left off":
        # Let user choose from their existing progress files on Drive
        selected_file = st.selectbox("Select progress file to continue", [f['name'] for f in progress_json_files], key='select_progress_file')
        if st.button("Load Progress", key='load_progress_button'):
            # Download the selected file from Drive
            file_id = next((f['id'] for f in progress_json_files if f['name'] == selected_file), None)
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

    elif choice == "Create Word List from Story":
        create_word_list_from_story()

    # After handling main options, check if a word list has been generated
    if 'generated_word_list' in st.session_state:
        st.markdown("---")
        st.subheader("Generated Word List Options")

        # Option 1: Download is already handled within create_word_list_from_story()

        # Option 2: Practice the generated word list
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Practice This Word List", key='practice_word_list_button'):
                df_exercise = st.session_state['generated_word_list'].rename(columns={
                    "Original Word": st.session_state['word_list_source_language'],
                    f"Translation ({st.session_state['word_list_target_language']})": st.session_state['word_list_target_language']
                })

                # Setup the exercise in the practice_session
                practice_session.setup_new_exercise(
                    df=df_exercise,
                    source_language=st.session_state['word_list_source_language'],
                    target_language=st.session_state['word_list_target_language'],
                    exercise_name=f"{st.session_state['story_name']}"
                )

                # Save progress
                practice_session.save_progress_data(
                    cookies, 
                    drive_manager=st.session_state['drive_manager'], 
                    user_folder_id=st.session_state['user_folder_id']
                )

                # Navigate to Practice page
                st.session_state['page'] = 'Practice'
                st.rerun()
        with col2:
            if st.button("Clear Word List", key='clear_word_list_button'):
                del st.session_state['generated_word_list']
                del st.session_state['word_list_source_language']
                del st.session_state['word_list_target_language']
                del st.session_state['story_name']
                st.success("Word list cleared.")

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

def create_word_list_from_story():
    st.subheader("Create Word List from Story")
    st.write("Paste your story below and generate a word list with translations.")

    # Input fields
    story = st.text_area("Enter your story here:", height=300)
    story_name = st.text_input("Enter the name of your story here:", key='story_name_input')

    source_language_name = st.selectbox(
        "Source Language",
        list(LANGUAGE_OPTIONS.keys()),
        index=0,
        key='source_language_story_selectbox'
    )
    target_language_name = st.selectbox(
        "Target Language",
        list(LANGUAGE_OPTIONS.keys()),
        index=1,
        key='target_language_translate_selectbox'
    )
    api_key = st.text_input("Enter your OpenAI API Key:", type="password")

    if st.button("Generate Word List", key='generate_word_list_button'):
        if not story.strip():
            st.error("Please enter a story.")
            return
        if not story_name.strip():
            st.error("Please enter a name for your story.")
            return
        if not api_key.strip():
            st.error("Please enter your OpenAI API key.")
            return

        # Clear any existing word list
        if 'generated_word_list' in st.session_state:
            del st.session_state['generated_word_list']
            del st.session_state['word_list_source_language']
            del st.session_state['word_list_target_language']
            del st.session_state['story_name']

        # Set OpenAI API key
        openai.api_key = api_key.strip()

        # Store story name in session state
        st.session_state['story_name'] = story_name.strip()

        # Process the story
        with st.spinner('Generating word list and translations...'):
            try:
                word_list = generate_word_list_from_story(story, source_language_name)
                if word_list:
                    # Translate the word list
                    translated_words = translate_words(word_list, source_language_name, target_language_name)

                    # Create a DataFrame with original and translated words
                    df_translated = pd.DataFrame(translated_words, columns=["Original Word", f"Translation ({target_language_name})"])

                    # Store the DataFrame and language names in session state
                    st.session_state['generated_word_list'] = df_translated
                    st.session_state['word_list_source_language'] = source_language_name
                    st.session_state['word_list_target_language'] = target_language_name

                    # Display the word list with translations
                    st.success("Word list with translations generated successfully!")
                    st.dataframe(df_translated)

                    # Provide download option
                    csv = df_translated.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Word List as CSV",
                        data=csv,
                        file_name=f'word_list_{story_name.strip().replace(" ", "_")}.csv',
                        mime='text/csv',
                        key='download_word_list_button'
                    )
                else:
                    st.warning("No words were extracted from the story.")
            except Exception as e:
                st.error(f"An error occurred: {e}\n{traceback.format_exc()}")

    # No buttons here. Buttons are handled in show_main_page()

def split_text_into_chunks(text, max_tokens=1000):
    """
    Splits the text into chunks that are manageable by the OpenAI API.

    Args:
        text (str): The input text to split.
        max_tokens (int): Maximum number of tokens per chunk.

    Returns:
        List[str]: A list of text chunks.
    """
    import math
    from transformers import GPT2Tokenizer

    tokenizer = get_tokenizer()
    tokens = tokenizer.encode(text)
    total_tokens = len(tokens)
    num_chunks = math.ceil(total_tokens / max_tokens)
    chunks = []
    for i in range(num_chunks):
        start = i * max_tokens
        end = start + max_tokens
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
    return chunks

@st.cache_resource
def get_tokenizer():
    from transformers import GPT2Tokenizer
    return GPT2Tokenizer.from_pretrained("gpt2")

def generate_word_list_from_story(story, source_language):
    """
    Generates a word list from the provided story using OpenAI API with Structured Outputs.

    Args:
        story (str): The story text.
        source_language (str): The language of the story.

    Returns:
        List[str]: A list of unique words in dictionary form.
    """
    # Split the story into manageable chunks
    chunks = split_text_into_chunks(story, max_tokens=1000)

    unique_words = set()

    for idx, chunk in enumerate(chunks):
        st.write(f"Processing chunk {idx + 1} of {len(chunks)}...")
        prompt = (
            f"Extract all unique words from the following {source_language} text in their dictionary form "
            f"(unconjugated, no suffixes), including phrasal verbs.\n\n{chunk}\n\n"
            "Provide the output as a JSON object adhering to the following schema:\n"
            "{\n"
            "  \"words\": [\n"
            "    \"word1\",\n"
            "    \"word2\",\n"
            "    \"word3\"\n"
            "  ]\n"
            "}"
        )

        try:
            response = openai.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                response_format=WordExtractionResponse,
                temperature=0.0,
                max_tokens=1500,
            )
        except openai.error.OpenAIError as e:
            st.error(f"OpenAI API error during word extraction: {e}")
            st.stop()

        # Check for refusal
        if hasattr(response.choices[0].message, 'refusal') and response.choices[0].message.refusal:
            st.error(f"Refusal from OpenAI API: {response.choices[0].message.refusal}")
            continue

        # Extract words
        extracted_words = response.choices[0].message.parsed.words
        unique_words.update(extracted_words)

    # Convert set to sorted list
    sorted_words = sorted(unique_words, key=lambda x: x.lower())
    return sorted_words

def translate_words(word_list, source_language, target_language):
    """
    Translates a list of words from source_language to target_language using OpenAI API with Structured Outputs.

    Args:
        word_list (List[str]): The list of words to translate.
        source_language (str): The language of the original words.
        target_language (str): The target language for translation.

    Returns:
        List[Tuple[str, str]]: A list of tuples containing original and translated words.
    """
    translated = []
    batch_size = 50  # Adjust based on API limits and performance
    total_words = len(word_list)

    for i in range(0, len(word_list), batch_size):
        batch = word_list[i:i + batch_size]
        st.write(f"Translating words {i + 1} to {i + len(batch)} of {total_words}...")
        prompt = (
            f"Translate the following {source_language} words to {target_language}.\n\n"
            f"Provide the output as a JSON object adhering to the following schema:\n"
            "{\n"
            "  \"translations\": [\n"
            "    {\n"
            "      \"original\": \"word1\",\n"
            "      \"translation\": \"translated_word1\"\n"
            "    },\n"
            "    {\n"
            "      \"original\": \"word2\",\n"
            "      \"translation\": \"translated_word2\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        try:
            response = openai.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt + "\n\nWords:\n" + ", ".join(batch)}
                ],
                response_format=TranslationResponse,
                temperature=0.0,
                max_tokens=3000,
            )
        except openai.error.OpenAIError as e:
            st.error(f"OpenAI API error during translation: {e}")
            st.stop()

        # Check for refusal
        if hasattr(response.choices[0].message, 'refusal') and response.choices[0].message.refusal:
            st.error(f"Refusal from OpenAI API: {response.choices[0].message.refusal}")
            continue

        # Extract translations
        translations = response.choices[0].message.parsed.translations
        for item in translations:
            translated.append((item.original, item.translation))

    return translated

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
