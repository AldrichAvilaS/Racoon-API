from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from .db import User
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user

# Endpoint para iniciar sesión
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Datos incompletos"}), 400

    user = User.query.filter_by(username=data['username']).first()
    if user is None or not check_password_hash(user.password, data['password']):
        return jsonify({"error": "Credenciales inválidas"}), 401

    # Generar el token JWT usando user.id como identidad
    access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=2))

    return jsonify({
        "message": "Inicio de sesión exitoso",
        "access_token": access_token,
        "active": user.active,
        "user_type": user.role.name,
        "user_id": user.id
    }), 200

# Endpoint para verificar si la sesión está activa
@auth_bp.route('/verify-session', methods=['GET'])
@jwt_required()
def verify_session():
    user = get_current_user()
    if user:
        return jsonify({
            'authenticated': True,
            'user_type': user.role.name,
            'active': user.active
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

# Endpoint para restablecer contraseña
@auth_bp.route('/forget_password', methods=['POST'])
def forget_password():
    try:
        data = request.get_json()
        if 'username' not in data:
            return jsonify({"error": "El campo 'username' es obligatorio"}), 400

        user = User.query.filter_by(username=data['username']).first()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        # Aquí puedes implementar la lógica para enviar un correo de recuperación
        # Por ejemplo, utilizando Flask-Mail o cualquier otro servicio de correo

        return jsonify({"message": "Correo de recuperación enviado", "email": user.email}), 200

    except Exception as e:
        return jsonify({"error": "Error en el servidor", "details": str(e)}), 500
