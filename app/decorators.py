from functools import wraps
from flask import jsonify
from flask_login import current_user

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Usuario no autenticado"}), 401
            if current_user.role_id not in roles:
                return jsonify({"error": "Acceso denegado"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
