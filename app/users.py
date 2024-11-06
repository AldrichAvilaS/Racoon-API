from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from .db import Role, db, User, Student, Teacher, Academy
from .logs import log_api_request
from .decorators import role_required

users_bp = Blueprint('users', __name__)

# Función auxiliar para obtener el usuario actual basado en el identificador
def get_current_user():
    identifier = get_jwt_identity()
    user = None

    # Buscar al usuario según el identificador
    student = Student.query.filter_by(boleta=identifier).first()
    if student:
        user = student.user
    else:
        teacher = Teacher.query.filter_by(rfc=identifier).first()
        if teacher:
            user = teacher.user
        else:
            academy = Academy.query.filter_by(academy_id=identifier).first()
            if academy:
                user = academy.main_teacher.user
            else:
                # Asumimos que los administradores se autentican con user.id
                user = User.query.filter_by(id=identifier, role_id=0).first()

    return user

# Registrar un nuevo usuario
@users_bp.route('/', methods=['POST'])
@jwt_required()
@role_required(0, 1)  # Solo Administrador (0) o Academia (1)
def add_user():
    current_user = get_current_user()

    data = request.get_json()

    # Validar datos requeridos
    required_fields = ['username', 'email', 'password', 'role_id']
    if not data or not all(field in data for field in required_fields):
        log_api_request(get_jwt_identity(), 'POST - Agregar Usuario - Datos incompletos', "users", "none", 400)
        return jsonify({"error": "Datos incompletos"}), 400

    # Verificar si el rol existe
    role_id = data['role_id']
    existing_role = Role.query.get(role_id)
    if existing_role is None:
        log_api_request(get_jwt_identity(), 'POST - Agregar Usuario - Rol inexistente', "users", "none", 400)
        return jsonify({"error": f"El rol con ID {role_id} no existe."}), 400

    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password,
        active=True,
        role_id=role_id
    )

    try:
        db.session.add(new_user)
        db.session.commit()

        # Si el usuario es un estudiante o profesor, crear los registros correspondientes
        if role_id == 3:  # Estudiante
            if 'boleta' not in data:
                log_api_request(get_jwt_identity(), 'POST - Agregar Usuario - Boleta requerida para estudiantes', "users", "none", 400)
                return jsonify({"error": "El campo 'boleta' es obligatorio para estudiantes."}), 400
            new_student = Student(
                user_id=new_user.id,
                boleta=data['boleta'],
                current_semester=data.get('current_semester')
            )
            db.session.add(new_student)
            db.session.commit()
        elif role_id == 2:  # Profesor
            if 'rfc' not in data:
                log_api_request(get_jwt_identity(), 'POST - Agregar Usuario - RFC requerido para profesores', "users", "none", 400)
                return jsonify({"error": "El campo 'rfc' es obligatorio para profesores."}), 400
            new_teacher = Teacher(
                user_id=new_user.id,
                rfc=data['rfc']
            )
            db.session.add(new_teacher)
            db.session.commit()

        log_api_request(get_jwt_identity(), 'POST - Usuario creado con éxito', "users", "none", 201)
        return jsonify({"message": "Usuario creado con éxito"}), 201
    except IntegrityError as e:
        db.session.rollback()
        if 'UNIQUE constraint failed' in str(e.orig):
            log_api_request(get_jwt_identity(), 'POST - Error - Username o email en uso', "users", "none", 400)
            return jsonify({"error": "El nombre de usuario o email ya está en uso."}), 400
        else:
            log_api_request(get_jwt_identity(), 'POST - Error al crear usuario', "users", "none", 500)
            return jsonify({"error": "Error al crear el usuario."}), 500
    except Exception as e:
        db.session.rollback()
        log_api_request(get_jwt_identity(), 'POST - Error general', "users", "none", 500, error_message=str(e))
        return jsonify({"error": str(e)}), 500

# Obtener todos los usuarios
@users_bp.route('/', methods=['GET'])
@jwt_required()
@role_required(0, 1)  # Solo Administrador (0) o Academia (1)
def get_users():
    current_user = get_current_user()
    users = User.query.all()
    log_api_request(get_jwt_identity(), 'GET - Obtener todos los usuarios', "users", "none", 200)
    users_data = []
    for user in users:
        user_info = {
            'username': user.username,
            'email': user.email,
            'role': user.role.name
        }
        if user.role_id == 3 and user.student:
            user_info['boleta'] = user.student.boleta
        if user.role_id == 2 and user.teacher:
            user_info['rfc'] = user.teacher.rfc
        users_data.append(user_info)
    return jsonify(users_data), 200

