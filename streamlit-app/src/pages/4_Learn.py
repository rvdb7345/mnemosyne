# src/pages/3_ReversoContext.py

import streamlit as st
import random
import re
import logging

from sections.components import apply_custom_css, render_feedback
from sections.practice_session import PracticeSession, PracticeSet
from utils.helpers import tts_audio, LANGUAGE_OPTIONS
from utils.chatgpt_api import get_chatgpt_response
from utils.chatgpt_schema import ChatGPTUsageResponse, ChatGPTSynonymsResponse
import openai
from openai import OpenAI  # Updated import based on new SDK

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def app():
    st.title("ChatGPT Context Practice")
    apply_custom_css()

    # Sidebar: API Key Input
    st.sidebar.header("Configuration")
    api_key_input = st.sidebar.text_input("OpenAI API Key", type="password")

    openai.api_key = api_key_input

    if not api_key_input:
        st.sidebar.warning("Please enter your OpenAI API Key to enable ChatGPT functionalities.")
        st.stop()  # Stop execution until API key is provided

    # Instantiate OpenAI client with the provided API key
    client = OpenAI(api_key=api_key_input)

    practice_session = st.session_state.get('practice_session', None)
    if not practice_session:
        st.error("No active practice session found. Please go to Main Menu to start/load an exercise.")
        return

    # Let user choose whether to base the context list on normal practice or mistakes
    data_source = st.sidebar.radio("Context Source:", ["Practice Words", "Mistakes Words"])

    # Tolerance / ignore accents
    practice_session.tolerance = st.sidebar.slider("Tolerance for typos (0-100)", 0, 100, practice_session.tolerance)
    practice_session.ignore_accents = st.sidebar.checkbox("Ignore accents", value=practice_session.ignore_accents)

    # Select difficulty level
    difficulty_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
    selected_difficulty = st.sidebar.selectbox("Select Difficulty Level:", difficulty_levels)

    # Option to fetch multiple sentences
    fetch_multiple = st.sidebar.checkbox("Fetch Multiple Sentences")
    if fetch_multiple:
        num_sentences = st.sidebar.number_input("Number of Sentences:", min_value=1, max_value=10, value=3)
    else:
        num_sentences = 1

    # Show directions
    directions = [
        f"{practice_session.source_language} to {practice_session.target_language}",
        f"{practice_session.target_language} to {practice_session.source_language}"
    ]
    selected_direction = st.selectbox("Direction:", directions)

    # Initialize context sets
    if selected_direction not in practice_session.context_sets:
        practice_session.context_sets[selected_direction] = PracticeSet()

    context_set = practice_session.context_sets[selected_direction]

    # Populate context set if empty
    if not context_set.word_list:
        fill_context_set_from_source(practice_session, context_set, selected_direction, data_source)
        # Save after initialization
        practice_session.save_progress_data()

    # Show progress
    pset = context_set
    current_index = pset.current_index
    total_words = len(pset.word_list)

    if total_words == 0:
        st.info(f"No words found in {data_source.lower()} for {selected_direction}.")
        return

    progress_frac = min(current_index / total_words, 1.0)
    st.progress(progress_frac)
    st.write(f"Context item {min(current_index+1, total_words)} of {total_words}")

    # Display feedback from last question
    render_feedback(pset.last_feedback_message)

    if current_index >= total_words:
        st.success("🎉 No more context items left to study in this direction!")
        return

    # Identify current word pair
    current_word_pair = pset.word_list[current_index]
    src_lang = practice_session.source_language
    tgt_lang = practice_session.target_language
    src_code = LANGUAGE_OPTIONS.get(src_lang, "en")
    tgt_code = LANGUAGE_OPTIONS.get(tgt_lang, "en")

    if selected_direction == f"{src_lang} to {tgt_lang}":
        word_in_from_lang = current_word_pair.get(src_lang, "")
        correct_translation = current_word_pair.get(tgt_lang, "")
        from_code = src_code
        to_code = tgt_code
    else:
        word_in_from_lang = current_word_pair.get(tgt_lang, "")
        correct_translation = current_word_pair.get(src_lang, "")
        from_code = tgt_code
        to_code = src_code

    st.subheader("Word/Phrase")
    st.markdown(f"**{word_in_from_lang}**")

    chosen_word = st.text_input("Which word/phrase to fetch context from ChatGPT?", value=correct_translation)

    # Auto-fetch or let user do it
    auto_fetch = st.sidebar.checkbox("Always Fetch ChatGPT Context")
    if auto_fetch and chosen_word.strip():
        fetch_chatgpt_data(chosen_word, from_code, to_code, selected_difficulty, num_sentences, client)

    if st.button("Fetch ChatGPT Context"):
        if chosen_word.strip():
            fetch_chatgpt_data(chosen_word, from_code, to_code, selected_difficulty, num_sentences, client)
        else:
            st.warning("Please enter a non-empty word.")

    # Grab usage examples & synonyms from st.session_state if we have them
    usage_examples = st.session_state.get("chatgpt_usage_examples", [])
    synonyms_data = st.session_state.get("chatgpt_synonyms_data", [])

    # Build quiz questions
    quiz_questions = build_context_quiz(chosen_word, usage_examples, synonyms_data)

    if not quiz_questions:
        st.write("No context quiz available yet. Try fetching ChatGPT data above.")
        # fallback input
        fallback_quiz_form(pset, practice_session, current_word_pair, word_in_from_lang, correct_translation, selected_direction, data_source)
        return
    else:
        # We do have quiz questions
        st.write("## Context Quiz")
        answers = {}
        for i, qdata in enumerate(quiz_questions, start=1):
            qtype = qdata["type"]
            prompt = qdata["question_text"]
            st.write(f"**Question {i}:** {prompt}")

            if qtype == "fill_blank":
                ans = st.text_input(f"Q{i} Answer", key=f"fill_blank_{i}")
                answers[i] = ans
            elif qtype == "multiple_choice":
                opts = qdata["options"]
                ans = st.radio(f"Q{i} Options", options=opts, key=f"mc_{i}")
                answers[i] = ans
            else:
                ans = st.text_area(f"Q{i} Explanation", key=f"short_ans_{i}")
                answers[i] = ans
            st.write("---")

        if st.button("Submit Quiz"):
            correct_count = 0
            total_count = len(quiz_questions)

            for i, qdata in enumerate(quiz_questions, start=1):
                qtype = qdata["type"]
                correct_ans = qdata["answer"]
                user_ans = answers[i]

                if qtype in ("fill_blank", "multiple_choice"):
                    if user_ans.strip().lower() == correct_ans.strip().lower():
                        st.success(f"Q{i}: Correct! Your answer: {user_ans}")
                        correct_count += 1
                    else:
                        st.error(f"Q{i}: Incorrect. You said '{user_ans}', correct is '{correct_ans}'.")
                else:
                    st.info(f"Q{i} was open-ended. Your answer: {user_ans}")
                    st.write(f"Reference: {correct_ans}")

            st.write(f"**Score: {correct_count}/{total_count}**")

            # If fully correct, treat as a success
            fully_correct = (correct_count == total_count)
            update_context_progress(
                fully_correct,
                word_in_from_lang,
                correct_translation,
                current_word_pair,
                practice_session,
                pset,
                selected_direction
            )

    # TTS Buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Hear Question"):
            audio_html = tts_audio(word_in_from_lang, from_code)
            st.markdown(audio_html, unsafe_allow_html=True)
    with col2:
        if st.button("Hear Answer"):
            audio_html = tts_audio(correct_translation, to_code)
            st.markdown(audio_html, unsafe_allow_html=True)

