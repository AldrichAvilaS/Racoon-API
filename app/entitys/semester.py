# 0.1 Operaciones relacionadas a semestres
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_current_user, jwt_required, get_jwt_identity
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from ..db.db import Academy, Enrollment, Subject, db, Group, Semester, User, Student, Teacher
from ..logs.logs import log_api_request  
from ..authorization.decorators import role_required  


# Crear el blueprint para semestre
semester_bp = Blueprint('semester', __name__)

#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/semester/create-semester | POST | create_semester | semester | message, semester_id | 201

# Endpoint para crear un nuevo semestre
@semester_bp.route('/create-semester', methods=['POST'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1)  # Administrador (0) y Academia (1)
def create_semester():
    data = request.get_json()

    # Validar que se reciban los datos necesarios
    if not data or 'semester' not in data:
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        # Crear el nuevo semestre
        new_semester = Semester(
            semester=data['semester'],  # Nombre del semestre (ej. "2024-01")
            created_at=db.func.current_date(),  # Fecha actual de creación (solo la fecha)
            finished_at = data.get('finished_at', func.date_add(func.current_date(), text("INTERVAL 6 MONTH")))  # Fecha de finalización (opcional)
        )
        
        db.session.add(new_semester)
        db.session.commit()

        return jsonify({"message": "Semestre creado exitosamente", "semester_id": new_semester.id}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Error al crear el semestre"}), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
   


#ruta del endpoint | metodo http | funcion a ejecutar | json que recibe | variables que regresa | codigo de respuesta
#http://localhost:5000/semester/ | GET | get_semesters | No requiere datos | semesters_data | 200

# Endpoint para obtener todos los semestres
@semester_bp.route('/', methods=['GET'])
@jwt_required()  # Requiere autenticación con JWT
#@role_required(0, 1)  # Administrador (0) y Academia (1)
def get_semesters():
    # Obtener todos los semestres
    semesters = Semester.query.all()

    # Serializar los datos
    semesters_data = [{
        "id": semester.id,
        "semester": semester.semester,
        "created_at": semester.created_at,
        "finished_at": semester.finished_at
    } for semester in semesters]

    return jsonify(semesters_data), 200



