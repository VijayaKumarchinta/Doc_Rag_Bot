from ..rag.answer_service import generate_answer
from ..rag.prompt import build_prompt
from ..rag.query_router import classify
from ..rag.retriever import retrieve
from ..utils.citation_builder import build_citations

class ChatService:

    def __init__(self, *, top_k=None):
        self._top_k = top_k

    def answer(self, question, document_ids=None, *, session_id=None):
        """Answer a user question using the ingested documents.

        Args:
            question: user question text.
            document_ids: optional list of document ids to restrict retrieval.
            session_id: optional chat session id (forwarded into the response
                so callers can correlate messages).

        Returns:
            Dict with keys:
                answer: str                    -- generated answer text.
                sources: list[str]             -- human-readable source labels.
                citations: list[dict]          -- structured citations.
                intent: str                    -- routing intent.
                intent_reason: str             -- short routing reason.
                follow_up: str | None          -- suggested follow-up, if any.
                retrieved_count: int           -- number of excerpts retrieved.
                session_id: str | None         -- forwarded session id.
        """
        routing = classify(question)

        snippets = []
        if routing.intent == "document":
            snippets = retrieve(question, document_ids=document_ids, top_k=self._top_k)

        citations = build_citations(snippets)
        prompt_text, _ = build_prompt(question, snippets, citations=citations)

        if routing.intent == "generic":
            answer = self._generic_answer(question)
        elif routing.intent == "unanswerable":
            answer = self._unanswerable_answer(question, routing)
        else:
            answer = generate_answer(prompt_text)

        return {
            "answer": answer,
            "sources": [c["label"] for c in citations],
            "citations": citations,
            "intent": routing.intent,
            "intent_reason": routing.reason,
            "follow_up": routing.follow_up_question,
            "retrieved_count": len(snippets),
            "session_id": session_id,
        }

    @staticmethod
    def _generic_answer(question: str) -> str:
        lower = question.strip().lower()
        if any(k in lower for k in ("hello", "hi", "hey")):
            return (
                "Hello! I can answer questions about the PDF, Excel, and CSV files "
                "you've uploaded. Upload a document and then ask me something about "
                "its contents."
            )
        if "help" in lower:
            return (
                "I can search your uploaded documents for answers. Try asking about "
                "specific totals, names, tables, or sections in your PDF, Excel, or CSV "
                "files."
            )
        if any(k in lower for k in ("thank", "thanks")):
            return "You're welcome!"
        if "who are you" in lower or "what are you" in lower:
            return (
                "I'm the document Q&A assistant for your uploaded files. I can search "
                "your PDF, Excel, and CSV documents and answer questions grounded in "
                "their contents."
            )
        if "bye" in lower or "goodbye" in lower:
            return "Goodbye!"
        return (
            "I'm here to help with your uploaded documents. Try asking a question about "
            "the contents of your PDF, Excel, or CSV files."
        )

    @staticmethod
    def _unanswerable_answer(question: str, routing) -> str:
        base = routing.follow_up_question or (
            "I don't have information about that in your uploaded documents."
        )
        return f"{base} I can only answer questions about the files you have uploaded."
