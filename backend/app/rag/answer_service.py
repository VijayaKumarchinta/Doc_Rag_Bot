# backend/app/rag/answer_service.py

from google import genai
from google.genai import types

from ..config import Config


def _client():
    return genai.Client(api_key=Config.GOOGLE_API_KEY)


def generate_answer(prompt_text, model=None):
    """Return the model-generated answer text for `prompt_text`.

    The first '.google-genai' token in `prompt_text` is treated as the system
    instruction and the remainder as the user prompt, matching how the prompt
    builder emits the SYSTEM_PROMPT prefix.
    """
    if model is None:
        model = Config.GEMINI_MODEL
    if not Config.GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is not configured")

    client = _client()
    # Split the system prompt we prepend from the user prompt so Gemini treats the
    # system part as instructions and the rest as the user turn.
    prefix = ".google-genai"
    if prompt_text.startswith(prefix):
        system = prompt_text[len(prefix):]
        user = ""
    else:
        # Fallback: if the prompt was constructed without the prefix, send the
        # whole thing as the user prompt and pass an empty system instruction.
        system = ""
        user = prompt_text

    contents = []
    if system:
        contents.append(types.UserContent(parts=[types.TextPart(text=system)]))
    if user:
        contents.append(types.UserContent(parts=[types.TextPart(text=user)]))

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system or None,
            temperature=0.2,
        ),
    )
    # The SDK returns candidate text under `.text` when available.
    text = getattr(response, "text", None)
    if not text:
        # Defensive fallback for unexpected response shapes.
        candidates = getattr(response, "candidates", None)
        if candidates:
            for c in candidates:
                role_parts = getattr(c, "content", None)
                if role_parts is not None:
                    parts = getattr(role_parts, "parts", None)
                    if parts:
                        texts = [getattr(p, "text", "") for p in parts]
                        text = "".join(t for t in texts if t)
                        if text:
                            break
    return text or ""
