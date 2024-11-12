import streamlit as st
import os
import pandas as pd
import random
import unicodedata
import difflib
import json
from datetime import datetime
from io import BytesIO
from gtts import gTTS
import base64
import re
import itertools

# ---------------------------
# Helper Functions
# ---------------------------

def create_dir(path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)

def get_users(exercises_dir):
    """Retrieve user directories."""
    users = [f for f in os.listdir(exercises_dir) if os.path.isdir(os.path.join(exercises_dir, f))]
    return users

def get_exercises(user, exercises_dir):
    """Retrieve exercise files for a user."""
    user_exercises_dir = os.path.join(exercises_dir, user)
    if not os.path.exists(user_exercises_dir):
        create_dir(user_exercises_dir)
    files = [f for f in os.listdir(user_exercises_dir) if f.endswith('.txt') or f.endswith('.csv')]
    return files

def load_exercise(file_path):
    """Load exercise data from a file."""
    try:
        if file_path.endswith('.txt'):
            df = pd.read_csv(file_path, sep='\t', header=None, names=['Turkish', 'English'])
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path, header=None, names=['Turkish', 'English'])
        else:
            st.error("Unsupported file format.")
            return None
        return df
    except Exception as e:
        st.error(f"Error reading the file: {e}")
        return None

def normalize_text(text):
    """Normalize text by removing accents and converting to lowercase."""
    text = unicodedata.normalize('NFD', text)
    text = ''.join([char for char in text if not unicodedata.combining(char)])
    return text.lower()

def compare_strings(a, b, tolerance, ignore_accents):
    """
    Compare two strings with a given tolerance.
    Returns a tuple (is_correct: bool, correct_answer: str)
    """
    original_a = a
    original_b = b
    if ignore_accents:
        a = normalize_text(a)
        b = normalize_text(b)
    else:
        a = a.lower()
        b = b.lower()
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    return ratio * 100 >= tolerance, original_b

def tts_audio(word, language):
    """Generate Text-to-Speech audio and return HTML audio tag."""
    try:
        tts = gTTS(text=word, lang=language)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_data = fp.read()
        b64 = base64.b64encode(audio_data).decode()
        audio_html = f'<audio autoplay="true" controls src="data:audio/mp3;base64,{b64}"></audio>'
        return audio_html
    except Exception as e:
        return f"<p>Error generating audio: {e}</p>"

def expand_parentheses(s):
    """
    Expand a string with optional text in parentheses into all possible combinations.
    E.g., "(the) food" -> ["food", "the food"]
    """
    # Pattern to find text in parentheses
    pattern = re.compile(r'\(([^)]+)\)')
    # Find all matches
    matches = list(pattern.finditer(s))
    if not matches:
        return [s.strip()]
    
    # Extract segments and optional texts
    segments = []
    for i, match in enumerate(matches):
        start, end = match.span()
        fixed_text = s[:start]
        optional_text = match.group(1).strip()
        segments.append([fixed_text, fixed_text + optional_text])
        s = s[end:]
    segments.append([s])  # Add the remaining fixed text
    
    # Generate all combinations
    combinations = itertools.product(*segments)
    expanded = [''.join(comb).strip() for comb in combinations]
    return list(set(expanded))

def get_progress_file(username, exercise, direction, progress_dir):
    """Generate the progress file path based on user, exercise, and direction."""
    filename = f"progress_{exercise}_{direction.replace(' ', '_')}.json"
    return os.path.join(progress_dir, username, filename)

