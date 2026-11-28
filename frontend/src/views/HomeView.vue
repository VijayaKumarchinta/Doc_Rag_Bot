<template>
  <div class="page">
    <header class="header">
      <div class="header-top">
        <div class="logo">
          <div class="logo-mark">R</div>
          <div class="logo-text">
            <h2>Document RAG</h2>
            <p>Enterprise Document Q&amp;A</p>
          </div>
        </div>
        <div class="header-actions">
          <button
            type="button"
            class="icon-btn"
            aria-label="Switch to dark/light theme"
            @click="theme = theme === 'dark' ? 'light' : 'dark'"
          >
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          </button>
          <button type="button" class="icon-btn" aria-label="New chat" @click="newChat">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          </button>
        </div>
      </div>
      <div v-if="sessionTitle" class="session-bar">
        <span class="session-title">{{ sessionTitle }}</span>
        <button type="button" class="icon-btn" aria-label="Clear conversation" @click="chat.clear()">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2"/><path d="M19 6v12a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>
        </button>
      </div>
    </header>

    <div class="layout">
      <aside class="panel sidebar" :class="{ 'is-open': sessionsOpen }">
        <div class="panel-head">
          <h2>Chats</h2>
          <button type="button" class="icon-btn" aria-label="Close chat list" @click="sessionsOpen = false">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>
        <button type="button" class="new-chat" @click="newChat">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          <span>New chat</span>
        </button>
        <nav class="sessions" :class="{ open: sessionsOpen }">
          <p class="muted">Today</p>
          <button
            v-for="chat in today"
            :key="chat.id"
            type="button"
            class="session"
            :class="{ active: chat.id === chatId }"
            @click="switchSession(chat.id)"
          >
            {{ chat.title || 'Untitled' }}
          </button>
        </nav>
      </aside>

      <aside class="panel rail">
        <div class="panel-head">
          <h2>Documents</h2>
          <button
            type="button"
            class="icon-btn"
            :aria-label="`${docs.documents.length} documents`"
            @click="documentsOpen = !documentsOpen"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>
          </button>
        </div>
        <UploadPanel
          @upload-started="docs.uploading = true"
          @upload-finished="docs.uploading = false"
          @upload-error="docs.error = $event"
        />
        <DocumentList
          :docs="docs.documents"
          :highlighted-id="docs.highlightedId"
          @remove="docs.remove($event, { confirm: $event === 'confirmed' })"
          @highlight="docs.highlight($event)"
        />
        <p v-if="docs.error && !docs.documents.length" class="error">{{ docs.error }}</p>
        <p v-if="docs.confirmingId" class="confirm">
          This will remove the document and its indexed content. <button type="button" @click="docs.remove(docs.confirmingId, { confirm: true })">Remove</button>
          <button type="button" @click="docs.confirmingId = null">Cancel</button>
        </p>
      </aside>

      <main class="chat">
        <div class="chat-wrap">
          <header class="chat-header">
            <div class="chat-header-left">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
              <h2 class="chat-title">{{ chatTitle }}</h2>
            </div>
          </header>

          <div ref="scrollBox" class="messages">
            <p v-if="!chat.messages.length" class="muted intro">
              Upload a file, then ask a question about it. Every answer shows the
              file and page or rows it came from.
            </p>

            <div v-if="!chat.messages.length" class="welcome">
              <div class="welcome-card">
                <div class="welcome-avatar">
                  <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>
                </div>
                <p class="welcome-text">
                  Hello! I'm your Document RAG assistant. I can answer questions
                  about the PDF, Excel, and CSV files you upload.
                </p>
                <div class="quick-questions">
                  <button type="button" class="chip" @click="ask('Summarize the manual')">Summarize the manual</button>
                  <button type="button" class="chip" @click="ask('What is the policy on expense reports?')">What is the policy on expense reports?</button>
                </div>
              </div>
            </div>

            <ChatMessage
              v-for="(message, index) in chat.messages"
              :key="index"
              :message="message"
            />

            <p v-if="chat.asking" class="muted">Searching your files…</p>
            <p v-if="chatError" class="error">{{ chatError }}</p>
          </div>

          <div class="composer-bar">
            <label class="composer-label" for="chat-input"></label>
            <div class="composer-field">
              <input
                id="chat-input"
                v-model="question"
                type="text"
                placeholder="Ask a question about your documents…"
                :disabled="chat.asking"
              />
              <button
                type="submit"
                class="composer-btn"
                :disabled="chat.asking || !question.trim()"
                @click="submit"
              >
                Ask
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>

    <input
      ref="dropTarget"
      type="file"
      accept=".pdf,.xlsx,.xls,.csv"
      multiple
      hidden
      @change="onFilesSelected"
    />
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref, watch, computed } from 'vue'
import UploadPanel from '../components/UploadPanel.vue'
import DocumentList from '../components/DocumentList.vue'
import ChatMessage from '../components/ChatMessage.vue'
import { useDocumentsStore } from '../stores/documents'
import { useChatStore } from '../stores/chat'

