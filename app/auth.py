from flask import Blueprint, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from .db import User
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

# Inicializa el LoginManager
login_manager = LoginManager()

# Cargar usuario
@login_manager.user_loader
def load_user(boleta):
    return User.query.get(int(boleta))

# Endpoint para iniciar sesión
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'boleta' not in data or 'password' not in data:
        return jsonify({"error": "Datos incompletos"}), 400

    user = User.query.get(data['boleta'])
    if user is None or not check_password_hash(user.password, data['password']):
        return jsonify({"error": "Credenciales inválidas"}), 401

    login_user(user)  # Inicia sesión
    return jsonify({"message": "Inicio de sesión exitoso", 
                    "user_type": user.get_role()
                    }), 200

# Endpoint para cerrar sesión
@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()  # Cierra sesión
    return jsonify({"message": "Cierre de sesión exitoso"}), 200
