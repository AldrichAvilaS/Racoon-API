# app/__init__.py
from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from datetime import timedelta
from flask import session
from .db import init_db, db, User

# Importa y registra los Blueprints
from .users import users_bp
from .auth import auth_bp

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True, origins=["http://192.168.0.180:8080"])  # Permite el uso de cookies
    
    # Configuración de la base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/test'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Establece la clave secreta
    app.secret_key = 'd822d96ef56c589c3904a372381fa378'  # Cambia esto por una clave secreta única


    app.config['SESSION_COOKIE_NAME'] = 'session'  # Cambia el nombre de la cookie
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Evita que la cookie sea accesible mediante JavaScript
    app.config['SESSION_COOKIE_SECURE'] = False  # Cambia a True si usas HTTPS
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Cambia a 'Strict' si quieres una mayor protección
    # Hace la sesión permanente y configura el tiempo de vida
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=14)  # Establece la duración de la sesión, en este caso 7 días.
    app.config['SESSION_COOKIE_PATH'] = '/'  #Hacer la cookie accesible a toda la app
    #session.permanent = True
    # Inicializa la base de datos
    init_db(app)

    login_manager.init_app(app)
    
    # Cargar usuario
    @login_manager.user_loader
    def load_user(boleta):
        return User.query.get(int(boleta))
    
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app
