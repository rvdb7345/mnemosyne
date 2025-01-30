# src/sections/practice_utils.py

import random
import re
import streamlit as st
import json

from sections.components import render_flashcard, render_feedback
from utils.helpers import compare_strings, expand_parentheses, tts_audio, LANGUAGE_OPTIONS
from sections.practice_session import PracticeSession


def practice_logic(
    practice_session: PracticeSession,
    mode: str = 'practice',
    direction: str = 'Source to Target'
):
    """
    Main practice logic for practice or mistakes mode.
    Now places the tolerance slider and "ignore accents" checkbox in the sidebar.
    No references to cookies; progress is saved directly to Google Drive via practice_session.
    """

    # Sidebar controls for tolerance and ignore_accents
    practice_session.tolerance = st.sidebar.slider(
        "Tolerance for typos (0 to 100)",
        min_value=0,
        max_value=100,
        value=practice_session.tolerance,
        key=f'tolerance_{mode}'
    )
    practice_session.ignore_accents = st.sidebar.checkbox(
        "Ignore accents",
        value=practice_session.ignore_accents,
        key=f'ignore_accents_{mode}'
    )

    source_language = practice_session.source_language
    target_language = practice_session.target_language
    source_language_code = LANGUAGE_OPTIONS.get(source_language, "en")
    target_language_code = LANGUAGE_OPTIONS.get(target_language, "en")

    # Fetch the appropriate practice set
    if mode == 'practice':
        practice_set = practice_session.practice_sets.get(direction)
    else:  # mode == 'mistakes'
        practice_set = practice_session.mistakes_sets.get(direction)

    if not practice_set:
        st.error(f"No data found for the selected direction: {direction}")
        return

    tolerance = practice_session.tolerance
    ignore_accents = practice_session.ignore_accents

    # Calculate correct/incorrect so far
    num_correct = sum(1 for item in practice_set.progress if item['correct'])
    num_incorrect = sum(1 for item in practice_set.progress if not item['correct'])

    # Display progress bar
    total_words = len(practice_set.word_list)
    if practice_set.current_index < total_words:
        progress_percent = practice_set.current_index / total_words
    else:
        progress_percent = 1.0
    st.progress(progress_percent)
    st.write(
        f"Word {min(practice_set.current_index + 1, total_words)} of {total_words} "
        f"— ✅ {num_correct} | ❌ {num_incorrect}"
    )

    # Display feedback message (if any)
    render_feedback(practice_set.last_feedback_message)

    # Possibly clear the text input
    if getattr(practice_session, f'clear_input_{mode}', False):
        if 'user_input' in st.session_state:
            del st.session_state['user_input']
        setattr(practice_session, f'clear_input_{mode}', False)

    # Main quiz logic
    if practice_set.current_index < total_words:
        # Show the question
        current_word_pair = practice_set.word_list[practice_set.current_index]
        if direction == f"{source_language} to {target_language}":
            question = current_word_pair[source_language]
            answer = current_word_pair[target_language]
            tts_language = source_language_code
        else:
            question = current_word_pair[target_language]
            answer = current_word_pair[source_language]
            tts_language = target_language_code

        render_flashcard(question)

        # Input form
        with st.form(key=f'answer_form_{mode}_{direction}', clear_on_submit=True):
            user_input = st.text_input("Your answer:", key='user_input')
            submit = st.form_submit_button(label='Submit')

        if submit:
            practice_set.last_feedback_message = None  # clear previous feedback
            user_input = st.session_state.get('user_input', '')

            # Acceptable answers: possibly split by commas or parentheses
            acceptable_answers = parse_acceptable_answers(answer)
            correct = False
            original_correct_answer = None

            for ans in acceptable_answers:
                is_correct, original_ans, exact_match = compare_strings(
                    user_input, ans, tolerance, ignore_accents
                )
                if is_correct:
                    correct = True
                    original_correct_answer = original_ans
                    break

            # Generate feedback
            if correct:
                if exact_match:
                    feedback = f"Correct! Your answer: **{user_input}**"
                else:
                    feedback = (f"Correct! Your answer: **{user_input}** "
                                f"(Exact: **{answer}**)")
                practice_set.last_feedback_message = ('success', feedback)

                if mode == 'practice':
                    # Remove from mistakes if it’s in there
                    practice_session.remove_from_mistakes(current_word_pair, direction)

            else:
                feedback = (
                    f"Incorrect! Your answer: **{user_input}**. "
                    f"Acceptable answers: **{', '.join(acceptable_answers)}**"
                )
                practice_set.last_feedback_message = ('error', feedback)
                if mode == 'practice':
                    # Add to mistakes
                    practice_session.add_mistake(current_word_pair, direction)

            # Set up TTS for answer
            practice_session.pronounce_answer_trigger = True
            practice_session.pronounce_answer_text = answer
            practice_session.pronounce_answer_lang = (
                target_language_code
                if direction == f"{source_language} to {target_language}"
                else source_language_code
            )

            # Update progress
            if mode == 'practice':
                practice_session.update_progress_practice(
                    direction, question, user_input, answer, correct, current_word_pair
                )
            else:
                practice_session.update_progress_mistakes(
                    direction, question, user_input, answer, correct, current_word_pair
                )

            # Save progress (no cookies)
            practice_session.save_progress_data(
                drive_manager=st.session_state.get('drive_manager'),
                user_folder_id=st.session_state.get('user_folder_id'),
                async_save=True
            )

            setattr(practice_session, f'clear_input_{mode}', True)
            st.rerun()

    else:
        # No more words
        if mode == 'practice':
            st.success("🎉 You have completed all words in this exercise!")
        else:
            st.success("🎉 You have completed all mistakes!")

    # Buttons row
    colass, colrem, colpro = st.columns(3)
    with colass:
        if st.button('Change Assessment'):
            change_assessment(practice_session, mode=mode, direction=direction)
    with colrem:
        if st.button('Remove this question'):
            remove_current_question(practice_session, mode=mode, direction=direction)
    with colpro:
        if st.button("Hear Pronunciation"):
            audio_html = tts_audio(question, tts_language)
            st.markdown(audio_html, unsafe_allow_html=True)

    # "Options" expander
    with st.expander("Options"):
        col1, col2, col3 = st.columns(3)
        with col1:
            # Reset progress
            reset_label = "Reset Progress" if mode == 'practice' else "Reset Mistakes Progress"
            if st.button(reset_label):
                if mode == 'practice':
                    practice_session.reset_practice_progress(direction)
                else:
                    practice_session.reset_mistakes_progress(direction)
                practice_session.save_progress_data(
                    drive_manager=st.session_state.get('drive_manager'),
                    user_folder_id=st.session_state.get('user_folder_id'),
                    async_save=True
                )
                st.success(f"{reset_label} has been reset.")
                st.rerun()

        with col2:
            if st.button("Download progress"):
                # Save current progress data
                progress_json = practice_session.save_progress_data(
                    drive_manager=st.session_state.get('drive_manager'),
                    user_folder_id=st.session_state.get('user_folder_id'),
                    async_save=False  # to ensure we have a local copy before download
                )
                # Download button
                st.download_button(
                    label="Download Progress",
                    data=progress_json,
                    file_name=f"{practice_session.exercise_name}_{mode}_progress.json",
                    mime="application/json"
                )

        with col3:
            if st.button("Pronounce Answer"):
                pronounce_answer(practice_session)


