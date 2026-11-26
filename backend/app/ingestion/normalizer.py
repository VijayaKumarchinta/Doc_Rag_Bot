from dataclasses import dataclass, asdict

@dataclass
class Segment:
    text: str
    metadata: dict

def _collapse_ws(text):
    return ' '.join(text.split())

def text_segment(text, *, document_id, source_file, file_type, page_number=None,
                 sheet_name=None, row_start=None, row_end=None, headers=None,
                 chunk_index=0):
    md = {
        'document_id': document_id,
        'source_file': source_file,
        'file_type': file_type,
        'chunk_index': chunk_index,
    }
    if page_number is not None:
        md['page_number'] = page_number
    if sheet_name is not None:
        md['sheet_name'] = sheet_name
    if row_start is not None:
        md['row_start'] = row_start
    if row_end is not None:
        md['row_end'] = row_end
    if headers is not None:
        md['headers'] = list(headers)
    return Segment(text=text, metadata=md)

def clean_pdf_page_text(text):
    return _collapse_ws(text or '')


def rows_to_tsv(headers, rows):
    lines = ['\t'.join(str(h) for h in headers)]
    for r in rows:
        lines.append('\t'.join('' if v is None else str(v) for v in r))
    return '\n'.join(lines)


def segment_to_dict(seg):
    return asdict(seg)