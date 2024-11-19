import streamlit as st
import random
import json
from datetime import datetime
from utils.helpers import compare_strings, expand_parentheses, tts_audio


# Language options with codes for gTTS compatibility
LANGUAGE_OPTIONS = {
    "English": "en",
    "Turkish": "tr",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Dutch": "nl",
    "Russian": "ru",
    "Portuguese": "pt",
}

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

    
    # No need to initialize the cookie manager here; use the one passed from main.py

    # Check if we have exercise data or progress data in session_state
    if 'exercise_df' not in st.session_state and 'progress_data' not in st.session_state:
        st.error("No exercise or progress data found. Please go back and upload an exercise or progress file.")
        st.stop()

    # If progress_data is in session_state, we are continuing practice
    if 'progress_data' in st.session_state:
        # Load progress data
        progress_data = json.loads(st.session_state['progress_data'])
        # Reconstruct the necessary variables
        st.session_state['word_list'] = progress_data['word_list']
        st.session_state['current_index'] = progress_data['current_index']
        st.session_state['mistakes'] = progress_data['mistakes']
        st.session_state['progress'] = progress_data['progress']
        st.session_state['feedback_message'] = progress_data.get('feedback_message', None)
        st.session_state['source_language'] = progress_data['source_language']
        st.session_state['target_language'] = progress_data['target_language']
        st.session_state['direction'] = progress_data['direction']
        st.session_state['tolerance'] = progress_data['tolerance']
        st.session_state['ignore_accents'] = progress_data['ignore_accents']
        st.session_state['exercise_name'] = progress_data.get('exercise_name', 'Exercise')
        st.session_state['loaded_progress_practice'] = True
        st.session_state['pronounce_answer_trigger'] = False
        st.session_state['practice_started'] = True
        # Remove progress_data from session_state to avoid re-loading
        del st.session_state['progress_data']

    # Starting a new exercise
    elif not st.session_state.get('practice_started', False):
        df = st.session_state['exercise_df']
        source_language = st.session_state['source_language']
        target_language = st.session_state['target_language']

        st.session_state['direction'] = st.radio(
            f"Select practice direction ({source_language} to {target_language})",
            (f"{source_language} to {target_language}", f"{target_language} to {source_language}"),
            key='direction_radio'
        )
        st.session_state['tolerance'] = st.slider(
            "Tolerance for typos (0 to 100)",
            min_value=0,
            max_value=100,
            value=80,
            key='tolerance_slider'
        )
        st.session_state['ignore_accents'] = st.checkbox(
            "Ignore accents in typing",
            key='ignore_accents_checkbox'
        )
        st.session_state['exercise_name'] = st.session_state.get('exercise_name', 'Exercise')

        if st.button('Start Practice', key='start_practice_button'):
            # Initialize session state variables
            st.session_state['word_list'] = df.to_dict('records')
            random.shuffle(st.session_state['word_list'])
            st.session_state['current_index'] = 0
            st.session_state['mistakes'] = []
            st.session_state['progress'] = []
            st.session_state['feedback_message'] = None
            st.session_state['loaded_progress_practice'] = True
            st.session_state['pronounce_answer_trigger'] = False
            st.session_state['practice_started'] = True
            st.rerun()

    # Proceed with the practice logic
    if st.session_state.get('practice_started', False):
        source_language = st.session_state['source_language']
        target_language = st.session_state['target_language']
        source_language_code = LANGUAGE_OPTIONS.get(source_language, "en")
        target_language_code = LANGUAGE_OPTIONS.get(target_language, "en")
        direction = st.session_state['direction']
        tolerance = st.session_state['tolerance']
        ignore_accents = st.session_state['ignore_accents']
        exercise_name = st.session_state['exercise_name']

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
            st.session_state['current_word_pair'] = current_word_pair
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

                # Set flag to hear answer pronunciation automatically
                st.session_state['pronounce_answer_trigger'] = True
                st.session_state['pronounce_answer_text'] = answer
                st.session_state['pronounce_answer_lang'] = (
                    target_language_code if direction == f"{source_language} to {target_language}" else source_language_code
                )

                # Save progress with timestamp
                st.session_state['progress'].append({
                    'question': question,
                    'your_answer': user_input,
                    'correct_answer': answer,
                    'correct': correct,
                    'timestamp': datetime.now().isoformat(),
                    'word_pair': current_word_pair
                })
                # Update current index
                st.session_state['current_index'] += 1
                st.session_state['clear_input'] = True

                # Save progress data to session_state and cookies
                save_progress_data(cookies)

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
                    st.session_state['pronounce_answer_trigger'] = False
                    st.session_state['pronounce_answer_text'] = ''
                    st.session_state['pronounce_answer_lang'] = ''
                    save_progress_data(cookies)
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
                st.session_state['pronounce_answer_trigger'] = False
                st.session_state['pronounce_answer_text'] = ''
                st.session_state['pronounce_answer_lang'] = ''
                st.success("Progress has been reset.")
                # Remove progress data from cookies
                if 'progress_data' in cookies:
                    del cookies['progress_data']
                    cookies.save()
                st.rerun()

        # Option to download progress
        if st.button("Generate Downloadable Progress"):
            # Prepare progress data
            progress_data = {
                'word_list': st.session_state['word_list'],
                'current_index': st.session_state['current_index'],
                'mistakes': st.session_state['mistakes'],
                'progress': st.session_state['progress'],
                'feedback_message': st.session_state.get('feedback_message', None),
                'source_language': st.session_state['source_language'],
                'target_language': st.session_state['target_language'],
                'direction': st.session_state['direction'],
                'tolerance': st.session_state['tolerance'],
                'ignore_accents': st.session_state['ignore_accents'],
                'exercise_name': st.session_state['exercise_name'],
            }
            progress_json = json.dumps(progress_data)
            # Create a download button
            st.download_button(
                label="Download Progress",
                data=progress_json,
                file_name=f"{exercise_name}_progress.json",
                mime="application/json"
            )

        # Non-intrusive options
        if 'current_word_pair' in st.session_state and st.session_state['current_word_pair'] is not None:
            with st.expander("Options"):
                col1, col2, col3 = st.columns(3)
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
                        # Save progress data to session_state and cookies
                        save_progress_data(cookies)
                with col2:
                    if st.button('Remove this question'):
                        # Remove the current word pair
                        st.session_state['word_list'].pop(current_index - 1)
                        if st.session_state['current_word_pair'] in st.session_state['mistakes']:
                            st.session_state['mistakes'].remove(st.session_state['current_word_pair'])
                        # Remove the last progress entry
                        st.session_state['progress'].pop()
                        # Adjust total_words since the word_list has changed
                        total_words = len(st.session_state['word_list'])
                        if current_index - 1 >= total_words:
                            st.write("You have completed all words in this exercise!")
                            st.stop()
                        # Save progress data to session_state and cookies
                        save_progress_data(cookies)
                        st.success('Question removed from test set.')
                with col3:
                    if st.button("Pronounce Answer"):
                        if 'pronounce_answer_text' in st.session_state:
                            answer_audio_html = tts_audio(
                                st.session_state['pronounce_answer_text'],
                                st.session_state['pronounce_answer_lang']
                            )
                            st.markdown(answer_audio_html, unsafe_allow_html=True)
                        else:
                            st.markdown("No answer to pronounce yet", unsafe_allow_html=True)

def save_progress_data(cookies):
    # Save progress data to session_state for downloading
    progress_data = {
        'word_list': st.session_state['word_list'],
        'current_index': st.session_state['current_index'],
        'mistakes': st.session_state['mistakes'],
        'progress': st.session_state['progress'],
        'feedback_message': st.session_state.get('feedback_message', None),
        'source_language': st.session_state['source_language'],
        'target_language': st.session_state['target_language'],
        'direction': st.session_state['direction'],
        'tolerance': st.session_state['tolerance'],
        'ignore_accents': st.session_state['ignore_accents'],
        'exercise_name': st.session_state['exercise_name'],
    }
    st.session_state['progress_data_to_download'] = json.dumps(progress_data)
    # Save progress data to cookies
    cookies['progress_data'] = st.session_state['progress_data_to_download']
    cookies.save()
