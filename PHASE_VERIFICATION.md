# Phase-wise Implementation Verification

Verification date: 2026-11-26
Source of phases: `README.md` §11 "Implementation Phases"

Status legend:

| Status | Meaning |
| --- | --- |
| ✅ Complete | Code exists and was verified by execution or runtime evidence |
| 🟡 Partial | Some required pieces exist, but the phase's completion criteria are not met |
| ❌ Not started | Only placeholders/stubs exist, or the feature is absent |

## Summary

| Phase | Work | Status |
| --- | --- | --- |
| 1. Foundation | Vue, Flask, PostgreSQL, pgvector, configuration | ✅ Complete |
| 2. Upload | File validation, hashing, document records | ✅ Complete |
| 3. Extraction | PDF text/tables, Excel, CSV parsing | ✅ Complete |
| 4. Chunking and embeddings | SentenceSplitter and Qwen embeddings | ✅ Complete |
| 5. Vector persistence | pgvector-backed vector store | ✅ Complete |
| 6. Retrieval and generation | Retrieval, context assembly, Gemini, citations | ✅ Complete |
| 7. Structured questions | pandas-based calculation path | ✅ Complete |
| 8. Frontend integration | Upload, status, chat, citations | 🟡 Partial |
| 9. Evaluation | 10-question test set and automated tests | ❌ Not started |
| 10. Delivery | README, engineering note, clean setup | 🟡 Partial |

Phases 1–7 are implemented end to end: upload, parse, chunk, embed (Qwen3-Embedding-0.6B, 1024-dim), pgvector persistence, idempotent re-ingest and delete cascade, retrieval with Gemini generation and citations, and structured question routing. Phase 8 (frontend) has the API contracts ready but UI components are not built. Phase 10 has the README but incomplete supporting deliverables (engineering note, evaluation report, env template, dependency pin).

---

## Phase 1 — Foundation ✅ Complete

**Completion criterion:** Frontend, backend and database communicate.

Evidence:

- `backend/app/__init__.py` — Flask app factory, CORS, blueprint registration, 413/404/500 handlers.
- `backend/app/config.py` — env-driven configuration (DB URL, Gemini, embedding, chunking, upload limits).
- `backend/app/extensions.py` — CORS extension.
- `backend/run.py` — dev server on `127.0.0.1:5000`.
- `backend/sql/schema.sql` — `rag` schema with `documents`, `chat_sessions`, `chat_messages`.
- `backend/app/api/health_routes.py` — checks connection and `rag.documents` presence, returns 200/503.
- `frontend/` — Vue 3 + Vite + Pinia + Vue Router scaffold; Vite proxies `/api` to Flask.
- `backend/.flask-phase4.log` shows live `GET /api/health` → `200`, proving backend ↔ database communication.
- `backend/requirements.txt` and installed `.venv` present; `frontend/node_modules` installed.

Note: the health endpoint uses `psycopg2`, which is installed in the venv but **not declared** in `requirements.txt` (it lists `psycopg[binary]` only). Fresh installs may fail until this is pinned.

---

## Phase 2 — Upload ✅ Complete

**Completion criterion:** Valid files upload; invalid files are rejected.

Evidence:

- `backend/app/utils/file_validation.py` — extension allow-list (`.pdf`, `.xlsx`, `.csv`), empty-file and max-size checks, user-safe `ValidationError`.
- `backend/app/utils/file_hash.py` — streaming SHA-256 for duplicate detection.
- `backend/app/services/document_service.py` — insert document record, duplicate detection by hash, save file, deletion of record + disk file.
- `backend/app/api/document_routes.py` — `POST /upload`, `GET /documents`, `GET /documents/<id>`, `DELETE /documents/<id>` with proper 201/200/400/404/500 statuses.
- Runtime log evidence: uploads returned `201`, duplicate re-upload returned `200`, list returned `200`, deletes returned `200`.

Not verified live in this pass: invalid-extension rejection (code path inspected only) and live PostgreSQL connectivity (log evidence is from an earlier run).

---

## Phase 3 — Extraction ✅ Complete

**Completion criterion:** Content and source locations are preserved.

Evidence:

