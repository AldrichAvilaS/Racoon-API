from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_current_user, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from ..db.db import Academy, Enrollment, Subject, db, Group, Semester, User, Student, Teacher
from ..logs.logs import log_api_request  
from ..authorization.decorators import role_required  

#crear el blueprint para las materias
subject_bp = Blueprint('subject', __name__)


#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/subject/create-subject | POST | create_subject | subject | message, subject_id | 201
# Endpoint para crear una nueva materia
@subject_bp.route('/create-subject', methods=['POST'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1)  # Administrador (0) y Academia (1)
def create_subject():
    user = get_current_user()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json()

    # Validar que se reciban los datos necesarios
    required_fields = ['subject_name', 'academy_id', 'group_id', 'teacher_id']
    if not data or not all(field in data for field in required_fields):
        log_api_request(user.id, "POST - Crear Materia - Datos incompletos", 400)
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        # Verificar que la academia exista
        academy = Academy.query.get(data['academy_id'])
        if not academy:
            log_api_request(user.id, f"POST - Crear Materia - Academia no encontrada (ID: {data['academy_id']})", 404)
            return jsonify({"error": "Academia no encontrada"}), 404

        # Verificar que el grupo exista
        group = Group.query.get(data['group_id'])
        if not group:
            log_api_request(user.id, f"POST - Crear Materia - Grupo no encontrado (ID: {data['group_id']})", 404)
            return jsonify({"error": "Grupo no encontrado"}), 404

        # Verificar que el profesor exista y tenga el rol adecuado
        teacher_user = User.query.get(data['teacher_id'])
        if not teacher_user or teacher_user.role_id != 2:  # Profesor tiene role_id = 2
            log_api_request(user.id, f"POST - Crear Materia - Profesor no encontrado o no válido (ID: {data['teacher_id']})", 404)
            return jsonify({"error": "Profesor no encontrado o no válido"}), 404

        # Crear la nueva materia
        new_subject = Subject(
            subject_name=data['subject_name'],  # Nombre de la materia
            academy_id=data['academy_id'],  # Academia asociada
            teacher_id=data['teacher_id'],  # Profesor asignado
            group_id=data['group_id'],  # Grupo al que pertenece la materia
            description=data.get('description', ''),  # Descripción opcional de la materia
            swift_scope=data.get('swift_scope', '')  # Swift scope opcional si es necesario
        )

        db.session.add(new_subject)
        db.session.commit()

        log_api_request(user.id, f"POST - Materia creada, ID: {new_subject.subject_id}, Nombre: {new_subject.subject_name}", 201)
        return jsonify({"message": "Materia creada exitosamente", "subject_id": new_subject.subject_id}), 201

    except IntegrityError:
        db.session.rollback()
        log_api_request(user.id, "POST - Crear Materia - Error de integridad", 500)
        return jsonify({"error": "Error al crear la materia"}), 500

    except Exception as e:
        db.session.rollback()
        log_api_request(user.id, f"POST - Crear Materia - Error: {str(e)}", 500)
        return jsonify({"error": str(e)}), 500


#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/subject/subjects | GET | get_subjects | No requiere datos | subjects_data | 200
# Endpoint para obtener todas las materias de una academia
@subject_bp.route('/subjects', methods=['GET'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1)  # Administrador (0) y Academia (1)
def get_subjects():
    user = get_current_user()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Obtener todas las materias de la academia del usuario
    subjects = Subject.query.filter_by(academy_id=user.academy_id).all()

    subjects_data = []
    for subject in subjects:
        teacher = Teacher.query.filter_by(user_id=subject.teacher_id).first()
        group = Group.query.get(subject.group_id)
        subjects_data.append({
            "subject_id": subject.subject_id,
            "subject_name": subject.subject_name,
            "teacher_name": teacher.full_name,
            "group_name": group.name,
            "description": subject.description,
            "swift_scope": subject.swift_scope
        })

    log_api_request(user.id, f"GET - Obtener materias de la academia (ID: {user.academy_id})", 200)
    return jsonify(subjects_data), 200


#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/subject/subject-by-group | GET | get_subject_by_group | group_id | subject_data | 200
#endpoint para obtener una materia por grupo
@subject_bp.route('/subject-by-group', methods=['GET'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1)  # Administrador (0) y Academia (1)
def get_subject_by_group():
    user = get_current_user()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    group_id = request.args.get('group_id')

    if not group_id:
        log_api_request(user.id, "GET - Obtener Materia por Grupo - Datos incompletos", 400)
        return jsonify({"error": "Datos incompletos"}), 400

    # Verificar que el grupo exista
    group = Group.query.get(group_id)
    if not group:
        log_api_request(user.id, f"GET - Obtener Materia por Grupo - Grupo no encontrado (ID: {group_id})", 404)
        return jsonify({"error": "Grupo no encontrado"}), 404

    # Obtener la materia asociada al grupo
    subject = Subject.query.filter_by(group_id=group_id).first()
    if not subject:
        log_api_request(user.id, f"GET - Obtener Materia por Grupo - Materia no encontrada para el grupo {group_id}", 404)
        return jsonify({"error": "Materia no encontrada"}), 404

    teacher = Teacher.query.filter_by(user_id=subject.teacher_id).first()
    subject_data = {
        "subject_id": subject.subject_id,
        "subject_name": subject.subject_name,
        "teacher_name": teacher.full_name,
        "group_name": group.name,
        "description": subject.description,
        "swift_scope": subject.swift_scope
    }

    log_api_request(user.id, f"GET - Materia por Grupo (ID: {group_id})", 200)
    return jsonify(subject_data), 200


#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/subject/get-swift-scope | GET | get_swift_scope | subject_id | swift_scope | 200
#endpoint para obtener el contenedor swift_scope de una materia
@subject_bp.route('/get-swift-scope', methods=['GET'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1)  # Administrador (0) y Academia (1)
def get_swift_scope():
    user = get_current_user()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    subject_id = request.args.get('subject_id')

    if not subject_id:
        return jsonify({"error": "Datos incompletos"}), 400

    # Verificar que la materia exista
    subject = Subject.query.get(subject_id)
    if not subject:
        return jsonify({"error": "Materia no encontrada"}), 404

    return jsonify({"swift_scope": subject.swift_scope}), 200
