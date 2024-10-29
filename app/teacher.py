from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from .db import db, Teacher
from .logs import log_api_request
from .decorators import role_required

teacher_bp = Blueprint('teacher_bp', __name__)

# Registrar un nuevo profesor
@teacher_bp.route('/', methods=['POST'])
@jwt_required()
@role_required(0, 1)  # Solo roles específicos pueden crear profesores
def add_teacher():
    current_user_id = get_jwt_identity()
    
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data or 'nombre' not in data:
        log_api_request(current_user_id, 'POST - Agregar Profesor - Datos incompletos', "teacher", "none", 400)
        return jsonify({"error": "Datos incompletos"}), 400

    hashed_password = generate_password_hash(data['password'])
    new_teacher = Teacher(
        email=data['email'],
        password=hashed_password,
        nombre=data['nombre']
    )

    try:
        db.session.add(new_teacher)
        db.session.commit()
        log_api_request(current_user_id, 'POST - Profesor creado con éxito', "teacher", str(new_teacher.id), 201)
        return jsonify({"message": "Profesor creado con éxito"}), 201
    except IntegrityError as e:
        db.session.rollback()
        if 'Duplicate entry' in str(e.orig):
            log_api_request(current_user_id, 'POST - Error - Email en uso', "teacher", "none", 400)
            return jsonify({"error": "El email ya está en uso."}), 400
        else:
            log_api_request(current_user_id, 'POST - Error al crear profesor', "teacher", "none", 500)
            return jsonify({"error": "Error al crear el profesor."}), 500
    except Exception as e:
        db.session.rollback()
        log_api_request(current_user_id, 'POST - Error general', "teacher", "none", 500, error_message=str(e))
        return jsonify({"error": str(e)}), 500

# Obtener todos los profesores
@teacher_bp.route('/', methods=['GET'])
@jwt_required()
@role_required(0, 1)  # Solo roles específicos pueden acceder
def get_teachers():
    current_user_id = get_jwt_identity()
    teachers = Teacher.query.all()
    log_api_request(current_user_id, 'GET - Obtener todos los profesores', "teacher", "none", 200)
    return jsonify([{'id': teacher.id, 'email': teacher.email, 'nombre': teacher.nombre} for teacher in teachers]), 200

# Obtener un profesor por ID
@teacher_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@role_required(0, 1)  # Solo roles específicos pueden acceder
def get_teacher(id):
    current_user_id = get_jwt_identity()
    teacher = Teacher.query.get(id)
    if teacher is None:
        log_api_request(current_user_id, 'GET - Profesor no encontrado', "teacher", str(id), 404)
        return jsonify({"error": "Profesor no encontrado"}), 404

    log_api_request(current_user_id, 'GET - Profesor encontrado', "teacher", str(id), 200)
    return jsonify({'id': teacher.id, 'email': teacher.email, 'nombre': teacher.nombre}), 200

# Actualizar un profesor
@teacher_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@role_required(0, 1)  # Solo roles específicos pueden actualizar
def update_teacher(id):
    current_user_id = get_jwt_identity()
    data = request.get_json()
    teacher = Teacher.query.get(id)

    if teacher is None:
        log_api_request(current_user_id, 'PUT - Profesor no encontrado', "teacher", str(id), 404)
        return jsonify({"error": "Profesor no encontrado"}), 404

    # Actualizar solo los campos proporcionados en la solicitud
    if 'email' in data and data['email'] is not None:
        teacher.email = data['email']
    if 'nombre' in data and data['nombre'] is not None:
        teacher.nombre = data['nombre']
    if 'password' in data and data['password'] is not None:
        teacher.password = generate_password_hash(data['password'])

    db.session.commit()
    log_api_request(current_user_id, 'PUT - Profesor actualizado con éxito', "teacher", str(id), 200)
    return jsonify({"message": "Profesor actualizado con éxito"}), 200

# Eliminar un profesor
@teacher_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@role_required(0)  # Solo usuarios con rol 0 pueden acceder
def delete_teacher(id):
    current_user_id = get_jwt_identity()
    teacher = Teacher.query.get(id)
    if teacher is None:
        log_api_request(current_user_id, 'DELETE - Profesor no encontrado', "teacher", str(id), 404)
        return jsonify({"error": "Profesor no encontrado"}), 404

    db.session.delete(teacher)
    db.session.commit()
    log_api_request(current_user_id, 'DELETE - Profesor eliminado', "teacher", str(id), 200)
    return jsonify({"message": "Profesor eliminado con éxito"}), 200

@teacher_bp.route('/info', methods=['GET'])
@jwt_required()
@role_required(0, 1, 2, 3)  # Permitir acceso a múltiples roles si es necesario
def info_teacher():
    teacher_id = get_jwt_identity()  # Obtener el ID del profesor autenticado
    teacher = Teacher.query.get(teacher_id)

    if teacher is None:
        log_api_request(teacher_id, 'GET - Información del profesor no encontrada', "teacher", str(teacher_id), 404)
        return jsonify({"error": "Profesor no encontrado"}), 404

    #log_api_request(teacher_id, 'GET - Información del profesor obtenida', "teacher", str(teacher_id), 200)
    return jsonify({
        "id": teacher.id,
        "nombre": teacher.nombre,
        "email": teacher.email,
        "active": teacher.active,
        "confirmed_at": teacher.confirmed_at
    }), 200
