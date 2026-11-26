from flask import Blueprint, request

from ..config import Config
from ..services.chat_service import ChatService

chat_bp = Blueprint('chat', __name__, url_prefix='/api')

# One service instance per app lifetime is fine; the service does not hold
# request state. Top-K can be overridden from Config.TOP_K if needed.
_chat_service = ChatService(top_k=Config.TOP_K)


@chat_bp.post('/chat')
def ask():
    body = request.get_json(silent=True) or {}
    question = (body.get('question') or '').strip()
    if not question:
        return {'error': 'Missing or empty "question"'}, 400

    session_id = body.get('session_id')
    document_ids = body.get('document_ids')
    if document_ids is not None:
        document_ids = list(document_ids)

    try:
        result = _chat_service.answer(
            question=question,
            document_ids=document_ids,
            session_id=session_id,
        )
    except Exception as exc:
        # Keep error responses stable and user-safe; do not leak internals.
        return {'error': 'Chat request failed', 'detail': str(exc)}, 500

    return result


@chat_bp.get('/sessions/<session_id>/messages')
def messages(session_id):
    return {'session_id': session_id, 'messages': []}
