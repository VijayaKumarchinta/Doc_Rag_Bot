import json
import os
import time
import traceback
import psycopg2

from ..config import Config
from ..rag.chunker import chunk_segments
from ..rag.embedding_model import embed_texts
from ..rag.vector_store import upsert_many, delete_by_document
from .pdf_parser import parse_pdf
from .pdf_table_parser import parse_pdf_tables
from .spreadsheet_parser import parse_csv, parse_excel
from .normalizer import segment_to_dict

def _connect():
    conn = psycopg2.connect(Config.DATABASE_URL)
    with conn.cursor() as cur:
        cur.execute('SET search_path TO rag, public')
    return conn

def _set_status(doc_id, status, error=None):
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            'UPDATE documents SET status = %s WHERE id = %s',
            (status, doc_id),
        )
    if error:
        print(f'[ingestion] {doc_id} -> {status}: {error}')

def _path_for(doc_id, filename):
    return os.path.join(Config.UPLOAD_DIR, f'{doc_id}_{filename}')

def parse_document(doc_id, filename, file_type):
    path = _path_for(doc_id, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    if file_type == 'pdf':
        segments = parse_pdf(path, document_id=doc_id, source_file=filename) \
                 + parse_pdf_tables(path, document_id=doc_id, source_file=filename)
    elif file_type == 'csv':
        segments = parse_csv(path, document_id=doc_id, source_file=filename)
    elif file_type == 'excel':
        segments = parse_excel(path, document_id=doc_id, source_file=filename)
    else:
        raise ValueError(f'Unsupported file_type: {file_type}')

    return [segment_to_dict(s) for s in segments]

def chunk_document(doc_id, filename, file_type):
    return chunk_segments(parse_document(doc_id, filename, file_type))

def ingest(doc_id, filename, file_type):
    t0 = time.time()
    try:
        _set_status(doc_id, 'processing')

        chunks = chunk_document(doc_id, filename, file_type)
        if not chunks:
            _set_status(doc_id, 'failed', error='no chunks produced')
            return {
                'status': 'failed',
                'chunk_count': 0,
                'error': 'no chunks produced',
                'timings': {},
            }

        texts = [c['text'] for c in chunks]
        t1 = time.time()
        vectors = embed_texts(texts)
        t2 = time.time()

        delete_by_document(doc_id)

        payload = [
            {'text': c['text'], 'metadata': c['metadata'], 'embedding': v}
            for c, v in zip(chunks, vectors)
        ]
        inserted = upsert_many(doc_id, payload)
        t3 = time.time()

        _set_status(doc_id, 'embedded')

        return {
            'status': 'embedded',
            'chunk_count': inserted,
            'error': None,
            'timings': {
                'parse_chunk_s': round(t1 - t0, 2),
                'embed_s': round(t2 - t1, 2),
                'upsert_s': round(t3 - t2, 2),
                'total_s': round(t3 - t0, 2),
            },
        }
    except Exception as e:
        tb = traceback.format_exc(limit=1)
        _set_status(doc_id, 'failed', error=str(e))
        print(tb)
        return {
            'status': 'failed',
            'chunk_count': 0,
            'error': str(e),
            'timings': {},
        }

def segments_as_json(doc_id, filename, file_type):
    return json.dumps(parse_document(doc_id, filename, file_type), indent=2)

def chunks_as_json(doc_id, filename, file_type):
    return json.dumps(chunk_document(doc_id, filename, file_type), indent=2)