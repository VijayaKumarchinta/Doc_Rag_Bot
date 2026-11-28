from uuid import UUID, uuid4

from flask import Blueprint, current_app, request

from ..config import Config
from ..services import session_store
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

    # Clients echo back the id we return; anything missing or malformed starts
    # a new session rather than failing the question.
    raw_session_id = body.get('session_id')
    if session_store.is_valid_session_id(raw_session_id):
        session_id = str(UUID(str(raw_session_id)))
    else:
        session_id = str(uuid4())

    document_ids = body.get('document_ids')
    if document_ids is not None:
        document_ids = list(document_ids)

    try:
        result = _chat_service.answer(
            question=question,
            document_ids=document_ids,
            session_id=session_id,
        )
    except RuntimeError as exc:
        # Missing model configuration, not a document problem: say so plainly
        # instead of returning a generic 500.
        return {'error': 'Answer model is not configured', 'detail': str(exc)}, 503
    except Exception as exc:
        # Keep error responses stable and user-safe; do not leak internals.
        return {'error': 'Chat request failed', 'detail': str(exc)}, 500

    # Only persist successful turns, so a failed request cannot leave a
    # dangling user message with no answer behind it. A database problem must
    # not discard an answer the user already paid for, so log it and continue.
    try:
        session_store.append_turn(session_id, question, result['answer'])
    except Exception:
        current_app.logger.exception(
            'Failed to persist chat turn for session %s', session_id
        )
    result['session_id'] = session_id

    return result


@chat_bp.get('/sessions/<session_id>/messages')
def messages(session_id):
    return {
        'session_id': session_id,
        'messages': session_store.history(session_id),
    }
