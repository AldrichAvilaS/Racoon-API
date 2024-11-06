# app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from datetime import timedelta
from .db import init_db, db, User

# Importa y registra los Blueprints
from .users import users_bp
from .auth import auth_bp
from .file import file_bp
from .groups import groups_bp
from .events import logs_bp


def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)  # Permite el uso de credenciales
    
    # Configuración de la base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/test'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 1 GB
    # Establece la clave secreta para firmar JWT
    app.config['JWT_SECRET_KEY'] = 'd822d96ef56c589c3904a372381fa378'  # Cambia esto por una clave secreta única
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=2)  # Duración de los tokens de 2 dias
    # Inicializa Migrate
    migrate = Migrate(app, db)
    
    # Inicializa la base de datos
    init_db(app)

    # Inicializa JWTManager
    jwt = JWTManager(app)

    # Registra los blueprints
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(file_bp, url_prefix='/file')
    app.register_blueprint(groups_bp, url_prefix='/groups')
    app.register_blueprint(logs_bp, url_prefix='/logs')

    #inicializar openstack auth_openstack
    return app
