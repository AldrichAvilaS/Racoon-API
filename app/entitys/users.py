from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from ..db.db import Role, db, User, Student, Teacher, Academy
from ..logs.logs import log_api_request
from ..authorization.decorators import role_required
from ..openstack.user_openstack import create_user 
users_bp = Blueprint('users', __name__)

# Función auxiliar para obtener el usuario actual basado en el identificador
def get_current_user():
    identifier = get_jwt_identity()
    user = None
    print(identifier)
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
                user = User.query.filter_by(id=identifier, role_id=get_role_id_by_name('Administrador')).first()

    return user

def get_role_id_by_name(role_name):
    role = Role.query.filter_by(name=role_name).first()
    if role:
        return role.role_id
    return None  # O puedes lanzar una excepción si el rol no existe

def get_role_name_by_value(role_value):
    role_mapping = {
        0: 'Administrador',
        1: 'Academia',
        2: 'Profesor',
        3: 'Estudiante'
    }
    return role_mapping.get(role_value, None)  # Retorna None si el valor no está en el diccionario


#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/users/ | POST | add_user | {username, email, password, role_id} | message, error | 201, 400, 500
# Registrar un nuevo usuario
# entrada:
# {
#    "username": "admin",
#    "email": "example@gmail.com",
#    "password": "root",
#    "role_id": 0
# }
# salida:
# {message: "Usuario creado con éxito"} | 201
# {error: "Datos incompletos"} | 400
# {error: "El rol con ID {role_id} no existe."} | 400
# {error: "El campo 'boleta' es obligatorio para estudiantes."} | 400
# {error: "El campo 'rfc' es obligatorio para profesores."} | 400
# {error: "El nombre de usuario o email ya está en uso."} | 400
# {error: "Error al crear el usuario."} | 500
# {error: str(e)} | 500

@users_bp.route('/', methods=['POST'])
@jwt_required()
#@role_required(0, 1, 2)  # Solo Administrador (0) o Academia (1)
def add_user():
    print("se creara un usuario")
    data = request.get_json()

    # Validar datos requeridos
    required_fields = ['username', 'email', 'role_id']
    if not data or not all(field in data for field in required_fields):
        log_api_request(get_jwt_identity(), 'POST - Agregar Usuario - Datos incompletos', "users", "none", 400)
        return jsonify({"error": "Datos incompletos"}), 400

    # Verificar si el rol existe
    print(data)
    print(data['role_id'])
    #pasar de cadena a entero
    role_id = get_role_id_by_name(get_role_name_by_value(int (data['role_id'])))
    print("role name ",get_role_name_by_value(data['role_id']))
    print("Rol del Usuario Creado",role_id)
    existing_role = Role.query.get(role_id)
    print(existing_role)
    if existing_role is None:
        log_api_request(get_jwt_identity(), 'POST - Agregar Usuario - Rol inexistente', "users", "none", 400)
        return jsonify({"error": f"El rol con ID {role_id} no existe."}), 400

    password = data.get('password')
    if isinstance(password, int):
        password = str(password)
    hashed_password = generate_password_hash(password)


    try:
        new_user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password,
        active=False,
        role_id=role_id,
        storage_limit = 2,  # Por defecto, 2 GB de almacenamiento
        openstack_id = '0'
    )
        print("se intentara en el try creara un usuario")
        db.session.add(new_user)
        db.session.commit()

        # Si el usuario es un estudiante o profesor, crear los registros correspondientes
        if role_id == get_role_id_by_name('Estudiante'):  # Estudiante
            if 'boleta' not in data:
                log_api_request(get_jwt_identity(), 'POST - Agregar Usuario - Boleta requerida para estudiantes', "users", "none", 400)
                return jsonify({"error": "El campo 'boleta' es obligatorio para estudiantes."}), 400
            print("se creara un estudiante")
            new_student = Student(
                user_id=new_user.id,
                boleta=data['boleta'],
                current_semester=1
            )
            openstack_id = create_user(data['boleta'], 'student')
            new_user.openstack_id = openstack_id
            db.session.add(new_student)
            db.session.commit()
        elif role_id == get_role_id_by_name('Profesor'):  # Profesor
            if 'rfc' not in data:
                log_api_request(get_jwt_identity(), 'POST - Agregar Usuario - RFC requerido para profesores', "users", "none", 400)
                return jsonify({"error": "El campo 'rfc' es obligatorio para profesores."}), 400
            print("se creara un profesor")
            new_teacher = Teacher(
                user_id=new_user.id,
                rfc=data['rfc']
            )
            openstack_id = create_user(data['rfc'], 'teacher')
            new_user.openstack_id = openstack_id
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

