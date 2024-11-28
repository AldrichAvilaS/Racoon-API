from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_current_user, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from ..db.db import Academy, Enrollment, Subject, db, Group, Semester, User, Student, Teacher
from werkzeug.security import generate_password_hash
from ..logs.logs import log_api_request  
from ..authorization.decorators import role_required  

#crear el blueprint para las academias

academy_bp = Blueprint('academy', __name__)

#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/academy/ | POST | create_academy | academy | message, academy_id | 201

# Crear una nueva academia
@academy_bp.route('/', methods=['POST'])
@jwt_required()
#@role_required(0,1)  # Solo administradores pueden crear academias
def create_academy():
    data = request.get_json()

    # Validar datos requeridos
    required_fields = ['name', 'main_teacher_rfc']
    if not data or not all(field in data for field in required_fields):
        # log_api_request(get_jwt_identity(), 'POST - Crear Academia - Datos incompletos', "academies", "none", 400)
        return jsonify({"error": "Datos incompletos"}), 400

    # Verificar que el profesor principal exista y sea un profesor
    main_teacher = Teacher.query.filter_by(rfc=data['main_teacher_rfc']).first()
    if not main_teacher:
        # log_api_request(get_jwt_identity(), 'POST - Crear Academia - Profesor principal no encontrado', "academies", "none", 404)
        return jsonify({"error": "Profesor principal no encontrado"}), 404

    # Crear la nueva academia
    new_academy = Academy(
        name=data['name'],
        description=data.get('description', data['name']),  # Descripción opcional, si no se proporciona se usa el nombre
        main_teacher_id=main_teacher.user_id,  # Asignar el user_id del profesor principal
        password=generate_password_hash(data['name'])
    )

    try:
        db.session.add(new_academy)
        #crear la academia en openstack
        create_academy(new_academy.academy_id)
        db.session.commit()
        # log_api_request(get_jwt_identity(), 'POST - Academia creada con éxito', "academies", str(new_academy.academy_id), 201)
        return jsonify({"message": "Academia creada con éxito", "academy_id": new_academy.academy_id}), 201
    except IntegrityError as e:
        db.session.rollback()
        log_api_request(get_jwt_identity(), 'POST - Error al crear academia', "academies", "none", 500)
        return jsonify({"error": "Error al crear la academia."}), 500
    except Exception as e:
        db.session.rollback()
        log_api_request(get_jwt_identity(), 'POST - Error general', "academies", "none", 500, error_message=str(e))
        return jsonify({"error": str(e)}), 500
    
#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/academy/ | GET | get_academies | No requiere datos | academies_data | 200

# Obtener todas las academias
@academy_bp.route('/', methods=['GET'])
@jwt_required()
# @role_required(0, 1)  # Administradores y academias pueden acceder
def get_academies():
    try:
        academies = Academy.query.all()
        log_api_request(get_jwt_identity(), 'GET - Obtener todas las academias', "academies", "none", 200)
        
        academies_data = []
        for academy in academies:
            # Verificar si hay un profesor principal
            main = Teacher.query.filter_by(user_id=academy.main_teacher_id).first() 
            main_teacher_rfc = main.rfc
            
            academy_info = {
                'academy_id': academy.academy_id,
                'name': academy.name,
                'description': academy.description,
                'main_teacher_rfc': main_teacher_rfc  # Obtener el RFC del profesor principal
            }
            academies_data.append(academy_info)

        return jsonify(academies_data), 200
    
    except Exception as e:
        log_api_request(get_jwt_identity(), 'GET - Error al obtener academias', "academies", "none", 500, error_message=str(e))
        return jsonify({"error": "Error al obtener academias."}), 500

#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/academy/<int:academy_id> | GET | get_academy | No requiere datos | academy_data | 200
# Obtener una academia por ID
@academy_bp.route('/<int:academy_id>', methods=['GET'])
@jwt_required()
# @role_required(0, 1)
def get_academy(academy_id):
    try:
        academy = Academy.query.get(academy_id)
        if not academy:
            log_api_request(get_jwt_identity(), 'GET - Academia no encontrada', "academies", str(academy_id), 404)
            return jsonify({"error": "Academia no encontrada"}), 404

        # Verificar si hay un profesor principal
        main = Teacher.query.filter_by(user_id=academy.main_teacher_id).first() 
        main_teacher_rfc = main.rfc if main else None  # Manejar el caso donde no hay profesor principal

        log_api_request(get_jwt_identity(), 'GET - Academia encontrada', "academies", str(academy_id), 200)
        academy_data = {
            'academy_id': academy.academy_id,
            'name': academy.name,
            'description': academy.description,
            'main_teacher_rfc': main_teacher_rfc  # Obtener el RFC del profesor principal
        }
        return jsonify(academy_data), 200
    
    except Exception as e:
        log_api_request(get_jwt_identity(), 'GET - Error al obtener academia', "academies", str(academy_id), 500, error_message=str(e))
        return jsonify({"error": "Error al obtener la academia."}), 500

#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/academy/<int:academy_id> | PUT | update_academy | academy | message | 200
# Actualizar una academia
@academy_bp.route('/<int:academy_id>', methods=['PUT'])
@jwt_required()
#@role_required(0, 1)
def update_academy(academy_id):
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


#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/academy/<int:academy_id> | DELETE | delete_academy | No requiere datos | message | 200

# Eliminar una academia
@academy_bp.route('/<int:academy_id>', methods=['DELETE'])
@jwt_required()
#@role_required(0)  # Solo administradores pueden eliminar academias
def delete_academy(academy_id):
    academy = Academy.query.get(academy_id)
    if not academy:
        log_api_request(get_jwt_identity(), 'DELETE - Academia no encontrada', "academies", str(academy_id), 404)
        return jsonify({"error": "Academia no encontrada"}), 404

    db.session.delete(academy)
    db.session.commit()
    log_api_request(get_jwt_identity(), 'DELETE - Academia eliminada', "academies", str(academy_id), 200)
    return jsonify({"message": "Academia eliminada con éxito"}), 200


#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/academy/info | GET | info_academy | No requiere datos | academy_data | 200

# Obtener información de la academia autenticada
@academy_bp.route('/info', methods=['GET'])
@jwt_required()
#@role_required(1)  # Solo academias pueden acceder
def info_academy():
    academy = Academy.query.filter_by(academy_id=get_jwt_identity()).first()
    if not academy:
        return jsonify({"error": "Academia no encontrada"}), 404

    teacher = Teacher.query.filter_by(user_id=academy.main_teacher_id).first()
    academy_data = {
        'academy_id': academy.academy_id,
        'name': academy.name,
        'description': academy.description,
        'main_teacher_rfc': teacher.rfc
    }
    return jsonify(academy_data), 200