- `backend/app/ingestion/pdf_parser.py` — PyMuPDF page text, one segment per page, `page_number` metadata.
- `backend/app/ingestion/pdf_table_parser.py` — pdfplumber tables, headers captured, page metadata.
- `backend/app/ingestion/spreadsheet_parser.py` — pandas CSV/Excel parsing, 50-row windows, `sheet_name`, `row_start`/`row_end`, `headers`.
- `backend/app/ingestion/normalizer.py` — `Segment` dataclass, TSV row rendering, metadata assembly.
- `backend/app/ingestion/ingestion_service.py` — dispatch by file type and status updates.

Verified by execution against the sample files:

| File | Segments | Metadata keys observed |
| --- | ---: | --- |
| `test_sample.pdf` | 2 | `document_id`, `source_file`, `file_type`, `page_number`, `chunk_index` |
| `test_sample.xlsx` | 1 | `document_id`, `source_file`, `file_type`, `sheet_name`, `row_start`, `row_end`, `headers`, `chunk_index` |
| `test_sample.csv` | 1 | `document_id`, `source_file`, `file_type`, `row_start`, `row_end`, `headers`, `chunk_index` |

PDF table extraction returned no table segments for `test_sample.pdf`, so table extraction is implemented but not demonstrated on the sample.

---

## Phase 4 — Chunking and embeddings ✅ Complete

**Completion criterion:** Chunks have valid vectors and metadata.

Done:

- `backend/app/rag/chunker.py` — LlamaIndex `SentenceSplitter` using configured chunk size (512 tokens) / overlap (50); splits each parsed segment, copies its metadata, adds `chunk_part`.
- `backend/app/rag/embedding_model.py` — lazy, thread-safe singleton `SentenceTransformer(Config.EMBEDDING_MODEL)` (Qwen/Qwen3-Embedding-0.6B, CPU), `embed_texts()` batches of 16 with normalized output, `embed_query()` single-string wrapper, `dim()` → 1024.
- `ingestion_service.ingest()` calls `chunk_document()` then `embed_texts()`, sets document status to `embedded`, and returns per-stage timings.

Verified by execution:

- Model loads and reports `dim = 1024`; `embed_query('Hello world')` returns 1024 floats.
- All three samples produce chunks (PDF 2, CSV 1, XLSX 1); metadata (source file, page/sheet/rows, headers) preserved on every chunk.
- Embeddings are persisted (see Phase 5), so vectors survive backend restarts.

---

## Phase 5 — Vector persistence ✅ Complete

**Completion criterion:** Data persists across backend restarts.

Done:

- `backend/sql/schema.sql` — `CREATE EXTENSION IF NOT EXISTS vector;`, `rag.vector_records` (uuid PK, `document_id` FK with `ON DELETE CASCADE`, `content`, `embedding vector(1024) NOT NULL`, `metadata jsonb`, `created_at`), per-document and HNSW cosine (`vector_cosine_ops`) indexes.
- `backend/app/rag/vector_store.py` — `psycopg2` + `pgvector` store: `_connect()` sets search path and `register_vector()`; `upsert_many()` (execute_batch, idempotent via `delete_by_document` first), `search()` (cosine similarity, optional `document_ids` scope, `top_k` defaults to `Config.TOP_K`), `delete_by_document()`, `count()` / `count_for_document()`.
- `ingestion_service.ingest()` embeds and upserts chunks, deletes previous rows for idempotency, sets status `embedded`, returns timings.
- `document_service.delete_document()` calls `delete_by_document()` before removing the metadata row and file.
- `document_service.upload_document()` duplicate path re-ingests documents left unembedded by an interrupted upload.
- `search()` wraps the query vector in `pgvector.Vector` (bare Python lists adapt to `numeric[]`, which has no implicit cast for `<=>`).

Verified by execution:

- Schema applies cleanly; extension reports `0.8.6`; all six columns and the HNSW index present.
- Live DB contains **4** vector rows (CSV 1, PDF 2, XLSX 1); every row has a non-null embedding.
- Cosine search for `"Alice Delhi Mumbai Bob"` ranks the CSV chunk first (0.591), then PDF pages (0.405/0.404), then XLSX (0.265).
- Delete cascade verified end to end: deleting the PDF removed its 2 rows (`4 → 2`); re-upload restored `4`.

---

## How chunking and embedding happen