const docs = useDocumentsStore()
const chat = useChatStore()
const scrollBox = ref(null)
const question = ref('')
const dropTarget = ref(null)
const sessionsOpen = ref(false)
const documentsOpen = ref(true)

const sessionTitle = computed(() => {
  if (!chat.sessionId) return ''
  const saved = sessionStorage.getItem('rag_session_title_' + chat.sessionId)
  return saved || chat.title || 'New chat'
})

const chatTitle = computed(() => {
  return chat.title || sessionTitle.value || 'New chat'
})

const today = ref([])
const chatId = ref(null)
const chatError = ref('')

function hydrateSessions() {
  const ids = Object.keys(sessionStorage)
    .filter((key) => /^rag_session_/.test(key))
    .map((key) => ({ id: key.slice('rag_session_'.length), title: sessionStorage.getItem('rag_session_title_' + key) }))
    .filter((s) => s.id)
    .sort((a, b) => (b.id > a.id ? -1 : 1))
  today.value = ids.slice(0, 5)
  chatId.value = chat.sessionId
}

// Switch to a chat session and restore its messages.
async function switchSession(id) {
  if (id === chat.sessionId) return
  chat.sessionId = id
  chat.restore()
  sessionsOpen.value = false
}

function newChat() {
  chat.clear()
  chat.sessionId = null
  sessionStorage.removeItem('rag_session_id')
  Object.keys(sessionStorage).forEach((key) => {
    if (/^rag_session_/.test(key) || /^rag_session_title_/.test(key)) {
      sessionStorage.removeItem(key)
    }
  })
  question.value = ''
}

function onFilesSelected(event) {
  const files = Array.from(event.target.files || [])
  if (!files.length) return
  docs.upload(files)
  dropTarget.value.value = ''
}

function submit() {
  const text = question.value.trim()
  if (!text) return
  question.value = ''
  chat.ask(text, null)
}

function ask(text) {
  question.value = text
  submit()
}

watch(
  () => chat.messages.length,
  async () => {
    await nextTick()
    if (scrollBox.value) scrollBox.value.scrollTop = scrollBox.value.scrollHeight
  },
)

watch(
  () => chat.asking,
  (asking) => {
    if (asking) {
      const input = document.getElementById('chat-input')
      if (input) input.focus()
    }
  },
)

onMounted(() => {
  hydrateSessions()
  docs.refresh()
  chat.restore()
})
</script>

<style scoped>
.page {
  font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
  color: #111827;
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}
.header h1 {
  margin: 0;
  font-size: 1rem;
}
.header p {
  margin: 0.25rem 0 0;
  font-size: 0.8rem;
  color: #6b7280;
}
.layout {
  flex: 1;
  display: flex;
  min-height: 0;
}
.panel {
  width: 300px;
  flex-shrink: 0;
  border-right: 1px solid #e5e7eb;
  padding: 1rem;
  overflow-y: auto;
}
.panel h2 {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6b7280;
  margin: 0 0 0.75rem;
}
.chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}
.muted {
  color: #6b7280;
  font-size: 0.8rem;
}
.intro {
  margin: 0;
  max-width: 28rem;
  line-height: 1.5;
}
.error {
  margin: 0.85rem 0 0;
  padding: 0.5rem 0.65rem;
  font-size: 0.78rem;
  color: #991b1b;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 0.4rem;
}
</style>

