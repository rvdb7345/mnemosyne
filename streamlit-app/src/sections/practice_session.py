# src/sections/practice_session.py

from dataclasses import dataclass, field
from datetime import datetime
import random
import json
import pandas as pd

@dataclass
class PracticeSet:
    word_list: list = field(default_factory=list)
    progress: list = field(default_factory=list)
    current_index: int = 0
    last_feedback_message: tuple = None
    practice_started: bool = False

@dataclass
class PracticeSession:
    # General Settings
    tolerance: int = 80
    ignore_accents: bool = False
    source_language: str = 'Source'
    target_language: str = 'Target'
    exercise_name: str = ''
    exercise_df: pd.DataFrame = None
    original_word_list: list = field(default_factory=list)
    mistakes: list = field(default_factory=list)
    
    # Direction-specific Practice Sets
    practice_sets: dict = field(default_factory=dict)
    mistakes_sets: dict = field(default_factory=dict)
    
    # Pronunciation Fields
    pronounce_answer_trigger: bool = False
    pronounce_answer_text: str = ''
    pronounce_answer_lang: str = ''
    
    def setup_new_exercise(self, df, source_language, target_language, exercise_name):
        """Setup a new exercise with provided DataFrame and language settings."""
        self.exercise_df = df
        self.source_language = source_language
        self.target_language = target_language
        self.exercise_name = exercise_name
        self.original_word_list = self.exercise_df.to_dict('records')
        self.practice_sets = {}
        self.mistakes_sets = {}

        # Define both directions
        directions = [
            f"{self.source_language} to {self.target_language}",
            f"{self.target_language} to {self.source_language}"
        ]
        
        for direction in directions:
            # Initialize Practice Set
            self.practice_sets[direction] = PracticeSet(
                word_list=self.original_word_list.copy(),
                progress=[],
                current_index=0,
                last_feedback_message=None,
                practice_started=False
            )
            random.shuffle(self.practice_sets[direction].word_list)
            
            # Initialize Mistakes Set
            self.mistakes_sets[direction] = PracticeSet(
                word_list=self.mistakes.copy(),
                progress=[],
                current_index=0,
                last_feedback_message=None,
                practice_started=False
            )
            random.shuffle(self.mistakes_sets[direction].word_list)
        
        # Save initial progress data
        self.save_progress_data(cookies=None)  # Pass None if not saving immediately
    
    def load_from_progress(self, progress_data):
        """Load session data from progress data."""
        self.source_language = progress_data.get('source_language', 'Source')
        self.target_language = progress_data.get('target_language', 'Target')
        self.exercise_name = progress_data.get('exercise_name', 'Exercise')
        self.tolerance = progress_data.get('tolerance', 80)
        self.ignore_accents = progress_data.get('ignore_accents', False)
        self.exercise_df = pd.DataFrame(progress_data.get('exercise_data', []))
        self.original_word_list = self.exercise_df.to_dict('records')
        self.mistakes = progress_data.get('mistakes', [])
        
        # Define both directions
        directions = [
            f"{self.source_language} to {self.target_language}",
            f"{self.target_language} to {self.source_language}"
        ]
        
        for direction in directions:
            # Load Practice Set
            practice_data = progress_data.get('practice_sets', {}).get(direction, {})
            self.practice_sets[direction] = PracticeSet(
                word_list=practice_data.get('word_list', self.original_word_list.copy()),
                progress=practice_data.get('progress', []),
                current_index=practice_data.get('current_index', 0),
                last_feedback_message=practice_data.get('last_feedback_message', None),
                practice_started=practice_data.get('practice_started', False)
            )
            random.shuffle(self.practice_sets[direction].word_list)
            
            # Load Mistakes Set
            mistakes_data = progress_data.get('mistakes_sets', {}).get(direction, {})
            self.mistakes_sets[direction] = PracticeSet(
                word_list=mistakes_data.get('word_list', self.mistakes.copy()),
                progress=mistakes_data.get('progress', []),
                current_index=mistakes_data.get('current_index', 0),
                last_feedback_message=mistakes_data.get('last_feedback_message', None),
                practice_started=mistakes_data.get('practice_started', False)
            )
            random.shuffle(self.mistakes_sets[direction].word_list)
    
    def reset_practice_progress(self, direction):
        """Reset the progress for the specified practice direction."""
        if direction in self.practice_sets:
            self.practice_sets[direction].word_list = self.original_word_list.copy()
            random.shuffle(self.practice_sets[direction].word_list)
            self.practice_sets[direction].progress = []
            self.practice_sets[direction].current_index = 0
            self.practice_sets[direction].last_feedback_message = None
            self.practice_sets[direction].practice_started = False
    
    def reset_mistakes_progress(self, direction):
        """Reset the progress for the specified mistakes direction."""
        if direction in self.mistakes_sets:
            self.mistakes_sets[direction].word_list = self.mistakes.copy()
            random.shuffle(self.mistakes_sets[direction].word_list)
            self.mistakes_sets[direction].progress = []
            self.mistakes_sets[direction].current_index = 0
            self.mistakes_sets[direction].last_feedback_message = None
            self.mistakes_sets[direction].practice_started = False
    
    def save_progress_data(self, cookies):
        """Save progress data to the session and cookies."""
        progress_data = {
            'source_language': self.source_language,
            'target_language': self.target_language,
            'exercise_name': self.exercise_name,
            'tolerance': self.tolerance,
            'ignore_accents': self.ignore_accents,
            'exercise_data': self.exercise_df.to_dict('records'),
            'mistakes': self.mistakes,
            'practice_sets': {
                direction: {
                    'word_list': set.word_list,
                    'progress': set.progress,
                    'current_index': set.current_index,
                    'last_feedback_message': set.last_feedback_message,
                    'practice_started': set.practice_started
                }
                for direction, set in self.practice_sets.items()
            },
            'mistakes_sets': {
                direction: {
                    'word_list':set.word_list,
                    'progress': set.progress,
                    'current_index': set.current_index,
                    'last_feedback_message': set.last_feedback_message,
                    'practice_started': set.practice_started
                }
                for direction, set in self.mistakes_sets.items()
            }
        }
    
        progress_json = json.dumps(progress_data)
        if cookies:
            cookies['progress_data'] = progress_json
        
        return progress_json
    
    def update_progress_practice(self, direction, question, user_input, answer, correct, current_word_pair):
        """Update the progress after an answer is submitted in practice mode."""
        practice_set = self.practice_sets.get(direction)
        if practice_set:
            practice_set.progress.append({
                'question': question,
                'your_answer': user_input,
                'correct_answer': answer,
                'correct': correct,
                'timestamp': datetime.now().isoformat(),
                'word_pair': current_word_pair
            })
            practice_set.current_index += 1
    
    def update_progress_mistakes(self, direction, question, user_input, answer, correct, current_word_pair):
        """Update the progress after an answer is submitted in mistakes mode."""
        mistakes_set = self.mistakes_sets.get(direction)
        if mistakes_set:
            mistakes_set.progress.append({
                'question': question,
                'your_answer': user_input,
                'correct_answer': answer,
                'correct': correct,
                'timestamp': datetime.now().isoformat(),
                'word_pair': current_word_pair
            })
            mistakes_set.current_index += 1
    
    def add_mistake(self, word_pair, direction):
        """Add a word pair to the mistakes list for the specified direction."""
        if word_pair not in self.mistakes:
            self.mistakes.append(word_pair)
            if direction in self.mistakes_sets:
                self.mistakes_sets[direction].word_list.append(word_pair)
                random.shuffle(self.mistakes_sets[direction].word_list)
