# src/sections/context_practice.py

import streamlit as st
import random
import logging

from sections.components import apply_custom_css, render_feedback
from sections.practice_session import PracticeSession, PracticeSet
from utils.helpers import tts_audio, LANGUAGE_OPTIONS
from utils.chatgpt_api import fetch_multiple_choice_data
from utils.chatgpt_schema import MultipleChoiceQuestion
import openai
from openai import OpenAI  # Updated import based on new SDK

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_mcq_data():
    if "mcq_data" in st.session_state:
        del st.session_state["mcq_data"]
    if "options" in st.session_state:
        del st.session_state["options"]

def app():
    st.title("ChatGPT Context Practice")
    apply_custom_css()

    # Sidebar: API Key Input
    st.sidebar.header("Configuration")
    api_key_input = st.sidebar.text_input("OpenAI API Key", type="password")
    if "api_key" not in st.session_state:
        st.session_state.api_key = api_key_input
        openai.api_key = api_key_input

    if not api_key_input:
        st.sidebar.warning(
            "Please enter your OpenAI API Key to enable ChatGPT functionalities."
        )
        st.stop()  # Stop execution until API key is provided

    # Instantiate OpenAI client with the provided API key
    client = OpenAI(api_key=api_key_input)

    # Retrieve or initialize PracticeSession from session state
    practice_session: PracticeSession = st.session_state.get("practice_session", None)
    if not practice_session:
        st.error(
            "No active practice session found. Please go to Main Menu to start/load an exercise."
        )
        return

    # Let user choose configuration options
    st.sidebar.header("Settings")
    # Select difficulty level
    difficulty_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
    selected_difficulty = st.sidebar.selectbox(
        "Select Difficulty Level:", difficulty_levels, on_change=clear_mcq_data
    )

    # Show directions
    directions = [
        f"{practice_session.source_language} to {practice_session.target_language}",
        f"{practice_session.target_language} to {practice_session.source_language}",
    ]
    selected_direction = st.sidebar.selectbox("Direction:", directions, on_change=clear_mcq_data)
    
    # select your known language with a dirty hack for english to go first
    known_language_options = [practice_session.source_language, practice_session.target_language]
    if "English" in known_language_options and not known_language_options[0] == "English":
        known_language_options.remove("English")
        known_language_options.insert(0, "English")
    known_language = st.sidebar.selectbox("Known Language:", known_language_options, on_change=clear_mcq_data)

    # Show word sets
    word_set_options = ["full list", "mistakes"]
    selected_word_set = st.sidebar.selectbox("Word set:", word_set_options, on_change=clear_mcq_data)

    # Map selected_word_set to the corresponding context set
    if selected_word_set == "full list":
        context_set = practice_session.context_sets.get(selected_direction)
        word_set_key = "context_sets"
    else:
        context_set = practice_session.mistakes_context_sets.get(selected_direction)
        word_set_key = "mistakes_context_sets"

    # Initialize the context set if not already initialized
    if not context_set:
        context_set = PracticeSet()
        if selected_word_set == "full list":
            practice_session.context_sets[selected_direction] = context_set
        else:
            practice_session.mistakes_context_sets[selected_direction] = context_set

    render_feedback(context_set.last_feedback_message)

    # Populate context set if empty
    if not context_set.word_list:
        fill_context_set_from_source(
            practice_session, context_set, selected_direction, selected_word_set
        )
        # Save after initialization
        practice_session.save_progress_data()

    # Show progress
    pset = context_set
    current_index = pset.current_index
    total_words = len(pset.word_list)

    if total_words == 0:
        st.info(
            f"No words available for {selected_direction} in '{selected_word_set}' set."
        )
        return

    progress_frac = min(current_index / total_words, 1.0)
    st.progress(progress_frac)
    st.write(f"Word {min(current_index + 1, total_words)} of {total_words}")

    if current_index >= total_words:
        st.success("🎉 No more words left to study in this direction!")
        return

    # Identify current word pair
    current_word_pair = pset.word_list[current_index]
    src_lang = practice_session.source_language
    tgt_lang = practice_session.target_language
    src_code = LANGUAGE_OPTIONS.get(src_lang, "en")
    tgt_code = LANGUAGE_OPTIONS.get(tgt_lang, "en")

    if selected_direction == f"{src_lang} to {tgt_lang}":
        word_to_translate = current_word_pair.get(src_lang, "")
        correct_translation = current_word_pair.get(tgt_lang, "")
        from_code = src_code
        to_code = tgt_code
    else:
        word_to_translate = current_word_pair.get(tgt_lang, "")
        correct_translation = current_word_pair.get(src_lang, "")
        from_code = tgt_code
        to_code = src_code

    st.subheader("Translate the following word:")
    st.markdown(f"**{word_to_translate}**")

    # Fetch ChatGPT data
    if "mcq_data" not in st.session_state:
        with st.spinner("Fetching data from ChatGPT..."):
            mcq_response = fetch_multiple_choice_data(
                word=word_to_translate,
                translated_word=correct_translation,
                known_language=known_language,
                from_lang=selected_direction.split(" to ")[0],
                to_lang=selected_direction.split(" to ")[1],
                difficulty=selected_difficulty,
                client=client,
            )
            if mcq_response:
                st.session_state["mcq_data"] = mcq_response
            else:
                st.error("Failed to fetch multiple-choice data from ChatGPT.")
                return

            mcq_data: MultipleChoiceQuestion = st.session_state["mcq_data"]

            # Assemble multiple-choice options
            options = mcq_data.answer_options
            random.shuffle(options)
            st.session_state["options"] = options

    if "mcq_data" in st.session_state:
        # Display sentence with blank
        st.markdown("**Sentence with Blank:**")
        st.markdown(st.session_state["mcq_data"].question_sentence)

        # Display multiple-choice options
        st.markdown("**Choose the correct translation:**")
        
        with st.form(key=f'answer_form', clear_on_submit=True):
            user_selection = st.radio(
                "Options:", options=st.session_state["options"], key="mcq_options"
            )
            submit = st.form_submit_button(label='Submit')

    # Button to submit answer
    if submit:
        context_set.last_feedback_message = None  # clear previous feedback
        if user_selection.strip().lower() == st.session_state["mcq_data"].correct_answer.strip().lower():
            feedback = f"Correct! Your answer: **{user_selection}**"
            context_set.last_feedback_message = ("success", feedback)
            update_context_progress(
                correct=True,
                word_in_from_lang=word_to_translate,
                correct_translation=correct_translation,
                word_pair=current_word_pair,
                practice_session=practice_session,
                pset=pset,
                direction=selected_direction,
                word_set=selected_word_set,
            )
        else:
            feedback = (
                f"Incorrect! Your answer: **{user_selection}**. "
                f"Correct answer: **{st.session_state['mcq_data'].correct_answer}**"
            )
            context_set.last_feedback_message = ("error", feedback)
            update_context_progress(
                correct=False,
                word_in_from_lang=word_to_translate,
                correct_translation=st.session_state["mcq_data"].correct_answer,
                word_pair=current_word_pair,
                practice_session=practice_session,
                pset=pset,
                direction=selected_direction,
                word_set=selected_word_set,
            )

        # Clear the mcq_data for the next word
        del st.session_state["mcq_data"]
        st.rerun()

    # Button to reveal the correct translation
    if st.button("Reveal Translation"):
        st.info(f"The correct translation is: **{st.session_state['mcq_data'].correct_answer}**")
        
    if st.button("Reveal Sentence Translation"):
        st.info(f"{st.session_state['mcq_data'].full_sentence_translation}")

    # TTS Buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔊 Hear Word"):
            audio_html = tts_audio(word_to_translate, from_code)
            st.markdown(audio_html, unsafe_allow_html=True)
    with col2:
        if st.button("🔊 Hear Translation"):
            audio_html = tts_audio(correct_translation, to_code)
            st.markdown(audio_html, unsafe_allow_html=True)

    # "Options" expander
    with st.expander("Options"):
        col1, col2, col3 = st.columns(3)
        with col1:
            # Reset progress
            reset_label = (
                "Reset Progress"
                if selected_word_set == "full list"
                else "Reset Mistakes Progress"
            )
            if st.button(reset_label):
                if selected_word_set == "full list":
                    practice_session.reset_context_progress(selected_direction)
                else:
                    practice_session.reset_mistakes_context_progress(selected_direction)
                practice_session.save_progress_data(
                    drive_manager=st.session_state.get("drive_manager"),
                    user_folder_id=st.session_state.get("user_folder_id"),
                    async_save=True,
                )
                st.success(f"{reset_label} has been reset.")
                st.rerun()

        with col2:
            if st.button("Download progress"):
                # Save current progress data
                progress_json = practice_session.save_progress_data(
                    drive_manager=st.session_state.get("drive_manager"),
                    user_folder_id=st.session_state.get("user_folder_id"),
                    async_save=False,  # to ensure we have a local copy before download
                )
                # Download button
                st.download_button(
                    label="Download Progress",
                    data=progress_json,
                    file_name=f"{practice_session.exercise_name}_context_{selected_word_set}_progress.json",
                    mime="application/json",
                )

        with col3:
            if st.button("Pronounce Answer"):
                pronounce_answer(practice_session)


