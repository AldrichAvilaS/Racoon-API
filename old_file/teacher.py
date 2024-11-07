from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from .db import db, Teacher, User, Role
from .logs import log_api_request
from .decorators import role_required

teacher_bp = Blueprint('teacher_bp', __name__)

def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user

# Registrar un nuevo profesor
@teacher_bp.route('/', methods=['POST'])
@jwt_required()
#@role_required(0, 1)  # Solo roles específicos pueden crear profesores
def add_teacher():
    current_user = get_current_user()
    
    data = request.get_json()
    required_fields = ['username', 'email', 'password', 'rfc']
    if not data or not all(field in data for field in required_fields):
        log_api_request(current_user.id, 'POST - Agregar Profesor - Datos incompletos', "teacher", "none", 400)
        return jsonify({"error": "Datos incompletos"}), 400

    hashed_password = generate_password_hash(data['password'])
    
    try:
        # Crear el usuario
        new_user = User(
            username=data['username'],
            email=data['email'],
            password=hashed_password,
            role_id=2  # Rol de Profesor
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Crear el registro de Teacher asociado
        new_teacher = Teacher(
            user_id=new_user.id,
            rfc=data['rfc']
        )
        db.session.add(new_teacher)
        db.session.commit()

        log_api_request(current_user.id, 'POST - Profesor creado con éxito', "teacher", str(new_teacher.user_id), 201)
        return jsonify({"message": "Profesor creado con éxito"}), 201
    except IntegrityError as e:
        db.session.rollback()
        if 'UNIQUE constraint failed' in str(e.orig):
            log_api_request(current_user.id, 'POST - Error - Email o Username en uso', "teacher", "none", 400)
            return jsonify({"error": "El email o nombre de usuario ya está en uso."}), 400
        else:
            log_api_request(current_user.id, 'POST - Error al crear profesor', "teacher", "none", 500)
            return jsonify({"error": "Error al crear el profesor."}), 500
    except Exception as e:
        db.session.rollback()
        log_api_request(current_user.id, 'POST - Error general', "teacher", "none", 500, error_message=str(e))
        return jsonify({"error": str(e)}), 500

# Obtener todos los profesores
@teacher_bp.route('/', methods=['GET'])
@jwt_required()
#@role_required(0, 1)  # Solo roles específicos pueden acceder
def get_teachers():
    current_user = get_current_user()
    # Obtenemos todos los usuarios con rol de profesor
    teachers = User.query.filter_by(role_id=2).all()
    log_api_request(current_user.id, 'GET - Obtener todos los profesores', "teacher", "none", 200)
    return jsonify([{
        'user_id': teacher.id,
        'username': teacher.username,
        'email': teacher.email,
        'rfc': teacher.teacher.rfc  # Accedemos al modelo Teacher asociado
    } for teacher in teachers]), 200

# Obtener un profesor por ID
@teacher_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
#@role_required(0, 1)  # Solo roles específicos pueden acceder
def get_teacher(user_id):
    current_user = get_current_user()
    teacher = User.query.get(user_id)
    if teacher is None or teacher.role_id != 2:
        log_api_request(current_user.id, 'GET - Profesor no encontrado', "teacher", str(user_id), 404)
        return jsonify({"error": "Profesor no encontrado"}), 404

    log_api_request(current_user.id, 'GET - Profesor encontrado', "teacher", str(user_id), 200)
    return jsonify({
        'user_id': teacher.id,
        'username': teacher.username,
        'email': teacher.email,
        'rfc': teacher.teacher.rfc
    }), 200

# Actualizar un profesor
@teacher_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
#@role_required(0, 1)  # Solo roles específicos pueden actualizar
def update_teacher(user_id):
    current_user = get_current_user()
    data = request.get_json()
    teacher = User.query.get(user_id)

    if teacher is None or teacher.role_id != 2:
        log_api_request(current_user.id, 'PUT - Profesor no encontrado', "teacher", str(user_id), 404)
        return jsonify({"error": "Profesor no encontrado"}), 404

    # Actualizar solo los campos proporcionados en la solicitud
    if 'email' in data and data['email']:
        teacher.email = data['email']
    if 'username' in data and data['username']:
        teacher.username = data['username']
    if 'password' in data and data['password']:
        teacher.password = generate_password_hash(data['password'])
    if 'rfc' in data and data['rfc']:
        teacher.teacher.rfc = data['rfc']  # Actualizamos el RFC en el modelo Teacher

    db.session.commit()
    log_api_request(current_user.id, 'PUT - Profesor actualizado con éxito', "teacher", str(user_id), 200)
    return jsonify({"message": "Profesor actualizado con éxito"}), 200

# Eliminar un profesor
@teacher_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
#@role_required(0)  # Solo usuarios con rol 0 pueden acceder
def delete_teacher(user_id):
    current_user = get_current_user()
    teacher = User.query.get(user_id)
    if teacher is None or teacher.role_id != 2:
        log_api_request(current_user.id, 'DELETE - Profesor no encontrado', "teacher", str(user_id), 404)
        return jsonify({"error": "Profesor no encontrado"}), 404

    # Eliminamos el registro en Teacher
    db.session.delete(teacher.teacher)
    # Eliminamos el usuario
    db.session.delete(teacher)
    db.session.commit()
    log_api_request(current_user.id, 'DELETE - Profesor eliminado', "teacher", str(user_id), 200)
    return jsonify({"message": "Profesor eliminado con éxito"}), 200

# Obtener información del profesor autenticado
@teacher_bp.route('/info', methods=['GET'])
@jwt_required()
#@role_required(2)  # Solo el profesor puede acceder a su información
def info_teacher():
    current_user = get_current_user()
    if current_user.role_id != 2:
        return jsonify({"error": "Acceso denegado"}), 403

    teacher = current_user
    return jsonify({
        "rfc": teacher.teacher.rfc,
        "username": teacher.username,
        "email": teacher.email,
        "active": teacher.active,
        "confirmed_at": teacher.confirmed_at
    }), 200
