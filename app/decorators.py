from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from .db import User

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @jwt_required()  # Asegura que el usuario esté autenticado con JWT
        def decorated_function(*args, **kwargs):
            # Obtener la identidad desde el token JWT
            boleta = get_jwt_identity()
            user = User.query.get(boleta)

            if not user:
                return jsonify({"error": "Usuario no encontrado"}), 404
            if user.role_id not in roles:
                return jsonify({"error": "Acceso denegado"}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator
