from __future__ import annotations

import os
import hashlib
import math
import re
from functools import lru_cache

import google.generativeai as genai
from dotenv import load_dotenv
from google.api_core import exceptions as google_exceptions


DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_OPENAI_MODEL = "gpt-5"
DEFAULT_XAI_MODEL = "grok-4.3"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
XAI_BASE_URL = "https://api.x.ai/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_EMBEDDING_MODEL = "models/gemini-embedding-001"
LOCAL_EMBEDDING_DIMENSIONS = 768
SUPPORTED_PROVIDERS = ("gemini", "openai", "xai", "groq")


class LLMError(RuntimeError):
    """User-safe exception raised when the LLM provider cannot return a response."""


class ProviderQuotaError(LLMError):
    """Raised when a provider can be retried through a configured fallback."""

    def __init__(self, provider: str, message: str) -> None:
        super().__init__(message)
        self.provider = provider


def _load_env_settings() -> None:
    # Streamlit is long-lived, so .env edits must replace values already in os.environ.
    load_dotenv(override=True)


@lru_cache(maxsize=1)
def _load_api_key() -> str:
    _load_env_settings()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMError(
            "Missing Gemini API key. Add GEMINI_API_KEY to your .env file before asking a question."
        )
    return api_key


def _load_openai_api_key() -> str:
    _load_env_settings()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMError(
            "Missing OpenAI API key. Add OPENAI_API_KEY to your .env file before asking a question."
        )
    return api_key


def _load_xai_api_key() -> str:
    _load_env_settings()
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise LLMError(
            "Missing xAI API key. Add XAI_API_KEY to your .env file before asking a question."
        )
    return api_key


def _load_groq_api_key() -> str:
    _load_env_settings()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        legacy_key = os.getenv("XAI_API_KEY") or ""
        if legacy_key.startswith("gsk_"):
            api_key = legacy_key
    if not api_key:
        raise LLMError(
            "Missing Groq API key. Add GROQ_API_KEY to your .env file before asking a question."
        )
    return api_key


def _configured_provider() -> str:
    _load_env_settings()
    provider = (os.getenv("LLM_PROVIDER") or "gemini").strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise LLMError("Unsupported LLM_PROVIDER. Use 'gemini', 'openai', 'xai', or 'groq' in .env.")
    return provider


def _configured_provider_order() -> tuple[str, ...]:
    _load_env_settings()
    providers = [_configured_provider()]
    fallback_value = os.getenv("LLM_PROVIDER_FALLBACKS") or ""
    providers.extend(part.strip().lower() for part in fallback_value.split(",") if part.strip())

    ordered: list[str] = []
    for provider in providers:
        if provider not in SUPPORTED_PROVIDERS:
            raise LLMError(
                "Unsupported provider in LLM_PROVIDER_FALLBACKS. "
                "Use only 'gemini', 'openai', 'xai', or 'groq'."
            )
        if provider not in ordered:
            ordered.append(provider)
    return tuple(ordered)


def _configured_gemini_model_name(model_name: str | None = None) -> str:
    _load_env_settings()
    return model_name or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL


