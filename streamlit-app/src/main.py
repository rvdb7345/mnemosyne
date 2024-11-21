import streamlit as st
import pandas as pd
import json  # Import json for parsing progress data
from utils.helpers import create_dir
from utils.file_paths import add_project_to_path, ProjectPaths
from streamlit_cookies_controller import CookieController

st.set_page_config(page_title="Vocabulary Practice App", layout="wide")

# Initialize cookie manager
cookies = CookieController()

pp = ProjectPaths()
add_project_to_path(pp)

# Initialize base directory
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

def main():
    if 'page' not in st.session_state:
        st.session_state['page'] = 'main'

    if st.session_state['page'] == 'main':
        show_main_page()
    elif st.session_state['page'] == 'practice':
        show_practice_page()

def show_main_page():
    st.title("Vocabulary Practice App")
    st.write("Please select an option:")

    options = ["Upload Progress", "Start New Exercise", "Select a Predefined Exercise"]
    
    # Check if progress data is in cookies
    if cookies.get('progress_data'):
        options += ["Continue where you left off"]

    choice = st.selectbox("Select an option", options, key='main_choice_selectbox')

    if choice == "Continue where you left off":
        # Load progress data from cookies into session_state
        st.session_state['progress_data'] = cookies['progress_data']
        
        # Parse the progress data to reconstruct exercise_df
        try:
            progress_json = json.loads(st.session_state['progress_data'])
            word_list = progress_json.get('word_list', [])
            if word_list:
                st.session_state['exercise_df'] = pd.DataFrame(word_list)
            else:
                st.error("No word list found in the progress data.")
                return
        except json.JSONDecodeError:
            st.error("Failed to decode progress data. Please ensure the progress file is valid.")
            return

        # Navigate to Practice page
        st.session_state['page'] = 'practice'
        st.rerun()
        
    elif choice == "Upload Progress":
        st.write("Upload your progress file to continue.")
        progress_file = st.file_uploader("Upload Progress File", type=['json'], key='progress_file_uploader')
        if progress_file is not None:
            try:
                # Load progress data into session_state
                progress_content = progress_file.getvalue().decode("utf-8")
                st.session_state['progress_data'] = progress_content

                # Parse the progress data to reconstruct exercise_df
                progress_json = json.loads(st.session_state['progress_data'])
                word_list = progress_json.get('word_list', [])
                if word_list:
                    st.session_state['exercise_df'] = pd.DataFrame(word_list)
                else:
                    st.error("No word list found in the progress file.")
                    return

                # Navigate to Practice page
                st.session_state['page'] = 'practice'
                st.rerun()
            except json.JSONDecodeError:
                st.error("Failed to decode progress file. Please upload a valid JSON file.")
            except Exception as e:
                st.error(f"An error occurred while uploading progress: {e}")

    elif choice == "Start New Exercise":
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
                            cleaned_lines.append('\t'.join(parts[:2]))

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

                    # Save the exercise data to session_state
                    st.session_state['exercise_df'] = df
                    st.session_state['source_language'] = source_language_name
                    st.session_state['target_language'] = target_language_name
                    st.session_state['exercise_name'] = custom_exercise_name
                    # Navigate to Practice page
                    st.session_state['page'] = 'practice'
                    st.rerun()
                except Exception as e:
                    st.error(f"Error uploading exercise: {e}")
            else:
                st.error("Please provide both a file and a custom exercise name.")
                
    elif choice == "Select a Predefined Exercise":
        options = ["Select list", "Dutch Frequency List", "Spanish Frequency List", "Turkish Frequency List"]
        prefab_exercise_choice = st.selectbox("Select an option", options, key='prefab_exercise_selectbox')
        
        if prefab_exercise_choice != "Select list":
            if prefab_exercise_choice == "Dutch Frequency List":
                from standard_exercises.standard_exercise_definition import DutchVocabList
                vocab_list = DutchVocabList()
                df = vocab_list.load_exercise()
            elif prefab_exercise_choice == "Spanish Frequency List":
                from standard_exercises.standard_exercise_definition import SpanishVocabList
                vocab_list = SpanishVocabList()
                df = vocab_list.load_exercise()

            st.session_state['exercise_df'] = df
            st.session_state['source_language'] = vocab_list.source_language_name
            st.session_state['target_language'] = vocab_list.target_language_name
            st.session_state['exercise_name'] = vocab_list.exercise_name
            # Navigate to Practice page
            st.session_state['page'] = 'practice'
            st.rerun()

def show_practice_page():
    from sections import practice
    practice.show(cookies)

if __name__ == "__main__":
    main()
