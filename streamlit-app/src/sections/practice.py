# sections/practice.py

import streamlit as st
from sections.components import apply_custom_css
from sections.practice_utils import practice_logic
from utils.helpers import LANGUAGE_OPTIONS
import random

def show_practice(practice_session, cookies):
    apply_custom_css()
    current_mode = 'practice'  # Set mode to 'practice'

    st.title("Practice New Words")

    # Check if we have exercise data
    if practice_session.exercise_df is None or practice_session.exercise_df.empty:
        st.error("No exercise data found. Please go back and upload an exercise file.")
        st.stop()

    # Initialize direction options
    practice_session.direction_options = [
        f"{practice_session.source_language} to {practice_session.target_language}",
        f"{practice_session.target_language} to {practice_session.source_language}"
    ]

    # Set default direction if not already set or mode has changed
    if practice_session.current_mode != current_mode or not practice_session.direction:
        practice_session.direction = practice_session.direction_options[0]
        practice_session.direction_radio = practice_session.direction

    # Sidebar elements for direction, tolerance, and ignore accents
    source_language = practice_session.source_language
    target_language = practice_session.target_language

    selected_direction = st.sidebar.radio(
        "Select practice direction",
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
    # Initialize the practice session if not started or mode changed
    if not practice_session.practice_started or practice_session.current_mode != current_mode:
        practice_session.load_progress()
        practice_session.current_mode = current_mode
        practice_session.practice_started = True
        # **Reset word_list to original_word_list**
        practice_session.word_list = practice_session.original_word_list.copy()
        random.shuffle(practice_session.word_list)
        practice_session.current_index = 0
        st.rerun()

    # Proceed with the practice logic
    if practice_session.practice_started and practice_session.current_mode == current_mode:
        practice_logic(practice_session, cookies, mode=current_mode)
