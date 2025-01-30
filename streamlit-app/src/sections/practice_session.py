# src/sections/practice_session.py

from dataclasses import dataclass, field
from datetime import datetime
import random
import json
import pandas as pd
import os
import concurrent.futures
from googleapiclient.http import MediaFileUpload

@dataclass
class PracticeSet:
    word_list: list = field(default_factory=list)
    progress: list = field(default_factory=list)
    current_index: int = 0
    last_feedback_message: tuple = None
    practice_started: bool = False

@dataclass
class PracticeSession:
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    # General Settings
    tolerance: int = 80
    ignore_accents: bool = False
    source_language: str = 'Source'
    target_language: str = 'Target'
    exercise_name: str = ''
    exercise_df: pd.DataFrame = None
    original_word_list: list = field(default_factory=list)

    # Mistakes are tracked by direction
    mistakes: dict = field(default_factory=dict)
    mistakes_context: dict = field(default_factory=dict)
    complete_context: dict = field(default_factory=dict)

    # Direction-specific sets
    practice_sets: dict = field(default_factory=dict)
    mistakes_sets: dict = field(default_factory=dict)
    context_sets: dict = field(default_factory=dict)
    mistakes_context_sets: dict = field(default_factory=dict)

    # Pronunciation
    pronounce_answer_trigger: bool = False
    pronounce_answer_text: str = ''
    pronounce_answer_lang: str = ''

    def setup_new_exercise(self, df, source_language, target_language, exercise_name):
        """Initialize a brand new exercise from a DataFrame."""
        self.exercise_df = df
        self.source_language = source_language
        self.target_language = target_language
        self.exercise_name = exercise_name
        self.original_word_list = self.exercise_df.to_dict('records')
        self.practice_sets = {}
        self.mistakes_sets = {}
        self.context_sets = {}
        self.mistakes_context_sets = {}
        self.mistakes = {}
        self.mistakes_context = {}
        self.complete_context = {}

        # Define all directions
        directions = [
            f"{self.source_language} to {self.target_language}",
            f"{self.target_language} to {self.source_language}"
        ]

        for direction in directions:
            # Initialize Practice Sets
            pset = PracticeSet(
                word_list=self.original_word_list.copy(),
                progress=[],
                current_index=0,
                last_feedback_message=None,
                practice_started=False
            )
            random.shuffle(pset.word_list)
            self.practice_sets[direction] = pset

            # Initialize Mistakes Sets
            self.mistakes[direction] = []
            mset = PracticeSet(
                word_list=self.mistakes[direction].copy(),
                progress=[],
                current_index=0,
                last_feedback_message=None,
                practice_started=False
            )
            random.shuffle(mset.word_list)
            self.mistakes_sets[direction] = mset

            # Initialize Context Sets
            self.complete_context[direction] = []
            cset = PracticeSet(
                word_list=self.complete_context[direction].copy(),
                progress=[],
                current_index=0,
                last_feedback_message=None,
                practice_started=False
            )
            random.shuffle(cset.word_list)
            self.context_sets[direction] = cset

            # Initialize Mistakes Context Sets
            self.mistakes_context[direction] = []
            mcset = PracticeSet(
                word_list=self.mistakes_context[direction].copy(),
                progress=[],
                current_index=0,
                last_feedback_message=None,
                practice_started=False
            )
            random.shuffle(mcset.word_list)
            self.mistakes_context_sets[direction] = mcset

        # Optionally save progress now
        self.save_progress_data()

    def load_from_progress(self, progress_data):
        """Load entire practice state from a dictionary of progress data."""
        self.source_language = progress_data.get('source_language', 'Source')
        self.target_language = progress_data.get('target_language', 'Target')
        self.exercise_name = progress_data.get('exercise_name', 'Exercise')
        self.tolerance = progress_data.get('tolerance', 80)
        self.ignore_accents = progress_data.get('ignore_accents', False)
        self.exercise_df = pd.DataFrame(progress_data.get('exercise_data', []))
        self.original_word_list = self.exercise_df.to_dict('records')
        self.mistakes = progress_data.get('mistakes', {})
        self.mistakes_context = progress_data.get('mistakes_context', {})
        self.complete_context = progress_data.get('complete_context', {})

        directions = [
            f"{self.source_language} to {self.target_language}",
            f"{self.target_language} to {self.source_language}"
        ]

        self.practice_sets = {}
        self.mistakes_sets = {}
        self.context_sets = {}
        self.mistakes_context_sets = {}

        for direction in directions:
            # Load Practice Sets
            practice_data = progress_data.get('practice_sets', {}).get(direction, {})
            self.practice_sets[direction] = PracticeSet(
                word_list=practice_data.get('word_list', self.original_word_list.copy()),
                progress=practice_data.get('progress', []),
                current_index=practice_data.get('current_index', 0),
                last_feedback_message=practice_data.get('last_feedback_message'),
                practice_started=practice_data.get('practice_started', False)
            )

            # Load Mistakes Sets
            mistakes_data = progress_data.get('mistakes_sets', {}).get(direction, {})
            self.mistakes_sets[direction] = PracticeSet(
                word_list=mistakes_data.get('word_list', self.mistakes.get(direction, []).copy()),
                progress=mistakes_data.get('progress', []),
                current_index=mistakes_data.get('current_index', 0),
                last_feedback_message=mistakes_data.get('last_feedback_message'),
                practice_started=mistakes_data.get('practice_started', False)
            )

            # Load Context Sets
            context_data = progress_data.get('context_sets', {}).get(direction, {})
            self.context_sets[direction] = PracticeSet(
                word_list=context_data.get('word_list', self.complete_context.get(direction, []).copy()),
                progress=context_data.get('progress', []),
                current_index=context_data.get('current_index', 0),
                last_feedback_message=context_data.get('last_feedback_message'),
                practice_started=context_data.get('practice_started', False)
            )

            # Load Mistakes Context Sets
            mistakes_context_data = progress_data.get('mistakes_context_sets', {}).get(direction, {})
            self.mistakes_context_sets[direction] = PracticeSet(
                word_list=mistakes_context_data.get('word_list', self.mistakes_context.get(direction, []).copy()),
                progress=mistakes_context_data.get('progress', []),
                current_index=mistakes_context_data.get('current_index', 0),
                last_feedback_message=mistakes_context_data.get('last_feedback_message'),
                practice_started=mistakes_context_data.get('practice_started', False)
            )

    def reset_practice_progress(self, direction):
        """Reset the practice set for a given direction."""
        if direction in self.practice_sets:
            pset = self.practice_sets[direction]
            pset.word_list = self.original_word_list.copy()
            random.shuffle(pset.word_list)
            pset.progress = []
            pset.current_index = 0
            pset.last_feedback_message = None
            pset.practice_started = False

    def reset_mistakes_progress(self, direction):
        """Reset the mistakes set for a given direction."""
        if direction in self.mistakes_sets:
            mset = self.mistakes_sets[direction]
            mset.word_list = self.mistakes[direction].copy()  # or [] if empty
            random.shuffle(mset.word_list)
            mset.progress = []
            mset.current_index = 0
            mset.last_feedback_message = None
            mset.practice_started = False

    def reset_context_progress(self, direction):
        """Reset the complete context set for a given direction."""
        if direction in self.context_sets:
            cset = self.context_sets[direction]
            cset.word_list = self.complete_context.get(direction, []).copy()
            random.shuffle(cset.word_list)
            cset.progress = []
            cset.current_index = 0
            cset.last_feedback_message = None
            cset.practice_started = False

    def reset_mistakes_context_progress(self, direction):
        """Reset the mistakes context set for a given direction."""
        if direction in self.mistakes_context_sets:
            mcset = self.mistakes_context_sets[direction]
            mcset.word_list = self.mistakes_context.get(direction, []).copy()
            random.shuffle(mcset.word_list)
            mcset.progress = []
            mcset.current_index = 0
            mcset.last_feedback_message = None
            mcset.practice_started = False

    def add_mistake(self, word_pair, direction):
        """Add a word pair to the mistakes list for the given direction."""
        if word_pair not in self.mistakes[direction]:
            self.mistakes[direction].append(word_pair)
            if direction in self.mistakes_sets:
                self.mistakes_sets[direction].word_list.append(word_pair)

    def remove_from_mistakes(self, word_pair, direction):
        """Remove a word pair from mistakes for the given direction."""
        if word_pair in self.mistakes[direction]:
            self.mistakes[direction].remove(word_pair)
        if word_pair in self.mistakes_sets[direction].word_list:
            self.mistakes_sets[direction].word_list.remove(word_pair)

    def add_context(self, word_pair, direction):
        """Add a word pair to the complete context list for the given direction."""
        if word_pair not in self.complete_context.setdefault(direction, []):
            self.complete_context[direction].append(word_pair)
            if direction in self.context_sets:
                self.context_sets[direction].word_list.append(word_pair)

    def remove_context(self, word_pair, direction):
        """Remove a word pair from the complete context list for the given direction."""
        if word_pair in self.complete_context.get(direction, []):
            self.complete_context[direction].remove(word_pair)
        if word_pair in self.context_sets.get(direction, PracticeSet()).word_list:
            self.context_sets[direction].word_list.remove(word_pair)

    def add_mistakes_context(self, word_pair, direction):
        """Add a word pair to the mistakes context list for the given direction."""
        if word_pair not in self.mistakes_context.setdefault(direction, []):
            self.mistakes_context[direction].append(word_pair)
            if direction in self.mistakes_context_sets:
                self.mistakes_context_sets[direction].word_list.append(word_pair)

    def remove_mistakes_context(self, word_pair, direction):
        """Remove a word pair from the mistakes context list for the given direction."""
        if word_pair in self.mistakes_context.get(direction, []):
            self.mistakes_context[direction].remove(word_pair)
        if word_pair in self.mistakes_context_sets.get(direction, PracticeSet()).word_list:
            self.mistakes_context_sets[direction].word_list.remove(word_pair)

    def update_progress_practice(self, direction, question, user_input, answer, correct, current_word_pair):
        """Record practice progress for the given direction."""
        pset = self.practice_sets.get(direction)
        if pset:
            pset.progress.append({
                'question': question,
                'your_answer': user_input,
                'correct_answer': answer,
                'correct': correct,
                'timestamp': datetime.now().isoformat(),
                'word_pair': current_word_pair
            })
            pset.current_index += 1

    def update_progress_mistakes(self, direction, question, user_input, answer, correct, current_word_pair):
        """Record mistakes progress for the given direction."""
        mset = self.mistakes_sets.get(direction)
        if mset:
            mset.progress.append({
                'question': question,
                'your_answer': user_input,
                'correct_answer': answer,
                'correct': correct,
                'timestamp': datetime.now().isoformat(),
                'word_pair': current_word_pair
            })
            mset.current_index += 1

    def update_progress_context(self, direction, question, user_input, answer, correct, current_word_pair):
        """Record context practice progress for the given direction."""
        cset = self.context_sets.get(direction)
        if cset:
            cset.progress.append({
                'question': question,
                'your_answer': user_input,
                'correct_answer': answer,
                'correct': correct,
                'timestamp': datetime.now().isoformat(),
                'word_pair': current_word_pair
            })
            cset.current_index += 1

    def update_progress_mistakes_context(self, direction, question, user_input, answer, correct, current_word_pair):
        """Record mistakes context progress for the given direction."""
        mcset = self.mistakes_context_sets.get(direction)
        if mcset:
            mcset.progress.append({
                'question': question,
                'your_answer': user_input,
                'correct_answer': answer,
                'correct': correct,
                'timestamp': datetime.now().isoformat(),
                'word_pair': current_word_pair
            })
            mcset.current_index += 1

    def _upload_in_background(self, drive_manager, user_folder_id, local_path):
        """Internal method to handle file upload on a separate thread."""
        if not drive_manager or not user_folder_id:
            return
        filename = os.path.basename(local_path)
        existing_file_id = drive_manager.get_file_id_by_name(user_folder_id, filename)
        media = MediaFileUpload(local_path, mimetype='application/json', resumable=True)

        if existing_file_id:
            # Update existing file
            drive_manager.service.files().update(
                fileId=existing_file_id,
                media_body=media,
                fields='id'
            ).execute()
        else:
            # Create a new file
            drive_manager.upload_file_to_directory(local_path, user_folder_id, mime_type='application/json')

    def setup_context_sets(self):
        """
        Initialize or reset the context_sets similarly to practice_sets.
        Only call this if you want to set up brand new context sets for all directions.
        """
        self.context_sets = {}
        self.mistakes_context_sets = {}
        directions = [
            f"{self.source_language} to {self.target_language}",
            f"{self.target_language} to {self.source_language}"
        ]
        for direction in directions:
            # Initialize Context Sets
            cset = PracticeSet(
                word_list=self.complete_context.get(direction, self.original_word_list.copy()),
                progress=[],
                current_index=0,
                last_feedback_message=None,
                practice_started=False
            )
            random.shuffle(cset.word_list)
            self.context_sets[direction] = cset

            # Initialize Mistakes Context Sets
            mcset = PracticeSet(
                word_list=self.mistakes_context.get(direction, self.mistakes[direction].copy()),
                progress=[],
                current_index=0,
                last_feedback_message=None,
                practice_started=False
            )
            random.shuffle(mcset.word_list)
            self.mistakes_context_sets[direction] = mcset

        self.save_progress_data()

    def save_progress_data(self, drive_manager=None, user_folder_id=None, async_save=True):
        """
        Serializes the current session into JSON and optionally uploads to Google Drive.
        """
        progress_data = {
            'source_language': self.source_language,
            'target_language': self.target_language,
            'exercise_name': self.exercise_name,
            'tolerance': self.tolerance,
            'ignore_accents': self.ignore_accents,
            'exercise_data': self.exercise_df.to_dict('records') if self.exercise_df is not None else [],
            'mistakes': self.mistakes,
            'mistakes_context': self.mistakes_context,
            'complete_context': self.complete_context,
            'practice_sets': {},
            'mistakes_sets': {},
            'context_sets': {},
            'mistakes_context_sets': {}
        }

        # Fill practice_sets data
        for direction, pset in self.practice_sets.items():
            progress_data['practice_sets'][direction] = {
                'word_list': pset.word_list,
                'progress': pset.progress,
                'current_index': pset.current_index,
                'last_feedback_message': pset.last_feedback_message,
                'practice_started': pset.practice_started
            }

        # Fill mistakes_sets data
        for direction, mset in self.mistakes_sets.items():
            progress_data['mistakes_sets'][direction] = {
                'word_list': mset.word_list,
                'progress': mset.progress,
                'current_index': mset.current_index,
                'last_feedback_message': mset.last_feedback_message,
                'practice_started': mset.practice_started
            }

        # Fill context_sets data
        for direction, cset in self.context_sets.items():
            progress_data['context_sets'][direction] = {
                'word_list': cset.word_list,
                'progress': cset.progress,
                'current_index': cset.current_index,
                'last_feedback_message': cset.last_feedback_message,
                'practice_started': cset.practice_started
            }

        # Fill mistakes_context_sets data
        for direction, mcset in self.mistakes_context_sets.items():
            progress_data['mistakes_context_sets'][direction] = {
                'word_list': mcset.word_list,
                'progress': mcset.progress,
                'current_index': mcset.current_index,
                'last_feedback_message': mcset.last_feedback_message,
                'practice_started': mcset.practice_started
            }

        # Convert to JSON
        progress_json = json.dumps(progress_data, ensure_ascii=False)

        # If we have a Drive manager & folder, store in a temp path and upload
        if drive_manager and user_folder_id:
            filename = f"{self.exercise_name}_progress.json"
            os.makedirs("temp_progress", exist_ok=True)
            local_path = os.path.join("temp_progress", filename)
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(progress_json)

            if async_save:
                self.executor.submit(
                    self._upload_in_background,
                    drive_manager,
                    user_folder_id,
                    local_path
                )
            else:
                self._upload_in_background(drive_manager, user_folder_id, local_path)

        return progress_json
