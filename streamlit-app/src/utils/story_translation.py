import streamlit as st
import openai
import pandas as pd
import traceback
from typing import List, Tuple, Dict
from pydantic import BaseModel


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
    # Add more languages as needed
}

# Define Pydantic models for Structured Outputs
class WordExtractionResponse(BaseModel):
    words: List[str]

class TranslationItem(BaseModel):
    original: str
    translation: str

class TranslationResponse(BaseModel):
    translations: List[TranslationItem]

def create_word_list_from_story():
    st.subheader("Create Word List from Story")
    st.write("Paste your story below and generate a word list with translations.")

    # Input fields
    story = st.text_area("Enter your story here:", height=300)
    story_name = st.text_input("Enter the name of your story here:", key='story_name_input')

    source_language_name = st.selectbox(
        "Source Language",
        list(LANGUAGE_OPTIONS.keys()),
        index=0,
        key='source_language_story_selectbox'
    )
    target_language_name = st.selectbox(
        "Target Language",
        list(LANGUAGE_OPTIONS.keys()),
        index=1,
        key='target_language_translate_selectbox'
    )
    api_key = st.text_input("Enter your OpenAI API Key:", type="password")

    if st.button("Generate Word List", key='generate_word_list_button'):
        if not story.strip():
            st.error("Please enter a story.")
            return
        if not story_name.strip():
            st.error("Please enter a name for your story.")
            return
        if not api_key.strip():
            st.error("Please enter your OpenAI API key.")
            return

        # Clear any existing word list
        if 'generated_word_list' in st.session_state:
            del st.session_state['generated_word_list']
            del st.session_state['word_list_source_language']
            del st.session_state['word_list_target_language']
            del st.session_state['story_name']

        # Set OpenAI API key
        openai.api_key = api_key.strip()

        # Store story name in session state
        st.session_state['story_name'] = story_name.strip()

        # Process the story
        with st.spinner('Generating word list and translations...'):
            try:
                word_list = generate_word_list_from_story(story, source_language_name)
                if word_list:
                    # Translate the word list
                    translated_words = translate_words(word_list, source_language_name, target_language_name)

                    # Create a DataFrame with original and translated words
                    df_translated = pd.DataFrame(translated_words, columns=["Original Word", f"Translation ({target_language_name})"])

                    # Store the DataFrame and language names in session state
                    st.session_state['generated_word_list'] = df_translated
                    st.session_state['word_list_source_language'] = source_language_name
                    st.session_state['word_list_target_language'] = target_language_name

                    # Display the word list with translations
                    st.success("Word list with translations generated successfully!")
                    st.dataframe(df_translated)

                    # Provide download option
                    csv = df_translated.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Word List as CSV",
                        data=csv,
                        file_name=f'word_list_{story_name.strip().replace(" ", "_")}.csv',
                        mime='text/csv',
                        key='download_word_list_button'
                    )
                else:
                    st.warning("No words were extracted from the story.")
            except Exception as e:
                st.error(f"An error occurred: {e}\n{traceback.format_exc()}")

    # No buttons here. Buttons are handled in show_main_page()

def split_text_into_chunks(text, max_tokens=1000):
    """
    Splits the text into chunks that are manageable by the OpenAI API.

    Args:
        text (str): The input text to split.
        max_tokens (int): Maximum number of tokens per chunk.

    Returns:
        List[str]: A list of text chunks.
    """
    import math
    from transformers import GPT2Tokenizer

    tokenizer = get_tokenizer()
    tokens = tokenizer.encode(text)
    total_tokens = len(tokens)
    num_chunks = math.ceil(total_tokens / max_tokens)
    chunks = []
    for i in range(num_chunks):
        start = i * max_tokens
        end = start + max_tokens
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
    return chunks

@st.cache_resource
def get_tokenizer():
    from transformers import GPT2Tokenizer

    return GPT2Tokenizer.from_pretrained("gpt2")

def generate_word_list_from_story(story, source_language):
    """
    Generates a word list from the provided story using OpenAI API with Structured Outputs.

    Args:
        story (str): The story text.
        source_language (str): The language of the story.

    Returns:
        List[str]: A list of unique words in dictionary form.
    """
    # Split the story into manageable chunks
    chunks = split_text_into_chunks(story, max_tokens=1000)

    unique_words = set()

    for idx, chunk in enumerate(chunks):
        st.write(f"Processing chunk {idx + 1} of {len(chunks)}...")
        prompt = (
            f"Extract all unique words from the following {source_language} text in their dictionary form "
            f"(unconjugated, no suffixes), including phrasal verbs.\n\n{chunk}\n\n"
            "Provide the output as a JSON object adhering to the following schema:\n"
            "{\n"
            "  \"words\": [\n"
            "    \"word1\",\n"
            "    \"word2\",\n"
            "    \"word3\"\n"
            "  ]\n"
            "}"
        )

        try:
            response = openai.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                response_format=WordExtractionResponse,
                temperature=0.0,
                max_tokens=1500,
            )
        except openai.error.OpenAIError as e:
            st.error(f"OpenAI API error during word extraction: {e}")
            st.stop()

        # Check for refusal
        if hasattr(response.choices[0].message, 'refusal') and response.choices[0].message.refusal:
            st.error(f"Refusal from OpenAI API: {response.choices[0].message.refusal}")
            continue

        # Extract words
        extracted_words = response.choices[0].message.parsed.words
        unique_words.update(extracted_words)

    # Convert set to sorted list
    sorted_words = sorted(unique_words, key=lambda x: x.lower())
    return sorted_words

def translate_words(word_list, source_language, target_language):
    """
    Translates a list of words from source_language to target_language using OpenAI API with Structured Outputs.

    Args:
        word_list (List[str]): The list of words to translate.
        source_language (str): The language of the original words.
        target_language (str): The target language for translation.

    Returns:
        List[Tuple[str, str]]: A list of tuples containing original and translated words.
    """
    translated = []
    batch_size = 50  # Adjust based on API limits and performance
    total_words = len(word_list)

    for i in range(0, len(word_list), batch_size):
        batch = word_list[i:i + batch_size]
        st.write(f"Translating words {i + 1} to {i + len(batch)} of {total_words}...")
        prompt = (
            f"Translate the following {source_language} words to {target_language}.\n\n"
            f"Provide the output as a JSON object adhering to the following schema:\n"
            "{\n"
            "  \"translations\": [\n"
            "    {\n"
            "      \"original\": \"word1\",\n"
            "      \"translation\": \"translated_word1\"\n"
            "    },\n"
            "    {\n"
            "      \"original\": \"word2\",\n"
            "      \"translation\": \"translated_word2\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        try:
            response = openai.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt + "\n\nWords:\n" + ", ".join(batch)}
                ],
                response_format=TranslationResponse,
                temperature=0.0,
                max_tokens=3000,
            )
        except openai.error.OpenAIError as e:
            st.error(f"OpenAI API error during translation: {e}")
            st.stop()

        # Check for refusal
        if hasattr(response.choices[0].message, 'refusal') and response.choices[0].message.refusal:
            st.error(f"Refusal from OpenAI API: {response.choices[0].message.refusal}")
            continue

        # Extract translations
        translations = response.choices[0].message.parsed.translations
        for item in translations:
            translated.append((item.original, item.translation))

    return translated