SYSTEM_PROMPT = (
    "You are a document question-answering assistant. You answer ONLY using the "
    "excerpts provided from the user's uploaded files.\n"
    "Rules:\n"
    "1. Use only the provided excerpts. Never use outside knowledge, and never "
    "invent facts, numbers, names, dates or sources.\n"
    "2. If the excerpts do not contain the answer, reply that the answer was not "
    "found in the uploaded files. Do not guess.\n"
    "3. Answer the question directly and briefly. For numbers, copy them exactly "
    "as they appear; do not round or estimate.\n"
    "4. Finish with a 'Source:' line naming the file and the page, sheet or row "
    "range the answer came from, using the source labels given with the excerpts."
)

# Splits the assembled prompt into system instruction and user turn. Keeping it
# explicit avoids guessing where the instruction text ends.
PROMPT_SEPARATOR = "\n\n---\n\n"


def build_prompt(question, contexts, citations=None):
    """Return (prompt_text, summary) for the given question and excerpts."""
    if citations is None:
        citations = []

    user_parts = [f"Question: {question}"]

    if contexts:
        user_parts.append("")
        user_parts.append("Excerpts from the uploaded files:")
        for i, ctx in enumerate(contexts, start=1):
            metadata = ctx.get("metadata") or {}
            user_parts.append("")
            user_parts.append(f"[Excerpt {i}]")
            user_parts.append(ctx.get("content") or "")
            user_parts.append(f"[Source {i}: {_source_label(metadata, citations)}]")
    else:
        user_parts.append("")
        user_parts.append(
            "No excerpts matched the question. Tell the user the answer was not "
            "found in the uploaded files."
        )

    user_prompt = "\n".join(part for part in user_parts if part)
    prompt_text = f"{SYSTEM_PROMPT}{PROMPT_SEPARATOR}{user_prompt}"
    return prompt_text, _user_prompt_summary(contexts, citations)


def _user_prompt_summary(contexts, citations):
    return {
        "excerpt_count": len(contexts),
        "citation_count": len(citations),
    }


def _source_label(metadata, citations):
    """Human-readable source label for one excerpt (file + page/sheet/rows)."""
    citation = next(
        (
            c
            for c in citations
            if c.get("document_id") == metadata.get("document_id")
            and c.get("chunk_index") == metadata.get("chunk_index")
        ),
        None,
    )
    if citation and citation.get("label"):
        return citation["label"]

    parts = []
    if metadata.get("source_file"):
        parts.append(metadata["source_file"])
    file_type = metadata.get("file_type")
    if file_type:
        parts.append(f"({file_type})")
    if metadata.get("page_number") is not None:
        parts.append(f"page {metadata['page_number']}")
    if metadata.get("sheet_name"):
        parts.append(f"sheet \"{metadata['sheet_name']}\"")
    if metadata.get("row_start") is not None and metadata.get("row_end") is not None:
        parts.append(f"rows {metadata['row_start']}-{metadata['row_end']}")
    if metadata.get("chunk_index") is not None:
        parts.append(f"chunk {metadata['chunk_index']}")
    return ", ".join(parts) if parts else "unknown source"
