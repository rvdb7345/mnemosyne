import streamlit as st
import random
import json
from datetime import datetime
from dataclasses import dataclass, field
from utils.helpers import compare_strings, expand_parentheses, tts_audio, LANGUAGE_OPTIONS
import pandas as pd

@dataclass
class PracticeSession:
    # Fields
    practice_started: bool = False
    progress_data: dict = field(default_factory=dict)
    direction: str = ''
    direction_radio: str = ''
    tolerance: int = 80
    ignore_accents: bool = False
    exercise_df: pd.DataFrame = None
    exercise_name: str = ''
    source_language: str = 'Source'
    target_language: str = 'Target'
    direction_options: list = field(default_factory=list)
    word_list: list = field(default_factory=list)
    current_index: int = 0
    mistakes: list = field(default_factory=list)
    progress: list = field(default_factory=list)
    pronounce_answer_trigger: bool = False
    pronounce_answer_text: str = ''
    pronounce_answer_lang: str = ''
    current_word_pair: dict = field(default_factory=dict)
    clear_input: bool = False
    last_feedback_message: tuple = None  # Feedback message to display

    # Methods (same as before, with minor adjustments)
    def initialize_base_settings(self):
        """Initialize or reset the base settings for the practice session."""
        self.word_list = self.exercise_df.to_dict('records')
        random.shuffle(self.word_list)
        self.current_index = 0
        self.mistakes = []
        self.progress = []
        self.pronounce_answer_trigger = False
        self.pronounce_answer_text = ''
        self.pronounce_answer_lang = ''
        self.current_word_pair = {}
        self.clear_input = True
        self.last_feedback_message = None  # Reset feedback message

    def reset_progress(self):
        """Reset the progress for the current direction."""
        self.initialize_base_settings()
        # Remove progress data for current direction
        direction_key = self.direction.replace(" ", "_").lower()
        progress_data = self.progress_data or {}
        if direction_key in progress_data:
            del progress_data[direction_key]
        self.progress_data = progress_data

    def load_progress(self):
        """Load progress for the current direction."""
        direction_key = self.direction.replace(" ", "_").lower()
        progress_data = self.progress_data or {}
        if direction_key in progress_data:
            direction_progress = progress_data[direction_key]
            self.word_list = direction_progress['word_list']
            self.current_index = direction_progress['current_index']
            self.mistakes = direction_progress['mistakes']
            self.progress = direction_progress['progress']
            self.pronounce_answer_trigger = False
            self.practice_started = True
            self.last_feedback_message = None  # Reset feedback message
        else:
            # Initialize for the new direction
            self.initialize_base_settings()

    def save_progress_data(self, cookies):
        """Save progress data to the session and cookies."""
        progress_data = self.progress_data or {}
        direction_key = self.direction.replace(" ", "_").lower()
        progress_data[direction_key] = {
            'word_list': self.word_list,
            'current_index': self.current_index,
            'mistakes': self.mistakes,
            'progress': self.progress,
            # Exclude 'feedback_message' to prevent serialization issues
        }
        # Include additional session state data
        progress_data['source_language'] = self.source_language
        progress_data['target_language'] = self.target_language
        progress_data['exercise_name'] = self.exercise_name
        progress_data['tolerance'] = self.tolerance
        progress_data['ignore_accents'] = self.ignore_accents
        # Save progress data to practice_session for downloading
        self.progress_data = progress_data
        progress_json = json.dumps(progress_data)
        # Save progress data to cookies
        cookies.set('progress_data', progress_json)

    def update_progress(self, question, user_input, answer, correct, current_word_pair):
        """Update the progress after an answer is submitted."""
        self.progress.append({
            'question': question,
            'your_answer': user_input,
            'correct_answer': answer,
            'correct': correct,
            'timestamp': datetime.now().isoformat(),
            'word_pair': current_word_pair
        })
        self.current_index += 1
        self.clear_input = True

    def practice_mistakes(self):
        """Set up the session to practice mistakes."""
        self.word_list = self.mistakes.copy()
        random.shuffle(self.word_list)
        self.current_index = 0
        self.mistakes = []
        self.progress = []
        self.last_feedback_message = None
        self.clear_input = True
        self.current_word_pair = None
        self.pronounce_answer_trigger = False
        self.pronounce_answer_text = ''
        self.pronounce_answer_lang = ''

