#logica de manejo de logs 
#Version 0.3
from flask import request
from .db import db, APILog

def log_api_request(user_id, operation, container_name, object_name, status_code, error_message=None):
    """
    Registra una operación de la API en la base de datos.
    """
    new_log = APILog(
        user_id=user_id,
        operation=operation,
        container_name=container_name,
        object_name=object_name,
        status_code=status_code,
        error_message=error_message
    )
    db.session.add(new_log)
    db.session.commit()
