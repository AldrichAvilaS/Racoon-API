# app/__init__.py
from flask import Flask
from flask_cors import CORS

# Importa y registra los Blueprints
from .user import user_bp
from .project import project_bp
from .object import object_bp
from .role import role_bp


def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)  # Permite el uso de credenciales
    
    # Establece la clave secreta para firmar JWT
    app.config['JWT_SECRET_KEY'] = 'd822d96ef56c589c3904a372381fa378'  # Cambia esto por una clave secreta única
    
    # Registra los blueprints
    
    app.register_blueprint(user_bp, url_prefix='/user')

    app.register_blueprint(project_bp, url_prefix='/project')
    
    app.register_blueprint(object_bp, url_prefix='/object')
    
    app.register_blueprint(role_bp, url_prefix='/role')
    
    return app
