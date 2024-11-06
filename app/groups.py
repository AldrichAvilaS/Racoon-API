# 0.1 Operaciones relacionadas a grupos
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from .db import Academy, Enrollment, Subject, db, Group, Semester, User, Student, Teacher
from .logs import log_api_request  
from .decorators import role_required  

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

# Endpoint para crear un nuevo grupo
@groups_bp.route('/create-group', methods=['POST'])
@jwt_required()  # Requiere autenticación con JWT
@role_required(0, 1)  # Administrador (0) y Academia (1)
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

# Endpoint para crear un nuevo semestre
@groups_bp.route('/create-semester', methods=['POST'])
@jwt_required()  # Requiere autenticación con JWT
@role_required(0, 1)  # Administrador (0) y Academia (1)
def create_semester():
    user = get_current_user()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json()

    # Validar que se reciban los datos necesarios
    if not data or 'semester' not in data:
        log_api_request(user.id, "POST - Crear Semestre - Datos incompletos", 400)  # Log opcional
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        # Crear el nuevo semestre
        new_semester = Semester(
            semester=data['semester'],  # Nombre del semestre (ej. "2024-01")
            created_at=db.func.current_timestamp(),  # Fecha actual de creación
        )
        
        db.session.add(new_semester)
        db.session.commit()

        log_api_request(user.id, f"POST - Semestre creado, ID: {new_semester.id}, Nombre: {new_semester.semester}", 201)  # Log opcional
        return jsonify({"message": "Semestre creado exitosamente", "semester_id": new_semester.id}), 201

    except IntegrityError:
        db.session.rollback()
        log_api_request(user.id, "POST - Crear Semestre - Error de integridad", 500)  # Log opcional
        return jsonify({"error": "Error al crear el semestre"}), 500

    except Exception as e:
        db.session.rollback()
        log_api_request(user.id, f"POST - Crear Semestre - Error: {str(e)}", 500)  # Log opcional
        return jsonify({"error": str(e)}), 500
    
# Endpoint para crear una nueva materia
@groups_bp.route('/create-subject', methods=['POST'])
@jwt_required()  # Requiere autenticación con JWT
@role_required(0, 1)  # Administrador (0) y Academia (1)
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
    
# Endpoint para crear una nueva academia
@groups_bp.route('/create-academy', methods=['POST'])
@jwt_required()  # Requiere autenticación con JWT
@role_required(0, 2)  # Administrador (0) y Profesor (2)
def create_academy():
    user = get_current_user()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json()

    # Validar que se reciban los datos necesarios
    required_fields = ['name', 'main_teacher_id']
    if not data or not all(field in data for field in required_fields):
        log_api_request(user.id, "POST - Crear Academia - Datos incompletos", 400)
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        # Verificar que el profesor principal (main_teacher) exista y sea un profesor
        main_teacher_user = User.query.get(data['main_teacher_id'])
        if not main_teacher_user or main_teacher_user.role_id != 2:  # Profesor tiene role_id = 2
            log_api_request(user.id, f"POST - Crear Academia - Profesor no encontrado o no válido (ID: {data['main_teacher_id']})", 404)
            return jsonify({"error": "Profesor principal no encontrado o no válido"}), 404

        # Crear la nueva academia
        new_academy = Academy(
            name=data['name'],  # Nombre de la academia
            description=data.get('description', ''),  # Descripción opcional
            main_teacher_id=data['main_teacher_id']  # Profesor principal asociado
        )

        db.session.add(new_academy)
        db.session.commit()

        log_api_request(user.id, f"POST - Academia creada, ID: {new_academy.academy_id}, Nombre: {new_academy.name}", 201)
        return jsonify({"message": "Academia creada exitosamente", "academy_id": new_academy.academy_id}), 201

    except IntegrityError:
        db.session.rollback()
        log_api_request(user.id, "POST - Crear Academia - Error de integridad", 500)
        return jsonify({"error": "Error al crear la academia"}), 500

    except Exception as e:
        db.session.rollback()
        log_api_request(user.id, f"POST - Crear Academia - Error: {str(e)}", 500)
        return jsonify({"error": str(e)}), 500
    
# Endpoint para crear una nueva inscripción
@groups_bp.route('/enroll', methods=['POST'])
@jwt_required()  # Requiere autenticación con JWT
@role_required(0, 1)  # Administrador (0) y Academia (1)
def create_enrollment():
    user = get_current_user()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json()

    # Validar que se reciban los datos necesarios
    required_fields = ['user_id', 'subject_id']
    if not data or not all(field in data for field in required_fields):
        log_api_request(user.id, "POST - Crear Inscripción - Datos incompletos", 400)
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        # Verificar que el estudiante exista
        student_user = User.query.get(data['user_id'])
        if not student_user or student_user.role_id != 3:  # Estudiante tiene role_id = 3
            log_api_request(user.id, f"POST - Crear Inscripción - Estudiante no encontrado o no válido (ID: {data['user_id']})", 404)
            return jsonify({"error": "Estudiante no encontrado o no válido"}), 404

        # Verificar que la materia exista
        subject = Subject.query.get(data['subject_id'])
        if not subject:
            log_api_request(user.id, f"POST - Crear Inscripción - Materia no encontrada (ID: {data['subject_id']})", 404)
            return jsonify({"error": "Materia no encontrada"}), 404

        # Verificar si la inscripción ya existe
        existing_enrollment = Enrollment.query.filter_by(user_id=data['user_id'], subject_id=data['subject_id']).first()
        if existing_enrollment:
            log_api_request(user.id, f"POST - Crear Inscripción - Inscripción ya existe para el estudiante {data['user_id']} en la materia {data['subject_id']}", 400)
            return jsonify({"error": "El estudiante ya está inscrito en esta materia"}), 400

        # Crear la nueva inscripción
        new_enrollment = Enrollment(
            user_id=data['user_id'],  # ID del estudiante
            subject_id=data['subject_id'],  # ID de la materia
            status=data.get('status', 'active')  # Estado de la inscripción (por defecto 'active')
        )

        db.session.add(new_enrollment)
        db.session.commit()

        log_api_request(user.id, f"POST - Inscripción creada para el estudiante {data['user_id']} en la materia {data['subject_id']}", 201)
        return jsonify({"message": "Inscripción creada exitosamente", "enrollment_id": new_enrollment.enrollment_id}), 201

    except IntegrityError:
        db.session.rollback()
        log_api_request(user.id, "POST - Crear Inscripción - Error de integridad", 500)
        return jsonify({"error": "Error al crear la inscripción"}), 500

    except Exception as e:
        db.session.rollback()
        log_api_request(user.id, f"POST - Crear Inscripción - Error: {str(e)}", 500)
        return jsonify({"error": str(e)}), 500
