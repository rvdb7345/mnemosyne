
import pandas as pd

from dataclasses import dataclass

@dataclass
class VocabList:
    """Class for keeping track of an item in inventory."""
    exercise_name: str
    source_language_name: str
    target_language_name: str
    exercise_path: str

    def load_exercise(self):
        return pd.read_csv(
            self.exercise_path,
            sep='\t',
            header=None,
            names=[self.source_language_name, self.target_language_name]
        )
        
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