def show(cookies):
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

    # Check if we have exercise data in session_state
    if 'exercise_df' not in st.session_state:
        st.error("No exercise data found. Please go back and upload an exercise file.")
        st.stop()

    # Initialize practice session if not already in session_state
    if 'practice_session' not in st.session_state:
        st.session_state['practice_session'] = PracticeSession()
        # Set initial values from session_state
        practice_session = st.session_state['practice_session']
        practice_session.exercise_df = st.session_state['exercise_df']
        practice_session.exercise_name = st.session_state.get('exercise_name', 'Exercise')
        practice_session.source_language = st.session_state.get('source_language', 'Source')
        practice_session.target_language = st.session_state.get('target_language', 'Target')
        practice_session.direction_options = [
            f"{practice_session.source_language} to {practice_session.target_language}",
            f"{practice_session.target_language} to {practice_session.source_language}"
        ]
        practice_session.direction = practice_session.direction_options[0]
        practice_session.direction_radio = practice_session.direction
    else:
        practice_session = st.session_state['practice_session']

    # Sidebar elements for direction, tolerance, and ignore accents
    source_language = practice_session.source_language
    target_language = practice_session.target_language

    selected_direction = st.sidebar.radio(
        f"Select practice direction ({source_language} to {target_language})",
        practice_session.direction_options,
        index=practice_session.direction_options.index(practice_session.direction_radio)
    )

    if selected_direction != practice_session.direction_radio:
        practice_session.direction_radio = selected_direction
        practice_session.direction = practice_session.direction_radio
        # Load progress for the new direction
        practice_session.load_progress()
        st.rerun()

    practice_session.tolerance = st.sidebar.slider(
        "Tolerance for typos (0 to 100)",
        min_value=0,
        max_value=100,
        value=practice_session.tolerance
    )

    practice_session.ignore_accents = st.sidebar.checkbox(
        "Ignore accents",
        value=practice_session.ignore_accents
    )

    if not practice_session.practice_started:
        if st.button('Start Practice', key='start_practice_button'):
            # Initialize practice session variables
            practice_session.practice_started = True
            practice_session.load_progress()
            st.rerun()

    # Proceed with the practice logic
    if practice_session.practice_started:
        practice_logic(practice_session, cookies)

