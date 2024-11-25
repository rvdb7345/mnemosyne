# standard_exercise_definition.py

import pandas as pd

class VocabList:
    """Base class for predefined vocabulary lists."""
    
    def __init__(self, exercise_name, source_language_name, target_language_name, exercise_path):
        self.exercise_name = exercise_name
        self.source_language_name = source_language_name
        self.target_language_name = target_language_name
        self.exercise_path = exercise_path

    def load_exercise(self):
        """Load the exercise data from the specified path."""
        try:
            return pd.read_csv(
                self.exercise_path,
                sep='\t',
                header=None,
                names=[self.source_language_name, self.target_language_name]
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"Exercise file not found at path: {self.exercise_path}")
        except Exception as e:
            raise Exception(f"Error loading exercise: {e}")

class DutchVocabList(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Dutch Frequency List",
            source_language_name='Dutch',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/DutchEnglishFrequencySimplified.txt"
        )

class SpanishVocabList(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Spanish Frequency List",
            source_language_name='Spanish',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/SpanishEnglishFrequencySimplified.txt"
        )

# Add more predefined VocabList subclasses here as needed
# For example:
# class GermanVocabList(VocabList):
#     def __init__(self):
#         super().__init__(
#             exercise_name="German Frequency List",
#             source_language_name='German',
#             target_language_name='English',
#             exercise_path="streamlit-app/src/standard_exercises/GermanEnglishFrequencySimplified.txt"
#         )
