# src/pages/3_Mistakes.py

import streamlit as st
import random

from sections.components import apply_custom_css
from sections.practice_utils import practice_logic

def app():
    st.title("Practice Your Mistakes")
    apply_custom_css()

    practice_session = st.session_state.get('practice_session', None)
    if not practice_session:
        st.error("No active practice session found. Please go to Main Menu to start or load an exercise.")
        return

    available_directions = list(practice_session.mistakes_sets.keys())
    if not available_directions:
        st.info("No mistakes to practice right now!")
        return

    selected_direction = st.selectbox("Select Mistakes Direction", available_directions)
    tolerance = st.slider("Tolerance for typos (0 to 100)", 0, 100, practice_session.tolerance)
    ignore_accents = st.checkbox("Ignore accents", value=practice_session.ignore_accents)

    practice_session.tolerance = tolerance
    practice_session.ignore_accents = ignore_accents

    practice_set = practice_session.mistakes_sets[selected_direction]
    if not practice_set.practice_started:
        practice_set.practice_started = True

    practice_logic(
        practice_session=practice_session,
        mode='mistakes',
        direction=selected_direction
    )


app()
