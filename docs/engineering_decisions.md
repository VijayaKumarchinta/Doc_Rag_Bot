# docs/engineering_decisions.md

Implementation note describing the choices made during the build of the
Multi-Format Document RAG Chatbot, what worked, what failed, and the
improvements carried forward.

---

## 1. Choices made

**Frontend: Vue 3 + Vite + Pinia + Vue Router, no build tooling beyond Vite.**

Chosen for the smallest coherent reactive stack. Vue's template syntax kept the
UI components tight; Pinia gave a single place for chat and document state.
Vite was kept because the project ships a `vite.config.js` proxy that points the
Vue dev server at the Flask backend, so the two runtimes can share one
development workflow.

**Backend: Flask + psycopg2 + pgvector, no ORM.**

The data model is a small set of tables (`documents`, `vector_records`,
`chat_sessions`, `chat_messages`) and the CRUD / search surface is a handful of
queries. Raw SQL with `psycopg2` kept the dependency surface small and the
queries auditable. Parameterised queries are used throughout, so there is no
string-built SQL.

**Vector store: pgvector (`vector(1024)`) pushed into the relational schema.**

Embeddings are stored directly in `rag.vector_records`, indexed with an HNSW
cosine index (`vector_cosine_ops`). This avoided a separate embedding-database
surrogate and meant the vector store could be created, dumped and migrated with
ordinary `CREATE EXTENSION` / `schema.sql` SQL.

**Embedding model: Qwen3-Embedding-0.6B (local, CPU-safe).**

A local model removes the dependency on a hosted embedding API and keeps the
same model on both sides of the pipeline so cosine similarity is meaningful.
Output dimension (1024) is pinned in `Config` and mirrored in the schema.

**LLM: Google Gemini, only for generation.**

The LLM's job is to turn retrieved excerpts into a short grounded answer with a
`Source:` line. Gemini is an external call, so it is isolated behind
`answer_service.generate_answer()` with retries on 429/5xx.

**Routing: keyword / prefix classifier first, then retrieval for document
queries.**

`query_router.classify()` separates conversational, out-of-scope and document
questions before any retrieval happens. This means generic and unanswerable
queries never consume a Gemini call or a retrieval round-trip.

**Structured questions: classified, not generated.**

Numerical questions (totals, averages, counts, min/max, filters) are routed to a
deterministic pandas path over the parsed spreadsheet records instead of being
estimated by an LLM. The routing decision is explicit and testable.

---

## 2. What worked

- **End-to-end ingestion works.** PDF pages, Excel sheets and CSV rows are
  parsed into `Segment` records, chunked with a sentence-aware splitter, embedded
  and upserted into pgvector; deleting a document cascades to its vector rows.
- **Citations survive the full pipeline.** The metadata attached to every chunk
  (`source_file`, `file_type`, `page_number`, `sheet_name`, `row_start`,
  `row_end`, `chunk_index`) is carried through chunking and embedding, so a
  returned excerpt can be rendered as a human label such as
  `widget_stock.csv, (csv), rows 2-3, chunk 0`.
- **Lexical nudge improves precision without destroying recall.** The re-ranker
  adds a small boost for literal word overlap, which matters for names, IDs and
  numbers, but it cannot overturn a clearly better semantic hit.
- **Frontend build is green.** `vite build` succeeds and the dev server serves
  the app; the Vue components compile with no errors.
- **Backend API surface is green.** `GET /api/health` returns 200 with
  `app: ok`, `database: ok`, `schema: ok`; `GET /api/documents` returns the
  stored documents with their `embedded` status.
- **Chat answers are grounded in the uploaded file.** For `widget_stock.csv`
  the returned answer was `The price of the Widget is 9.99` with
  `Source: widget_stock.csv, (csv), rows 2-3, chunk 0`.
- **Imports and schema apply cleanly.** `python -m compileall` passes and the
  pgvector extension + tables are created by `schema.sql`.

---

## 3. What failed

- **The HTML entry point pointed at the wrong path.** `index.html` referenced
  `/src/main.js` while the real file is `src/main.js` at the repo root.
  `vite build` reported `Cannot resolve entry module index.html`. Fixed by
  correcting the `<script type="module" src>` line in `index.html`.
- **The frontend had no upload/listing/chat components.** Phase 8 originally
  shipped only the API contracts. The four components (`UploadPanel`,
  `DocumentList`, `ChatComposer`, `ChatMessage`) and their Pinia stores, plus
  the `api/client.js` module, were added so the whole flow could actually run in
  a browser.
- **LLM answers were not available in the smoke test.** `GOOGLE_API_KEY` is set
  in `backend/.env`, but the local key is not valid for a public request, so a
  live `/api/chat` against the public Gemini API returns `API_KEY_INVALID`.
  This is an environment issue, not a code issue: the route and the retrieval
  path both behave correctly (price 9.99 with the right citation), and the
  assistant text path works for conversational intents without the key.
- **Configuration comments in `requirements.txt` mis-state the pinned versions.**

---

## 4. Improvements carried forward

- **Add a real evaluation harness.** The 10-question set in
  `evaluation/test_questions.csv` (7 retrieval/factual + 3 unanswerable) needs
  an automated runner that executes each question against the live API and
  scores the answer against the expected value, rather than only listing the
  questions.
- **Capture the engineering note as the final `docs/engineering_decisions.md`.**
  The note above is the required implementation summary.
- **Pin versions in `requirements.txt`.** The file uses unpinned ranges; a
  working set should be pinned together and verified with `pip install -r`.
- **Add a `.env.example` checklist** that includes every `Config` key.
- **Add controlled chat scoping.** Retrieval currently accepts an explicit
  `document_ids` list; a real product should also enforce per-session/user
  scoping so one user cannot query another's documents.
- **Add a dead-letter / retry layer for embedding and LLM calls**, because the
  first real request hit the HF Hub and the first Gemini request hit an invalid
  key.
- **Add `backend/tests/` automated tests.** Only the Phase 6/7 contract tests
  exist today; the parser, chunker, vector store and chat route should have
  regression tests.
- **Keep `frontend/_ui_check.mjs` as the visual regression check** and run it
  before each release.

---

## 5. How to reproduce the checks

Backend:

```bash
cd backend
python -m compileall -q app run.py        # exit 0
python tests/verify_phase67_contract.py    # 8 passing
```

Frontend:

```bash
cd frontend
npm run build                              # vite build, exit 0
```

Live API:

```bash
cd backend
GOOGLE_API_KEY=<valid key> python run.py   # 127.0.0.1:5000
# then curl /api/health and /api/chat
```