<style>
:root {
  --primary: #2563eb;
  --primary-dark: #1d4ed8;
  --bg: #f9fafb;
  --surface: #ffffff;
  --ink: #111827;
  --muted: #4b5563;
  --border: #e5e7eb;
  --error: #b91c1c;
  --error-tint: #fef2f2;
  --error-border: #fecaca;
  --success: #15803d;
  --warning: #b45309;
  --info-tint: #eff6ff;
  --radius: 8px;
  --radius-sm: 12px;
  --radius-xl: 16px;
}

.page {
  font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
  color: var(--ink);
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page.dark {
  --bg: #0f172a;
  --surface: #1e293b;
  --ink: #e2e8f0;
  --muted: #94a3b8;
  --border: #334155;
  --error: #dc2626;
  --error-tint: #3a1f1f;
  --error-border: #7f1d1d;
  --info-tint: #1e3a5f;
  --success: #22c55e;
  --warning: #f59e0b;
  --primary: #3b82f6;
  --primary-dark: #2563eb;
}

.header {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  flex-shrink: 0;
}

.header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.logo-mark {
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary);
  border-radius: var(--radius-sm);
  color: #fff;
  font-weight: 700;
}

.logo-text h2 {
  margin: 0;
  font-size: 1.1rem;
}

.logo-text p {
  margin: 0;
  font-size: 0.7rem;
  color: var(--muted);
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--muted);
  cursor: pointer;
  padding: 0;
}

.icon-btn:hover {
  color: var(--primary);
  border-color: var(--primary);
}

.icon-btn:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

.session-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

.session-title {
  font-size: 0.8rem;
  color: var(--muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.layout {
  flex: 1;
  display: flex;
  min-height: 0;
}

.panel {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--border);
}

.panel-head h2 {
  margin: 0;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted);
}

.rail {
  border-right: 1px solid var(--border);
}

.sidebar {
  border-right: none;
  min-width: 240px;
}

.sidebar.is-open {
  position: fixed;
  inset: 0;
  z-index: 30;
  background: var(--surface);
  overflow-y: auto;
  border-right: 1px solid var(--border);
}

.sessions {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-top: 0.5rem;
}

.sessions.open {
  display: flex;
}

.sessions:not(.open) {
  display: none;
}

.session {
  display: flex;
  width: 100%;
  text-align: left;
  padding: 0.55rem 0.6rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.session:hover {
  background: var(--info-tint);
}

.session.active {
  background: var(--primary-tint, #eff6ff);
  color: var(--primary-dark, #1d4ed8);
  font-weight: 600;
}

.new-chat {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.5rem;
  border: 1px dashed var(--border);
  border-radius: var(--radius-sm);
  color: var(--muted);
  cursor: pointer;
  font-size: 0.75rem;
  margin-bottom: 0.5rem;
}

.new-chat:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.new-chat svg {
  width: 14px;
  height: 14px;
}

.upload {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.5rem;
  overflow-y: auto;
}

.preview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.preview-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.2rem 0.4rem;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--surface);
  font-size: 0.68rem;
}

.preview-name {
  max-width: 12rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-remove {
  cursor: pointer;
  color: var(--muted);
  font-size: 1rem;
  line-height: 1;
  border: none;
  background: none;
  padding: 0;
}

.preview-remove:hover {
  color: var(--error);
}

.dropzone {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  align-items: center;
  text-align: center;
  padding: 1rem;
  border: 2px dashed var(--border);
  border-radius: var(--radius-xl);
  cursor: pointer;
  font-size: 0.8rem;
  color: var(--muted);
  background: var(--bg);
}

.dropzone:hover,
.dropzone.dragging {
  border-color: var(--primary);
  background: var(--info-tint);
}

.dropzone strong {
  color: var(--ink);
}

.confirm {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem;
  border: 1px solid var(--error-border);
  border-radius: var(--radius-sm);
  background: var(--error-tint);
  font-size: 0.75rem;
}

.confirm button {
  font-size: 0.72rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}

.confirm button + button {
  margin-left: 0.25rem;
}

.chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chat-title {
  margin: 0;
  font-size: 0.85rem;
  color: var(--muted);
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.welcome {
  align-self: center;
  text-align: center;
  max-width: 24rem;
  padding: 1rem;
}

.welcome-avatar {
  width: 3.5rem;
  height: 3.5rem;
  margin: 0 auto 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary);
  color: #fff;
  border-radius: 999px;
}

.welcome-text {
  margin: 0 0 0.75rem;
  line-height: 1.5;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  justify-content: center;
}

.chip {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.7rem;
  padding: 0.3rem 0.6rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--ink);
  cursor: pointer;
}

.chip:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.bubble {
  margin: 0;
  padding: 0.55rem 0.75rem;
  border-radius: 0.6rem;
  font-size: 0.875rem;
  line-height: 1.55;
  white-space: pre-wrap;
}

.message.user .bubble {
  background: var(--primary);
  color: #fff;
  align-self: flex-end;
}

.message.assistant .bubble {
  background: var(--surface);
  border: 1px solid var(--border);
  border-bottom-left-radius: 0.2rem;
}

.citations {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.3rem;
  margin-top: 0.4rem;
}

.citations .muted {
  font-size: 0.68rem;
}

.chip {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: 0.35rem;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--ink);
  cursor: pointer;
}

