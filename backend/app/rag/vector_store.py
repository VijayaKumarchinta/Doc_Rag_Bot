import json
import psycopg2
import psycopg2.extras

from pgvector import Vector
from pgvector.psycopg2 import register_vector
from ..config import Config

def _connect():
    conn = psycopg2.connect(Config.DATABASE_URL)
    with conn.cursor() as cur:
        cur.execute('SET search_path TO rag, public')
    register_vector(conn)
    return conn

def delete_by_document(document_id):
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            'DELETE FROM vector_records WHERE document_id = %s',
            (document_id,),
        )
        return cur.rowcount

def upsert_many(document_id, chunks_with_vectors):
    if not chunks_with_vectors:
        return 0
    rows = [
        (
            document_id,
            c['text'],
            c['embedding'],
            json.dumps(c['metadata']),
        )
        for c in chunks_with_vectors
    ]
    with _connect() as conn, conn.cursor() as cur:
        psycopg2.extras.execute_batch(
            cur,
            'INSERT INTO vector_records (document_id, content, embedding, metadata) '
            'VALUES (%s, %s, %s, %s::jsonb)',
            rows,
            page_size=100,
        )
    return len(rows)

def search(query_vector, top_k=None, document_ids=None):
    if top_k is None:
        top_k = Config.TOP_K

    qv = Vector(query_vector)
    sql = [
        'SELECT content, metadata, 1 - (embedding <=> %s) AS similarity',
        'FROM vector_records',
    ]
    params = [qv]
    if document_ids:
        sql.append('WHERE document_id = ANY(%s::uuid[])')
        params.append(list(document_ids))
    sql.append('ORDER BY embedding <=> %s')
    params.append(qv)
    sql.append('LIMIT %s')
    params.append(top_k)

    with _connect() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(' '.join(sql), params)
        return [
            {
                'content': r['content'],
                'metadata': r['metadata'],
                'similarity': float(r['similarity']),
            }
            for r in cur.fetchall()
        ]

def count():
    with _connect() as conn, conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM vector_records')
        return int(cur.fetchone()[0])

def count_for_document(document_id):
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            'SELECT COUNT(*) FROM vector_records WHERE document_id = %s',
            (document_id,),
        )
        return int(cur.fetchone()[0])