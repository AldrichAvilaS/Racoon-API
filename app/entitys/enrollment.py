from datetime import date, datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_current_user, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from ..db.db import Enrollment, Subject, db, User, Student, Teacher
from ..logs.logs import log_api_request  
from ..authorization.decorators import role_required  
from ..openstack.conteners import create_project, assigment_role

#crear el blueprint para las materias
enrollment_bp = Blueprint('enrollment', __name__)

#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/enrollment/enroll | POST | create_enrollment | enrollment | message, enrollment_id | 201

# Endpoint para crear una nueva inscripción
@enrollment_bp.route('/enroll', methods=['POST'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1)  # Administrador (0) y Academia (1)
def create_enrollment():
    user_apply = get_jwt_identity()

    if not user_apply:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json()
    print("data", data)
    # Validar que se reciban los datos necesarios
    required_fields = ['user_id', 'subject_id']
    if not data or not all(field in data for field in required_fields):
        # log_api_request(user.id, "POST - Crear Inscripción - Datos incompletos", 400)
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        # Verificar que el estudiante exista
        #obtener estudiante por boleta
        student_user = Student.query.filter_by(boleta=data['user_id']).first()
        print("student_user", student_user)

        if not student_user:  # Estudiante tiene role_id = 3
            # log_api_request(user.id, f"POST - Crear Inscripción - Estudiante no encontrado o no válido (ID: {data['user_id']})", 404)
            return jsonify({"error": "Estudiante no encontrado o no válido"}), 404

        # Verificar que la materia exista
        subject = Subject.query.filter_by(subject_name = data['subject_id']).first() 
        print(subject)

        if not subject:
            # log_api_request(user.id, f"POST - Crear Inscripción - Materia no encontrada (ID: {data['subject_id']})", 404)
            return jsonify({"error": "Materia no encontrada"}), 404

        user = User.query.filter_by(id=student_user.user_id).first()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        print("user", user)

        # Verificar si la inscripción ya existe
        existing_enrollment = Enrollment.query.filter_by(user_id=user.id, subject_id=subject.subject_id).first()
        if existing_enrollment:
            print("existing_enrollment", existing_enrollment)
            # log_api_request(user.id, f"POST - Crear Inscripción - Inscripción ya existe para el estudiante {data['user_id']} en la materia {data['subject_id']}", 400)
            return jsonify({"error": "El estudiante ya está inscrito en esta materia"}), 400

        print("antes de hacer enrollment")
        print("user.id", user.id, f"{subject.subject_name}",)
        user_id = user.id
        subject_id = subject.subject_id
        print("subject.subject_id", subject.subject_id)
        print("date.today()", date.today())
        
        # Crear la nueva inscripción
        new_enrollment = Enrollment(
            user_id=user_id,  # ID del estudiante
            enrollment_date = date.today(), #fecha de inscripcion cuando se hace
            subject_id=subject_id,  # ID de la materia
            status='active'  # Estado de la inscripción (por defecto 'active')
        )
        print("new_enrollment", new_enrollment)

        db.session.add(new_enrollment)
        db.session.commit()

        assigment_role(student_user.boleta, subject.subject_name, "student")
        # log_api_request(user.id, f"POST - Inscripción creada para el estudiante {data['user_id']} en la materia {data['subject_id']}", 201)
        return jsonify({"message": "Inscripción creada exitosamente", "enrollment_id": new_enrollment.enrollment_id}), 201

    except IntegrityError:
        db.session.rollback()
        # log_api_request(user.id, "POST - Crear Inscripción - Error de integridad", 500)
        return jsonify({"error": "Error al crear la inscripción"}), 500

    except Exception as e:
        db.session.rollback()
        print("error", e)
        # log_api_request(user.id, f"POST - Crear Inscripción - Error: {str(e)}", 500)
        return jsonify({"error": str(e)}), 500


#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/enrollment/get-enrolled-students | GET | get_enrolled_students | subject_id | students | 200
 
#Endpoint para obtener alumnos inscritos en una materia
@enrollment_bp.route('/get-enrolled-students', methods=['GET'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1, 2)  # Administrador (0), Academia (1) y Profesor (2)
def get_enrolled_students():
    user = get_current_user()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    subject_id = request.args.get('subject_id')

    if not subject_id:
        log_api_request(user.id, "GET - Obtener Alumnos Inscritos - Datos incompletos", 400)
        return jsonify({"error": "Datos incompletos"}), 400

    # Verificar que la materia exista
    subject = Subject.query.get(subject_id)
    if not subject:
        log_api_request(user.id, f"GET - Obtener Alumnos Inscritos - Materia no encontrada (ID: {subject_id})", 404)
        return jsonify({"error": "Materia no encontrada"}), 404

    # Verificar que el usuario tenga permisos para acceder a los alumnos inscritos
    if user.role_id == 2 and subject.teacher_id != user.id:  # Profesor
        log_api_request(user.id, f"GET - Obtener Alumnos Inscritos - Permiso denegado para la materia {subject_id}", 403)
        return jsonify({"error": "Permiso denegado"}), 403
    
    # Obtener los alumnos inscritos en la materia
    enrollments = Enrollment.query.filter_by(subject_id=subject_id).all()
    students = []
    for enrollment in enrollments:
        student = Student.query.filter_by(user_id=enrollment.user_id).first()
        if student:
            students.append({
                "student_id": student.student_id,
                "user_id": student.user_id,
                # "name": student.user.username,
                "email": student.user.email
            })
    
    log_api_request(user.id, f"GET - Alumnos inscritos en la materia {subject_id}", 200)
    return jsonify(students), 200


#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/enrollment/get-enrolled-subjects | GET | get_enrolled_subjects | No requiere datos | subjects | 200

#Endpoint para obtener materias inscritas por un alumno
@enrollment_bp.route('/get-enrolled-subjects', methods=['GET'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1, 3)  # Administrador (0), Academia (1) y Estudiante (3)
def get_enrolled_subjects():
    user = get_jwt_identity()

    print("user", user)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    user_id = Student.query.filter_by(boleta=user).first().user_id
    # Obtener las inscripciones del estudiante
    enrollments = Enrollment.query.filter_by(user_id=user_id).all()
    subjects = []
    for enrollment in enrollments:
        subject = Subject.query.get(enrollment.subject_id)
        if subject:
            subjects.append({
                "subject_id": subject.subject_id,
                "subject_name": subject.subject_name,
                "status": enrollment.status
            })
    print("subjects", subjects)
    # log_api_request(user.id, "GET - Materias inscritas por el estudiante", 200)
    return jsonify(subjects), 200
