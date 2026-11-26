from ..config import Config

SYSTEM_PROMPT = (
    "You are a precise, evidence-grounded document QA assistant."
    " You answer ONLY from the uploaded documents you were given. "
    " You are NOT a general-knowledge model: if the excerpts do not contain enough "
    " information to answer, say so plainly and do not invent facts, figures, names, "
    " numbers, or sources. "
    " For every factual claim, cite the exact source by referring to the fields in the "
    " excerpt metadata (for example `source_file`, `page_number`, `sheet_name`, "
    " `row_start`/`row_end`, `chunk_index`). Never invent document IDs, titles, or "
    " page numbers. "
    " If a question is a calculation or lookup over a spreadsheet, answer it exactly "
    " and do not round or approximate data. "
    " Answer in the same language the user asked in. "
)


def build_prompt(question, contexts, citations=None):
    if citations is None:
        citations = []

    user_parts = [f"Question: {question}"]

    if contexts:
        user_parts.append("")
        user_parts.append("Relevant excerpts (each excerpt is be followed by its source):")
        for i, ctx in enumerate(contexts, start=1):
            md = ctx.get("metadata") or {}
            content = ctx.get("content") or ""
            user_parts.append("")
            user_parts.append(f"[Excerpt {i}]")
            user_parts.append(content)
            label = _source_label(md, citations)
            if label:
                user_parts.append(f"[Source {i}: {label}]")
    else:
        user_parts.append("")
        user_parts.append(
            "No excerpts were found that match the question. If the answer cannot be "
            "derived from the provided excerpts, state that clearly and do not invent "
            "facts, figures, names, or sources. "
        )

    return "\n".join(part for part in user_parts if part), _user_prompt_summary(contexts, citations)


def _user_prompt_summary(contexts, citations):
    return {
        "excerpt_count": len(contexts),
        "citation_count": len(citations),
    }


def _source_label(metadata, citations):
    """Human-readable source label for a single excerpt, matched to its citation."""
    citation = next(
        (c for c in citations if c.get("document_id") == metadata.get("document_id")
         and c.get("chunk_index") == metadata.get("chunk_index")),
        None,
    )
    if citation and citation.get("label"):
        return citation["label"]

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


def build_prompt(question, contexts, citations=None):
    if citations is None:
        citations = []

    user_parts = [f"Question: {question}"]

    if contexts:
        user_parts.append("")
        user_parts.append("Relevant excerpts:")
        for i, ctx in enumerate(contexts, start=1):
            md = ctx.get("metadata") or {}
            user_parts.append("")
            user_parts.append(f"[Excerpt {i}]")
            user_parts.append(ctx.get("content") or "")
            user_parts.append(
                "Source: "
                + _describe_source(md, citations)
            )
    else:
        user_parts.append("")
        user_parts.append(
            "No relevant excerpts were found. If you know the answer from the "
            "provided excerpts only, answer it; otherwise tell the user you could "
            "not find relevant evidence in their documents."
        )

    return "\n".join(part for part in user_parts if part), _user_prompt_summary(contexts, citations)


def _user_prompt_summary(contexts, citations):
    return {
        "excerpt_count": len(contexts),
        "citation_count": len(citations),
    }


def _describe_source(metadata, citations):
    citation = next(
        (c for c in citations if c.get("document_id") == metadata.get("document_id")
         and c.get("chunk_index") == metadata.get("chunk_index")),
        None,
    )
    if citation and citation.get("label"):
        return citation["label"]

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
