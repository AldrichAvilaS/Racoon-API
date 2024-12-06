from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_current_user, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from ..db.db import Academy, Enrollment, Subject, db, Group, Semester, User, Student, Teacher
from ..logs.logs import log_api_request  
from ..authorization.decorators import role_required  
from ..openstack.conteners import create_project, assigment_role
from . group import create_group_inner_api
#crear el blueprint para las materias
subject_bp = Blueprint('subject', __name__)


#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/subject/create-subject | POST | create_subject | subject | message, subject_id | 201
# Endpoint para crear una nueva materia
@subject_bp.route('/create-subject', methods=['POST'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1)  # Administrador (0) y Academia (1)
def create_subject():
    user = get_jwt_identity()
    
    print("user", get_jwt_identity())
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json()
    print("data: ", data)
    # Validar que se reciban los datos necesarios
    required_fields = ['subject_name','group_id']
    if not data or not all(field in data for field in required_fields):
        # log_api_request(user.id, "POST - Crear Materia - Datos incompletos", 400)
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        print("se intentara crear la materia")
        # Verificar que la academia exista
        academy = user 
        if not academy:
            # log_api_request(user.id, f"POST - Crear Materia - Academia no encontrada (ID: {data['academy_id']})", 404)
            return jsonify({"error": "Academia no encontrada"}), 404
        print("la academia se verifico", academy)

        try:
            # Verificar que el grupo exista si no lo crea
            group = Group.query.filter_by(name=data['group_id']).first()
            if not group:
                group = create_group_inner_api(data['group_id'])
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "Error al crear el grupo inexistente"}), 500


        print("el grupo se verifico", group)
        
        print("se intentara verificar el profesor")
        
        teacher_id = data.get('teacher_id', 'XXXX000000XX0')
        if teacher_id == '':
            teacher_id = 'XXXX000000XX0'

        print("teacher_id", teacher_id)
        # Verificar que el profesor exista y tenga el rol adecuado
        teacher_user = Teacher.query.filter_by(rfc=teacher_id).first()
        # teacher_user = Teacher.query.get(teacher_id)
        print("teacher_user", teacher_user)
        print("teacher_user.rfc", teacher_user.rfc)
        if not teacher_user:  
            # log_api_request(user.id, f"POST - Crear Materia - Profesor no encontrado o no válido (ID: {data['teacher_id']})", 404)
            return jsonify({"error": "Profesor no encontrado o no válido"}), 404
        
        print("el profesor se verifico", teacher_user.user_id)
        
        print("se intentara crear el proyecto")

        semester = Semester.query.filter_by(id=group.semester_id).first()
        
        project_name = f"{semester.semester}_{group.name}_{data['subject_name']}"
        print("project name: ", project_name)

        swift_account = create_project(project_name)
        swift_account = swift_account['account']
        print("swift_account ", swift_account)
        # Crear la nueva materia
        new_subject = Subject(
            subject_name=project_name,  # Nombre de la materia
            academy_id=academy,  # Academia asociada
            teacher_id=teacher_user.user_id,  # Profesor asignado
            group_id=group.id,  # Grupo al que pertenece la materia
            description=data.get('description', data['subject_name'])
        )

        db.session.add(new_subject)
        db.session.commit()
        assigment_role(academy, project_name, "academy")
        if not teacher_id == 'XXXX000000XX0':
            assigment_role(teacher_user.rfc, project_name, "teacher")

        # log_api_request(user.id, f"POST - Materia creada, ID: {new_subject.subject_id}, Nombre: {new_subject.subject_name}", 201)
        return jsonify({"message": "Materia creada exitosamente", "subject_id": new_subject.subject_id}), 201

    except IntegrityError:
        db.session.rollback()
        # log_api_request(user.id, "POST - Crear Materia - Error de integridad", 500)
        return jsonify({"error": "Error al crear la materia"}), 500

    except Exception as e:
        db.session.rollback()
        # log_api_request(user.id, f"POST - Crear Materia - Error: {str(e)}", 500)
        return jsonify({"error": str(e)}), 500


