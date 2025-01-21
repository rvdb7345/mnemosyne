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

    :param prompt: The prompt string to send to the API.
    :param schema: The Pydantic model defining the JSON schema.
    :param client: The instantiated OpenAI client.
    :param model: The model to use.
    :param temperature: Sampling temperature.
    :param max_tokens: Maximum number of tokens in the response.
    :return: Parsed response object or None if an error occurs.
    """
    try:
        logger.info("Sending prompt to ChatGPT API with Structured Outputs.")
        response = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant for language learning.",
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


def fetch_multiple_choice_data(
    word: str,
    translated_word: str,
    from_lang: str,
    to_lang: str,
    difficulty: str,
    client: OpenAI,
) -> Optional[MultipleChoiceQuestion]:
    """
    Constructs the prompt and fetches multiple-choice data from ChatGPT.

    :param word: The word to translate.
    :param from_lang: Source language.
    :param to_lang: Target language.
    :param difficulty: Difficulty level.
    :param client: OpenAI client instance.
    :return: Parsed MultipleChoiceQuestion or None.
    """
    prompt = (
        f"Generate a multiple-choice question for language learning.\n\n"
        f"Word to translate: '{word}'\n"
        f"Correct translation: '{translated_word}' \n"
        f"Source Language: {from_lang}\n"
        f"Target Language: {to_lang}\n"
        f"Difficulty Level: {difficulty}\n\n"
    )

    return get_chatgpt_response(prompt, MultipleChoiceQuestion, client, max_tokens=300)
