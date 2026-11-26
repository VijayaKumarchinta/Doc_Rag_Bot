# Multi-Format Document RAG Chatbot

A document-based Retrieval-Augmented Generation (RAG) application that allows users to upload PDF, Excel (`.xlsx`) and CSV files, then ask questions about their contents.

The application extracts and normalizes document content, preserves source locations, creates chunks and embeddings, and stores them in **PostgreSQL with pgvector**. When a user asks a question, the system retrieves relevant evidence and uses Google Gemini to generate a human-readable, evidence-grounded answer with source citations.

---

## 1. Project Overview

The application contains two primary RAG pipelines.

### Pipeline 1: Document ingestion

```text
Upload document
      |
      v
File validation
      |
      v
Document parsing
(PDF / Excel / CSV)
      |
      v
Content normalization
+ source metadata
      |
      v
LlamaIndex SentenceSplitter
      |
      v
Qwen3-Embedding-0.6B
      |
      v
PostgreSQL + pgvector
```

Supported input formats:

- PDF (`.pdf`)
- Excel (`.xlsx`)
- CSV (`.csv`)

### Pipeline 2: Retrieval and generation

```text
User question
      |
      v
Query processing
      |
      v
Qwen3 query embedding
      |
      v
LlamaIndex retriever
      |
      v
PostgreSQL + pgvector search
      |
      v
Relevant chunks + source metadata
      |
      v
Evidence/context assembly
      |
      v
Google Gemini
      |
      v
Grounded answer + citations
```

**Structured-data path:** numerical questions such as totals, averages, counts, minimums, maximums, filters and groupings must be handled with deterministic pandas operations over the relevant spreadsheet records. Vector similarity and LLM arithmetic are not substitutes for exact calculations. The query service should route these questions to a controlled tabular operation and return the contributing source rows.

---

## 2. Technology Stack

| Layer | Technology |
| --- | --- | --- |
| Frontend | Vue.js 3 |
| Build tool | Vite |
| Backend | Python + Flask |
| PDF text extraction | PyMuPDF |
| PDF table extraction | pdfplumber |
| Excel processing | pandas + openpyxl |
| CSV processing | pandas |
| Chunking | LlamaIndex SentenceSplitter |
| Embedding model | Qwen/Qwen3-Embedding-0.6B |(cosine similarity search - get the information based on meaning rather than keywords)
| Vector database | PostgreSQL + pgvector |
| LLM | Google Gemini (gemini-3.8-flash) |
| RAG orchestration | LlamaIndex |

---

## 3. Technology Research and Selection

### Research and select the tools, libraries, embedding model, vector store and LLM

After reviewing the available technologies and their suitability for this document-based RAG application, the following stack was selected:

```Vue_vite(frontend)``` - for component based ui, rich in reactive state management, and fast development

```PYthon+Flask(backend)``` - lightweight REST API framework with ai/ml support

```PyMUPDF+Pdfplumber(pdf parser)``` - pymupdf for page-wise extraction and plumber for table extraction

```Pandas+openpyxl(excel/csv parser)``` - helps to structure the data and numerical calculations

```llamaIndex-SentenceSplitter(chunking)``` - sentence-aware chunking with configurable chunk size and overlap

```Qwen3-Embedding-0.6B(Embedding)``` - a multilingual embedding model that supports instruction-aware retrieval

```postgresql+pgvector(Database)``` - Persistent Vector storage,similarity search, all the documents metadata in one database

```Gemini Flash(LLM)``` - hosted llm for generating natural-language answers from the context

```LlamaIndex(orchestration)``` - helps in co-originating the two workflows

---

## 4. System Architecture

```Frontend -> REST API -> Flask Backend -> Ingestion service -> File Validation -> File Parsing -> content normalization -> sentence splitter -> Qwen embeddings -> Postgresql(document uploading)```
```Frontend -> REST API -> Flask Backend-> User -> query validation -> embeddings -> pg vector search -> gemini generation -> postgresql -> get the response in frontend(retrieval and generation)```

---

## 5. Data and Source Metadata Design

The application must retain enough metadata to identify the exact source of every retrieved chunk.