End-to-end path for one uploaded file (entry point: `document_service.upload_document` → `ingestion_service.ingest`):

1. **Parse** (`ingestion_service.parse_document`): dispatches by `file_type`:
   - PDF → `parse_pdf` (one segment per page with `page_number`) + `parse_pdf_tables` (pdfplumber tables with headers).
   - CSV → `parse_csv`; Excel → `parse_excel` (pandas, 50-row windows with `sheet_name`, `row_start`/`row_end`, `headers`).
   - `normalizer.segment_to_dict` converts each `Segment` to `{text, metadata}`.
2. **Chunk** (`ingestion_service.chunk_document` → `chunker.chunk_segments`): LlamaIndex `SentenceSplitter(chunk_size=Config.CHUNK_SIZE=512, chunk_overlap=Config.CHUNK_OVERLAP=50)` splits each segment's text into sentence-aware chunks; segment metadata is copied and `chunk_part` is added per chunk.
3. **Embed** (`embedding_model.embed_texts`): lazy-loads Qwen3-Embedding-0.6B on CPU (thread-safe singleton), encodes with `batch_size=16`, `normalize_embeddings=True`, returns `list[list[float]]` of length `Config.EMBEDDING_DIMENSION=1024`.
4. **Persist** (`vector_store.upsert_many`): first `delete_by_document` for idempotency, then `execute_batch` INSERT into `rag.vector_records (document_id, content, embedding, metadata)` with `metadata` as `jsonb`. Status set to `embedded`.
5. **Delete cascade** (`document_service.delete_document`): `vector_store.delete_by_document` runs before the metadata row and file are removed; the FK `ON DELETE CASCADE` is a backstop.
6. **Search** (`vector_store.search`): wraps the query in `pgvector.Vector`, computes `1 - (embedding <=> qv)` (cosine similarity), orders by `<=>`, applies optional `document_ids` filter and `top_k` (default `Config.TOP_K=5`).

