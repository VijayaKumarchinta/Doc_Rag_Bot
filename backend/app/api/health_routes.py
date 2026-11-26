import psycopg2

from flask import Blueprint, jsonify
from ..config import Config

health_bp = Blueprint('health', __name__, url_prefix='/api')

@health_bp.get('/health')
def health():
    db_ok = False
    schema_ok = False
    try:
        with psycopg2.connect(Config.DATABASE_URL) as conn, conn.cursor() as cur:
            cur.execute('SELECT 1')
            db_ok = True
            cur.execute("SELECT to_regclass('rag.documents') IS NOT NULL")
            schema_ok = bool(cur.fetchone()[0])
    except Exception:
        pass

    status = 200 if (db_ok and schema_ok) else 503
    return jsonify({
        'app': 'ok',
        'database': 'ok' if db_ok else 'unreachable',
        'schema': 'ok' if schema_ok else 'missing',
    }), status