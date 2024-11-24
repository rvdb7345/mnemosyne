# sections/mistakes.py

import streamlit as st
from sections.components import apply_custom_css
from sections.practice_utils import practice_logic
from utils.helpers import LANGUAGE_OPTIONS

def show_mistakes(practice_session, cookies):
    apply_custom_css()
    current_mode = 'mistakes'  # Set mode to 'mistakes'

    st.title("Practice Mistakes")

    if not practice_session.mistakes:
        st.info("No mistakes to practice.")
        return

    # Initialize direction options
    practice_session.direction_options = [
        f"{practice_session.source_language} to {practice_session.target_language}",
        f"{practice_session.target_language} to {practice_session.source_language}"
    ]

    # Set default direction if not already set or mode has changed
    if practice_session.current_mode != current_mode or not practice_session.direction:
        practice_session.direction = practice_session.direction_options[0]
        practice_session.direction_radio = practice_session.direction

    # Allow user to select direction
    selected_direction = st.sidebar.radio(
        "Select practice direction",
        practice_session.direction_options,
        index=practice_session.direction_options.index(practice_session.direction_radio)
    )

    if selected_direction != practice_session.direction_radio:
        practice_session.direction_radio = selected_direction
        practice_session.direction = practice_session.direction_radio
        st.rerun()
        
    # Initialize the mistakes practice session if not started or mode changed
    if not practice_session.practice_started or practice_session.current_mode != current_mode:
        # practice_session.practice_mistakes()
        practice_session.current_mode = current_mode
        practice_session.practice_started = True
        st.rerun()

    # Proceed with the practice logic
    if practice_session.practice_started and practice_session.current_mode == current_mode:
        practice_session.practice_mistakes()
        practice_logic(practice_session, cookies, mode=current_mode)