def practice_logic(practice_session, cookies):
    source_language = practice_session.source_language
    target_language = practice_session.target_language
    source_language_code = LANGUAGE_OPTIONS.get(source_language, "en")
    target_language_code = LANGUAGE_OPTIONS.get(target_language, "en")
    direction = practice_session.direction
    tolerance = practice_session.tolerance
    ignore_accents = practice_session.ignore_accents
    exercise_name = practice_session.exercise_name

    # Calculate counts
    num_correct = sum(1 for item in practice_session.progress if item['correct'])
    num_incorrect = sum(1 for item in practice_session.progress if not item['correct'])

    # Display progress bar and current word number
    total_words = len(practice_session.word_list)
    current_index = practice_session.current_index

    if current_index < total_words:
        progress_percent = current_index / total_words
    else:
        progress_percent = 1.0
    st.progress(progress_percent)
    st.write(f"Word {min(current_index + 1, total_words)} of {total_words} — ✅ {num_correct} | ❌ {num_incorrect}")

    # Display feedback message (if any)
    if practice_session.last_feedback_message is not None:
        msg_type, msg = practice_session.last_feedback_message
        if msg_type == 'success':
            st.success(msg, icon="✅")
        else:
            st.error(msg, icon="❌")

    # Before creating the text_input, check if we need to clear the input
    if practice_session.clear_input:
        if 'user_input' in st.session_state:
            del st.session_state['user_input']
        practice_session.clear_input = False

    # Main quiz logic
    if current_index < total_words:
        # Display the question and get user input
        current_word_pair = practice_session.word_list[current_index]
        practice_session.current_word_pair = current_word_pair
        if direction == f"{source_language} to {target_language}":
            question = current_word_pair[source_language]
            answer = current_word_pair[target_language]
            tts_language = source_language_code
        else:
            question = current_word_pair[target_language]
            answer = current_word_pair[source_language]
            tts_language = target_language_code

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
            practice_session.last_feedback_message = None

            # Get the user's input
            user_input = st.session_state.get('user_input', '')

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

            # Update feedback message
            if correct:
                feedback = f"Correct! Your answer: **{original_ans}**"
                practice_session.last_feedback_message = ('success', feedback)
                if current_word_pair in practice_session.mistakes:
                    practice_session.mistakes.remove(current_word_pair)
            else:
                feedback = f"Incorrect! Your answer: **{user_input}**. Acceptable answers were: **{', '.join(acceptable_answers)}**"
                practice_session.last_feedback_message = ('error', feedback)
                if current_word_pair not in practice_session.mistakes:
                    practice_session.mistakes.append(current_word_pair)

            # Set flag to hear answer pronunciation automatically
            practice_session.pronounce_answer_trigger = True
            practice_session.pronounce_answer_text = answer
            practice_session.pronounce_answer_lang = (
                target_language_code if direction == f"{source_language} to {target_language}" else source_language_code
            )

            # Update progress
            practice_session.update_progress(question, user_input, answer, correct, current_word_pair)

            # Save progress data
            practice_session.save_progress_data(cookies)

            # Clear the user input
            practice_session.clear_input = True

            st.rerun()

    else:
        st.write("You have completed all words in this exercise!")

    # Option to practice mistakes at any time
    if st.button("Practice Mistakes"):
        if practice_session.mistakes:
            practice_session.practice_mistakes()
            practice_session.save_progress_data(cookies)
            st.rerun()
        else:
            st.info("No mistakes to practice.")

    if st.button("Reset Progress"):
        practice_session.reset_progress()
        practice_session.save_progress_data(cookies)
        st.success("Progress has been reset.")
        # Remove progress data from cookies
        if 'progress_data' in cookies:
            cookies.delete('progress_data')
        st.rerun()

    # Option to download progress
    if st.button("Generate Downloadable Progress"):
        # Save current progress data
        practice_session.save_progress_data(cookies)
        # Prepare progress data
        progress_data = practice_session.progress_data
        progress_json = json.dumps(progress_data)
        # Create a download button
        st.download_button(
            label="Download Progress",
            data=progress_json,
            file_name=f"{practice_session.exercise_name}_progress.json",
            mime="application/json"
        )

    # Non-intrusive options
    if practice_session.current_word_pair:
        with st.expander("Options"):
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button('Change Assessment'):
                    change_assessment(practice_session, cookies)
            with col2:
                if st.button('Remove this question'):
                    remove_current_question(practice_session, cookies)
            with col3:
                if st.button("Pronounce Answer"):
                    pronounce_answer(practice_session)

def change_assessment(practice_session, cookies):
    # Reverse the 'correct' value
    practice_session.progress[-1]['correct'] = not practice_session.progress[-1]['correct']
    # Update mistakes list
    current_word_pair = practice_session.current_word_pair
    if practice_session.progress[-1]['correct']:
        if current_word_pair in practice_session.mistakes:
            practice_session.mistakes.remove(current_word_pair)
        feedback = f"Corrected to correct. Your answer: **{practice_session.progress[-1]['your_answer']}**"
        st.success(feedback)
    else:
        if current_word_pair not in practice_session.mistakes:
            practice_session.mistakes.append(current_word_pair)
        feedback = f"Corrected to incorrect. Your answer: **{practice_session.progress[-1]['your_answer']}**"
        st.error(feedback)
    # Save progress data
    practice_session.save_progress_data(cookies)

def remove_current_question(practice_session, cookies):
    current_index = practice_session.current_index
    current_word_pair = practice_session.current_word_pair
    # Remove the current word pair
    practice_session.word_list.pop(current_index - 1)
    if current_word_pair in practice_session.mistakes:
        practice_session.mistakes.remove(current_word_pair)
    # Remove the last progress entry
    practice_session.progress.pop()
    # Adjust total_words since the word_list has changed
    total_words = len(practice_session.word_list)
    if current_index - 1 >= total_words:
        st.write("You have completed all words in this exercise!")
        st.stop()
    # Save progress data
    practice_session.save_progress_data(cookies)
    st.success('Question removed from test set.')

def pronounce_answer(practice_session):
    if practice_session.pronounce_answer_text:
        answer_audio_html = tts_audio(
            practice_session.pronounce_answer_text,
            practice_session.pronounce_answer_lang
        )
        st.markdown(answer_audio_html, unsafe_allow_html=True)
    else:
        st.markdown("No answer to pronounce yet", unsafe_allow_html=True)
