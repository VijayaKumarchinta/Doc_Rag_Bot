# Frontend Flow — Phase 8 Implementation Plan

**Date:** 2026-11-26  
**Status:** Planning — API layer complete, UI components pending

---

## Overview

This document describes the planned frontend architecture for Phase 8 (Frontend Integration). The backend API endpoints from Phases 1–7 are ready; this phase builds the Vue 3 UI to exercise them.

## Backend API Surface (Ready)

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/health` | GET | Health check (DB connectivity) |
| `/api/upload` | POST | Upload PDF/Excel/CSV files |
| `/api/documents` | GET | List uploaded documents |
| `/api/documents/<id>` | GET | Get document details |
| `/api/documents/<id>` | DELETE | Delete document + cascade |
| `/api/chat` | POST | Ask question, get answer with citations |
| `/api/sessions/<session_id>/messages` | GET | Get chat history for session |

### Chat Request Format
```json
{
  "question": "string",
  "session_id": "string (optional)",
  "document_ids": ["uuid", ...] (optional)
}
```

### Chat Response Format
```json
{
  "answer": "string",
  "sources": ["label", ...],
  "citations": [{"label": "...", "metadata": {...}}],
  "intent": "document|generic|unanswerable|calculation",
  "intent_reason": "string",
  "follow_up": "string | null",
  "retrieved_count": 5,
  "session_id": "string | null"
}
```

---

## Planned Component Structure

```
frontend/src/
├── api/
│   └── client.js          # Axios instance, API wrappers
├── components/
│   ├── DocumentUpload.vue       # Drag-drop file upload
│   ├── DocumentList.vue         # Uploaded documents table
│   ├── IngestionStatus.vue      # Upload progress/status
│   ├── ChatInput.vue            # Question input + send
│   ├── ChatMessage.vue          # Single message display
│   ├── ChatWindow.vue           # Chat history + input
│   └── CitationCard.vue         # Citation source display
├── stores/
│   ├── documents.js             # Pinia store: documents state
│   └── chat.js                  # Pinia store: chat sessions
├── views/
│   ├── HomeView.vue             # Main view (upload + chat)
│   └── DocumentView.vue         # Single document details
└── router/
    └── index.js                 # Vue Router routes
```

---

## User Flow

### 1. Upload Flow
```
User lands on HomeView
  → Sees upload area (DocumentUpload component)
  → Drops/selects file (.pdf, .xlsx, .csv)
  → Upload progress shown (IngestionStatus)
  → On success: document appears in DocumentList
  → On failure: error message displayed
```

### 2. Chat Flow
```
User types question in ChatInput
  → Click send or press Enter
  → POST /api/chat with question
  → Loading state while waiting
  → Response displayed as ChatMessage
  → Citations shown below answer (CitationCard)
  → If follow_up provided, show as suggestion
  → Session ID tracked for history
```

### 3. Document Context Flow
```
User can filter chat by document
  → Select documents from DocumentList
  → document_ids sent with chat request
  → Answer grounded only in selected docs
```

---

## State Management (Pinia)

### Documents Store (`stores/documents.js`)
- `documents`: array of document records
- `loading`: boolean
- `error`: string | null
- Actions: `fetchDocuments()`, `uploadDocument(file)`, `deleteDocument(id)`

### Chat Store (`stores/chat.js`)
- `sessions`: map of session_id → messages
- `currentSessionId`: string | null
- `loading`: boolean
- Actions: `sendMessage(question, documentIds)`, `getMessages(sessionId)`

---

## API Client (`api/client.js`)

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api', // Vite proxy to Flask
})

export function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function getDocuments() {
  return api.get('/documents')
}

export function deleteDocument(id) {
  return api.delete(`/documents/${id}`)
}

export function sendChatMessage(question, sessionId = null, documentIds = null) {
  return api.post('/chat', { question, session_id: sessionId, document_ids: documentIds })
}

export function getMessages(sessionId) {
  return api.get(`/sessions/${sessionId}/messages`)
}
```

---

## Routing

| Path | Component | Purpose |
| --- | --- | --- |
| `/` | HomeView | Upload + chat on one page |
| `/documents` | DocumentView | Document list/details (optional) |

---

## Dependencies to Add

```bash
npm install axios
# Pinia and Vue Router already installed
```

---

## Implementation Order

1. **API client** (`api/client.js`) — wraps all backend endpoints
2. **Pinia stores** (`stores/documents.js`, `stores/chat.js`) — state management
3. **Components** (bottom-up: CitationCard → ChatMessage → ChatInput → ChatWindow → DocumentUpload → DocumentList)
4. **Views** (HomeView integrates upload + chat)
5. **Router** (wire views to paths)
6. **Polish** (loading states, error handling, responsive layout)

---

## Notes

- Vite is already configured to proxy `/api` to Flask on `127.0.0.1:5000`
- Frontend dev server runs on port 5173
- CORS is enabled on Flask backend
- The backend `.env` must have `GOOGLE_API_KEY` set for chat to work end-to-end
