import os
from dotenv import load_dotenv

load_dotenv()

def _int_env(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

    DATABASE_URL = os.getenv('DATABASE_URL')

    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.8-flash')

    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'Qwen/Qwen3-Embedding-0.6B')
    EMBEDDING_DIMENSION = _int_env('EMBEDDING_DIMENSION', 1024)

    UPLOAD_DIR = os.getenv('UPLOAD_DIR', 'data/uploads')
    MAX_CONTENT_LENGTH = _int_env('MAX_CONTENT_LENGTH', 20 * 1024 * 1024)

    CHUNK_SIZE = _int_env('CHUNK_SIZE', 512)
    CHUNK_OVERLAP = _int_env('CHUNK_OVERLAP', 50)
    TOP_K = _int_env('TOP_K', 5)