def handle_exercise_upload(uploaded_file, custom_name, user, exercises_dir):
    """Handle uploading a new exercise with a custom name."""
    if uploaded_file is not None and custom_name:
        try:
            if uploaded_file.name.endswith('.txt'):
                df = pd.read_csv(uploaded_file, sep='\t', header=None, names=['Turkish', 'English'])
            elif uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, header=None, names=['Turkish', 'English'])
            else:
                st.error("Unsupported file format.")
                return
            # Save the file to the user's exercises folder
            user_exercises_dir = os.path.join(exercises_dir, user)
            save_path = os.path.join(user_exercises_dir, uploaded_file.name)
            with open(save_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Exercise '{custom_name}' uploaded successfully!")
            # Reload the exercises list
            st.session_state['exercise_names'] = get_exercises(user, exercises_dir)
        except Exception as e:
            st.error(f"Error uploading exercise: {e}")
    else:
        st.error("Please provide both a file and a custom exercise name.")

# ---------------------------
# Apply Custom CSS for Flashcard Styling
# ---------------------------

st.markdown("""
    <style>
    .flashcard {
        background-color: #F0F8FF;
        border-radius: 10px;
        padding: 50px;
        text-align: center;
        font-size: 24px;
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------
# Initialize Base Directories
# ---------------------------

EXERCISES_DIR = 'exercises'
PROGRESS_DIR = 'progress'
create_dir(EXERCISES_DIR)
create_dir(PROGRESS_DIR)

# ---------------------------
# Login/Signup System
# ---------------------------

if 'username' not in st.session_state:
    st.title("Vocabulary Practice App")

    users = get_users(EXERCISES_DIR)
    st.header("Login")
    username = st.selectbox("Select your username", options=[""] + users)

    st.write("or")
    new_user = st.text_input("Sign up with a new username")

    login_button = st.button("Login")

    if login_button:
        if new_user:
            # Sign up new user
            username = new_user.strip()
            if username == "":
                st.error("Username cannot be empty.")
            elif username in users:
                st.error("Username already exists. Please choose a different username.")
            else:
                # Create a folder for the new user
                user_exercises_dir = os.path.join(EXERCISES_DIR, username)
                create_dir(user_exercises_dir)
                st.success(f"User '{username}' created successfully!")
                st.session_state['username'] = username
                st.rerun()
        elif username:
            # Existing user
            st.session_state['username'] = username
            st.rerun()
        else:
            st.error("Please select an existing username or sign up with a new one.")

else:
    # User is logged in
    username = st.session_state['username']
    st.sidebar.title(f"Welcome, {username}!")
    st.sidebar.markdown("---")

    # Navigation options
    navigation = st.sidebar.radio("Go to", ["Practice", "Review Answers", "Upload Exercise", "Practice Mistakes"])

    st.session_state['page'] = navigation

    # Logout option
    if st.sidebar.button("Logout"):
        del st.session_state['username']
        st.rerun()

    # ---------------------------
    # Practice Page
    # ---------------------------
    
    if st.session_state['page'] == 'Practice':
        # Get the list of exercises
        exercises = get_exercises(username, EXERCISES_DIR)
        if not exercises:
            st.info("No exercises available. Please upload an exercise.")
            st.stop()

        selected_exercise = st.sidebar.selectbox("Select an exercise", exercises)

        direction = st.sidebar.radio("Select practice direction", ("Turkish to English", "English to Turkish"))

        tolerance = st.sidebar.slider("Tolerance for typos (0 to 100)", min_value=0, max_value=100, value=80)
        ignore_accents = st.sidebar.checkbox("Ignore accents in typing")

        # Load the exercise data
        exercise_path = os.path.join(EXERCISES_DIR, username, selected_exercise)
        df = load_exercise(exercise_path)
        if df is None:
            st.stop()

        # Progress file path per user
        user_progress_dir = os.path.join(PROGRESS_DIR, username)
        create_dir(user_progress_dir)
        progress_file = get_progress_file(username, selected_exercise, direction, PROGRESS_DIR)

        # Initialize session state
        if 'initialized_practice' not in st.session_state:
            st.session_state['initialized_practice'] = True
            st.session_state['prev_exercise'] = selected_exercise
            st.session_state['prev_direction'] = direction
            st.session_state['word_list'] = df.to_dict('records')
            random.shuffle(st.session_state['word_list'])
            st.session_state['current_index'] = 0
            st.session_state['mistakes'] = []
            st.session_state['progress'] = []
            st.session_state['feedback_message'] = None
            st.session_state['user_input'] = ''
            st.session_state['clear_input'] = False
            st.session_state['loaded_progress'] = False

        # Reset session state if exercise or direction has changed
        if st.session_state['prev_exercise'] != selected_exercise or st.session_state['prev_direction'] != direction:
            st.session_state['prev_exercise'] = selected_exercise
            st.session_state['prev_direction'] = direction
            st.session_state['word_list'] = df.to_dict('records')
            random.shuffle(st.session_state['word_list'])
            st.session_state['current_index'] = 0
            st.session_state['mistakes'] = []
            st.session_state['progress'] = []
            st.session_state['feedback_message'] = None
            st.session_state['user_input'] = ''
            st.session_state['clear_input'] = False
            st.session_state['loaded_progress'] = False

        # Load progress if it exists
        if os.path.exists(progress_file) and not st.session_state.get('loaded_progress_practice', False):
            with open(progress_file, 'r') as f:
                st.session_state['progress'] = json.load(f)
            # Update current index and mistakes
            st.session_state['current_index'] = len(st.session_state['progress'])
            st.session_state['mistakes'] = [item['word_pair'] for item in st.session_state['progress'] if not item['correct']]
            st.session_state['loaded_progress'] = True
            st.session_state['loaded_progress_practice'] = True

        # Display the latest feedback message
        if st.session_state.get('feedback_message'):
            msg_type, msg = st.session_state['feedback_message']
            if msg_type == 'success':
                st.success(msg)
            else:
                st.error(msg)

        # Display progress bar and current word number
        total_words = len(st.session_state['word_list'])
        current_index = st.session_state['current_index']
        if current_index < total_words:
            progress_percent = current_index / total_words
        else:
            progress_percent = 1.0
        st.progress(progress_percent)
        st.write(f"Word {min(current_index + 1, total_words)} of {total_words}")

        # Before creating the text_input, check if we need to clear the input
        if st.session_state.get('clear_input', False):
            st.session_state['user_input'] = ''
            st.session_state['clear_input'] = False

        # Main quiz logic
        if current_index < total_words:
            current_word_pair = st.session_state['word_list'][current_index]
            if direction == "Turkish to English":
                question = current_word_pair['Turkish']
                answer = current_word_pair['English']
                tts_language = 'tr'
            else:
                question = current_word_pair['English']
                answer = current_word_pair['Turkish']
                tts_language = 'en'

            # Display the word in a flashcard
            st.markdown(f'<div class="flashcard">{question}</div>', unsafe_allow_html=True)

            # Option to hear the pronunciation
            if st.button("Hear Pronunciation"):
                audio_html = tts_audio(question, tts_language)
                st.markdown(audio_html, unsafe_allow_html=True)

            # Use a form to allow Enter key submission
            with st.form(key='answer_form', clear_on_submit=True):
                user_input = st.text_input("Your answer:", key='user_input')
                submit = st.form_submit_button(label='Submit')

            if submit:
                # Get the user's input from session state
                user_input = st.session_state['user_input']

                # Split the correct answer into multiple acceptable answers
                acceptable_answers_raw = [ans.strip() for ans in answer.split(',')]
                # Expand each acceptable answer to account for optional text in parentheses
                acceptable_answers = []
                for ans in acceptable_answers_raw:
                    expanded = expand_parentheses(ans)
                    acceptable_answers.extend(expanded)
                # Remove duplicates from acceptable answers
                acceptable_answers = list(set(acceptable_answers))
                # Check if the user's input matches any of the acceptable answers
                correct = False
                for ans in acceptable_answers:
                    is_correct, original_ans = compare_strings(user_input, ans, tolerance, ignore_accents)
                    if is_correct:
                        correct = True
                        break

                # Update feedback message in session state
                if correct:
                    feedback = f"Correct! Your answer: **{original_ans}**"
                    st.session_state['feedback_message'] = ('success', feedback)
                    # If the word was previously a mistake, remove it from mistakes
                    if current_word_pair in st.session_state['mistakes']:
                        st.session_state['mistakes'].remove(current_word_pair)
                else:
                    feedback = f"Incorrect! Your answer: **{user_input}**. Acceptable answers were: **{', '.join(acceptable_answers)}**"
                    st.session_state['feedback_message'] = ('error', feedback)
                    # Add to mistakes if not already present
                    if current_word_pair not in st.session_state['mistakes']:
                        st.session_state['mistakes'].append(current_word_pair)

                # Save progress with timestamp
                st.session_state['progress'].append({
                    'question': question,
                    'your_answer': user_input,
                    'correct_answer': answer,
                    'correct': correct,
                    'timestamp': datetime.now().isoformat(),
                    'word_pair': current_word_pair  # For mistake practice
                })
                st.session_state['current_index'] += 1
                # Save progress to a file
                with open(progress_file, 'w') as f:
                    json.dump(st.session_state['progress'], f)
                # Set the flag to clear the input on next run
                st.session_state['clear_input'] = True
                # Rerun the script to update the page
                st.rerun()
        else:
            st.write("You have completed all words in this exercise!")

            # Option to practice mistakes
            if st.button("Practice Mistakes"):
                if st.session_state['mistakes']:
                    # Replace word list with mistakes
                    st.session_state['word_list'] = st.session_state['mistakes']
                    random.shuffle(st.session_state['word_list'])
                    st.session_state['current_index'] = 0
                    st.session_state['mistakes'] = []
                    st.session_state['progress'] = []
                    st.session_state['feedback_message'] = None
                    st.session_state['user_input'] = ''
                    st.session_state['clear_input'] = False
                    # Remove progress file
                    if os.path.exists(progress_file):
                        os.remove(progress_file)
                    st.rerun()
                else:
                    st.info("No mistakes to practice.")

            # Option to reset progress
            if st.button("Reset Progress"):
                reset_confirm = st.warning("Are you sure you want to reset all progress? This cannot be undone.")
                if st.button("Yes, Reset Progress"):
                    # Remove progress file
                    if os.path.exists(progress_file):
                        os.remove(progress_file)
                    # Reset session state variables related to practice
                    st.session_state['progress'] = []
                    st.session_state['current_index'] = 0
                    st.session_state['mistakes'] = []
                    st.session_state['feedback_message'] = None
                    st.session_state['user_input'] = ''
                    st.session_state['clear_input'] = False
                    st.success("Progress has been reset.")
                    st.rerun()
                if st.button("Cancel"):
                    st.session_state['reset_confirmation'] = False

    # ---------------------------
    # Review Answers Page
    # ---------------------------
    
    elif st.session_state['page'] == 'Review Answers':
        st.header("Review Your Answers")

        # Load progress data
        user_progress_dir = os.path.join(PROGRESS_DIR, username)
        create_dir(user_progress_dir)

        # Get all progress files for the user
        progress_files = [f for f in os.listdir(user_progress_dir) if f.endswith('.json')]
        if not progress_files:
            st.info("No answers to review yet. Start practicing!")
        else:
            # Select which progress file to review
            selected_progress_file = st.selectbox("Select exercise to review", progress_files)
            with open(os.path.join(user_progress_dir, selected_progress_file), 'r') as f:
                progress_data = json.load(f)

            # Filter options
            filter_option = st.selectbox("Filter by:", ["All", "Correct", "Incorrect"])

            # Prepare data for display
            progress_df = pd.DataFrame(progress_data)
            if filter_option == "Correct":
                progress_df = progress_df[progress_df['correct'] == True]
            elif filter_option == "Incorrect":
                progress_df = progress_df[progress_df['correct'] == False]

            if not progress_df.empty:
                st.dataframe(progress_df[['timestamp', 'question', 'your_answer', 'correct_answer', 'correct']].sort_values(by='timestamp', ascending=False))
            else:
                st.info("No records match the selected filter.")

            # Option to reset progress with confirmation
            if st.button("Reset Progress for this Exercise"):
                reset_confirm = st.warning("Are you sure you want to reset progress for this exercise? This cannot be undone.")
                if st.button("Yes, Reset"):
                    progress_file_path = os.path.join(user_progress_dir, selected_progress_file)
                    if os.path.exists(progress_file_path):
                        os.remove(progress_file_path)
                    st.success("Progress has been reset.")
                    st.rerun()
                if st.button("Cancel"):
                    st.session_state['reset_confirmation'] = False

    # ---------------------------
    # Upload Exercise Page
    # ---------------------------
    
    elif st.session_state['page'] == 'Upload Exercise':
        st.header("Upload a New Exercise")
        st.write("Please upload a TXT file (tab-separated) or a CSV file with two columns: 'Turkish' and 'English'.")

        uploaded_file = st.file_uploader("Choose a file", type=['txt', 'csv'])
        custom_exercise_name = st.text_input("Custom Exercise Name")
        if st.button("Upload Exercise"):
            if uploaded_file and custom_exercise_name:
                handle_exercise_upload(uploaded_file, custom_exercise_name, username, EXERCISES_DIR)
            else:
                st.error("Please provide both a file and a custom exercise name.")

    # ---------------------------
    # Practice Mistakes Page
    # ---------------------------
    
    elif st.session_state['page'] == 'Practice Mistakes':
        st.header("Practice Mistakes")

        # Load progress data
        user_progress_dir = os.path.join(PROGRESS_DIR, username)
        create_dir(user_progress_dir)

        # Get all progress files for the user
        progress_files = [f for f in os.listdir(user_progress_dir) if f.endswith('.json')]
        if not progress_files:
            st.info("No progress available to practice mistakes.")
        else:
            # Select which progress file to use
            selected_progress_file = st.selectbox("Select exercise to practice mistakes", progress_files)
            progress_file = os.path.join(user_progress_dir, selected_progress_file)

            with open(progress_file, 'r') as f:
                progress_data = json.load(f)

            # Select practice type
            practice_option = st.radio("Practice Type:", ["All Wrong Answers", "Uncorrected Only"])

            if practice_option == "All Wrong Answers":
                mistakes_to_practice = [item['word_pair'] for item in progress_data if not item['correct']]
            else:
                mistakes_to_practice = [item['word_pair'] for item in progress_data if not item['correct'] and not item.get('corrected', False)]

            if not mistakes_to_practice:
                st.info("No mistakes to practice in the selected option.")
            else:
                # Shuffle the mistakes list
                random.shuffle(mistakes_to_practice)

                # Initialize session state for practicing mistakes
                if 'initialized_mistakes' not in st.session_state:
                    st.session_state['initialized_mistakes'] = True
                    st.session_state['mistakes_word_list'] = mistakes_to_practice.copy()
                    st.session_state['mistakes_current_index'] = 0
                    st.session_state['mistakes_feedback_message'] = None
                    st.session_state['mistakes_user_input'] = ''
                    st.session_state['mistakes_clear_input'] = False

                # Display the latest feedback message
                if st.session_state.get('mistakes_feedback_message'):
                    msg_type, msg = st.session_state['mistakes_feedback_message']
                    if msg_type == 'success':
                        st.success(msg)
                    else:
                        st.error(msg)

                # Display progress bar and current word number
                total_mistakes = len(st.session_state['mistakes_word_list'])
                current_mistake_index = st.session_state['mistakes_current_index']
                if current_mistake_index < total_mistakes:
                    progress_percent = current_mistake_index / total_mistakes
                else:
                    progress_percent = 1.0
                st.progress(progress_percent)
                st.write(f"Mistake {min(current_mistake_index + 1, total_mistakes)} of {total_mistakes}")

                # Before creating the text_input, check if we need to clear the input
                if st.session_state.get('mistakes_clear_input', False):
                    st.session_state['mistakes_user_input'] = ''
                    st.session_state['mistakes_clear_input'] = False

                # Main quiz logic for mistakes
                if current_mistake_index < total_mistakes:
                    current_word_pair = st.session_state['mistakes_word_list'][current_mistake_index]
                    if 'Turkish' in current_word_pair:
                        question = current_word_pair['Turkish']
                        answer = current_word_pair['English']
                        tts_language = 'tr'
                    else:
                        question = current_word_pair['English']
                        answer = current_word_pair['Turkish']
                        tts_language = 'en'

                    # Display the word in a flashcard
                    st.markdown(f'<div class="flashcard">{question}</div>', unsafe_allow_html=True)

                    # Option to hear the pronunciation
                    if st.button("Hear Pronunciation"):
                        audio_html = tts_audio(question, tts_language)
                        st.markdown(audio_html, unsafe_allow_html=True)

                    # Use a form to allow Enter key submission
                    with st.form(key='mistakes_answer_form', clear_on_submit=True):
                        mistakes_user_input = st.text_input("Your answer:", key='mistakes_user_input')
                        mistakes_submit = st.form_submit_button(label='Submit')

                    if mistakes_submit:
                        # Get the user's input from session state
                        mistakes_user_input = st.session_state['mistakes_user_input']

                        # Split the correct answer into multiple acceptable answers
                        acceptable_answers_raw = [ans.strip() for ans in answer.split(',')]
                        # Expand each acceptable answer to account for optional text in parentheses
                        acceptable_answers = []
                        for ans in acceptable_answers_raw:
                            expanded = expand_parentheses(ans)
                            acceptable_answers.extend(expanded)
                        # Remove duplicates from acceptable answers
                        acceptable_answers = list(set(acceptable_answers))
                        # Check if the user's input matches any of the acceptable answers
                        correct = False
                        for ans in acceptable_answers:
                            is_correct, original_ans = compare_strings(mistakes_user_input, ans, 80, True)
                            if is_correct:
                                correct = True
                                break

                        # Update feedback message in session state
                        if correct:
                            feedback = f"Correct! Your answer: **{original_ans}**"
                            st.session_state['mistakes_feedback_message'] = ('success', feedback)
                            # Optionally mark as corrected
                            for item in st.session_state['progress']:
                                if item['word_pair'] == current_word_pair and not item['correct']:
                                    item['correct'] = True
                                    item['corrected'] = True
                            # Remove from mistakes_word_list
                            st.session_state['mistakes_word_list'].pop(current_mistake_index)
                        else:
                            feedback = f"Incorrect! Your answer: **{mistakes_user_input}**. Acceptable answers were: **{', '.join(acceptable_answers)}**"
                            st.session_state['mistakes_feedback_message'] = ('error', feedback)
                            # Keep the mistake in the list
                            st.session_state['mistakes_word_list'][current_mistake_index] = current_word_pair

                        # Save progress with timestamp
                        st.session_state['progress'].append({
                            'question': question,
                            'your_answer': mistakes_user_input,
                            'correct_answer': answer,
                            'correct': correct,
                            'timestamp': datetime.now().isoformat(),
                            'word_pair': current_word_pair  # For mistake practice
                        })
                        st.session_state['mistakes_current_index'] += 1
                        # Save progress to a file
                        with open(progress_file, 'w') as f:
                            json.dump(st.session_state['progress'], f)
                        # Set the flag to clear the input on next run
                        st.session_state['mistakes_clear_input'] = True
                        # Rerun the script to update the page
                        st.rerun()
                else:
                    st.write("You have completed all mistakes in this exercise!")
                    # Option to return to practice
                    if st.button("Return to Practice"):
                        st.session_state['page'] = 'Practice'
                        st.rerun()

    # ---------------------------
    # Review Answers Page
    # ---------------------------
    
    elif st.session_state['page'] == 'Review Answers':
        st.header("Review Your Answers")

        # Load progress data
        user_progress_dir = os.path.join(PROGRESS_DIR, username)
        create_dir(user_progress_dir)

        # Get all progress files for the user
        progress_files = [f for f in os.listdir(user_progress_dir) if f.endswith('.json')]
        if not progress_files:
            st.info("No answers to review yet. Start practicing!")
        else:
            # Select which progress file to review
            selected_progress_file = st.selectbox("Select exercise to review", progress_files)
            with open(os.path.join(user_progress_dir, selected_progress_file), 'r') as f:
                progress_data = json.load(f)

            # Filter options
            filter_option = st.selectbox("Filter by:", ["All", "Correct", "Incorrect"])

            # Prepare data for display
            progress_df = pd.DataFrame(progress_data)
            if filter_option == "Correct":
                progress_df = progress_df[progress_df['correct'] == True]
            elif filter_option == "Incorrect":
                progress_df = progress_df[progress_df['correct'] == False]

            if not progress_df.empty:
                st.dataframe(progress_df[['timestamp', 'question', 'your_answer', 'correct_answer', 'correct']].sort_values(by='timestamp', ascending=False))
            else:
                st.info("No records match the selected filter.")

            # Option to reset progress with confirmation
            if st.button("Reset Progress for this Exercise"):
                reset_confirm = st.warning("Are you sure you want to reset progress for this exercise? This cannot be undone.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes, Reset Progress"):
                        progress_file_path = os.path.join(user_progress_dir, selected_progress_file)
                        if os.path.exists(progress_file_path):
                            os.remove(progress_file_path)
                        # Reset session state variables related to practice
                        st.session_state['progress'] = []
                        st.session_state['current_index'] = 0
                        st.session_state['mistakes'] = []
                        st.session_state['feedback_message'] = None
                        st.session_state['user_input'] = ''
                        st.session_state['clear_input'] = False
                        st.success("Progress has been reset.")
                        st.rerun()
                with col2:
                    if st.button("Cancel"):
                        st.session_state['reset_confirmation'] = False

    # ---------------------------
    # Upload Exercise Page
    # ---------------------------
    
    elif st.session_state['page'] == 'Upload Exercise':
        st.header("Upload a New Exercise")
        st.write("Please upload a TXT file (tab-separated) or a CSV file with two columns: 'Turkish' and 'English'.")

        uploaded_file = st.file_uploader("Choose a file", type=['txt', 'csv'])
        custom_exercise_name = st.text_input("Custom Exercise Name")
        if st.button("Upload Exercise"):
            handle_exercise_upload(uploaded_file, custom_exercise_name, username, EXERCISES_DIR)

    # ---------------------------
    # Practice Mistakes Page (Alternative Implementation)
    # ---------------------------
    
    # Note: The 'Practice Mistakes' functionality is already integrated within the 'Practice' page.
    # If additional functionality is needed, implement it here.

    # ---------------------------
    # Additional Notes
    # ---------------------------
    
    # Ensure that all pages handle 'progress_file' correctly by defining it within their scope.
    # Avoid modifying session_state variables associated with widget keys after widget creation.
