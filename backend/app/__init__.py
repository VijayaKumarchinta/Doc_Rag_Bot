import os

from flask import Flask
from .api.health_routes import health_bp
from .api.document_routes import documents_bp
from .api.chat_routes import chat_bp
from .services.chat_service import ChatService
from .config import Config
from .extensions import cors

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.config['MAX_CONTENT_LENGTH'] = int(app.config.get('MAX_CONTENT_LENGTH', 20 * 1024 * 1024))

    os.makedirs(app.config['UPLOAD_DIR'], exist_ok=True)

    cors.init_app(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(chat_bp)

    @app.errorhandler(413)
    def too_large(_e):
        return {'error': 'File too large'}, 413

    @app.errorhandler(404)
    def not_found(_e):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def server_error(_e):
        return {'error': 'Internal server error'}, 500

    return app