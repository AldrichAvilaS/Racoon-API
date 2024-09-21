# app/__init__.py
from flask import Flask
from flask_login import LoginManager
from .db import init_db, db

# Importa y registra los Blueprints
from .users import users_bp
from .auth import auth_bp

login_manager = LoginManager()
def create_app():
    app = Flask(__name__)

    # Configuración de la base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/test'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa la base de datos
    init_db(app)

    login_manager.init_app(app)
    

    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app
