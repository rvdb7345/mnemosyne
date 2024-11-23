from dataclasses import dataclass, field
from datetime import datetime
import random
import json
import pandas as pd

@dataclass
class PracticeSession:
    # Fields
    practice_started: bool = False
    progress_data: dict = field(default_factory=dict)
    direction: str = ''
    direction_radio: str = ''
    tolerance: int = 80
    ignore_accents: bool = False
    exercise_df: pd.DataFrame = None
    exercise_name: str = ''
    source_language: str = 'Source'
    target_language: str = 'Target'
    direction_options: list = field(default_factory=list)
    word_list: list = field(default_factory=list)
    current_index: int = 0
    mistakes: list = field(default_factory=list)
    progress: list = field(default_factory=list)
    pronounce_answer_trigger: bool = False
    pronounce_answer_text: str = ''
    pronounce_answer_lang: str = ''
    current_word_pair: dict = field(default_factory=dict)
    clear_input: bool = False
    last_feedback_message: tuple = None  # Feedback message to display
    current_mode: str = 'practice'  # 'practice' or 'mistakes'
    loaded_progress_practice: bool = False  # Indicates if progress has been loaded

    # Methods
    def initialize_base_settings(self):
        """Initialize or reset the base settings for the practice session."""
        self.word_list = self.exercise_df.to_dict('records')
        random.shuffle(self.word_list)
        self.current_index = 0
        self.mistakes = []
        self.progress = []
        self.pronounce_answer_trigger = False
        self.pronounce_answer_text = ''
        self.pronounce_answer_lang = ''
        self.current_word_pair = {}
        self.clear_input = True
        self.last_feedback_message = None  # Reset feedback message

    def reset_progress(self):
        """Reset the progress for the current direction."""
        self.initialize_base_settings()
        # Remove progress data for current direction
        direction_key = self.direction.replace(" ", "_").lower()
        progress_data = self.progress_data or {}
        if direction_key in progress_data:
            del progress_data[direction_key]
        self.progress_data = progress_data

    def load_progress(self):
        """Load progress for the current direction."""
        direction_key = self.direction.replace(" ", "_").lower()
        progress_data = self.progress_data or {}
        if direction_key in progress_data:
            direction_progress = progress_data[direction_key]
            self.word_list = direction_progress['word_list']
            self.current_index = direction_progress['current_index']
            self.mistakes = direction_progress['mistakes']
            self.progress = direction_progress['progress']
            self.pronounce_answer_trigger = False
            self.practice_started = True
            self.last_feedback_message = None  # Reset feedback message
            self.loaded_progress_practice = True
        else:
            # Initialize for the new direction
            self.initialize_base_settings()

    def save_progress_data(self, cookies):
        """Save progress data to the session and cookies."""
        progress_data = self.progress_data or {}
        direction_key = self.direction.replace(" ", "_").lower()
        progress_data[direction_key] = {
            'word_list': self.word_list,
            'current_index': self.current_index,
            'mistakes': self.mistakes,
            'progress': self.progress,
        }
        # Include additional session state data
        progress_data['source_language'] = self.source_language
        progress_data['target_language'] = self.target_language
        progress_data['exercise_name'] = self.exercise_name
        progress_data['tolerance'] = self.tolerance
        progress_data['ignore_accents'] = self.ignore_accents

        # Save the exercise_df data
        progress_data['exercise_data'] = self.exercise_df.to_dict('records')

        # Save progress data to practice_session for downloading
        self.progress_data = progress_data
        progress_json = json.dumps(progress_data)
        # Save progress data to cookies
        cookies['progress_data'] = progress_json


    def update_progress(self, question, user_input, answer, correct, current_word_pair):
        """Update the progress after an answer is submitted."""
        self.progress.append({
            'question': question,
            'your_answer': user_input,
            'correct_answer': answer,
            'correct': correct,
            'timestamp': datetime.now().isoformat(),
            'word_pair': current_word_pair
        })
        self.current_index += 1
        self.clear_input = True

    def practice_mistakes(self):
        """Set up the session to practice mistakes."""
        self.word_list = self.mistakes.copy()
        random.shuffle(self.word_list)
        self.current_index = 0
        self.mistakes = []
        self.progress = []
        self.last_feedback_message = None
        self.clear_input = True
        self.current_word_pair = None
        self.pronounce_answer_trigger = False
        self.pronounce_answer_text = ''
        self.pronounce_answer_lang = ''
        self.practice_started = True
        self.current_mode = 'mistakes'  # Update mode
