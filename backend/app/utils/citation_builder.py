from collections import defaultdict


def build_citations(retrieved):
    """Normalize retrieved excerpts into stable source citations.

    The Phase 6/7 pipeline returns citations alongside the answer so users can
    see which document excerpt supported each claim. This function deduplicates
    by (document_id, chunk_index) so repeated retrievals of the same excerpt
    still yield one citation.

    Args:
        retrieved: list of dicts as returned by ``retriever.retrieve`` or
            ``vector_store.search``, each with at least:
                content: str
                metadata: dict
                similarity: float

    Returns:
        List of citation dicts, each containing:
            document_id: str
            source_file: str (may be missing)
            file_type: str
            chunk_index: int
            label: str          -- human-readable, e.g. 'report.pdf (PDF) page 3'
            snippet: str        -- short source excerpt (first ~120 chars)
            similarity: float   -- retrieval score for this citation
    """
    if not retrieved:
        return []

    out = []
    seen = set()
    for item in retrieved:
        md = item.get("metadata") or {}
        key = (str(md.get("document_id")), int(md.get("chunk_index", -1)))
        if key in seen:
            continue
        seen.add(key)

        content = item.get("content") or ""
        snippet = _snippet(content)
        label = _citation_label(md)

        out.append({
            "document_id": str(md.get("document_id") or ""),
            "source_file": md.get("source_file") or "",
            "file_type": md.get("file_type") or "",
            "chunk_index": int(md.get("chunk_index", -1)),
            "label": label,
            "snippet": snippet,
            "similarity": float(item.get("similarity", 0.0)),
        })

    return out


def _snippet(text: str, length: int = 120) -> str:
    text = text.strip()
    if len(text) <= length:
        return text
    cut = text[:length].rsplit(" ", 1)[0]
    if not cut:
        return text[:length] + "…"
    return cut + "…"


def _citation_label(metadata: dict) -> str:
    parts = []
    if metadata.get("source_file"):
        parts.append(metadata["source_file"])
    ft = metadata.get("file_type")
    if ft:
        parts.append(f"({ft})")
    if metadata.get("page_number") is not None:
        parts.append(f"page {metadata['page_number']}")
    if metadata.get("sheet_name"):
        parts.append(f"sheet \"{metadata['sheet_name']}\"")
    if metadata.get("row_start") is not None and metadata.get("row_end") is not None:
        parts.append(f"rows {metadata['row_start']}-{metadata['row_end']}")
    if metadata.get("chunk_index") is not None:
        parts.append(f"chunk {metadata['chunk_index']}")
    return ", ".join(parts) if parts else "unknown source"