| Entity | Important fields | Purpose |
| --- | --- | --- |
| `documents` | `id`, `filename`, `file_hash`, `file_type`, `status`, `uploaded_at` | Track uploaded files and ingestion state |
| Vector-store records | `id`, `document_id`, `content`, `embedding`, `metadata` | Store searchable chunks, vectors and source metadata |
| `chat_sessions` | `id`, `created_at` | Track conversations |
| `chat_messages` | `id`, `session_id`, `role`, `content`, `created_at` | Preserve chat history |

The LlamaIndex PostgreSQL vector-store table should be configured with an embedding dimension that matches the selected Qwen output. Keep application document records separate from the vector-store implementation details.

Required metadata:

**PDF**

```json
{
  "document_id": "doc_123",
  "source_file": "report.pdf",
  "file_type": "pdf",
  "page_number": 4,
  "chunk_index": 2
}
```

**Excel**

```json
{
  "document_id": "doc_456",
  "source_file": "sales.xlsx",
  "file_type": "excel",
  "sheet_name": "Sales",
  "row_start": 2,
  "row_end": 15,
  "headers": ["Order ID", "Product", "Amount"]
}
```

**CSV**

```json
{
  "document_id": "doc_789",
  "source_file": "customers.csv",
  "file_type": "csv",
  "row_start": 10,
  "row_end": 20,
  "headers": ["Customer ID", "Name", "City"]
}
```

Citations must be generated by the backend from retrieved metadata, not guessed by the LLM.

---

## 6. Project Structure

```text
document-rag-chatbot/
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── views/
│   │   ├── stores/
│   │   ├── router/
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── extensions.py
│   │   │
│   │   ├── api/
│   │   │   ├── document_routes.py
│   │   │   ├── chat_routes.py
│   │   │   └── health_routes.py
│   │   │
│   │   ├── ingestion/
│   │   │   ├── pdf_parser.py
│   │   │   ├── pdf_table_parser.py
│   │   │   ├── spreadsheet_parser.py
│   │   │   ├── normalizer.py
│   │   │   └── ingestion_service.py
│   │   │
│   │   ├── rag/
│   │   │   ├── chunker.py
│   │   │   ├── embedding_model.py
│   │   │   ├── vector_store.py
│   │   │   ├── retriever.py
│   │   │   ├── query_router.py
│   │   │   ├── prompt.py
│   │   │   └── answer_service.py
│   │   │
│   │   ├── services/
│   │   │   ├── document_service.py
│   │   │   └── chat_service.py
│   │   │
│   │   └── utils/
│   │       ├── file_validation.py
│   │       ├── file_hash.py
│   │       └── citation_builder.py
│   │
│   ├── sql/
│   │   └── schema.sql
│   ├── tests/
│   ├── data/
│   │   └── uploads/
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
│
├── evaluation/
│   ├── test_questions.csv
│   └── evaluation_report.md
│
├── docs/
│   └── engineering_decisions.md
│
├── .gitignore
└── README.md
```

---

## 7. Installation and Setup

### Prerequisites

- Python 3.14 (or a version supported by the pinned dependencies).
- Node.js and npm.
- PostgreSQL.
- pgvector extension installed for the PostgreSQL server.
- Google Gemini API key.
- Git.

### Clone the repository

```powershell
git clone <your-github-repository-url>
Set-Location document-rag-chatbot
```

### PostgreSQL setup

Create the database:

```sql
CREATE DATABASE document_rag_db;
```

Connect to `document_rag_db` and enable pgvector:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Execute the project's SQL schema:

```text
backend/sql/schema.sql
```

The schema must create the application metadata and chat tables. The LlamaIndex PostgreSQL vector store must use a vector column dimension matching the configured embedding output.

### Backend setup

Open PowerShell:

```powershell
Set-Location document-rag-chatbot
py -3.14 -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1

Set-Location backend
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Backend dependencies

The following is the intended dependency set. Validate compatible versions together and pin the working versions in `requirements.txt`.

```text
Flask
Flask-Cors
python-dotenv

PyMuPDF
pdfplumber
pandas
openpyxl

