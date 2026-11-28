import re
from dataclasses import dataclass

_DOCUMENT_PREFIXES = (
    "what",
    "who",
    "when",
    "where",
    "which",
    "how",
    "find",
    "list",
    "show",
    "give",
    "name",
    "identify",
    "total",
    "sum",
    "average",
    "count",
    "compare",
    "difference",
    "amount",
    "value",
    "cells",
    "columns",
    "rows",
    "headers",
    "contact",
    "date",
    "revenue",
    "sales",
    "clients",
    "customers",
)

_GENERIC_PREFIXES = (
    "hello",
    "hi",
    "hey",
    "thanks",
    "thank",
    "bye",
    "goodbye",
    "who are you",
    "what are you",
    "what is your",
    "tell me about yourself",
    "your name",
    "introduce yourself",
    "help",
    "can you",
    "could you",
    "do you know",
    "do you have",
    "can i",
    "is there",
    "explain",
    "define",
    "what does",
)

_UNANSWERABLE_HINTS = (
    "weather",
    "president",
    "meaning of life",
    "capital of",
    "population of",
    "current date",
    "today's date",
    "time",
    "who won",
    "score",
    "news",
    "recent",
)


@dataclass
class RouterResult:
    """Immutable routing decision for a single question."""

    intent: str
    reason: str
    follow_up_question: str | None = None


def classify(question: str) -> RouterResult:
    """Classify a user question into one of three intents.

    Returns:
        - intent ``"document"`` if the question is likely answerable from the
          documents that have been ingested.
        - intent ``"generic"`` if the question is conversational or metadata about
          the assistant and should be answered without retrieval.
        - intent ``"unanswerable"`` if the question is clearly out of scope for the
          document set (external factual queries the RAG system should not attempt).
    """
    q = _normalize(question)
    if not q:
        return RouterResult(
            intent="document",
            reason="empty question treated as document query (caller should validate first)",
        )

    if _matches_any(q, _GENERIC_PREFIXES, _word_boundary=True):
        return RouterResult(
            intent="generic",
            reason="matched a conversational/assistant prefix",
        )

    if _matches_any(q, _UNANSWERABLE_HINTS, _word_boundary=True):
        return RouterResult(
            intent="unanswerable",
            reason="matched an out-of-scope hint",
            follow_up_question=(
                "I don't have information about that topic in your uploaded documents. "
                "You may want to ask about the contents of your PDF, Excel, or CSV files."
            ),
        )

    if _is_document_style(q):
        return RouterResult(
            intent="document",
            reason="matches a document-question pattern",
        )
    
    return RouterResult(
        intent="document",
        reason="default routing to retrieval",
    )

_WORD = re.compile(r"[A-Za-z0-9]+")

def _normalize(text: str) -> str:
    text = text.strip()
    # Normalise common punctuation so prefix matching is robust across user input.
    text = re.sub(r"[^A-Za-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def _matches_any(normalized: str, candidates: tuple[str, ...], *, _word_boundary: bool) -> bool:
    if not candidates:
        return False
    if _word_boundary:
        words = set(_WORD.findall(normalized))
        cand_words = {c.strip().lower() for c in candidates if c.strip()}
        return bool(words & cand_words)
    # Fallback substring check (not used by the current candidate sets).
    return any(c.strip().lower() in normalized for c in candidates if c.strip())


def _is_document_style(normalized: str) -> bool:
    if not normalized:
        return False
    first_word = _WORD.match(normalized)
    if first_word is None:
        return False
    head = first_word.group().lower()
    # Many document questions start with a wh-word or a verb that signals a
    # content lookup. Use a small explicit allow-list rather than a broad regex.
    return head in _DOCUMENT_PREFIXES