# Obtener un usuario por identificador
@users_bp.route('/<identifier>', methods=['GET'])
@jwt_required()
@role_required(0, 1)  # Solo Administrador (0) o Academia (1)
def get_user(identifier):
    current_user = get_current_user()
    user = None

    # Buscar al usuario según el identificador
    student = Student.query.filter_by(boleta=identifier).first()
    if student:
        user = student.user
    else:
        teacher = Teacher.query.filter_by(rfc=identifier).first()
        if teacher:
            user = teacher.user
        else:
            # No se puede obtener un administrador o academia por identificador en este endpoint
            return jsonify({"error": "Usuario no encontrado"}), 404

    if user is None:
        log_api_request(get_jwt_identity(), 'GET - Usuario no encontrado', "users", identifier, 404)
        return jsonify({"error": "Usuario no encontrado"}), 404

    log_api_request(get_jwt_identity(), 'GET - Usuario encontrado', "users", identifier, 200)
    user_info = {
        'username': user.username,
        'email': user.email,
        'role': user.role.name
    }
    if user.role_id == 3 and user.student:
        user_info['boleta'] = user.student.boleta
    if user.role_id == 2 and user.teacher:
        user_info['rfc'] = user.teacher.rfc

    return jsonify(user_info), 200

# Actualizar un usuario
@users_bp.route('/<identifier>', methods=['PUT'])
@jwt_required()
@role_required(0, 1)
def update_user(identifier):
    current_user = get_current_user()
    data = request.get_json()
    user = None

    # Buscar al usuario según el identificador
    student = Student.query.filter_by(boleta=identifier).first()
    if student:
        user = student.user
    else:
        teacher = Teacher.query.filter_by(rfc=identifier).first()
        if teacher:
            user = teacher.user
        else:
            # No se puede actualizar un administrador o academia por identificador en este endpoint
            return jsonify({"error": "Usuario no encontrado"}), 404

    if user is None:
        log_api_request(get_jwt_identity(), 'PUT - Usuario no encontrado', "users", identifier, 404)
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Actualizar solo los campos proporcionados
    if 'email' in data and data['email']:
        user.email = data['email']
    if 'username' in data and data['username']:
        user.username = data['username']
    if 'password' in data and data['password']:
        user.password = generate_password_hash(data['password'])
    # No se permite cambiar el role_id directamente
    if user.role_id == 3 and 'boleta' in data and data['boleta']:
        user.student.boleta = data['boleta']
    if user.role_id == 2 and 'rfc' in data and data['rfc']:
        user.teacher.rfc = data['rfc']

    db.session.commit()
    log_api_request(get_jwt_identity(), 'PUT - Usuario actualizado con éxito', "users", identifier, 200)
    return jsonify({"message": "Usuario actualizado con éxito"}), 200

# Eliminar un usuario
@users_bp.route('/<identifier>', methods=['DELETE'])
@jwt_required()
@role_required(0)
def delete_user(identifier):
    current_user = get_current_user()
    user = None

    # Buscar al usuario según el identificador
    student = Student.query.filter_by(boleta=identifier).first()
    if student:
        user = student.user
    else:
        teacher = Teacher.query.filter_by(rfc=identifier).first()
        if teacher:
            user = teacher.user
        else:
            # No se puede eliminar un administrador o academia por identificador en este endpoint
            return jsonify({"error": "Usuario no encontrado"}), 404

    if user is None:
        log_api_request(get_jwt_identity(), 'DELETE - Usuario no encontrado', "users", identifier, 404)
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Eliminar registros asociados
    if user.role_id == 3 and user.student:
        db.session.delete(user.student)
    if user.role_id == 2 and user.teacher:
        db.session.delete(user.teacher)

    db.session.delete(user)
    db.session.commit()
    log_api_request(get_jwt_identity(), 'DELETE - Usuario eliminado', "users", identifier, 200)
    return jsonify({"message": "Usuario eliminado con éxito"}), 200

# Obtener los datos públicos del usuario autenticado
@users_bp.route('/info', methods=['GET'])
@jwt_required()
def info_user():
    current_user = get_current_user()

    if current_user is None:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Construir la respuesta según el rol del usuario
    user_info = {
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.name
    }

    if current_user.role_id == 3 and current_user.student:
        user_info["boleta"] = current_user.student.boleta
    if current_user.role_id == 2 and current_user.teacher:
        user_info["rfc"] = current_user.teacher.rfc

    return jsonify(user_info), 200

# ------------------------------
# Endpoints para Gestión de Academias
# ------------------------------

