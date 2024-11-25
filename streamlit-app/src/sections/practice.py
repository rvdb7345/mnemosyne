# src/sections/practice.py

import streamlit as st
from sections.components import apply_custom_css
from sections.practice_utils import practice_logic
import random

# src/sections/practice.py

import streamlit as st
from sections.components import apply_custom_css
from sections.practice_utils import practice_logic
import random

def show_practice(practice_session, cookies, mode='practice'):
    apply_custom_css()
    current_mode = mode  # 'practice' or 'mistakes'

    st.title("Practice" if mode == 'practice' else "Practice Mistakes")

    # Check if we have exercise or mistakes data
    if current_mode == 'practice':
        available_directions = list(practice_session.practice_sets.keys())
        if not available_directions:
            st.error("No practice data found. Please go back and upload an exercise file.")
            st.stop()
    elif current_mode == 'mistakes':
        available_directions = list(practice_session.mistakes_sets.keys())
        if not available_directions:
            st.info("No mistakes to practice.")
            return

    # Sidebar: Select Direction
    selected_direction = st.sidebar.selectbox(
        "Select Practice Direction",
        available_directions,
        key=f'select_direction_{mode}'
    )

    # Update tolerance and ignore accents settings
    tolerance = st.sidebar.slider(
        "Tolerance for typos (0 to 100)",
        min_value=0,
        max_value=100,
        value=practice_session.tolerance,
        key=f'tolerance_{mode}'
    )
    practice_session.tolerance = tolerance

    ignore_accents = st.sidebar.checkbox(
        "Ignore accents",
        value=practice_session.ignore_accents,
        key=f'ignore_accents_{mode}'
    )
    practice_session.ignore_accents = ignore_accents

    # Initialize the practice session if not started
    practice_set = practice_session.practice_sets.get(selected_direction) if mode == 'practice' else practice_session.mistakes_sets.get(selected_direction)
    if practice_set and not practice_set.practice_started:
        practice_set.practice_started = True
        st.rerun()

    # Proceed with the practice logic
    if practice_set and practice_set.practice_started:
        practice_logic(practice_session, cookies, mode=mode, direction=selected_direction)
