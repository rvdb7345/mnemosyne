# src/utils/chatgpt_schema.py
from pydantic import BaseModel, Field
from typing import List

# src/utils/chatgpt_schema.py

from pydantic import BaseModel, Field
from typing import List

class MultipleChoiceQuestion(BaseModel):
    """
    Represents the structure of a single multiple-choice question, including
    the question sentence, the list of answer options, the correct answer,
    and an English translation of the full sentence.
    """
    question_sentence: str = Field(
        ...,
        description="The question or sentence containing the blank/context in the target language."
    )
    answer_options: List[str] = Field(
        ...,
        description="Exactly 4 possible choices, each one a string."
    )
    correct_answer: str = Field(
        ...,
        description="The correct answer string, which must match one of the answer_options."
    )
    full_sentence_translation: str = Field(
        ...,
        description="An English translation of the entire question sentence for reference."
    )
