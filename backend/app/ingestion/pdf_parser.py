import pymupdf  

from .normalizer import text_segment, clean_pdf_page_text

def parse_pdf(path, *, document_id, source_file):
    segments = []
    with pymupdf.open(path) as doc:
        for i, page in enumerate(doc, start=1):
            text = clean_pdf_page_text(page.get_text('text'))
            if not text:
                continue
            segments.append(text_segment(
                text,
                document_id=document_id,
                source_file=source_file,
                file_type='pdf',
                page_number=i,
                chunk_index=i - 1,
            ))
    return segments