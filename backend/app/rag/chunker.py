from llama_index.core.node_parser import SentenceSplitter
from ..config import Config

def _build_splitter():
    return SentenceSplitter(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP,
    )

def _chunk_one(splitter, segment):
    text = segment.get('text') or ''
    md = dict(segment.get('metadata') or {})
    parts = splitter.split_text(text)
    chunks = []
    for i, part in enumerate(parts):
        if not part.strip():
            continue
        chunk_md = dict(md)
        chunk_md['chunk_part'] = i
        chunks.append({'text': part, 'metadata': chunk_md})
    return chunks

def chunk_segments(segments):
    splitter = _build_splitter()
    out = []
    for seg in segments:
        out.extend(_chunk_one(splitter, seg))
    return out