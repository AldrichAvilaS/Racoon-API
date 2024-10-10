from flask import Blueprint, request, jsonify
from flask_login import current_user
from werkzeug.security import generate_password_hash
from app.decorators import role_required  # Importar el decorador
from sqlalchemy.exc import IntegrityError
from .db import Role, db, User
from .logs import *

users_bp = Blueprint('users', __name__)

# Registrar un nuevo usuario
@users_bp.route('/', methods=['POST'])
def add_user():
    user_in_session = current_user  # Usa directamente current_user
    new_user_log(user_in_session, 'GET - Obtener todos los usuarios', 200)
    
    data = request.get_json()
    if not data or 'boleta' not in data or 'email' not in data or 'password' not in data:
        new_user_log(user_in_session, 'POST - Agregar Usuario - Datos incompletos', error_message=400)
        return jsonify({"error": "Datos incompletos"}), 400

    # Verifica si el rol existe
    role_id = data.get('role_id')
    if role_id is not None:
        existing_role = Role.query.get(role_id)  # Asegúrate de que Role es el modelo correcto
        if existing_role is None:
            new_user_log(user_in_session, 'POST - Agregar Usuario - Rol inexistente', error_message=400)
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
        new_user_log(user_in_session, 'POST - Agregar Usuario: ' + data['boleta'], 201)
        return jsonify({"message": "Usuario creado con éxito"}), 201
    except IntegrityError as e:
        db.session.rollback()  # Revierte la sesión en caso de error
        if 'Duplicate entry' in str(e.orig):  # Verifica si es un error por duplicado
            new_user_log(user_in_session, 'POST - Agregar Usuario - Boleta o email en uso', error_message=400)
            return jsonify({"error": "La boleta o el email ya están en uso."}), 400
        else:
            new_user_log(user_in_session, 'POST - Agregar Usuario - error al crear', error_message=500)
            return jsonify({"error": "Error al crear el usuario."}), 500
    except Exception as e:
        db.session.rollback()
        new_user_log(user_in_session, 'POST - Agregar Usuario - error ' + str(e), error_message=500)
        return jsonify({"error": str(e)}), 500

# Obtener todos los usuarios
@users_bp.route('/', methods=['GET'])
@role_required(0, 1)  # Solo usuarios con rol 0 o 1 pueden acceder
def get_users():
    user_in_session = current_user  # Usa directamente current_user
    users = User.query.all()
    new_user_log(user_in_session, 'GET - Obtener todos los usuarios', 200)
    return jsonify([{'boleta': user.boleta, 'email': user.email, 'nombre': user.nombre} for user in users]), 200

# Obtener un usuario por boleta
@users_bp.route('/<int:boleta>', methods=['GET'])
@role_required(0, 1)  # Solo usuarios con rol 0 o 1 pueden acceder
def get_user(boleta):
    user_in_session = current_user  # Usa directamente current_user
    user = User.query.get(boleta)
    if user is None:
        new_user_log(user, 'GET - Información - Usuario no encontrado: ' + str(boleta), error_message=404)
        return jsonify({"error": "Usuario no encontrado"}), 404
    new_user_log(user_in_session, 'GET - Obtener datos: ' + str(boleta), 200)
    return jsonify({'boleta': user.boleta, 'email': user.email, 'nombre': user.nombre}), 200

# Actualizar un usuario
@users_bp.route('/<int:boleta>', methods=['PUT'])
@role_required(0, 1)  # Solo usuarios con rol 0 o 1 pueden acceder
def update_user(boleta):
    user_in_session = current_user  # Usa directamente current_user
    data = request.get_json()
    user = User.query.get(boleta)
    if user is None:
        new_user_log(user_in_session, 'PUT - Usuario no actualizado - usuario no encontrado', error_message=404)
        return jsonify({"error": "Usuario no encontrado"}), 404

    if 'email' in data:
        user.email = data.get('email', user.email)
    if 'nombre' in data:
        user.nombre = data.get('nombre', user.nombre)
    if 'password' in data:
        user.password = generate_password_hash(data['password'])
    if 'role_id' in data:
        user.role_id = data['role_id']

    db.session.commit()
    new_user_log(user_in_session, 'PUT - Datos actualizados: ' + str(boleta), 200)
    return jsonify({"message": "Usuario actualizado con éxito"}), 200

# Eliminar un usuario
@users_bp.route('/<int:boleta>', methods=['DELETE'])
@role_required(0, 1)  # Solo usuarios con rol 0 o 1 pueden acceder
def delete_user(boleta):
    user_in_session = current_user  # Usa directamente current_user
    user = User.query.get(boleta)
    if user is None:
        new_user_log(user_in_session, 'DELETE - Usuario no eliminado - usuario no encontrado', error_message=404)
        return jsonify({"error": "Usuario no encontrado"}), 404

    db.session.delete(user)
    db.session.commit()
    new_user_log(user_in_session, 'DELETE - Usuario eliminado', 200)
    return jsonify({"message": "Usuario eliminado con éxito"}), 200

# Obtener los datos públicos del usuario autenticado
@role_required(0, 1, 2, 3)
@users_bp.route('/info', methods=['GET'])
def info_user():
    user = current_user  # Usa directamente current_user
    if user is None:
        new_user_log(user, 'GET - Información - Usuario no encontrado', error_message=404)
        return jsonify({"error": "Usuario no encontrado"}), 404

    new_user_log(user, 'GET - Información', 200)
    return jsonify({
        "boleta": user.get_id(),
        "name": user.nombre,  # Asegúrate de que tengas el atributo correcto
        "email": user.email
    }), 200
