import os
import uuid
import psycopg2
import psycopg2.extras

from ..config import Config
from ..utils.file_validation import validate_upload
from ..utils.file_hash import sha256_of_stream

def _connect():
    conn = psycopg2.connect(Config.DATABASE_URL)
    with conn.cursor() as cur:
        cur.execute('SET search_path TO rag, public')
    return conn

def _row_to_dict(row):
    return {
        'id': str(row['id']),
        'filename': row['filename'],
        'file_hash': row['file_hash'],
        'file_type': row['file_type'],
        'status': row['status'],
        'uploaded_at': row['uploaded_at'].isoformat(),
    }

def list_documents():
    with _connect() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            'SELECT id, filename, file_hash, file_type, status, uploaded_at '
            'FROM documents ORDER BY uploaded_at DESC'
        )
        return [_row_to_dict(r) for r in cur.fetchall()]

def get_document(doc_id):
    try:
        uuid.UUID(doc_id)
    except (ValueError, TypeError):
        return None
    with _connect() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            'SELECT id, filename, file_hash, file_type, status, uploaded_at '
            'FROM documents WHERE id = %s',
            (doc_id,),
        )
        row = cur.fetchone()
        return _row_to_dict(row) if row else None

def delete_document(doc_id):
    doc = get_document(doc_id)
    if not doc:
        return False
    from ..rag.vector_store import delete_by_document
    delete_by_document(doc_id)
    disk_path = os.path.join(Config.UPLOAD_DIR, f"{doc_id}_{doc['filename']}")
    with _connect() as conn, conn.cursor() as cur:
        cur.execute('DELETE FROM documents WHERE id = %s', (doc_id,))
    if os.path.exists(disk_path):
        try:
            os.remove(disk_path)
        except OSError:
            pass
    return True

def upload_document(file_storage, filename, mimetype):
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)

    ext = validate_upload(
        filename=filename,
        content_length=size,
        mimetype=mimetype,
        max_bytes=Config.MAX_CONTENT_LENGTH,
    )
    file_type = {'.pdf': 'pdf', '.xlsx': 'excel', '.csv': 'csv'}[ext]
    file_hash = sha256_of_stream(file_storage)

    with _connect() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            'SELECT id, filename, file_hash, file_type, status, uploaded_at '
            'FROM documents WHERE file_hash = %s',
            (file_hash,),
        )
        existing = cur.fetchone()
    if existing:
        doc = _row_to_dict(existing)
        # Re-run ingestion for documents left unembedded by an interrupted
        # upload (status 'pending'/'processing'/'failed'); otherwise the
        # duplicate short-circuit would keep them without vectors forever.
        if doc['status'] != 'embedded':
            from ..ingestion.ingestion_service import ingest
            ingestion_result = ingest(doc['id'], doc['filename'], doc['file_type'])
            doc['status'] = ingestion_result['status']
            return {
                'duplicate': True,
                'document': doc,
                'ingestion': ingestion_result,
            }
        return {'duplicate': True, 'document': doc}

    os.makedirs(Config.UPLOAD_DIR, exist_ok=True)

    with _connect() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            'INSERT INTO documents (filename, file_hash, file_type, status) '
            'VALUES (%s, %s, %s, %s) '
            'RETURNING id, filename, file_hash, file_type, status, uploaded_at',
            (filename, file_hash, file_type, 'pending'),
        )
        row = cur.fetchone()

    disk_path = os.path.join(Config.UPLOAD_DIR, f"{str(row['id'])}_{filename}")
    file_storage.save(disk_path)

    from ..ingestion.ingestion_service import ingest
    ingestion_result = ingest(str(row['id']), filename, file_type)

    doc = _row_to_dict(row)
    doc['status'] = ingestion_result['status']
    return {
        'duplicate': False,
        'document': doc,
        'ingestion': ingestion_result,
    }