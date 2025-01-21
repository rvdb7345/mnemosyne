# src/utils/chatgpt_schema.py

from pydantic import BaseModel
from typing import List

from pydantic import BaseModel, Field
from typing import List

class MultipleChoiceQuestion(BaseModel):
    sentence: str = Field(..., description="Sentence in target language containing a blank where the translated word fits contextually.")
    distractors: List[str] = Field(..., description="List of three distractor options that grammatically fit the sentence as alternatives for the correct translation.")
