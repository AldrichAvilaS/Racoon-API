from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from .db import Role, db, User
from .logs import *
from .decorators import role_required

users_bp = Blueprint('users', __name__)

# Registrar un nuevo usuario
@users_bp.route('/', methods=['POST'])
@role_required(1)  # Solo usuarios con rol 1 pueden acceder
def add_user():
    boleta = get_jwt_identity()  # Obtener la boleta del usuario autenticado
    user_in_session = User.query.get(boleta)  # Usuario autenticado
    
    data = request.get_json()
    
    if not data or 'boleta' not in data or 'email' not in data or 'password' not in data:
        new_user_log(boleta, 'POST - Agregar Usuario - Datos incompletos', 400)
        return jsonify({"error": "Datos incompletos"}), 400

    # Verifica si el rol existe
    role_id = data.get('role_id')
    if role_id is not None:
        existing_role = Role.query.get(role_id)
        if existing_role is None:
            new_user_log(boleta, 'POST - Agregar Usuario - Rol inexistente', 400)
            return jsonify({"error": f"El rol con ID {role_id} no existe."}), 400

    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        boleta=data['boleta'],
        email=data['email'],
        password=hashed_password,
        nombre=data.get('nombre', ''),
        role_id=role_id
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        new_user_log(boleta, 'POST - Agregar Usuario - Usuario creado con éxito: ' + str(new_user.boleta), 201)
        return jsonify({"message": "Usuario creado con éxito"}), 201
    except IntegrityError as e:
        db.session.rollback()  # Revierte la sesión en caso de error
        if 'Duplicate entry' in str(e.orig):  # Verifica si es un error por duplicado
            new_user_log(boleta, 'POST - Agregar Usuario - Boleta o email en uso', 400)
            return jsonify({"error": "La boleta o el email ya están en uso."}), 400
        else:
            new_user_log(boleta, 'POST - Agregar Usuario - Error al crear', 500)
            return jsonify({"error": "Error al crear el usuario."}), 500
    except Exception as e:
        db.session.rollback()
        new_user_log(boleta, 'POST - Agregar Usuario - Error ' + str(e), 500)
        return jsonify({"error": str(e)}), 500

# Obtener todos los usuarios
@users_bp.route('/', methods=['GET'])
@role_required(1)  # Solo usuarios con rol 1 pueden acceder
def get_users():
    boleta = get_jwt_identity()
    users = User.query.all()
    new_user_log(boleta, 'GET - Obtener todos los usuarios', 200)
    return jsonify([{'boleta': user.boleta, 'email': user.email, 'nombre': user.nombre} for user in users]), 200

# Obtener un usuario por boleta
@users_bp.route('/<int:boleta>', methods=['GET'])
@role_required(1)  # Solo usuarios con rol 1 pueden acceder
def get_user(boleta):
    current_boleta = get_jwt_identity()
    user = User.query.get(boleta)
    if user is None:
        new_user_log(current_boleta, 'GET - Información - Usuario no encontrado: ' + str(boleta), 404)
        return jsonify({"error": "Usuario no encontrado"}), 404
    new_user_log(current_boleta, 'GET - Obtener datos: ' + str(boleta), 200)
    return jsonify({'boleta': user.boleta, 'email': user.email, 'nombre': user.nombre}), 200

# Actualizar un usuario
@users_bp.route('/<int:boleta>', methods=['PUT'])
@role_required(1)  # Solo usuarios con rol 1 pueden acceder
def update_user(boleta):
    current_boleta = get_jwt_identity()
    data = request.get_json()
    user = User.query.get(boleta)

    if user is None:
        new_user_log(current_boleta, 'PUT - Usuario no actualizado - Usuario no encontrado', 404)
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Actualizar solo los campos proporcionados en la solicitud
    if 'email' in data and data['email'] is not None:
        user.email = data['email']
    if 'nombre' in data and data['nombre'] is not None:
        user.nombre = data['nombre']
    if 'password' in data and data['password'] is not None:
        user.password = generate_password_hash(data['password'])
    if 'role_id' in data and data['role_id'] is not None:
        user.role_id = data['role_id']

    db.session.commit()
    new_user_log(current_boleta, 'PUT - Datos actualizados: ' + str(boleta), 200)
    return jsonify({"message": "Usuario actualizado con éxito"}), 200

# Eliminar un usuario
@users_bp.route('/<int:boleta>', methods=['DELETE'])
@role_required(1)  # Solo usuarios con rol 1 pueden acceder
def delete_user(boleta):
    current_boleta = get_jwt_identity()
    user = User.query.get(boleta)
    if user is None:
        new_user_log(current_boleta, 'DELETE - Usuario no eliminado - Usuario no encontrado', 404)
        return jsonify({"error": "Usuario no encontrado"}), 404

    db.session.delete(user)
    db.session.commit()
    new_user_log(current_boleta, 'DELETE - Usuario eliminado', 200)
    return jsonify({"message": "Usuario eliminado con éxito"}), 200

# Obtener los datos públicos del usuario autenticado
@users_bp.route('/info', methods=['GET'])
@role_required(1, 2, 3)  # Diferentes roles pueden acceder
def info_user():
    boleta = get_jwt_identity()  # Obtener la boleta del token JWT
    user = User.query.get(boleta)
    
    if user is None:
        new_user_log(boleta, 'GET - Información - Usuario no encontrado', 404)
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    new_user_log(boleta, 'GET - Información del usuario', 200)
    return jsonify({
        "boleta": user.get_boleta(),
        "name": user.get_name(),
        "email": user.get_email()
    }), 200