def _configured_openai_model_name(model_name: str | None = None) -> str:
    _load_env_settings()
    return model_name or os.getenv("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL


def _configured_xai_model_name(model_name: str | None = None) -> str:
    _load_env_settings()
    return model_name or os.getenv("XAI_MODEL") or DEFAULT_XAI_MODEL


def _configured_groq_model_name(model_name: str | None = None) -> str:
    _load_env_settings()
    return model_name or os.getenv("GROQ_MODEL") or DEFAULT_GROQ_MODEL


@lru_cache(maxsize=4)
def _get_model(model_name: str) -> genai.GenerativeModel:
    genai.configure(api_key=_load_api_key())
    return genai.GenerativeModel(model_name)


def generate_response(prompt: str, model_name: str | None = None) -> str:
    """
    Generate a provider response for a fully-formed prompt.

    The rest of the app owns prompt construction. This function owns provider setup,
    API errors, and response validation so the LLM layer can be replaced later.
    """
    if not prompt or not prompt.strip():
        raise LLMError("Cannot generate a response from an empty prompt.")

    quota_errors: list[ProviderQuotaError] = []
    for provider in _configured_provider_order():
        try:
            return _generate_provider_response(provider, prompt, model_name)
        except ProviderQuotaError as exc:
            quota_errors.append(exc)

    if quota_errors:
        exhausted = ", ".join(error.provider for error in quota_errors)
        raise LLMError(
            f"All configured LLM providers reached quota or rate limits: {exhausted}. "
            "Check provider billing or limits, or change LLM_PROVIDER_FALLBACKS."
        ) from quota_errors[-1]

    raise LLMError("No configured LLM provider could generate a response.")


def _generate_provider_response(
    provider: str,
    prompt: str,
    model_name: str | None = None,
) -> str:
    if provider == "openai":
        return _generate_openai_response(prompt, model_name)
    if provider == "xai":
        return _generate_xai_response(prompt, model_name)
    if provider == "groq":
        return _generate_groq_response(prompt, model_name)
    return _generate_gemini_response(prompt, model_name)


def _generate_gemini_response(prompt: str, model_name: str | None = None) -> str:
    try:
        selected_model = _configured_gemini_model_name(model_name)
        response = _get_model(selected_model).generate_content(
            prompt,
            generation_config={
                "temperature": 0.55,
                "top_p": 0.9,
                "max_output_tokens": 8192,
            },
        )
    except google_exceptions.PermissionDenied as exc:
        raise LLMError("Gemini rejected the API key. Confirm that GEMINI_API_KEY is valid.") from exc
    except google_exceptions.ResourceExhausted as exc:
        raise ProviderQuotaError(
            "gemini",
            "Gemini quota or rate limit was reached. Please wait or check your quota.",
        ) from exc
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

    text = _extract_response_text(response)
    if not text or not text.strip():
        finish_reason = _finish_reason(response)
        raise LLMError(
            "Gemini returned an empty response"
            + (f" with finish reason {finish_reason}" if finish_reason else "")
            + ". Try rephrasing your question or asking again."
        )

    return text.strip()


def _generate_openai_response(prompt: str, model_name: str | None = None) -> str:
    try:
        from openai import (
            APIError,
            AuthenticationError,
            BadRequestError,
            NotFoundError,
            OpenAI,
            PermissionDeniedError,
            RateLimitError,
        )
    except ImportError as exc:
        raise LLMError("OpenAI support is not installed. Run pip install -r requirements.txt.") from exc

    try:
        client = OpenAI(api_key=_load_openai_api_key())
        response = client.responses.create(
            model=_configured_openai_model_name(model_name),
            input=prompt,
            max_output_tokens=8192,
        )
    except AuthenticationError as exc:
        raise LLMError("OpenAI rejected the API key. Confirm that OPENAI_API_KEY is valid.") from exc
    except RateLimitError as exc:
        raise ProviderQuotaError(
            "openai",
            "OpenAI API quota, billing limit, or rate limit was reached. "
            "Check API billing and usage limits, then try again.",
        ) from exc
    except BadRequestError as exc:
        raise LLMError("OpenAI rejected the request. The prompt or model configuration may be invalid.") from exc
    except NotFoundError as exc:
        raise LLMError(
            "The configured OpenAI model was not found or is not available for this API key. "
            "Set OPENAI_MODEL in .env to a model your key can access."
        ) from exc
    except APIError as exc:
        raise LLMError("OpenAI API failed while generating a response. Please try again.") from exc
    except Exception as exc:
        raise LLMError("Unexpected OpenAI failure. Check your API setup and network connection.") from exc

    text = str(getattr(response, "output_text", "") or "")
    if not text.strip():
        raise LLMError("OpenAI returned an empty response. Try rephrasing your question or asking again.")
    return text.strip()


def _generate_xai_response(prompt: str, model_name: str | None = None) -> str:
    try:
        from openai import (
            APIError,
            AuthenticationError,
            BadRequestError,
            NotFoundError,
            OpenAI,
            PermissionDeniedError,
            RateLimitError,
        )
    except ImportError as exc:
        raise LLMError("xAI support requires the OpenAI Python SDK. Run pip install -r requirements.txt.") from exc

    try:
        client = OpenAI(api_key=_load_xai_api_key(), base_url=XAI_BASE_URL)
        response = client.responses.create(
            model=_configured_xai_model_name(model_name),
            input=prompt,
            max_output_tokens=8192,
        )
    except AuthenticationError as exc:
        raise LLMError("xAI rejected the API key. Confirm that XAI_API_KEY is valid.") from exc
    except PermissionDeniedError as exc:
        raise LLMError(
            "xAI denied generation for this API key or team. "
            "Check xAI credits, licenses, and team permissions."
        ) from exc
    except RateLimitError as exc:
        raise ProviderQuotaError(
            "xai",
            "xAI API credits, quota, or rate limit was reached. "
            "Check xAI billing and usage limits, then try again.",
        ) from exc
    except BadRequestError as exc:
        if "api key" in str(exc).casefold():
            raise LLMError("xAI rejected the API key. Confirm that XAI_API_KEY is a key from xAI.") from exc
        raise LLMError("xAI rejected the request. The prompt or model configuration may be invalid.") from exc
    except NotFoundError as exc:
        raise LLMError(
            "The configured xAI model was not found or is not available for this API key. "
            "Set XAI_MODEL in .env to a model your key can access."
        ) from exc
    except APIError as exc:
        raise LLMError("xAI API failed while generating a response. Please try again.") from exc
    except Exception as exc:
        raise LLMError("Unexpected xAI failure. Check your API setup and network connection.") from exc

    text = str(getattr(response, "output_text", "") or "")
    if not text.strip():
        raise LLMError("xAI returned an empty response. Try rephrasing your question or asking again.")
    return text.strip()


def _generate_groq_response(prompt: str, model_name: str | None = None) -> str:
    try:
        from openai import (
            APIError,
            AuthenticationError,
            BadRequestError,
            NotFoundError,
            OpenAI,
            PermissionDeniedError,
            RateLimitError,
        )
    except ImportError as exc:
        raise LLMError("Groq support requires the OpenAI Python SDK. Run pip install -r requirements.txt.") from exc

    try:
        client = OpenAI(api_key=_load_groq_api_key(), base_url=GROQ_BASE_URL)
        response = client.responses.create(
            model=_configured_groq_model_name(model_name),
            input=prompt,
            max_output_tokens=8192,
        )
    except AuthenticationError as exc:
        raise LLMError("Groq rejected the API key. Confirm that GROQ_API_KEY is valid.") from exc
    except PermissionDeniedError as exc:
        raise LLMError("Groq denied generation for this API key or project. Check Groq permissions.") from exc
    except RateLimitError as exc:
        raise ProviderQuotaError(
            "groq",
            "Groq quota or rate limit was reached. Check Groq usage limits, then try again.",
        ) from exc
    except BadRequestError as exc:
        raise LLMError("Groq rejected the request. The prompt or model configuration may be invalid.") from exc
    except NotFoundError as exc:
        raise LLMError(
            "The configured Groq model was not found or is not available for this API key. "
            "Set GROQ_MODEL in .env to a model your key can access."
        ) from exc
    except APIError as exc:
        raise LLMError("Groq API failed while generating a response. Please try again.") from exc
    except Exception as exc:
        raise LLMError("Unexpected Groq failure. Check your API setup and network connection.") from exc

    text = str(getattr(response, "output_text", "") or "")
    if not text.strip():
        raise LLMError("Groq returned an empty response. Try rephrasing your question or asking again.")
    return text.strip()


def _extract_response_text(response: object) -> str:
    try:
        text = getattr(response, "text", None)
        if text:
            return str(text)
    except Exception:
        pass

    parts_text: list[str] = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            text = getattr(part, "text", None)
            if text:
                parts_text.append(str(text))
    return "\n".join(parts_text)


def _finish_reason(response: object) -> str:
    candidates = getattr(response, "candidates", []) or []
    if not candidates:
        return ""
    finish_reason = getattr(candidates[0], "finish_reason", "")
    return str(finish_reason) if finish_reason else ""


def generate_embedding(text: str, task_type: str) -> list[float]:
    if not text or not text.strip():
        raise LLMError("Cannot generate an embedding from empty text.")

    _load_env_settings()
    embedding_provider = (os.getenv("EMBEDDING_PROVIDER") or "local").strip().lower()
    if embedding_provider == "local":
        return _generate_local_embedding(text)

    embedding_model = os.getenv("GEMINI_EMBEDDING_MODEL") or DEFAULT_EMBEDDING_MODEL
    try:
        genai.configure(api_key=_load_api_key())
        result = genai.embed_content(
            model=embedding_model,
            content=text,
            task_type=task_type,
        )
    except google_exceptions.PermissionDenied as exc:
        raise LLMError("Gemini rejected the API key while generating embeddings.") from exc
    except google_exceptions.ResourceExhausted as exc:
        raise LLMError("Gemini embedding quota or rate limit was reached.") from exc
    except google_exceptions.NotFound as exc:
        raise LLMError(
            "The configured Gemini embedding model was not found. "
            "Set GEMINI_EMBEDDING_MODEL in .env to a supported embedding model."
        ) from exc
    except google_exceptions.GoogleAPIError as exc:
        raise LLMError("Gemini API failed while generating an embedding.") from exc
    except Exception as exc:
        raise LLMError("Unexpected embedding failure. Check your API setup and network connection.") from exc

    embedding = result.get("embedding") if isinstance(result, dict) else None
    if not embedding:
        raise LLMError("Gemini returned an empty embedding.")
    return embedding


def _generate_local_embedding(text: str) -> list[float]:
    """
    Deterministic local embedding used for RAG retrieval without API quota.

    This is intentionally lightweight: it hashes unigrams and bigrams into a fixed-size
    vector, then normalizes it for cosine search. It is not as semantically rich as a
    hosted embedding model, but it keeps the knowledge base usable when API quota is low.
    """
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_'-]*", text.casefold())
    if not tokens:
        tokens = [text.casefold()]

    vector = [0.0] * LOCAL_EMBEDDING_DIMENSIONS
    features = tokens + [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]

    for feature in features:
        digest = hashlib.sha256(feature.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % LOCAL_EMBEDDING_DIMENSIONS
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    magnitude = math.sqrt(sum(value * value for value in vector))
    if not magnitude:
        return vector
    return [value / magnitude for value in vector]
