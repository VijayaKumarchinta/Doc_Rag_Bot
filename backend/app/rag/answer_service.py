import time

from google import genai
from google.genai import types

from ..config import Config
from .prompt import PROMPT_SEPARATOR

# The hosted model occasionally answers 503/429 during demand spikes. Retry a
# couple of times before failing so a single blip does not break the chat.
_MAX_ATTEMPTS = 3
_RETRY_DELAY_S = 1.5
_TRANSIENT_CODES = {429, 500, 502, 503, 504}


def _is_transient(error):
    code = getattr(error, "code", None) or getattr(error, "status_code", None)
    if isinstance(code, int) and code in _TRANSIENT_CODES:
        return True
    text = str(error).lower()
    return "unavailable" in text or "high demand" in text or "503" in text


def _client():
    return genai.Client(api_key=Config.GOOGLE_API_KEY)


def generate_answer(prompt_text, model=None):
    """Return the model-generated answer text for ``prompt_text``.

    ``prompt.build_prompt`` joins the system instruction and the user turn with
    ``PROMPT_SEPARATOR``; the first part is passed to Gemini as the system
    instruction and the remainder as the user turn.
    """
    if model is None:
        model = Config.GEMINI_MODEL
    if not Config.GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is not configured")

    system, separator, user = prompt_text.partition(PROMPT_SEPARATOR)
    if not separator:
        # Prompt assembled elsewhere: send it all as the user turn.
        system, user = "", prompt_text

    client = _client()
    response = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=user or system,
                config=types.GenerateContentConfig(
                    system_instruction=system or None,
                    temperature=0.2,
                ),
            )
            break
        except Exception as error:
            if attempt == _MAX_ATTEMPTS or not _is_transient(error):
                if _is_transient(error):
                    raise RuntimeError(
                        "The answer model is temporarily unavailable. Please try again."
                    ) from error
                raise
            time.sleep(_RETRY_DELAY_S * attempt)

    text = getattr(response, "text", None)
    if not text:
        # Defensive fallback for unexpected response shapes.
        for candidate in getattr(response, "candidates", None) or []:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []
            joined = "".join(getattr(p, "text", "") or "" for p in parts)
            if joined:
                text = joined
                break
    return text or ""
