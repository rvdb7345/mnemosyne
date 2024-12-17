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
        
class DutchVocabList1000(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Dutch Frequency List 0 - 1000",
            source_language_name='Dutch',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/DutchEnglishFrequencySimplified1000.txt"
        )
        
class DutchVocabList2000(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Dutch Frequency List 1000 - 2000",
            source_language_name='Dutch',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/DutchEnglishFrequencySimplified2000.txt"
        )
        
class DutchVocabList3000(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Dutch Frequency List 2000 - 3000",
            source_language_name='Dutch',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/DutchEnglishFrequencySimplified3000.txt"
        )

class DutchVocabList4000(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Dutch Frequency List 3000 - 4000",
            source_language_name='Dutch',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/DutchEnglishFrequencySimplified4000.txt"
        )
        
class DutchVocabList5000(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Dutch Frequency List 4000 - 5000",
            source_language_name='Dutch',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/DutchEnglishFrequencySimplified5000.txt"
        )


class SpanishVocabList(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Spanish Frequency List",
            source_language_name='Spanish',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/SpanishEnglishFrequencySimplified.txt"
        )
        
class SpanishVocabList1000(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Spanish Frequency List 0 - 1000",
            source_language_name='Spanish',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/SpanishEnglishFrequencySimplified1000.txt"
        )
        
class SpanishVocabList2000(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Spanish Frequency List 1000 - 2000",
            source_language_name='Spanish',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/SpanishEnglishFrequencySimplified2000.txt"
        )

class SpanishVocabList3000(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Spanish Frequency List 2000 - 3000",
            source_language_name='Spanish',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/SpanishEnglishFrequencySimplified3000.txt"
        )

class SpanishVocabList4000(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Spanish Frequency List 3000 - 4000",
            source_language_name='Spanish',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/SpanishEnglishFrequencySimplified4000.txt"
        )

class SpanishVocabList5000(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Spanish Frequency List 4000 - 5000",
            source_language_name='Spanish',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/SpanishEnglishFrequencySimplified5000.txt"
        )

class TurkishDuolingoList(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Turkish Duolingo List",
            source_language_name='Turkish',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/TurkishEnglishDuolingo.txt"
        )
        
class TurkishVocabList(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Turkish Frequency List",
            source_language_name='Turkish',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/TurkishEnglishFrequencySimplified.txt"
        )

class TurkishVocabList1000(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Turkish Frequency List 0 - 1000",
            source_language_name='Turkish',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/TurkishEnglishFrequencySimplified1000.txt"
        )

class TurkishVocabList2000(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Turkish Frequency List 1000 - 2000",
            source_language_name='Turkish',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/TurkishEnglishFrequencySimplified2000.txt"
        )

class TurkishVocabList3000(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Turkish Frequency List 2000 - 3000",
            source_language_name='Turkish',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/TurkishEnglishFrequencySimplified3000.txt"
        )

class TurkishVocabList4000(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Turkish Frequency List 3000 - 4000",
            source_language_name='Turkish',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/TurkishEnglishFrequencySimplified4000.txt"
        )
        
class TurkishVocabList5000(VocabList):
    def __init__(self):
        super().__init__(
            exercise_name="Turkish Frequency List 4000 - 5000",
            source_language_name='Turkish',
            target_language_name='English',
            exercise_path="streamlit-app/src/standard_exercises/TurkishEnglishFrequencySimplified5000.txt"
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