# Crear una nueva academia
@users_bp.route('/academies', methods=['POST'])
@jwt_required()
@role_required(0)  # Solo administradores pueden crear academias
def create_academy():
    current_user = get_current_user()
    data = request.get_json()

    # Validar datos requeridos
    required_fields = ['name', 'main_teacher_rfc']
    if not data or not all(field in data for field in required_fields):
        log_api_request(get_jwt_identity(), 'POST - Crear Academia - Datos incompletos', "academies", "none", 400)
        return jsonify({"error": "Datos incompletos"}), 400

    # Verificar que el profesor principal exista y sea un profesor
    main_teacher = Teacher.query.filter_by(rfc=data['main_teacher_rfc']).first()
    if not main_teacher:
        log_api_request(get_jwt_identity(), 'POST - Crear Academia - Profesor principal no encontrado', "academies", "none", 404)
        return jsonify({"error": "Profesor principal no encontrado"}), 404

    # Crear la nueva academia
    new_academy = Academy(
        name=data['name'],
        description=data.get('description', ''),
        main_teacher_id=main_teacher.user_id  # Asignar el user_id del profesor principal
    )

    try:
        db.session.add(new_academy)
        db.session.commit()
        log_api_request(get_jwt_identity(), 'POST - Academia creada con éxito', "academies", str(new_academy.academy_id), 201)
        return jsonify({"message": "Academia creada con éxito", "academy_id": new_academy.academy_id}), 201
    except IntegrityError as e:
        db.session.rollback()
        log_api_request(get_jwt_identity(), 'POST - Error al crear academia', "academies", "none", 500)
        return jsonify({"error": "Error al crear la academia."}), 500
    except Exception as e:
        db.session.rollback()
        log_api_request(get_jwt_identity(), 'POST - Error general', "academies", "none", 500, error_message=str(e))
        return jsonify({"error": str(e)}), 500

# Obtener todas las academias
@users_bp.route('/academies', methods=['GET'])
@jwt_required()
@role_required(0, 1)  # Administradores y academias pueden acceder
def get_academies():
    current_user = get_current_user()
    academies = Academy.query.all()
    log_api_request(get_jwt_identity(), 'GET - Obtener todas las academias', "academies", "none", 200)
    academies_data = [{
        'academy_id': academy.academy_id,
        'name': academy.name,
        'description': academy.description,
        'main_teacher_rfc': academy.main_teacher.teacher.rfc  # Obtener el RFC del profesor principal
    } for academy in academies]
    return jsonify(academies_data), 200

# Obtener una academia por ID
@users_bp.route('/academies/<int:academy_id>', methods=['GET'])
@jwt_required()
@role_required(0, 1)
def get_academy(academy_id):
    current_user = get_current_user()
    academy = Academy.query.get(academy_id)
    if not academy:
        log_api_request(get_jwt_identity(), 'GET - Academia no encontrada', "academies", str(academy_id), 404)
        return jsonify({"error": "Academia no encontrada"}), 404

    log_api_request(get_jwt_identity(), 'GET - Academia encontrada', "academies", str(academy_id), 200)
    academy_data = {
        'academy_id': academy.academy_id,
        'name': academy.name,
        'description': academy.description,
        'main_teacher_rfc': academy.main_teacher.teacher.rfc
    }
    return jsonify(academy_data), 200

# Actualizar una academia
@users_bp.route('/academies/<int:academy_id>', methods=['PUT'])
@jwt_required()
@role_required(0, 1)
def update_academy(academy_id):
    current_user = get_current_user()
    data = request.get_json()
    academy = Academy.query.get(academy_id)
    if not academy:
        log_api_request(get_jwt_identity(), 'PUT - Academia no encontrada', "academies", str(academy_id), 404)
        return jsonify({"error": "Academia no encontrada"}), 404

    # Actualizar campos proporcionados
    if 'name' in data and data['name']:
        academy.name = data['name']
    if 'description' in data:
        academy.description = data['description']
    if 'main_teacher_rfc' in data and data['main_teacher_rfc']:
        # Verificar que el nuevo profesor principal exista
        main_teacher = Teacher.query.filter_by(rfc=data['main_teacher_rfc']).first()
        if not main_teacher:
            return jsonify({"error": "Profesor principal no encontrado"}), 404
        academy.main_teacher_id = main_teacher.user_id

    db.session.commit()
    log_api_request(get_jwt_identity(), 'PUT - Academia actualizada con éxito', "academies", str(academy_id), 200)
    return jsonify({"message": "Academia actualizada con éxito"}), 200

# Eliminar una academia
@users_bp.route('/academies/<int:academy_id>', methods=['DELETE'])
@jwt_required()
@role_required(0)  # Solo administradores pueden eliminar academias
def delete_academy(academy_id):
    current_user = get_current_user()
    academy = Academy.query.get(academy_id)
    if not academy:
        log_api_request(get_jwt_identity(), 'DELETE - Academia no encontrada', "academies", str(academy_id), 404)
        return jsonify({"error": "Academia no encontrada"}), 404

    db.session.delete(academy)
    db.session.commit()
    log_api_request(get_jwt_identity(), 'DELETE - Academia eliminada', "academies", str(academy_id), 200)
    return jsonify({"message": "Academia eliminada con éxito"}), 200

# Obtener información de la academia autenticada
@users_bp.route('/academies/info', methods=['GET'])
@jwt_required()
@role_required(1)  # Solo academias pueden acceder
def info_academy():
    current_user = get_current_user()
    academy = Academy.query.filter_by(academy_id=get_jwt_identity()).first()
    if not academy:
        return jsonify({"error": "Academia no encontrada"}), 404

    academy_data = {
        'academy_id': academy.academy_id,
        'name': academy.name,
        'description': academy.description,
        'main_teacher_rfc': academy.main_teacher.teacher.rfc
    }
    return jsonify(academy_data), 200