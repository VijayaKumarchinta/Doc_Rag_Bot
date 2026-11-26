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
    query_vector = embed_queries([question])[0]
    candidates = search(query_vector, top_k=candidate_pool, document_ids=ids)

    # Semantic re-rank + lexical primary sort so the LLM receives the most
    # relevant excerpts first. The re-ranker uses the cached SentenceTransformer
    # (a separate forward pass per candidate) but keeps the LLM context tight.
    top_n = (top_k or Config.TOP_K) * 3
    candidates = _semantic_rerank(candidates, [question], top_n)
    return candidates[:top_k] if top_k else candidates


def _semantic_rerank(candidates, queries, top_n=None):
    """Re-rank retrieved snippets and attach scoring fields.

    Ranking is PRIMARY lexical overlap with the question, with semantic vector
    similarity as a tie-breaker only. Qwen3-Embedding-0.6B is an embedding
    model, not a passage cross-encoder, so its raw cosine can misrank short
    numeric snippets; using it as the sole signal would make retrieval worse
    than the original lexical approach.     We attach both scores so the LLM / caller can see which signal led and
    the citation contract stays unchanged.
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

        # Secondary: semantic similarity (one forward pass over all candidates).
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
