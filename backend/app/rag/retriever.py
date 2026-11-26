from ..config import Config
from .vector_store import search


def retrieve(question, document_ids=None, *, top_k=None):
    """Return the top-K most relevant document excerpts for `question`.

    This is the retrieval leg of the Phase 6/7 pipeline. It embeds the user
    question with the same model used during ingestion, then queries pgvector
    with cosine distance (via the `<=>` operator and the HNSW index).

    Args:
        question: user question text.
        document_ids: optional list of document ids to restrict retrieval to a
            subset of ingested documents.
        top_k: override ``Config.TOP_K`` when provided.

    Returns:
        List of dicts with keys ``content``, ``metadata``, ``similarity``,
        exactly as ``vector_store.search`` returns.
    """
    from .embedding_model import embed_query

    if not question:
        return []

    query_vector = embed_query(question)
    ids = list(document_ids) if document_ids else None
    return search(query_vector, top_k=top_k, document_ids=ids)