#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/users/ | GET | get_users | No requiere datos | users_data | 200
# Obtener todos los usuarios
@users_bp.route('/', methods=['GET'])
@jwt_required()
# @role_required(0, 1)  # Solo Administrador (0) o Academia (1)
def get_users():
    role_filter =  get_role_id_by_name(get_role_name_by_value(request.args.get('role', type=int)))  # Obtener el rol desde la query string

    if role_filter is not None:
        users = User.query.filter_by(role_id=role_filter).all()  # Filtrar por rol
    else:
        users = User.query.all()  # Obtener todos los usuarios si no se especifica un rol

    log_api_request(get_jwt_identity(), 'GET - Obtener todos los usuarios', "users", "none", 200)
    
    users_data = []
    for user in users:
        user_info = {
            'username': user.username,
            'email': user.email,
            'role': user.role.name
        }
        if user.role_id == get_role_id_by_name('Estudiante') and user.student:
            student = Student.query.filter_by(user_id=user.id).first()
            user_info['boleta'] = student.boleta
        if user.role_id == get_role_id_by_name('Profesor') and user.teacher:
            teacher = Teacher.query.filter_by(user_id=user.id).first()
            user_info['rfc'] = teacher.rfc
        users_data.append(user_info)

    return jsonify(users_data), 200

#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/users/<identifier> | GET | get_user | No requiere datos | user_info | 200, 404
# Obtener un usuario por identificador
@users_bp.route('/<identifier>', methods=['GET'])
@jwt_required()
#@role_required(0, 1)  # Solo Administrador (0) o Academia (1)
def get_user(identifier):

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
    print(user.role_id)
    print(get_role_id_by_name('Profesor'))
    if user.role_id == get_role_id_by_name('Estudiante'):
        user_info['boleta'] = student.boleta
    if user.role_id == get_role_id_by_name('Profesor'):
        user_info['rfc'] = teacher.rfc

    return jsonify(user_info), 200

#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/users/<identifier> | PUT | update_user | {email, username, password, boleta, rfc} | message | 200
# Actualizar un usuario
@users_bp.route('/<identifier>', methods=['PUT'])
@jwt_required()
#@role_required(0, 1)
def update_user(identifier):

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
    user.active = True
    db.session.commit()
    log_api_request(get_jwt_identity(), 'PUT - Usuario actualizado con éxito', "users", identifier, 200)
    return jsonify({"message": "Usuario actualizado con éxito"}), 200

#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/users/<identifier> | DELETE | delete_user | No requiere datos | message | 200
# Eliminar un usuario
@users_bp.route('/<identifier>', methods=['DELETE'])
@jwt_required()
#@role_required(0)
def delete_user(identifier):
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

#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/users/info | GET | info_user | No requiere datos | user_info | 200
# Obtener los datos públicos del usuario autenticado
# entrada:
# No requiere
# salida:
# {username, email, role} | 200
# {error: "Usuario no encontrado"} | 404

@users_bp.route('/info', methods=['GET'])
@jwt_required()
def info_user():
    current_user = get_current_user()
    print(current_user)
    if current_user is None:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Construir la respuesta según el rol del usuario
    user_info = {
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.name
    }

    if current_user.role_id == get_role_id_by_name('Estudiante') and current_user.student:
        student = Student.query.filter_by(user_id=current_user.id).first()
        user_info["boleta"] = student.boleta
    if current_user.role_id == get_role_id_by_name('Profesor') and current_user.teacher:
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        user_info["rfc"] = teacher.rfc

    return jsonify(user_info), 200