def parse_acceptable_answers(answer_string: str):
    """
    Splits 'answer_string' by commas or any pattern like 'a)', 'b)', etc.
    and also expands parentheses for optional content.
    """
    # Regex that splits by commas or labels like 'a)' with optional whitespace
    split_pattern = re.compile(r',|\s*[a-zA-Z]\)\s*')

    raw_answers = [ans.strip() for ans in split_pattern.split(answer_string) if ans.strip()]
    expanded_answers = []
    for ans in raw_answers:
        expanded_answers.extend(expand_parentheses(ans))
    # Deduplicate
    return list(set(expanded_answers))


def change_assessment(practice_session: PracticeSession, mode='practice', direction='Source to Target'):
    """Toggle the 'correct' status of the last entry in progress and update mistakes accordingly."""
    if mode not in ['practice', 'mistakes']:
        st.warning("Invalid mode for assessment change.")
        return

    if mode == 'practice':
        practice_set = practice_session.practice_sets.get(direction)
    else:
        practice_set = practice_session.mistakes_sets.get(direction)

    if not practice_set or not practice_set.progress:
        st.warning("No previous answer to change assessment.")
        return

    last_entry = practice_set.progress[-1]
    last_entry['correct'] = not last_entry['correct']
    correct_status = last_entry['correct']
    user_answer = last_entry['your_answer']
    word_pair = last_entry['word_pair']

    if correct_status:
        feedback = f"Corrected to correct. Your answer: **{user_answer}**"
        practice_set.last_feedback_message = ('success', feedback)
        st.success(feedback)

        if mode == 'practice':
            # Remove from mistakes
            practice_session.remove_from_mistakes(word_pair, direction)
    else:
        feedback = f"Corrected to incorrect. Your answer: **{user_answer}**"
        practice_set.last_feedback_message = ('error', feedback)
        st.error(feedback)

        if mode == 'practice':
            # Add to mistakes
            practice_session.add_mistake(word_pair, direction)

    practice_session.save_progress_data(
        drive_manager=st.session_state.get('drive_manager'),
        user_folder_id=st.session_state.get('user_folder_id'),
        async_save=True
    )


def remove_current_question(practice_session: PracticeSession, mode='practice', direction='Source to Target'):
    """Remove the current question from the active list."""
    if mode == 'practice':
        practice_set = practice_session.practice_sets.get(direction)
    else:
        practice_set = practice_session.mistakes_sets.get(direction)

    if not practice_set:
        st.warning("No practice data found for the selected direction.")
        return

    if practice_set.current_index == 0:
        st.warning("No question to remove.")
        return

    # Remove question from word_list + progress
    current_word_pair = practice_set.word_list.pop(practice_set.current_index - 1)
    practice_set.progress.pop(practice_set.current_index - 1)
    practice_set.current_index -= 1

    if mode == 'practice':
        # Also remove from mistakes if present
        practice_session.remove_from_mistakes(current_word_pair, direction)

    practice_session.save_progress_data(
        drive_manager=st.session_state.get('drive_manager'),
        user_folder_id=st.session_state.get('user_folder_id'),
        async_save=True
    )
    st.success('Question removed from test set.')


def pronounce_answer(practice_session: PracticeSession):
    """Play TTS audio for the last known answer."""
    if practice_session.pronounce_answer_text:
        audio_html = tts_audio(
            practice_session.pronounce_answer_text,
            practice_session.pronounce_answer_lang
        )
        st.markdown(audio_html, unsafe_allow_html=True)
    else:
        st.markdown("No answer to pronounce yet.", unsafe_allow_html=True)
