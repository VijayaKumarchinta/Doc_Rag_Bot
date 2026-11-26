import re

from ..config import Config
from .embedding_model import embed_queries
from .vector_store import search


def retrieve(question, document_ids=None, *, top_k=None):
    if not question:
        return []

    ids = list(document_ids) if document_ids else None
    # Start with a generous candidate pool so the re-ranker can select the most
    # relevant excerpts for the model. TOP_K truncates near the end.
    candidate_pool = (top_k or Config.TOP_K) * 3
    query_vector = _build_query_vector(question)
    candidates = search(query_vector, top_k=candidate_pool, document_ids=ids)

    # Semantic re-rank + lexical primary sort so the LLM receives the most
    # relevant excerpts first.
    top_n = (top_k or Config.TOP_K) * 3
    candidates = _semantic_rerank(candidates, [question], top_n)
    return candidates[:top_k] if top_k else candidates


def _build_query_vector(question):
    """Return the normalized embedding vector for a single question."""
    return embed_queries([question])[0]


def _semantic_rerank(candidates, queries, top_n=None):
    """Re-rank retrieved snippets and attach scoring fields.

    The ranking is PRIMARY lexical overlap with the question (the most reliable
    filter for short passages), with semantic vector similarity as a
    tie-breaker only. Qwen3-Embedding-0.6B is an embedding model, not a passage
    cross-encoder, so its raw cosine can misrank short numeric snippets; using
    it as the sole signal would make retrieval worse than the original
    lexical approach. We attach both scores so the LLM / caller can see which
    signal led and the citation contract can stay unchanged.
    """
    if not candidates:
        return []
    if not queries:
        return candidates

    query_vectors = embed_queries(queries)
    results = []
    for candidate in candidates:
        text = candidate.get("content") or ""

        # Primary: lexical overlap with the question.
        words = set(re.findall(r"[A-Za-z0-9]+", queries[0].lower()))
        overlap = sum(1 for w in words if w in text)
        candidate["_rerank_score"] = float(overlap)

        # Secondary: semantic similarity (best-effort, one forward pass).
        if len(query_vectors) > 0:
            candidate["semantic_score"] = float(
                1.0 - _cosine_similarity(query_vectors[0], _chunk_vector(candidate))
            )
        else:
            candidate["semantic_score"] = 0.0

        results.append(candidate)

    def _sort_key(item):
        return (
            -item.get("_rerank_score", 0.0),
            -item.get("semantic_score", 0.0),
            -item.get("similarity", 0.0),
        )

    results.sort(key=_sort_key)
    return results[:top_n] if top_n is not None else results


def _chunk_vector(candidate):
    """Return the 1024-dim embedding for a candidate chunk.

    The chunk's embedding is not stored in search-result metadata, so it is
    rebuilt from the chunk text using the same cached model the rest of the
    pipeline uses. This keeps retrieval DB-independent.
    """
    text = candidate.get("content") or ""
    if not text:
        return None
    return embed_queries([text])[0]


def _cosine_similarity(a, b):
    """Cosine similarity between two normalized vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    # a and b are normalized, so dot product == cosine similarity.
    return max(-1.0, min(1.0, dot))