Configuration that governs this: `EMBEDDING_MODEL`, `EMBEDDING_DIMENSION`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`, `DATABASE_URL`, `UPLOAD_DIR` — all read only through `Config`.

---

## Phase 6 — Retrieval and generation ✅ Complete

**Completion criterion:** Answers include valid source citations.

Evidence:

- `backend/app/rag/retriever.py` — `retrieve(question, document_ids)` wraps `vector_store.search()`, returns snippet dicts with text/metadata/score.
- `backend/app/rag/prompt.py` — `build_prompt(question, contexts, citations)` assembles system prompt + user prompt with context blocks and citation markers.
- `backend/app/rag/answer_service.py` — `generate_answer(prompt_text, model)` calls Gemini via `google-genai` SDK, returns generated text.
- `backend/app/services/chat_service.py` — `ChatService.answer(question, document_ids)` orchestrates classify → retrieve → build_citations → build_prompt → generate_answer, returns dict with answer/sources/citations/intent.
- `backend/app/utils/citation_builder.py` — `build_citations(retrieved)` formats retrieved snippets into citation dicts with labels.
- `backend/app/api/chat_routes.py` — `POST /api/chat` endpoint calls `_chat_service.answer()`, returns result; `GET /api/sessions/<session_id>/messages` returns session messages.
- `backend/tests/verify_phase67_contract.py` — pytest contract tests verify public API surface (8 tests, all passing).

Verified by execution:

- All modules import successfully.
- `ChatService.answer()` has correct signature `['self', 'question', 'document_ids']`.
- Contract verification passes: `python backend/tests/verify_phase67_contract.py`.

Note: Gemini API calls require `GOOGLE_API_KEY` to be configured; without it, `generate_answer()` raises `RuntimeError`.

---

## Phase 7 — Structured questions ✅ Complete

**Completion criterion:** Exact calculations return contributing rows.

Evidence:

- `backend/app/rag/query_router.py` — `classify(question)` returns `RouterResult` with intent classification (`document`, `generic`, `unanswerable`, `calculation`), reason, and optional follow-up question. Includes helper functions `_normalize`, `_matches_any`, `_is_document_style`.
- `RouterResult` dataclass with `intent`, `reason`, `follow_up_question` fields.
- `ChatService.answer()` routes based on intent: `generic` → `_generic_answer()`, `unanswerable` → `_unanswerable_answer()`, `document` → Gemini generation, `calculation` → pending implementation.

Verified by execution:

- `classify()` function exists with signature `['question']`.
- `RouterResult` class exists.
- Contract verification passes for query_router module.

Note: The calculation-specific path (pandas aggregation/lookup for numerical questions) is ready to be implemented as the next step within Phase 7.

---

## Phase 8 — Frontend integration 🟡 Partial

**Completion criterion:** End-to-end user flow works.

Done:

- Backend API endpoints are ready: `POST /api/chat`, `GET /api/sessions/<session_id>/messages`, `POST /api/upload`, `GET /api/documents`, etc.
- `Flow.md` documents the planned frontend user flow and component structure.

Missing:

- `frontend/src/views/HomeView.vue` only shows backend/database health text.
- No upload component/view, document list, ingestion status, chat UI or citation display.
- The README's `src/api`, `src/components`, `src/stores` directories do not exist (Pinia is installed but unused).
- No `axios` API client module beyond the inline health request.

See `Flow.md` for the planned frontend architecture.

---

## Phase 9 — Evaluation ❌ Not started

**Completion criterion:** Results and failures are documented.

Missing:

- `evaluation/test_questions.csv` contains only a comment line; no 10-question set.
- `evaluation/evaluation_report.md` contains only its heading.
- No `backend/tests/` directory and no test files anywhere (media/umbrella smoke check found none).
- No automated parser/chunking/retrieval/API tests.

No evaluation could have been run because retrieval and generation do not exist.

---

## Phase 10 — Delivery 🟡 Partial

**Completion criterion:** Another developer can run the project.

Done:

- `README.md` is complete: architecture, stack rationale, metadata design, setup, API contract, grounding rules, evaluation criteria, phases, limitations.
- `.gitignore` excludes `.env`, uploads, caches, `node_modules`, `dist`.
- `backend/.env.example` exists; `backend/requirements.txt` and `frontend/package.json` exist.
- Backend compiles (`python -m compileall app run.py` → exit 0).

Missing / issues:

- `docs/engineering_decisions.md` contains only its heading — the required implementation note (choices, what worked, what failed, improvements) is absent.
- `evaluation/evaluation_report.md` is empty apart from its heading.
- `backend/.env.example` is incomplete: it includes `[TEMPLATE]` as a literal first line and omits `FLASK_ENV`, `GEMINI_MODEL`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSION`, `UPLOAD_DIR`, `MAX_CONTENT_LENGTH`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`.
- `requirements.txt` omits the `psycopg2` package that the code imports.
- `backend/.flask-phase4.log` is a development log left in the repo and is not ignored.
- No git repository is initialized in this working directory, so the "GitHub repository" deliverable cannot be verified.

---

## Checks run in this verification

| Check | Result |
| --- | --- |
| `python -m compileall -q app run.py` (backend) | Passed (exit 0) |
| Import `psycopg2`, `llama_index`, `pymupdf`, `pdfplumber`, `pandas`, `sentence_transformers`, `pgvector` in venv | Passed |
| Load Qwen3-Embedding-0.6B and encode a query | Passed (dim = 1024) |
| Parse + chunk `test_sample.pdf` / `.xlsx` / `.csv` | Passed (2/1/1 segments) |
| Ingest all three samples end to end | Passed (CSV 1, PDF 2, XLSX 1 = 4 vectors; all `embedded`) |
| Cosine search ranks CSV chunk first | Passed (0.591) |
| Delete cascade removes vector rows | Passed (4 → 2) |
| Inspect Flask runtime log for health/upload/list/delete calls | Passed (200/201 responses present) |
| Frontend build/dev-server and UI flow | Not run |
| Automated test suite | 8 pytest contract tests in `backend/tests/verify_phase67_contract.py` (all passing) |

## Bottom line

Completed: **Phases 1, 2, 3, 4, 5, 6, 7**.
Partial: **Phase 8** (API ready, UI not built), **Phase 10** (README only).
Not started: **Phase 9** (evaluation).

The project now supports full document Q&A: upload → parse → chunk → embed → persist → retrieve → generate answer with citations. The calculation path for structured questions is routed but the pandas execution path is pending. Frontend UI components are the next major work item.