def fill_context_set_from_source(practice_session, context_set, direction, data_source):
    """
    Fills the given 'context_set' with words from either the
    normal practice set or mistakes set for 'direction'.
    """
    if data_source == "Practice Words":
        base_set = practice_session.practice_sets.get(direction)
        if base_set:
            context_set.word_list = base_set.word_list.copy()
        else:
            context_set.word_list = []
    else:
        # "Mistakes Words"
        base_set = practice_session.mistakes_sets.get(direction)
        if base_set:
            context_set.word_list = base_set.word_list.copy()
        else:
            context_set.word_list = []

    random.shuffle(context_set.word_list)
    context_set.current_index = 0
    context_set.progress = []
    context_set.last_feedback_message = None

def fetch_chatgpt_data(chosen_word, from_lang_code, to_lang_code, difficulty, num_sentences, client):
    """Fetch ChatGPT usage examples & synonyms, store in session_state."""
    with st.spinner("Fetching data from ChatGPT..."):
        try:
            logger.info(f"Fetching ChatGPT data for word: {chosen_word}")

            # Prepare prompts with difficulty
            usage_prompt = (
                f"Provide {num_sentences} example sentences using the word '{chosen_word}' in the context of translating from {from_lang_code} to {to_lang_code}."
                f" Ensure the sentences are appropriate for {difficulty} level."
                f" For each sentence, omit the translation of '{chosen_word}' and replace it with a blank ('_____')."
                f" Provide the correct translation for the blank."
                f" Format the response as JSON adhering to the following schema:\n\n"
                f"{ChatGPTUsageResponse.schema_json(indent=2)}"
            )

            synonyms_prompt = (
                f"Provide 5 synonyms for the word '{chosen_word}' in {to_lang_code}."
                f" Ensure the synonyms are appropriate for {difficulty} level."
                f" Format the response as JSON adhering to the following schema:\n\n"
                f"{ChatGPTSynonymsResponse.schema_json(indent=2)}"
            )

            # Fetch usage examples
            usage_response = get_chatgpt_response(usage_prompt, ChatGPTUsageResponse, client, max_tokens=600)
            if usage_response:
                usage_examples = parse_chatgpt_usage(usage_response)
                if usage_examples:
                    st.session_state["chatgpt_usage_examples"] = usage_examples
                else:
                    st.session_state["chatgpt_usage_examples"] = []
                    st.warning("No usage examples found.")
            else:
                st.session_state["chatgpt_usage_examples"] = []
                st.warning("Failed to fetch usage examples from ChatGPT.")

            # Fetch synonyms
            synonyms_response = get_chatgpt_response(synonyms_prompt, ChatGPTSynonymsResponse, client, max_tokens=150)
            if synonyms_response:
                synonyms_data = parse_chatgpt_synonyms(synonyms_response)
                if synonyms_data:
                    st.session_state["chatgpt_synonyms_data"] = synonyms_data
                else:
                    st.session_state["chatgpt_synonyms_data"] = []
                    st.warning("No synonyms found.")
            else:
                st.session_state["chatgpt_synonyms_data"] = []
                st.warning("Failed to fetch synonyms from ChatGPT.")

            st.success("ChatGPT context fetched.")
        except Exception as e:
            st.error(f"Error contacting ChatGPT: {e}")

