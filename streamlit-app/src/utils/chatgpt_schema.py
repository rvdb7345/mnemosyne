# src/utils/chatgpt_schema.py

from pydantic import BaseModel
from typing import List

class SentenceWithBlank(BaseModel):
    sentence_with_blank: str
    correct_translation: str

class ChatGPTUsageResponse(BaseModel):
    word_from_language: str
    sentences: List[SentenceWithBlank]

class ChatGPTSynonymsResponse(BaseModel):
    synonyms: List[str]
