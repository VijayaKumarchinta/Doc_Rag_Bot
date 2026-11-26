import pdfplumber

from .normalizer import text_segment, rows_to_tsv

def parse_pdf_tables(path, *, document_id, source_file):
    segments = []
    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            try:
                tables = page.extract_tables() or []
            except Exception:
                tables = []
            for t_idx, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue
                header = table[0]
                body = table[1:]
                tsv = rows_to_tsv(header, body)
                if not tsv.strip():
                    continue
                segments.append(text_segment(
                    tsv,
                    document_id=document_id,
                    source_file=source_file,
                    file_type='pdf',
                    page_number=page_num,
                    chunk_index=t_idx,
                    headers=header,
                ))
    return segments