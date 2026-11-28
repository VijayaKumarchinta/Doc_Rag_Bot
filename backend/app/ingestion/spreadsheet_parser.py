import csv

import pandas as pd

from .normalizer import text_segment, rows_to_tsv

WINDOW = 50

# Real-world exports are rarely plain UTF-8 comma-separated: Excel on Windows
# writes cp1252 and often uses ';' as the separator. Try the common encodings in
# order and let pandas sniff the delimiter.
CSV_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")


def _emit_frame(df, *, document_id, source_file, file_type, sheet_name=None):
    segments = []
    if df.empty:
        return segments
    headers = [str(c) for c in df.columns]
    total = len(df)
    for start in range(0, total, WINDOW):
        window = df.iloc[start:start + WINDOW]
        row_start = start + 2
        row_end = start + len(window) + 1
        tsv = rows_to_tsv(headers, window.itertuples(index=False, name=None))
        if not tsv.strip():
            continue
        segments.append(text_segment(
            tsv,
            document_id=document_id,
            source_file=source_file,
            file_type=file_type,
            sheet_name=sheet_name,
            row_start=row_start,
            row_end=row_end,
            headers=headers,
            chunk_index=start // WINDOW,
        ))
    return segments


def _read_csv(path):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        if not handle.read().strip():
            raise ValueError("The CSV file has no data")

    last_error = None
    for encoding in CSV_ENCODINGS:
        try:
            return pd.read_csv(path, encoding=encoding, sep=None, engine="python")
        except (UnicodeDecodeError, pd.errors.ParserError, csv.Error) as error:
            last_error = error
    raise ValueError(f"Could not read the CSV file: {last_error}")


def parse_csv(path, *, document_id, source_file):
    df = _read_csv(path)
    return _emit_frame(df, document_id=document_id, source_file=source_file, file_type='csv')


def parse_excel(path, *, document_id, source_file):
    sheets = pd.read_excel(path, sheet_name=None, engine='openpyxl')
    out = []
    for name, df in sheets.items():
        out.extend(_emit_frame(
            df,
            document_id=document_id,
            source_file=source_file,
            file_type='excel',
            sheet_name=name,
        ))
    return out
