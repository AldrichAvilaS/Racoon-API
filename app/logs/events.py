from flask import Blueprint, request, jsonify
from ..authorization.decorators import role_required
from ..db.db import db, APILog
from flask_jwt_extended import jwt_required
from datetime import datetime

logs_bp = Blueprint('logs_bp', __name__)

# Obtener logs filtrados por user_identifier, container_name y rango de fechas opcional
@logs_bp.route('/', methods=['GET'])
@jwt_required()
#@role_required(0)  # Solo usuarios con rol "Administrador" pueden acceder
def get_logs():
    user_identifier = request.args.get('user_identifier')
    container_name = request.args.get('container_name')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Crear la consulta base
    query = APILog.query
    
    # Filtrar por user_identifier o container_name si están presentes
    if user_identifier:
        query = query.filter_by(user_identifier=user_identifier)
    if container_name:
        query = query.filter_by(container_name=container_name)
    
    # Filtrar por rango de fechas si están presentes
    if start_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(APILog.timestamp >= start_date)
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido para start_date. Use YYYY-MM-DD"}), 400

    if end_date:
        try:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(APILog.timestamp <= end_date)
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido para end_date. Use YYYY-MM-DD"}), 400

    #query por si no se quiere filtrado
    if not user_identifier and not container_name and not start_date and not end_date:
        query = APILog.query

    # Ejecutar la consulta y obtener los resultados
    logs = query.all()
    
    # Serializar los logs para el JSON de respuesta
    logs_data = [{
        "id": log.id,
        "user_identifier": log.user_identifier,
        "operation": log.operation,
        "container_name": log.container_name,
        "object_name": log.object_name,
        "status_code": log.status_code,
        "timestamp": log.timestamp,
        "error_message": log.error_message
    } for log in logs]

    return jsonify(logs_data), 200
