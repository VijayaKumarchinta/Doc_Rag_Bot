from flask import Blueprint, jsonify

chat_bp = Blueprint('chat', __name__, url_prefix='/api')

@chat_bp.post('/chat')
def ask():
    return jsonify({'error': 'not implemented yet'}), 501

@chat_bp.get('/sessions/<session_id>/messages')
def messages(session_id):
    return jsonify({'session_id': session_id, 'messages': []})
