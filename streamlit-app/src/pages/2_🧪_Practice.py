# src/pages/2_Practice.py

import streamlit as st
import random

from sections.components import apply_custom_css
from sections.practice_utils import practice_logic

def app():
    st.title("Practice Page")
    apply_custom_css()

    practice_session = st.session_state.get('practice_session', None)
    if not practice_session:
        st.error("No active practice session found. Please go to Main Menu to start an exercise.")
        return

    # For the "practice" mode, we rely on practice_session.practice_sets
    available_directions = list(practice_session.practice_sets.keys())
    if not available_directions:
        st.error("No practice data found. Please go back to the Main Menu and start or load an exercise.")
        return

    selected_direction = st.sidebar.selectbox("Select Practice Direction", available_directions)
    tolerance = st.sidebar.slider("Tolerance for typos (0 to 100)", 0, 100, practice_session.tolerance)
    ignore_accents = st.sidebar.checkbox("Ignore accents", value=practice_session.ignore_accents)

    # Update session state
    practice_session.tolerance = tolerance
    practice_session.ignore_accents = ignore_accents

    # Mark the practice as started if not already
    practice_set = practice_session.practice_sets[selected_direction]
    if not practice_set.practice_started:
        practice_set.practice_started = True

    # Proceed with the actual practice logic
    practice_logic(
        practice_session=practice_session,
        mode='practice',
        direction=selected_direction
    )


app()