def parse_chatgpt_usage(response: ChatGPTUsageResponse):
    """
    Parses the ChatGPTUsageResponse to extract usage examples.
    Returns a list of dictionaries with 'text' and 'translation'.
    """
    usage_examples = []
    for sentence in response.sentences:
        usage_examples.append({"text": sentence.sentence_with_blank, "translation": sentence.correct_translation})
    return usage_examples

def parse_chatgpt_synonyms(response: ChatGPTSynonymsResponse):
    """
    Parses the ChatGPTSynonymsResponse to extract synonyms.
    Returns a list of synonyms.
    """
    synonyms = response.synonyms
    return synonyms

def build_context_quiz(chosen_word, usage_examples, synonyms_data):
    """
    Build a small quiz with:
    - A fill-in-the-blank from the first usage example
    - A multiple-choice from synonyms
    synonyms_data => list of synonyms
    """
    quiz = []

    # Usage example quiz
    if usage_examples:
        ex = usage_examples[0]
        sentence = ex.get("text", "")
        translation = ex.get("translation", "")
        if "_____" in sentence:
            quiz.append({
                "type": "fill_blank",
                "question_text": f"Fill in the blank:\n\n**{sentence}**",
                "answer": chosen_word
            })
        else:
            quiz.append({
                "type": "short_answer",
                "question_text": (
                    f"Usage example:\n\n**{sentence}**\n\n"
                    f"What is the missing word?"
                ),
                "answer": chosen_word
            })

    # Synonyms multiple choice
    if synonyms_data:
        correct_syn = synonyms_data[0]
        distractors = synonyms_data[1:4] if len(synonyms_data) >= 4 else synonyms_data[1:]
        # Ensure there are enough distractors
        while len(distractors) < 3:
            distractors.append("None")
        options = [correct_syn] + distractors
        random.shuffle(options)
        quiz.append({
            "type": "multiple_choice",
            "question_text": f"Which is a correct synonym for **{chosen_word}**?",
            "options": options,
            "answer": correct_syn
        })

    return quiz

def fallback_quiz_form(pset, practice_session, current_word_pair, word_in_from_lang, correct_translation, selected_direction, data_source):
    """
    If no ChatGPT context is available, we still let the user guess.
    """
    st.write("Try a basic guess for the correct answer:")
    with st.form("fallback_form"):
        guess = st.text_input("Your guess:")
        sub = st.form_submit_button("Submit")
    if sub:
        # We'll treat it as correct if it exactly matches, but you could do fuzzy compare
        if guess.strip().lower() == correct_translation.strip().lower():
            st.success("Correct!")
            update_context_progress(True, word_in_from_lang, correct_translation, current_word_pair, practice_session, pset, selected_direction)
        else:
            st.error(f"Incorrect. You said '{guess}', correct is '{correct_translation}'.")
            update_context_progress(False, word_in_from_lang, correct_translation, current_word_pair, practice_session, pset, selected_direction)

def update_context_progress(correct, word_in_from_lang, correct_translation, word_pair, practice_session, pset, direction):
    """
    Record progress in context_sets, increment index, and save.
    """
    pset.last_feedback_message = None
    if correct:
        pset.last_feedback_message = ("success", f"Correct! The translation is '{correct_translation}'.")
    else:
        pset.last_feedback_message = ("error", f"Incorrect. The correct translation is '{correct_translation}'.")

    # Record progress
    pset.progress.append({
        "word": word_in_from_lang,
        "correct_translation": correct_translation,
        "correct": correct
    })

    pset.current_index += 1
    # Clamp if needed
    if pset.current_index > len(pset.word_list):
        pset.current_index = len(pset.word_list)

    # Save
    practice_session.save_progress_data()
    st.rerun()

app()
