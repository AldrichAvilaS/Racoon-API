from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from .db import User
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

# Endpoint para iniciar sesión
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'boleta' not in data or 'password' not in data:
        return jsonify({"error": "Datos incompletos"}), 400

    user = User.query.get(data['boleta'])
    if user is None or not check_password_hash(user.password, data['password']):
        return jsonify({"error": "Credenciales inválidas"}), 401

    # Generar el token JWT
    access_token = create_access_token(identity=user.boleta, expires_delta=timedelta(days=14))

    return jsonify({
        "message": "Inicio de sesión exitoso", 
        "access_token": access_token,
        "user_type": user.get_role()
    }), 200

# Endpoint para verificar si la sesión está activa
@auth_bp.route('/verify-session', methods=['GET'])
@jwt_required()  # Proteger con JWT
def verify_session():
    current_boleta = get_jwt_identity()
    user = User.query.get(current_boleta)
    
    if user:
        return jsonify({
            'authenticated': True,
            'user_type': user.get_role()
        }), 200
    else:
        return jsonify({
            'authenticated': False
        }), 401

# Endpoint para cerrar sesión
@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # No se requiere ninguna acción adicional en el servidor
    return jsonify({"message": "Cierre de sesión exitoso"}), 200
