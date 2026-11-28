import re

from ..config import Config
from .embedding_model import embed_queries
from .vector_store import search

_WORD = re.compile(r"[a-z0-9]+")

# Embedding similarity is the primary relevance signal: the query and every
# stored chunk are embedded with the same model, so their cosine score already
# captures meaning (paraphrases included). A literal word match is a weak extra
# signal — useful for names, IDs and numbers — so it can only nudge an excerpt
# up the list, never outrank a clearly better semantic hit.
_LEXICAL_BOOST = 0.02


def retrieve(question, document_ids=None, *, top_k=None):
    """Return the most relevant stored excerpts for ``question``.

    Args:
        question: user question text.
        document_ids: optional list of document ids to restrict retrieval to.
        top_k: override ``Config.TOP_K`` when provided.

    Returns:
        List of dicts with ``content``, ``metadata``, ``similarity`` exactly as
        ``vector_store.search`` returns them, ordered most relevant first.
    """
    if not question or not question.strip():
        return []

    limit = top_k or Config.TOP_K
    ids = list(document_ids) if document_ids else None

    query_vector = embed_queries([question])[0]
    # Fetch a wider pool than we return so the lexical nudge can re-order it
    # without changing which excerpts are candidates.
    candidates = search(query_vector, top_k=max(limit * 3, limit), document_ids=ids)
    return _rank(candidates, question)[:limit]


def _rank(candidates, question):
    """Order excerpts by embedding similarity, nudged by literal word overlap."""
    if not candidates:
        return []

    question_words = {w for w in _WORD.findall(question.lower()) if len(w) > 2}
    for candidate in candidates:
        text = (candidate.get("content") or "").lower()
        overlap = sum(1 for word in question_words if word in text)
        similarity = float(candidate.get("similarity") or 0.0)
        candidate["_rank_score"] = similarity + _LEXICAL_BOOST * overlap

    candidates.sort(key=lambda c: c["_rank_score"], reverse=True)
    return candidates
