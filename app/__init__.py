# app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
from .db import init_db, db, User

# Importa y registra los Blueprints
from .users import users_bp
from .auth import auth_bp

def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)  # Permite el uso de credenciales

    # Configuración de la base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/test'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Establece la clave secreta para firmar JWT
    app.config['JWT_SECRET_KEY'] = 'd822d96ef56c589c3904a372381fa378'  # Cambia esto por una clave secreta única
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=14)  # Duración de los tokens

    # Inicializa la base de datos
    init_db(app)

    # Inicializa JWTManager
    jwt = JWTManager(app)

    # Registra los blueprints
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app
