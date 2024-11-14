import base64
import difflib
from io import BytesIO, StringIO
import itertools
import os
import re
import unicodedata
from gtts import gTTS
import pandas as pd
import streamlit as st


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

def normalize_text(text):
    """Normalize text by removing accents and converting to lowercase."""
    text = unicodedata.normalize('NFD', text)
    text = ''.join([char for char in text if not unicodedata.combining(char)])
    return text.lower()

def compare_strings(a, b, tolerance, ignore_accents):
    """
    Compare two strings with a given tolerance.
    Returns a tuple (is_correct: bool, correct_answer: str)
    """
    original_a = a
    original_b = b
    if ignore_accents:
        a = normalize_text(a)
        b = normalize_text(b)
    else:
        a = a.lower()
        b = b.lower()
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    return ratio * 100 >= tolerance, original_b


def expand_parentheses(s):
    """
    Expand a string with optional text in parentheses into all possible combinations.
    E.g., "(the) food" -> ["food", "the food"]
    """
    # Pattern to find text in parentheses
    pattern = re.compile(r'\(([^)]+)\)')
    # Find all matches
    matches = list(pattern.finditer(s))
    if not matches:
        return [s.strip()]
    
    # Extract segments and optional texts
    segments = []
    for i, match in enumerate(matches):
        start, end = match.span()
        fixed_text = s[:start]
        optional_text = match.group(1).strip()
        segments.append([fixed_text, fixed_text + optional_text])
        s = s[end:]
    segments.append([s])  # Add the remaining fixed text
    
    # Generate all combinations
    combinations = itertools.product(*segments)
    expanded = [''.join(comb).strip() for comb in combinations]
    return list(set(expanded))

def create_dir(path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)

def get_users(exercises_dir):
    """Retrieve user directories."""
    users = [f for f in os.listdir(exercises_dir) if os.path.isdir(os.path.join(exercises_dir, f))]
    return users

def load_credentials(credentials_file):
    """Load credentials from a CSV file."""
    if os.path.exists(credentials_file):
        df = pd.read_csv(credentials_file)
        return dict(zip(df['username'], df['password']))
    else:
        return {}

def save_credentials(credentials_file, credentials):
    """Save credentials to a CSV file."""
    df = pd.DataFrame(list(credentials.items()), columns=['username', 'password'])
    df.to_csv(credentials_file, index=False)

def handle_exercise_upload(uploaded_file, custom_name, user, exercises_dir, source_language_name, target_language_name):
    if uploaded_file is not None and custom_name:
        try:
            source_language_code = LANGUAGE_OPTIONS[source_language_name]
            target_language_code = LANGUAGE_OPTIONS[target_language_name]
            if uploaded_file.name.endswith('.txt'):
                cleaned_lines = []
                for line in uploaded_file:
                    line = line.decode('utf-8').rstrip()
                    parts = line.split('\t')
                    cleaned_lines.append('\t'.join(parts[:2]))

                from io import StringIO
                cleaned_content = StringIO('\n'.join(cleaned_lines))
                df = pd.read_csv(cleaned_content, sep='\t', header=None, names=[source_language_name, target_language_name])
            
            elif uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, header=None, names=[source_language_name, target_language_name]).applymap(str.strip)
            else:
                st.error("Unsupported file format.")
                return

            user_exercises_dir = os.path.join(exercises_dir, user)
            os.makedirs(user_exercises_dir, exist_ok=True)
            save_path = os.path.join(user_exercises_dir, f"{custom_name}.csv")
            df.to_csv(save_path, index=False)
            st.success(f"Exercise '{custom_name}' uploaded successfully with languages {source_language_name} to {target_language_name}!")
        except Exception as e:
            st.error(f"Error uploading exercise: {e}")
    else:
        st.error("Please provide both a file and a custom exercise name.")



def get_progress_file(username, exercise, direction, progress_dir):
    filename = f"progress_{exercise}_{direction.replace(' ', '_')}.json"
    return os.path.join(progress_dir, username, filename)

def load_exercise(exercise_path):
    try:
        df = pd.read_csv(exercise_path)
        return df
    except Exception as e:
        st.error(f"Error loading exercise: {e}")
        return None

def get_exercises(user, exercises_dir):
    """Retrieve exercise files for a user."""
    user_exercises_dir = os.path.join(exercises_dir, user)
    if not os.path.exists(user_exercises_dir):
        create_dir(user_exercises_dir)
    files = [f for f in os.listdir(user_exercises_dir) if f.endswith('.txt') or f.endswith('.csv')]
    return files


def tts_audio(word, language):
    """Generate Text-to-Speech audio and return HTML audio tag."""
    try:
        tts = gTTS(text=word, lang=language)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_data = fp.read()
        b64 = base64.b64encode(audio_data).decode()
        audio_html = f'<audio autoplay="true" controls src="data:audio/mp3;base64,{b64}"></audio>'
        return audio_html
    except Exception as e:
        return f"<p>Error generating audio: {e}</p>"