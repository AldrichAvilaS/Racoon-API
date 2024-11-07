from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_current_user, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from ..db.db import Notice, db
from ..authorization.decorators import role_required  

#crear el blueprint para las noticias
notice_bp = Blueprint('notice', __name__)

# Endpoint para crear una nueva noticia
@notice_bp.route('/create-notice', methods=['POST'])
@jwt_required()  # Requiere autenticación con JWT
@role_required(0, 1)  # Administrador (0) y Academia (1)
def create_notice():
    user = get_current_user()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json()

    # Validar que se reciban los datos necesarios
    required_fields = ['content', 'date_at_finish']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        # Crear la nueva noticia
        new_notice = Notice(
            notice=data['content'],  # Contenido de la noticia
            date_at_publish=db.func.current_timestamp(),  # Fecha actual de creación
            date_at_finish = data.get('date_at_finish', None),  # Fecha de finalización (opcional)
        )
        
        db.session.add(new_notice)
        db.session.commit()

        return jsonify({"message": "Noticia creada exitosamente", "notice_id": new_notice.id}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Error al crear la noticia"}), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    