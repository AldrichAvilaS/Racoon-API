from flask import Blueprint, request, jsonify, session
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
    session.permanent = True
    print(f"Usuario {user.boleta} ha iniciado sesión.")  # Para depuración

    return jsonify({"message": "ok", 
                    "user_type": user.get_role()
                    }), 200

# Endpoint para cerrar sesión
@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    #data = request.get_json()
    #user = User.query.get(data['boleta'])
    #print(f"Usuario {user.boleta} ha cerrado sesión.")  # Para depuración
    print(session)
    logout_user()  # Cierra sesión
    print(f"Exitoso.")  # Para depuración
    return jsonify({"message": "Cierre de sesión exitoso"}), 200

@auth_bp.route('/verify-session', methods=['GET'])
def verify_session():
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user_type': current_user.user_type  # O cualquier otro dato que necesites
        }), 200
    else:
        return jsonify({
            'authenticated': False
        }), 401
