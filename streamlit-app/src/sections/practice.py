import streamlit as st
import os
import random
import json
from datetime import datetime
from utils.helpers import compare_strings, expand_parentheses, get_progress_file, load_exercise, create_dir, get_exercises, tts_audio

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
    .feedback {
        margin-top: 20px;
    }
    .options {
        font-size: 12px;
        color: gray;
    }
    </style>
    """, unsafe_allow_html=True)

def show():
    st.header("Practice Exercises")
    
    username = st.session_state.get('username')
    EXERCISES_DIR = "exercises"
    PROGRESS_DIR = "progress"
    
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
        st.session_state['current_word_pair'] = None
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
        st.session_state['current_word_pair'] = None
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

    # Calculate counts
    num_correct = sum(1 for item in st.session_state['progress'] if item['correct'])
    num_incorrect = sum(1 for item in st.session_state['progress'] if not item['correct'])

    # Display progress bar and current word number
    total_words = len(st.session_state['word_list'])
    current_index = st.session_state['current_index']
    
    if current_index < total_words:
        progress_percent = current_index / total_words
    else:
        progress_percent = 1.0
    st.progress(progress_percent)
    st.write(f"Word {min(current_index + 1, total_words)} of {total_words} — ✅ {num_correct} | ❌ {num_incorrect}")

    # Display feedback message (if any)
    if 'feedback_message' in st.session_state and st.session_state['feedback_message'] is not None:
        msg_type, msg = st.session_state['feedback_message']
        if msg_type == 'success':
            st.success(msg, icon="✅")
        else:
            st.error(msg, icon="❌")

    # Before creating the text_input, check if we need to clear the input
    if st.session_state.get('clear_input', False):
        if 'user_input' in st.session_state:
            del st.session_state['user_input']
        st.session_state['clear_input'] = False

    # Main quiz logic
    if current_index < total_words:
        # Display the question and get user input
        current_word_pair = st.session_state['word_list'][current_index]
        st.session_state['current_word_pair'] = current_word_pair  # Store current word pair
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
            # Clear previous feedback message
            st.session_state['feedback_message'] = None

            # Get the user's input from session state
            user_input = st.session_state['user_input']

            # Process the answer
            acceptable_answers_raw = [ans.strip() for ans in answer.split(',')]
            acceptable_answers = []
            for ans in acceptable_answers_raw:
                expanded = expand_parentheses(ans)
                acceptable_answers.extend(expanded)
            acceptable_answers = list(set(acceptable_answers))
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
                if current_word_pair in st.session_state['mistakes']:
                    st.session_state['mistakes'].remove(current_word_pair)
            else:
                feedback = f"Incorrect! Your answer: **{user_input}**. Acceptable answers were: **{', '.join(acceptable_answers)}**"
                st.session_state['feedback_message'] = ('error', feedback)
                if current_word_pair not in st.session_state['mistakes']:
                    st.session_state['mistakes'].append(current_word_pair)

            # Save progress with timestamp
            st.session_state['progress'].append({
                'question': question,
                'your_answer': user_input,
                'correct_answer': answer,
                'correct': correct,
                'timestamp': datetime.now().isoformat(),
                'word_pair': current_word_pair
            })
            with open(progress_file, 'w') as f:
                json.dump(st.session_state['progress'], f)

            # Prepare for next question
            st.session_state['current_index'] += 1
            st.session_state['clear_input'] = True

            # Since we're not rerunning, manually refresh the page elements
            st.rerun()

    else:
        st.write("You have completed all words in this exercise!")

        # Option to practice mistakes
        if st.button("Practice Mistakes"):
            if st.session_state['mistakes']:
                st.session_state['word_list'] = st.session_state['mistakes']
                random.shuffle(st.session_state['word_list'])
                st.session_state['current_index'] = 0
                st.session_state['mistakes'] = []
                st.session_state['progress'] = []
                st.session_state['feedback_message'] = None
                st.session_state['clear_input'] = True
                st.session_state['current_word_pair'] = None
                st.rerun()
            else:
                st.info("No mistakes to practice.")
        if st.button("Reset Progress"):
            st.session_state['current_index'] = 0
            st.session_state['mistakes'] = []
            st.session_state['progress'] = []
            st.session_state['feedback_message'] = None
            st.session_state['current_word_pair'] = None
            st.session_state['clear_input'] = True
            st.success("Progress has been reset.")
            st.rerun()

    # Non-intrusive options
    if 'current_word_pair' in st.session_state and st.session_state['current_word_pair'] is not None:
        with st.expander("Options"):
            col1, col2 = st.columns(2)
            with col1:
                if st.button('Change Assessment'):
                    # Reverse the 'correct' value
                    st.session_state['progress'][-1]['correct'] = not st.session_state['progress'][-1]['correct']
                    # Update mistakes list
                    if st.session_state['progress'][-1]['correct']:
                        if st.session_state['current_word_pair'] in st.session_state['mistakes']:
                            st.session_state['mistakes'].remove(st.session_state['current_word_pair'])
                        feedback = f"Corrected to correct. Your answer: **{st.session_state['progress'][-1]['your_answer']}**"
                        st.success(feedback)
                    else:
                        if st.session_state['current_word_pair'] not in st.session_state['mistakes']:
                            st.session_state['mistakes'].append(st.session_state['current_word_pair'])
                        feedback = f"Corrected to incorrect. Your answer: **{st.session_state['progress'][-1]['your_answer']}**"
                        st.error(feedback)
                    # Update progress file
                    with open(progress_file, 'w') as f:
                        json.dump(st.session_state['progress'], f)
            with col2:
                if st.button('Remove this question'):
                    # Remove the current word pair
                    st.session_state['word_list'].pop(current_index - 1)
                    if st.session_state['current_word_pair'] in st.session_state['mistakes']:
                        st.session_state['mistakes'].remove(st.session_state['current_word_pair'])
                    # Remove the last progress entry
                    st.session_state['progress'].pop()
                    # Update progress file
                    with open(progress_file, 'w') as f:
                        json.dump(st.session_state['progress'], f)
                    st.success('Question removed from test set.')
                    # Adjust total_words since the word_list has changed
                    total_words = len(st.session_state['word_list'])
                    if current_index - 1 >= total_words:
                        st.write("You have completed all words in this exercise!")
                        st.stop()

show()