def fill_context_set_from_source(practice_session, context_set, direction, word_set):
    """
    Fills the given 'context_set' with words from the normal practice set or mistakes set for 'direction'.
    """
    if word_set == "full list":
        base_set = practice_session.practice_sets.get(direction)
    else:
        base_set = practice_session.mistakes_sets.get(direction)

    if base_set:
        context_set.word_list = base_set.word_list.copy()
    else:
        context_set.word_list = []

    random.shuffle(context_set.word_list)
    context_set.current_index = 0
    context_set.progress = []
    context_set.last_feedback_message = None


def update_context_progress(
    correct,
    word_in_from_lang,
    correct_translation,
    word_pair,
    practice_session,
    pset,
    direction,
    word_set,
):
    """
    Record progress in context_sets or mistakes_context_sets, increment index, and save.
    """
    pset.last_feedback_message = None
    if correct:
        pset.last_feedback_message = (
            "success",
            f"Correct! The translation of {word_in_from_lang} is '{correct_translation}'.",
        )
    else:
        pset.last_feedback_message = (
            "error",
            f"Incorrect. The correct translation of {word_in_from_lang} is '{correct_translation}'.",
        )

    # Record progress
    pset.progress.append(
        {
            "word": word_in_from_lang,
            "correct_translation": correct_translation,
            "correct": correct,
        }
    )

    pset.current_index += 1
    # Clamp if needed
    if pset.current_index > len(pset.word_list):
        pset.current_index = len(pset.word_list)

    # Update mistakes context if incorrect
    if not correct and word_set == "mistakes":
        practice_session.add_mistakes_context(word_pair, direction)
    elif correct and word_set == "mistakes":
        practice_session.remove_mistakes_context(word_pair, direction)

    # Save
    practice_session.save_progress_data(
        drive_manager=st.session_state.get("drive_manager"),
        user_folder_id=st.session_state.get("user_folder_id"),
        async_save=True,
    )


def pronounce_answer(practice_session: PracticeSession):
    """Play TTS audio for the last known answer."""
    if practice_session.pronounce_answer_text:
        audio_html = tts_audio(
            practice_session.pronounce_answer_text,
            practice_session.pronounce_answer_lang,
        )
        st.markdown(audio_html, unsafe_allow_html=True)
    else:
        st.markdown("No answer to pronounce yet.", unsafe_allow_html=True)


if __name__ == "__main__":
    app()
