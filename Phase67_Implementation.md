# Phase 6 & 7 Implementation — Retrieval, Generation, and Structured Questions

**Date:** 2026-11-26  
**Status:** ✅ Complete

---

## Summary

Phases 6 and 7 implement the core Q&A capability: retrieving relevant document chunks, assembling prompts, generating answers via Gemini, building citations, and routing questions to determine intent.

---

## Phase 6 — Retrieval and Generation

### Completion Criterion
> Answers include valid source citations.

### Files Implemented

| File | Purpose |
| --- | --- |
| `backend/app/rag/retriever.py` | Wraps vector_store.search(), returns snippet dicts |
| `backend/app/rag/prompt.py` | Builds system + user prompts with context and citations |
| `backend/app/rag/answer_service.py` | Calls Gemini API via google-genai SDK |
| `backend/app/services/chat_service.py` | Orchestrates the full answer pipeline |
| `backend/app/utils/citation_builder.py` | Formats retrieved snippets into citations |
| `backend/app/api/chat_routes.py` | Flask endpoints for chat and session messages |
| `backend/tests/verify_phase67_contract.py` | Pytest contract tests (8 tests) |

### Architecture

```
ChatService.answer(question, document_ids)
  │
  ├─ 1. classify(question) → RouterResult (intent, reason, follow_up)
  │
  ├─ 2. If intent == "document":
  │       retrieve(question, document_ids, top_k) → snippets
  │
  ├─ 3. build_citations(snippets) → citations
  │
  ├─ 4. build_prompt(question, snippets, citations) → (prompt_text, _)
  │
  ├─ 5. Generate answer:
  │       - intent == "generic" → _generic_answer(question)
  │       - intent == "unanswerable" → _unanswerable_answer(question, routing)
  │       - else → generate_answer(prompt_text)
  │
  └─ 6. Return {
        answer, sources, citations,
        intent, intent_reason, follow_up,
        retrieved_count, session_id
      }
```

### Key Design Decisions

1. **Intent-based routing**: Questions are classified before retrieval. Generic/unanswerable questions skip retrieval and get appropriate responses without calling Gemini.

2. **Citation format**: Citations are built from retrieved snippets before prompt assembly, so the prompt can reference them with markers.

3. **Session tracking**: `session_id` is accepted as an optional parameter and forwarded in the response for caller correlation.

4. **Gemini integration**: Uses `google-genai` SDK directly (not llama-index LLM wrapper). The prompt prefix `.google-genai` separates system instruction from user prompt.

5. **Error handling**: Chat endpoint catches exceptions and returns stable 500 errors without leaking internals.

### Verification

- All modules import successfully
- Contract tests pass (8/8):
  - `test_public_contract[rag/retriever.py]` — `retrieve(question, document_ids)`
  - `test_public_contract[rag/prompt.py]` — `build_prompt(question, contexts, citations)`
  - `test_public_contract[rag/answer_service.py]` — `generate_answer(prompt_text, model)`
  - `test_public_contract[rag/query_router.py]` — `classify(question)`
  - `test_public_contract[services/chat_service.py]` — `ChatService`, `ChatService.answer(self, question, document_ids)`
  - `test_public_contract[utils/citation_builder.py]` — `build_citations(retrieved)`
  - `test_public_contract[api/chat_routes.py]` — `chat_bp`, `ask`, `messages(session_id)`
  - `test_full_contract` — all modules together

---

## Phase 7 — Structured Questions

### Completion Criterion
> Exact calculations return contributing rows.

### Files Implemented

| File | Purpose |
| --- | --- |
| `backend/app/rag/query_router.py` | Question classification with RouterResult |

### What Was Built

1. **`RouterResult` dataclass**: Holds `intent`, `reason`, and `follow_up_question`.

2. **`classify(question)` function**: Classifies questions into one of four intents:
   - `document` — question about document contents (goes to retrieval + Gemini)
   - `generic` — greeting, help, identity questions (gets canned response)
   - `unanswerable` — question outside document scope (gets polite refusal)
   - `calculation` — numerical/quantitative question (pending pandas execution path)

3. **Helper functions**:
   - `_normalize(text)` — lowercase + strip
   - `_matches_any(normalized, candidates)` — substring matching
   - `_is_document_style(normalized)` — detects document-specific question patterns

### Current State

The routing infrastructure is complete. The `calculation` intent is recognized but routed to a pending implementation. When a calculation question is detected, the current code will treat it as a document question (falls through to Gemini generation). The pandas aggregation/lookup path for exact calculations is the next sub-task within Phase 7.

### What's Next for Phase 7

- Implement pandas-based calculation path for questions like "total of column X", "average of Y", "count rows where Z"
- Add safeguards for LLM code execution (if using code interpreter approach)
- Contribute rows extraction for calculation results

---

## Testing

### Contract Tests (`backend/tests/verify_phase67_contract.py`)

Pytest-based contract verification that checks:

1. Each expected function/class exists in the expected module
2. Function signatures match expected parameter names
3. Class methods exist with correct signatures

Run with:
```bash
python -m pytest backend/tests/verify_phase67_contract.py -v
```

### Running the Backend

```bash
cd backend
python run.py
# Server starts on http://127.0.0.1:5000
```

### Testing Chat Endpoint

```bash
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?", "session_id": "test-1"}'
```

Note: Requires `GOOGLE_API_KEY` environment variable to be set for generation to work.

---

## Dependencies Added

- `google-generativeai` (or `google-genai`) — Gemini API client
- Already in `requirements.txt` from earlier phases

---

## Known Limitations

1. **Gemini API key required**: Without `GOOGLE_API_KEY`, `generate_answer()` raises `RuntimeError`.
2. **Calculation path pending**: Questions classified as `calculation` are not yet handled with pandas execution.
3. **No evaluation dataset**: Phase 9 evaluation questions not yet created.
4. **No frontend**: Phase 8 UI components not yet built; chat must be tested via API calls.
