from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from .db import User, Student, Teacher, Academy, Role

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @jwt_required()  # Asegura que el usuario esté autenticado con JWT
        def decorated_function(*args, **kwargs):
            # Obtener la identidad desde el token JWT
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
                    # Si es academia, el identificador será el academy_id
                    academy = Academy.query.filter_by(academy_id=identifier).first()
                    if academy:
                        user = academy.main_teacher.user
                    else:
                        # Asumimos que el administrador se autentica con su user_id
                        user = User.query.filter_by(id=identifier).first()

            if not user:
                return jsonify({"error": "Usuario no encontrado"}), 404
            if user.role_id not in roles:
                return jsonify({"error": "Acceso denegado"}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator
