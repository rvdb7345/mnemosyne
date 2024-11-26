# src/sections/practice_utils.py

import random
import streamlit as st
import json
from sections.components import render_flashcard, render_feedback
from utils.helpers import compare_strings, expand_parentheses, tts_audio, LANGUAGE_OPTIONS
from sections.practice_session import PracticeSession


def practice_logic(practice_session: PracticeSession, cookies, mode='practice', direction='Source to Target'):
    source_language = practice_session.source_language
    target_language = practice_session.target_language
    source_language_code = LANGUAGE_OPTIONS.get(source_language, "en")
    target_language_code = LANGUAGE_OPTIONS.get(target_language, "en")
    
    if mode == 'practice':
        practice_set = practice_session.practice_sets.get(direction)
    else:
        practice_set = practice_session.mistakes_sets.get(direction)

    if not practice_set:
        st.error(f"No data found for the selected direction: {direction}")
        return
    
    tolerance = practice_session.tolerance
    ignore_accents = practice_session.ignore_accents

    # Calculate counts
    num_correct = sum(1 for item in practice_set.progress if item['correct'])
    num_incorrect = sum(1 for item in practice_set.progress if not item['correct'])

    # Display progress bar and current word number
    total_words = len(practice_set.word_list)
    if practice_set.current_index < total_words:
        progress_percent = practice_set.current_index / total_words
    else:
        progress_percent = 1.0
    st.progress(progress_percent)
    st.write(f"Word {min(practice_set.current_index + 1, total_words)} of {total_words} — ✅ {num_correct} | ❌ {num_incorrect}")

    # Display feedback message (if any)
    render_feedback(practice_set.last_feedback_message)

    # Before creating the text_input, check if we need to clear the input
    if getattr(practice_session, f'clear_input_{mode}', False):
        if 'user_input' in st.session_state:
            del st.session_state['user_input']
        setattr(practice_session, f'clear_input_{mode}', False)

    # Main quiz logic
    if practice_set.current_index < total_words:
        # Display the question and get user input
        current_word_pair = practice_set.word_list[practice_set.current_index]
        if direction == f"{source_language} to {target_language}":
            question = current_word_pair[source_language]
            answer = current_word_pair[target_language]
            tts_language = source_language_code
        else:
            question = current_word_pair[target_language]
            answer = current_word_pair[source_language]
            tts_language = target_language_code

        # Display the word in a flashcard
        render_flashcard(question)

        # Option to hear the pronunciation
        if st.button("Hear Pronunciation"):
            audio_html = tts_audio(question, tts_language)
            st.markdown(audio_html, unsafe_allow_html=True)

        # Use a form to allow Enter key submission
        with st.form(key=f'answer_form_{mode}_{direction}', clear_on_submit=True):
            user_input = st.text_input("Your answer:", key='user_input')
            submit = st.form_submit_button(label='Submit')

        if submit:
            # Clear previous feedback message
            practice_set.last_feedback_message = None

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
            original_correct_answer = None
            for ans in acceptable_answers:
                is_correct, original_ans = compare_strings(user_input, ans, tolerance, ignore_accents)
                if is_correct:
                    correct = True
                    original_correct_answer = original_ans
                    break

            # Update feedback message
            if correct:
                feedback = f"Correct! Your answer: **{original_correct_answer}**"
                practice_set.last_feedback_message = ('success', feedback)
                st.success(feedback)
                if mode == 'practice':
                    # Remove from mistakes if previously marked as mistake
                    practice_session.mistakes = [wp for wp in practice_session.mistakes if wp != current_word_pair]
                    practice_session.mistakes_sets[direction].word_list = [wp for wp in practice_session.mistakes_sets[direction].word_list if wp != current_word_pair]
            else:
                feedback = f"Incorrect! Your answer: **{user_input}**. Acceptable answers were: **{', '.join(acceptable_answers)}**"
                practice_set.last_feedback_message = ('error', feedback)
                st.error(feedback)
                if mode == 'practice':
                    practice_session.add_mistake(current_word_pair, direction)

            # Set flag to hear answer pronunciation automatically
            practice_session.pronounce_answer_trigger = True
            practice_session.pronounce_answer_text = answer
            practice_session.pronounce_answer_lang = (
                target_language_code if direction == f"{source_language} to {target_language}" else source_language_code
            )

            # Update progress
            if mode == 'practice':
                practice_session.update_progress_practice(direction, question, user_input, answer, correct, current_word_pair)
            else:
                practice_session.update_progress_mistakes(direction, question, user_input, answer, correct, current_word_pair)

            # Save progress data
            practice_session.save_progress_data(cookies)

            # Clear the user input
            setattr(practice_session, f'clear_input_{mode}', True)

            st.rerun()

    else:
        if mode == 'practice':
            st.success("🎉 You have completed all words in this exercise!")
        else:
            st.success("🎉 You have completed all mistakes!")

    # Reset progress button
    reset_label = "Reset Progress" if mode == 'practice' else "Reset Mistakes Progress"
    if st.button(reset_label):
        if mode == 'practice':
            practice_session.reset_practice_progress(direction)
        else:
            practice_session.reset_mistakes_progress(direction)
        practice_session.save_progress_data(cookies)
        st.success(f"{reset_label} has been reset.")
        st.rerun()

    # Option to download progress
    if st.button("Generate Downloadable Progress"):
        # Save current progress data
        progress_json = practice_session.save_progress_data(cookies)

        # Create a download button
        st.download_button(
            label="Download Progress",
            data=progress_json,
            file_name=f"{practice_session.exercise_name}_{mode}_progress.json",
            mime="application/json"
        )

    # Non-intrusive options
    with st.expander("Options"):
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button('Change Assessment'):
                change_assessment(practice_session, cookies, mode=mode, direction=direction)
        with col2:
            if st.button('Remove this question'):
                remove_current_question(practice_session, cookies, mode=mode, direction=direction)
        with col3:
            if st.button("Pronounce Answer"):
                pronounce_answer(practice_session) 

def change_assessment(practice_session: PracticeSession, cookies, mode='practice', direction='Source to Target'):
    """
    Toggle the 'correct' status of the latest answer in the specified mode and direction.
    
    Args:
        practice_session (PracticeSession): The current practice session.
        cookies: The Streamlit cookies manager.
        mode (str): The mode in which to change the assessment ('practice' or 'mistakes').
        direction (str): The direction of the practice set.
    """
    if mode not in ['practice', 'mistakes']:
        st.warning("Invalid mode specified for assessment change.")
        return

    practice_set = practice_session.practice_sets.get(direction) if mode == 'practice' else practice_session.mistakes_sets.get(direction)

    if not practice_set or not practice_set.progress:
        st.warning("No previous answer to change assessment.")
        return

    # Toggle the 'correct' value of the last entry
    last_entry = practice_set.progress[-1]
    last_entry['correct'] = not last_entry['correct']
    correct_status = last_entry['correct']
    user_answer = last_entry['your_answer']

    # Update feedback message
    if correct_status:
        feedback = f"Corrected to correct. Your answer: **{user_answer}**"
        practice_set.last_feedback_message = ('success', feedback)
        st.success(feedback)
        if mode == 'practice':
            # Remove from mistakes if present
            if last_entry['word_pair'] in practice_session.mistakes:
                practice_session.mistakes.remove(last_entry['word_pair'])
            if last_entry['word_pair'] in practice_session.mistakes_sets[direction].word_list:
                practice_session.mistakes_sets[direction].word_list.remove(last_entry['word_pair'])
    else:
        feedback = f"Corrected to incorrect. Your answer: **{user_answer}**"
        practice_set.last_feedback_message = ('error', feedback)
        st.error(feedback)
        if mode == 'practice':
            if last_entry['word_pair'] not in practice_session.mistakes:
                practice_session.mistakes.append(last_entry['word_pair'])
            if last_entry['word_pair'] not in practice_session.mistakes_sets[direction].word_list:
                practice_session.mistakes_sets[direction].word_list.append(last_entry['word_pair'])
                random.shuffle(practice_session.mistakes_sets[direction].word_list)

    # Save the updated progress data
    practice_session.save_progress_data(cookies)

        
def remove_current_question(practice_session: PracticeSession, cookies, mode='practice', direction='Source to Target'):
    """
    Remove the current question from the practice or mistakes set.
    
    Args:
        practice_session (PracticeSession): The current practice session.
        cookies: The Streamlit cookies manager.
        mode (str): The mode ('practice' or 'mistakes').
        direction (str): The direction of the practice set.
    """
    practice_set = practice_session.practice_sets.get(direction) if mode == 'practice' else practice_session.mistakes_sets.get(direction)
    if not practice_set:
        st.warning("No practice data found for the selected direction.")
        return

    if practice_set.current_index == 0:
        st.warning("No question to remove.")
        return

    # Remove the current word pair
    current_word_pair = practice_set.word_list.pop(practice_set.current_index - 1)
    practice_set.progress.pop(practice_set.current_index - 1)
    practice_set.current_index -= 1

    if mode == 'practice':
        # Also remove from mistakes if present
        if current_word_pair in practice_session.mistakes:
            practice_session.mistakes.remove(current_word_pair)
        if current_word_pair in practice_session.mistakes_sets[direction].word_list:
            practice_session.mistakes_sets[direction].word_list.remove(current_word_pair)

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
        st.markdown("No answer to pronounce yet.", unsafe_allow_html=True)