.chip.active,
.chip:hover {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}

.message.assistant.highlighted .bubble {
  border-color: var(--primary);
}

.message.assistant.highlighted .citations .chip.active {
  background: var(--primary-dark);
  color: #fff;
}

.snippet {
  margin: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.72rem;
  background: var(--surface);
  border-left: 2px solid var(--primary);
  padding: 0.4rem 0.6rem;
  color: var(--ink);
  white-space: pre-wrap;
}

.composer-bar {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--surface);
  border-top: 1px solid var(--border);
}

.composer-field {
  display: flex;
  gap: 0.5rem;
}

.composer-field input {
  flex: 1;
  padding: 0.6rem 0.75rem;
  font-size: 0.875rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
}

.composer-field input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgb(37 99 235 / 0.15);
}

.composer-field input::placeholder {
  color: var(--muted);
}

.composer-btn {
  padding: 0.6rem 1rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: #fff;
  background: var(--primary);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.composer-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.composer-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted);
}

.muted {
  color: var(--muted);
  font-size: 0.8rem;
}

/* Spinner for async loading indicators. */
.spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Three-panel responsive layout. */
@media (min-width: 1140px) {
  .sidebar,
  .rail {
    position: sticky;
    top: 0;
  }
  .sidebar {
    position: sticky;
    top: 0;
    align-self: flex-start;
  }
  .rail {
    position: sticky;
    top: 0;
    align-self: flex-start;
  }
  .sidebar.is-open,
  .rail.is-open {
    position: sticky;
    top: 0;
  }
}

@media (max-width: 1139px) {
  .sidebar {
    position: fixed;
    inset: 0 0 0 auto;
    z-index: 30;
    background: var(--surface);
    overflow-y: auto;
    transform: translateX(0);
    transition: transform 0.2s ease;
  }
  .sidebar:not(.is-open) {
    transform: translateX(-100%);
  }
}

@media (max-width: 759px) {
  .sidebar,
  .rail {
    position: fixed;
    inset: 0 0 0 auto;
    z-index: 30;
    background: var(--surface);
    overflow-y: auto;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
  }
  .sidebar.is-open,
  .rail.is-open {
    transform: translateX(0);
  }
  .rail {
    left: auto;
  }
}

@media (max-width: 640px) {
  .header-top {
    flex-wrap: wrap;
  }
  .header-actions {
    order: 3;
    width: 100%;
  }
  .session-bar {
    flex-wrap: wrap;
  }
  .chat-title {
    font-size: 0.75rem;
  }
}
</style>