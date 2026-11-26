from flask import Blueprint, jsonify, request
from ..services.document_service import (
    delete_document as svc_delete,
    get_document as svc_get,
    list_documents as svc_list,
    upload_document as svc_upload,
)
from ..utils.file_validation import ValidationError

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')

@documents_bp.get('')
def list_documents():
    try:
        return jsonify({'documents': svc_list()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.post('/upload')
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'Missing form field "file"'}), 400
    f = request.files['file']
    if not f or f.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    try:
        result = svc_upload(f, f.filename, f.mimetype)
        status = 200 if result.get('duplicate') else 201
        return jsonify(result), status
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.get('/<doc_id>')
def get_document(doc_id):
    try:
        doc = svc_get(doc_id)
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        return jsonify(doc)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.delete('/<doc_id>')
def delete_document(doc_id):
    try:
        deleted = svc_delete(doc_id)
        if not deleted:
            return jsonify({'error': 'Document not found'}), 404
        return jsonify({'deleted': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500