llama-index-core
llama-index-vector-stores-postgres
llama-index-embeddings-huggingface
llama-index-llms-google-genai

sentence-transformers
transformers
torch

psycopg[binary]>=3.2
pgvector

pytest
```

Do not install ChromaDB or `llama-index-vector-stores-chroma`.

### Environment configuration

Create `backend/.env` from `backend/.env.example`.

```env
FLASK_ENV=development
SECRET_KEY=replace_with_a_secure_random_value

DATABASE_URL=postgresql://username:password@localhost:5432/document_rag_db

GOOGLE_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.8-flash

EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B
EMBEDDING_DIMENSION=1024

UPLOAD_DIR=data/uploads
MAX_CONTENT_LENGTH=20971520

CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K=5
```

Never commit `.env`, API credentials or uploaded private documents to GitHub.

### Run the backend

From the `backend` directory:

```powershell
python run.py
```

### Frontend setup

Open another PowerShell terminal:

```powershell
Set-Location document-rag-chatbot
npm create vite@latest frontend -- --template vue

Set-Location frontend
npm install
npm install axios
npm run dev
```

If the frontend directory already exists in the repository, do not run `npm create vite` again. Install its dependencies with `npm install`.

Configure the frontend API base URL to point to the Flask backend.

---

## 8. API Endpoints

| Method | Endpoint | Responsibility |
| --- | --- | --- |
| `POST` | `/api/documents/upload` | Upload and register a document |
| `GET` | `/api/documents` | List uploaded documents |
| `GET` | `/api/documents/<id>` | Get document details and ingestion status |
| `DELETE` | `/api/documents/<id>` | Delete a document and its indexed chunks |
| `POST` | `/api/chat` | Ask a question about selected documents |
| `GET` | `/api/sessions/<id>/messages` | Retrieve conversation history |
| `GET` | `/api/health` | Check application and database health |

For the first version, synchronous ingestion is acceptable for small files. Add a background job system only if measured processing time or file size makes synchronous processing unsuitable.

---

## 9. Grounding, Retrieval and Reliability

The chatbot must follow these rules:

1. Answer factual questions using retrieved document evidence.
2. Do not invent facts that are absent from the uploaded documents.
3. Return an insufficient-evidence response when relevant evidence cannot be found.
4. Include source references for factual claims.
5. Filter retrieval by the selected document IDs and the appropriate user/session scope.
6. Use pandas for exact spreadsheet calculations.
7. Handle parsing, embedding, database and LLM failures explicitly.
8. Do not execute arbitrary Python or SQL generated by the LLM.

A prompt instruction alone does not guarantee that an answer is grounded. The backend should inspect retrieval results, apply a tested retrieval threshold or evidence policy, and construct citations from actual retrieved metadata.

---

## 10. Testing and Evaluation

The project includes an evaluation sheet containing 10 questions.

| Test category | Number of questions |
| --- | ---: |
| PDF factual questions | 2 |
| PDF table question | 1 |
| Excel lookup question | 1 |
| Excel aggregation question | 1 |
| CSV question | 1 |
| Cross-document question | 1 |
| Unanswerable questions | 3 |
| **Total** | **10** |

Expected answers must be verified against the actual uploaded test documents. Do not invent expected answers before selecting the test files.

Evaluation criteria:

- **Extraction accuracy:** whether text, tables and rows are extracted correctly.
- **Retrieval relevance:** whether retrieved chunks support the question.
- **Answer correctness:** whether the generated answer matches the source evidence.
- **Citation accuracy:** whether citations point to the correct file, page, sheet or rows.
- **Faithfulness:** whether answer claims are supported by retrieved evidence.
- **Abstention accuracy:** whether the chatbot correctly declines unsupported questions.
- **Processing time:** time taken for ingestion and query processing.

Unit and integration tests should cover parsers, metadata preservation, chunking, embedding dimensions, vector persistence, retrieval, API validation and deletion.

---

## 11. Implementation Phases

| Phase | Work | Completion criteria |
| --- | --- | --- |
| 1. Foundation | Vue, Flask, PostgreSQL, pgvector and configuration | Frontend, backend and database communicate |
| 2. Upload | File validation, hashing and document records | Valid files upload; invalid files are rejected |
| 3. Extraction | PDF text/tables, Excel and CSV parsing | Content and source locations are preserved |
| 4. Chunking and embeddings | SentenceSplitter and Qwen embeddings | Chunks have valid vectors and metadata |
| 5. Vector persistence | LlamaIndex PostgreSQL vector store | Data persists across backend restarts |
| 6. Retrieval and generation | Retrieval, context assembly and Gemini | Answers include valid source citations |
| 7. Structured questions | pandas-based calculation path | Exact calculations return contributing rows |
| 8. Frontend integration | Upload, status, chat and citations | End-to-end user flow works |
| 9. Evaluation | Ten-question test set and automated tests | Results and failures are documented |
| 10. Delivery | README, engineering note and clean setup | Another developer can run the project |

---

## 12. Limitations and Future Improvements

### Known limitations

- Scanned PDFs may require OCR.
- Complex PDF layouts and borderless tables may need extraction tuning.
- Local embedding generation may be slow on CPU-only systems.
- Semantic retrieval alone is unsuitable for exact numerical calculations.
- Retrieval can fail when extraction or chunk boundaries lose important context.
- Gemini requires internet access and a valid API key.
- A small evaluation dataset cannot establish production-level reliability.

### Potential improvements

- OCR support for scanned PDFs.
- Hybrid keyword and vector retrieval.
- Reranking of retrieved chunks.
- More robust table-aware chunking.
- Background ingestion for large documents.
- Larger and more representative evaluation datasets.
- Improved document lifecycle and access control.

These improvements should be prioritized only after the baseline implementation is tested.

---

## 13. Security and Engineering Requirements

- Validate file extension, MIME type and file size.
- Generate a SHA-256 hash to detect duplicate files.
- Use parameterized database operations.
- Keep API credentials in environment variables.
- Exclude `.env`, uploaded files, local databases and model caches from Git.
- Scope retrieval to the documents the user is authorized to access.
- Delete associated vector records when a document is deleted.
- Record ingestion failures and expose processing status.
- Avoid logging API keys, passwords or document contents unnecessarily.

---

## 14. Deliverables

- [x] GitHub repository with complete source code.
- [x] README with architecture, tool choices and setup instructions.
- [x] Vue.js and Flask application.
- [x] PDF, Excel and CSV upload functionality.
- [x] Document extraction with page/sheet/row metadata.
- [x] LlamaIndex chunking and Qwen3 embeddings.
- [x] Persistent PostgreSQL + pgvector storage.
- [ ] Gemini-powered grounded answers with source citations.
- [ ] pandas-based structured calculations for spreadsheet questions.
- [ ] Evaluation sheet with 10 questions, including at least 3 unanswerable questions.
- [ ] Short implementation note describing choices, what worked, what failed and improvements.
- [x] `.env.example` and `.gitignore` with secrets excluded.

---

## 15. Official Documentation

- Vue.js: <https://vuejs.org/guide/introduction.html>
- Vite: <https://vite.dev/guide/>
- Flask: <https://flask.palletsprojects.com/>
- PyMuPDF: <https://pymupdf.readthedocs.io/>
- pdfplumber: <https://github.com/jsvine/pdfplumber>
- pandas: <https://pandas.pydata.org/docs/>
- openpyxl: <https://openpyxl.readthedocs.io/>
- LlamaIndex: <https://developers.llamaindex.ai/python/framework/>
- LlamaIndex PostgreSQL vector store: <https://developers.llamaindex.ai/python/examples/vector_stores/postgres/>
- Qwen3 Embedding: <https://huggingface.co/Qwen/Qwen3-Embedding-0.6B>
- pgvector: <https://github.com/pgvector/pgvector>
- Gemini API models: <https://ai.google.dev/gemini-api/docs/models>

---

**Project status:** Phases 1-5 complete (foundation, upload, extraction, chunking+embeddings, vector persistence). Phases 6-9 pending (retrieval+generation, structured queries, frontend, evaluation).
# Doc_Rag_Bot
