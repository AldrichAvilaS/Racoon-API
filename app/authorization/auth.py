from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from ..db.db import User, Student, Teacher, Academy
from datetime import timedelta
import re
auth_bp = Blueprint('auth', __name__)

def detect_identifier_type(identifier):
    # Detectar si es una boleta (estudiante)
    print(identifier)
    if identifier.isdigit() and len(identifier) == 10 and identifier.startswith(('20', '19')):
        return 'student'
    # Detectar si es un RFC (profesor)
    elif re.match(r'^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$', identifier, re.IGNORECASE):
        return 'teacher'
    # Detectar si es una academy_id (asumiendo que es un número entero pero no una boleta)
    elif identifier.isdigit() and len(identifier) == 8:
        return 'academy'
    # Detectar si es un administrador (por ejemplo, 'admin' o un username específico)
    elif identifier.lower() in ['admin', 'administrator']:
        return 'admin'
    else:
        return None

# Función auxiliar para obtener el usuario actual
def get_current_user():
    identifier = get_jwt_identity()
    user = None

    # Intentar obtener al usuario según el tipo de identificador
    user_type = detect_identifier_type(identifier)
    if user_type == 'student':
        student = Student.query.filter_by(boleta=identifier).first()
        if student:
            user = student.user
    elif user_type == 'teacher':
        teacher = Teacher.query.filter_by(rfc=identifier.upper()).first()
        if teacher:
            user = teacher.user
    elif user_type == 'academy':
        academy = Academy.query.filter_by(academy_id=int(identifier)).first()
        if academy:
            user = academy.main_teacher.user
    elif user_type == 'admin':
        user = User.query.filter_by(username=identifier).first()

    return user


def get_user_role_value(user):
    if user.role.name == 'Administrador':
        return 0
    elif user.role.name == 'Academia':
        return 1
    elif user.role.name == 'Profesor':
        return 2
    elif user.role.name == 'Estudiante':
        return 3
    else:
        return None  # O puedes lanzar una excepción si el rol no es válido


# Endpoint para iniciar sesión
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'identifier' not in data or 'password' not in data:
        return jsonify({"error": "Datos incompletos"}), 400

    identifier = data['identifier']
    password = data['password']

    # Detectar el tipo de usuario
    user_type = detect_identifier_type(identifier)
    print(user_type)
    if not user_type:
        return jsonify({"error": "Identificador no válido"}), 400

    # Buscar al usuario y verificar la contraseña
    user = None
    if user_type == 'student':
        student = Student.query.filter_by(boleta=identifier).first()
        if student:
            user = student.user
            print("el usuario es student ", user)
    elif user_type == 'teacher':
        teacher = Teacher.query.filter_by(rfc=identifier.upper()).first()
        if teacher:
            user = teacher.user
            print("el usuario es teacher ", user)
    elif user_type == 'academy':
        academy = Academy.query.filter_by(academy_id=int(identifier)).first()
        if academy:
            user = academy
            print("el usuario es academy ", user)
    elif user_type == 'admin':
        user = User.query.filter_by(username=identifier).first()
        print("el usuario es admin ", user.id)
        identifier = user.id
    else:
        return jsonify({"error": "Tipo de usuario no reconocido"}), 400

    # Verificar si el usuario existe y la contraseña es correcta
    if user is None or not check_password_hash(user.password, password):
        return jsonify({"error": "Credenciales inválidas"}), 401

    # Generar el token JWT usando el identificador especializado
    access_token = create_access_token(identity=identifier, expires_delta=timedelta(days=2))
    print("identicador", identifier)
    if user_type != 'academy':
        return jsonify({
            "message": "Inicio de sesión exitoso",
            "access_token": access_token,
            "active": user.active,
            "user_type": get_user_role_value(user),
            "user_id": identifier  # Enviamos el identificador especializado
        }), 200
    else:
        return jsonify({
            "message": "Inicio de sesión exitoso",
            "access_token": access_token,
            "active": True,
            "user_type": 1,
            "user_id": identifier  # Enviamos el identificador especializado
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
