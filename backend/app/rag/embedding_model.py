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
    return int(_get_model().get_sentence_embedding_dimension())

def embed_texts(texts):
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(
        texts,
        batch_size=16,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return [v.tolist() for v in vectors]

def embed_query(text):
    return embed_texts([text])[0]