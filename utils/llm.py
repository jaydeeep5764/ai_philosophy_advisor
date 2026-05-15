from __future__ import annotations

import os
from functools import lru_cache

import google.generativeai as genai
from dotenv import load_dotenv
from google.api_core import exceptions as google_exceptions


DEFAULT_MODEL = "gemini-2.5-flash"


class LLMError(RuntimeError):
    """User-safe exception raised when the LLM provider cannot return a response."""


@lru_cache(maxsize=1)
def _load_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMError(
            "Missing Gemini API key. Add GEMINI_API_KEY to your .env file before asking a question."
        )
    return api_key


def _configured_model_name(model_name: str | None = None) -> str:
    load_dotenv()
    return model_name or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL


@lru_cache(maxsize=4)
def _get_model(model_name: str) -> genai.GenerativeModel:
    genai.configure(api_key=_load_api_key())
    return genai.GenerativeModel(model_name)


def generate_response(prompt: str, model_name: str | None = None) -> str:
    """
    Generate a Gemini response for a fully-formed prompt.

    The rest of the app owns prompt construction. This function owns provider setup,
    API errors, and response validation so the LLM layer can be replaced later.
    """
    if not prompt or not prompt.strip():
        raise LLMError("Cannot generate a response from an empty prompt.")

    try:
        selected_model = _configured_model_name(model_name)
        response = _get_model(selected_model).generate_content(
            prompt,
            generation_config={
                "temperature": 0.55,
                "top_p": 0.9,
                "max_output_tokens": 1400,
            },
        )
    except google_exceptions.PermissionDenied as exc:
        raise LLMError("Gemini rejected the API key. Confirm that GEMINI_API_KEY is valid.") from exc
    except google_exceptions.ResourceExhausted as exc:
        raise LLMError("Gemini quota or rate limit was reached. Please wait or check your quota.") from exc
    except google_exceptions.InvalidArgument as exc:
        raise LLMError("Gemini rejected the request. The prompt or model configuration may be invalid.") from exc
    except google_exceptions.NotFound as exc:
        raise LLMError(
            "The configured Gemini model was not found or is not available for this API key. "
            "Set GEMINI_MODEL in .env to a model your key can access, such as gemini-2.5-flash."
        ) from exc
    except google_exceptions.GoogleAPIError as exc:
        raise LLMError("Gemini API failed while generating a response. Please try again.") from exc
    except Exception as exc:
        raise LLMError("Unexpected LLM failure. Check your API setup and network connection.") from exc

    text = getattr(response, "text", None)
    if not text or not text.strip():
        raise LLMError("Gemini returned an empty response. Try rephrasing your question.")

    return text.strip()