#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/subject/subjects | GET | get_subjects | No requiere datos | subjects_data | 200
# Endpoint para obtener todas las materias de una academia
@subject_bp.route('/subjects', methods=['GET'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1)  # Administrador (0) y Academia (1)
def get_subjects():
    print("se intentara obtener las materias de la academia: ")
    user= get_jwt_identity()
    # user = get_current_user()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    print("user", user)
    # Obtener todas las materias de la academia de  l usuario
    subjects = Subject.query.filter_by(academy_id=user).all()

    subjects_data = []
    for subject in subjects:
        teacher = Teacher.query.filter_by(user_id=subject.teacher_id).first()
        group = Group.query.get(subject.group_id)
        teacher_user = User.query.get(teacher.user_id)
        subjects_data.append({
            "subject_id": subject.subject_id,
            "subject_name": subject.subject_name,
            "teacher_name": teacher_user.username,
            "group_name": group.name,
            "description": subject.description
        })
        # print("subjects_data", subjects_data)

    # log_api_request(user.id, f"GET - Obtener materias de la academia (ID: {user.academy_id})", 200)
    return jsonify(subjects_data), 200

#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/subject/subjects | GET | get_subjects | No requiere datos | subjects_data | 200
# Endpoint para obtener todas las materias de una academia
@subject_bp.route('/subjects-teacher', methods=['GET'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1)  # Administrador (0) y Academia (1)
def get_subjects_by_teacher():
    print("se intentara obtener las materias de la academia: ")
    user= get_jwt_identity()
    # user = get_current_user()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    print("user", user)
    # Obtener todas las materias de la academia de  l usuario
    teacher = Teacher.query.filter_by(rfc=user).first()
    subjects = Subject.query.filter_by(teacher_id=teacher.user_id).all()

    subjects_data = []
    for subject in subjects:
        teacher = Teacher.query.filter_by(user_id=subject.teacher_id).first()
        group = Group.query.get(subject.group_id)
        teacher_user = User.query.get(teacher.user_id)
        subjects_data.append({
            "subject_id": subject.subject_id,
            "subject_name": subject.subject_name,
            "teacher_name": teacher_user.username,
            "group_name": group.name,
            "description": subject.description
        })
        # print("subjects_data", subjects_data)
    
    # log_api_request(user.id, f"GET - Obtener materias de la academia (ID: {user.academy_id})", 200)
    return jsonify(subjects_data), 200

#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/subject/subject-by-group | GET | get_subject_by_group | group_id | subject_data | 200
#endpoint para obtener una materia por grupo
@subject_bp.route('/subject-by-group', methods=['GET'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1)  # Administrador (0) y Academia (1)
def get_subject_by_group():
    user = get_jwt_identity()

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
        "description": subject.description
    }

    log_api_request(user.id, f"GET - Materia por Grupo (ID: {group_id})", 200)
    return jsonify(subject_data), 200

#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/subject/subject-by-id | GET | get_subject_by_id | subject_id | subject_data | 200
#endpoint para obtener los alumnos de una materia
@subject_bp.route('/subject-by-id', methods=['POST'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1)  # Administrador (0) y Academia (1)
def get_subject_by_id():
    user = get_jwt_identity()
    print("user", user)
    print("obtener alumnos de una materia")
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json()
    print("data", data)
    subject_id = data['subject_id']
    # subject_id = data('subject_id')

    if not subject_id:
        return jsonify({"error": "Datos incompletos"}), 400

    # Verificar que la materia exista
    subject = Subject.query.get(subject_id)
    if not subject:
        return jsonify({"error": "Materia no encontrada"}), 404

    teacher = Teacher.query.filter_by(user_id=subject.teacher_id).first()
    group = Group.query.get(subject.group_id)
    #obtener lista de alumnos inscritos en la materia
    students = Enrollment.query.filter_by(subject_id=subject_id).all()
    students_data = []
    for student in students:
        user = User.query.get(student.user_id)
        student_user = Student.query.get(student.user_id)
        students_data.append({
            "student_id": student_user.boleta,
            "full_name": user.username,
            "email": user.email,
            "group": group.name
        })
    
    

    return jsonify(students_data), 200



#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/subject/get-swift-scope | GET | get_swift_scope | subject_id | swift_scope | 200
#endpoint para obtener el contenedor swift_scope de una materia
@subject_bp.route('/get-swift-scope', methods=['GET'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1)  # Administrador (0) y Academia (1)
def get_swift_scope():
    user = get_jwt_identity()

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

def get_group_full_name(subject_id):
    subject = Subject.query.get(subject_id)
    group = Group.query.get(subject.group_id)
    semester = Semester.query.get(group.semester_id)
    return f"{semester.name}_{group.name}_{subject.subject_name}"