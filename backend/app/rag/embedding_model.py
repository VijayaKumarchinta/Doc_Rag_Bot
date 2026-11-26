import threading

from sentence_transformers import SentenceTransformer
from app.config import Config

_lock = threading.Lock()
_model = None

def _get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                _model = SentenceTransformer(Config.EMBEDDING_MODEL, device='cpu')
    return _model

def dim():
    """Return the embedding dimension of the loaded model (1024 for Qwen3)."""
    return int(_get_model().get_sentence_embedding_dimension())

def embed_texts(texts, batch_size=16, normalize=True):
    """Encode a list of strings into normalized vectors.

    Returns a list of lists of floats (one vector per input string).
    """
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=normalize,
    )
    return [v.tolist() for v in vectors]


def embed_query(text, batch_size=16):
    """Encode a single query string into a normalized vector.

    Returns a flat list of floats (one 1024-dim vector).
    """
    return embed_texts([text], batch_size=batch_size)[0]


def embed_queries(texts, batch_size=16):
    """Encode a list of query/answer strings into normalized vectors.

    Returns a list of flat lists of floats. This is the single, canonical
    SentenceTransformer-based entry point for the retrieval re-ranker and any
    other caller that needs multiple vectors.
    """
    return embed_texts(texts, batch_size=batch_size)

