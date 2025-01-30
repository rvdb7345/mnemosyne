import logging
from typing import Optional, Type, TypeVar
from openai import OpenAI
from pydantic import BaseModel, ValidationError
from .chatgpt_schema import MultipleChoiceQuestion

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a generic type for Pydantic models
T = TypeVar("T", bound=BaseModel)

def get_chatgpt_response(
    prompt: str,
    schema: Type[T],
    client: OpenAI,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 300,
) -> Optional[T]:
    """
    Sends a prompt to the ChatGPT API with Structured Outputs and returns the parsed response.
    """
    try:
        logger.info("Sending prompt to ChatGPT API with Structured Outputs.")
        response = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a language teacher creating a fill-in-the-blank question with multiple-choice "
                        "options for the given word."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=schema,
        )

        message = response.choices[0].message
        if hasattr(message, "parsed") and message.parsed:
            parsed_response = message.parsed
            logger.info("Received and parsed response from ChatGPT API.")
            return parsed_response
        elif hasattr(message, "refusal"):
            logger.warning(f"ChatGPT API refused the request: {message.refusal}")
            return None
        else:
            logger.error("Unexpected response format from ChatGPT API.")
            return None

    except ValidationError as ve:
        logger.error(f"Validation error: {ve}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


def determine_learning_direction(from_lang: str, known_language: str) -> str:
    """
    Determines whether the user is going from a 'known to unknown' language
    or 'unknown to known', based on whether `from_lang` matches the user's known language.
    
    :param from_lang: The language of the word shown to the user.
    :param known_language: The language the user already speaks.
    :return: A string "known_to_unknown" if `from_lang` == known_language,
             otherwise "unknown_to_known".
    """
    if from_lang.lower() == known_language.lower():
        return "known_to_unknown"
    return "unknown_to_known"


def fetch_multiple_choice_data(
    word: str,
    translated_word: str,
    known_language: str,
    from_lang: str,
    to_lang: str,
    difficulty: str,
    client: OpenAI,
) -> Optional[MultipleChoiceQuestion]:
    """
    Constructs the prompt and fetches multiple-choice data from ChatGPT.
    """

    # Build the prompt text based on 'direction'
    # - "known_to_unknown": The user sees a known-language word (word),
    #   must produce answers in the target language (translated_word).
    # - "unknown_to_known": The user sees an unknown-language word (translated_word),
    #   must produce answers in the known language (word).

    # NOTE: The question sentence itself must always be in the target language (to_lang).
    #       The user’s "known" language is used for answers only when direction=="unknown_to_known".

    direction = determine_learning_direction(from_lang, known_language)
    unknown_language = from_lang if from_lang != known_language else to_lang

    prompt = f"""
You are a helpful language-learning assistant that generates a single multiple-choice question.

1. The question sentence must be in {unknown_language}.
2. It should contain a blank or context for the user to fill with the correct word, which is:
   - known-language word: '{word}'
   - target-language word: '{translated_word}'
3. Provide exactly 4 answer options in {to_lang}, where:
   - One is the correct answer: '{translated_word}'.
   - The other 3 are plausible distractors in {to_lang}.
4. The sentence should reflect a '{difficulty}' level of complexity.
5. The {translated_word} and distractors should be conjugated to fit the sentence grammatically.
6. Include an English translation of your question sentence (full_sentence_translation).
7. Output only the following JSON with no extra keys or text:
   {{
     "question_sentence": "...",
     "answer_options": ["...", "...", "...", "..."],
     "correct_answer": "...",
     "full_sentence_translation": "..."
   }}

Example:
{{
  "question_sentence": "Bu ev mavi, o ev ___",
  "answer_options": ["Buyuk", "Kucuk", "Kahverengi", "Ogretmen"],
  "correct_answer": "Kahverengi",
  "full_sentence_translation": "This house is blue, that house is ___"
}}
"""

    logger.info(f"Prompt to ChatGPT:\n{prompt}")

    return get_chatgpt_response(
        prompt,
        MultipleChoiceQuestion,
        client,
        model="gpt-4o-mini",
        max_tokens=300
    )