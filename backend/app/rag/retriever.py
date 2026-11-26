from .vector_store import search
from .embedding_model import embed_query

def retrieve(question, document_ids=None, *, top_k=None):
    if not question:
        return []

    query_vector = embed_query(question)
    ids = list(document_ids) if document_ids else None
    return search(query_vector, top_k=top_k, document_ids=ids)
