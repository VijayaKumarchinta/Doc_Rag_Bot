import re

from ..config import Config
from .embedding_model import embed_query
from .vector_store import search


def retrieve(question, document_ids=None, *, top_k=None):
    if not question:
        return []

    ids = list(document_ids) if document_ids else None
    # Start with a generous candidate pool so the re-ranker can select the most
    # relevant excerpts for the model. TOP_K truncates near the end.
    candidate_pool = (top_k or Config.TOP_K) * 3
    query_vector = embed_query(question)
    candidates = search(query_vector, top_k=candidate_pool, document_ids=ids)

    # Re-rank by lexical overlap with the question so the LLM receives the most
    # relevant snippets (score + original similarity) first. Simple and
    # reliable for short passages; also keeps the 'similarity' field meaningful.
    words = set(re.findall(r"[A-Za-z0-9]+", question.lower()))
    scored = []
    for item in candidates:
        text = (item.get("content") or "").lower()
        overlap = sum(1 for w in words if w in text)
        item["_rerank_score"] = overlap
        scored.append(item)

    scored.sort(key=lambda x: x["_rerank_score"], reverse=True)
    return scored[:top_k] if top_k else scored
