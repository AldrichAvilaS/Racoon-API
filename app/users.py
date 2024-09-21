from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from app.decorators import role_required  # Importar el decorador
from .db import db, User

users_bp = Blueprint('users', __name__)

@users_bp.route('/', methods=['POST'])

# Registrar un nuevo usuario
@users_bp.route('/', methods=['POST'])
#@role_required(0, 1)  # Solo usuarios con rol 0 o 1 pueden acceder
def add_user():
    data = request.get_json()
    if not data or 'boleta' not in data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Datos incompletos"}), 400

    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        boleta=data['boleta'],
        email=data['email'],
        password=hashed_password,
        nombre=data.get('nombre', ''),
        role_id=data.get('role_id')  # Asegúrate de que el rol exista
    )

    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Usuario creado con éxito"}), 201

# Obtener todos los usuarios
@users_bp.route('/', methods=['GET'])
#@role_required(0, 1)  # Solo usuarios con rol 0 o 1 pueden acceder
def get_users():
    users = User.query.all()
    return jsonify([{'boleta': user.boleta, 'email': user.email, 'nombre': user.nombre} for user in users]), 200

# Obtener un usuario por boleta
@users_bp.route('/<int:boleta>', methods=['GET'])
@role_required(0, 1)  # Solo usuarios con rol 0 o 1 pueden acceder
def get_user(boleta):
    user = User.query.get(boleta)
    if user is None:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify({'boleta': user.boleta, 'email': user.email, 'nombre': user.nombre}), 200

# Actualizar un usuario
@users_bp.route('/<int:boleta>', methods=['PUT'])
@role_required(0, 1)  # Solo usuarios con rol 0 o 1 pueden acceder
def update_user(boleta):
    data = request.get_json()
    user = User.query.get(boleta)
    if user is None:
        return jsonify({"error": "Usuario no encontrado"}), 404

    user.email = data.get('email', user.email)
    user.nombre = data.get('nombre', user.nombre)
    if 'password' in data:
        user.password = generate_password_hash(data['password'])
    if 'role_id' in data:
        user.role_id = data['role_id']

    db.session.commit()
    return jsonify({"message": "Usuario actualizado con éxito"}), 200

# Eliminar un usuario
@users_bp.route('/<int:boleta>', methods=['DELETE'])
@role_required(0, 1)  # Solo usuarios con rol 0 o 1 pueden acceder
def delete_user(boleta):
    user = User.query.get(boleta)
    if user is None:
        return jsonify({"error": "Usuario no encontrado"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Usuario eliminado con éxito"}), 200
