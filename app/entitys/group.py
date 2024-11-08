# 0.1 Operaciones relacionadas a grupos
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from ..db.db import Academy, Enrollment, Subject, db, Group, Semester, User, Student, Teacher
from ..logs.logs import log_api_request  
from ..authorization.decorators import role_required  

# Crear el blueprint para grupos
groups_bp = Blueprint('groups', __name__)

# Función auxiliar para obtener el usuario actual
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
                user = User.query.filter_by(id=identifier).first()  # Para administradores

    return user

#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/groups/create-group | POST | create_group | group | message, group_id | 201

# Endpoint para crear un nuevo grupo
@groups_bp.route('/create-group', methods=['POST'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1)  # Administrador (0) y Academia (1)
def create_group():
    user = get_current_user()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json()

    # Validar que se reciban los datos necesarios
    if not data or 'name' not in data or 'semester_id' not in data:
        log_api_request(user.id, "POST - Crear Grupo - Datos incompletos", 400)  # Log opcional
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        # Verificar que el semestre exista
        semester = Semester.query.get(data['semester_id'])
        if not semester:
            log_api_request(user.id, f"POST - Crear Grupo - Semestre no encontrado (ID: {data['semester_id']})", 404)
            return jsonify({"error": "Semestre no encontrado"}), 404

        # Crear el nuevo grupo
        new_group = Group(
            name=data['name'],  # Nombre del grupo (ej. "6CV1")
            semester_id=data['semester_id']  # ID del semestre asociado
        )
        
        db.session.add(new_group)
        db.session.commit()

        log_api_request(user.id, f"POST - Grupo creado, ID: {new_group.id}, Nombre: {new_group.name}", 201)  # Log opcional
        return jsonify({"message": "Grupo creado exitosamente", "group_id": new_group.id}), 201

    except IntegrityError:
        db.session.rollback()
        log_api_request(user.id, "POST - Crear Grupo - Error de integridad", 500)  # Log opcional
        return jsonify({"error": "Error al crear el grupo"}), 500

    except Exception as e:
        db.session.rollback()
        log_api_request(user.id, f"POST - Crear Grupo - Error: {str(e)}", 500)  # Log opcional
        return jsonify({"error": str(e)}), 500
 
#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/groups/ | GET | get_groups | semester_id | groups_data | 200

# Endpoint para obtener todos los grupos de un semestre
@groups_bp.route('/groups/<int:semester_id>', methods=['GET'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1)  # Administrador (0) y Academia (1)
def get_groups(semester_id):
    user = get_current_user()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Obtener todos los grupos del semestre
    groups = Group.query.filter_by(semester_id=semester_id).all()

    # Serializar los datos
    groups_data = [{
        "id": group.id,
        "name": group.name,
        "semester_id": group.semester_id
    } for group in groups]

    return jsonify(groups_data), 200
