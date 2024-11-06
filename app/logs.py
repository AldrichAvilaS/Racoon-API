#logica de manejo de logs 
#Version 0.4
from flask import request
from .db import db, APILog, get_user_identifier

def log_api_request(user_id, operation, container_name=None, object_name=None, status_code=200, error_message=None):
    user_identifier = get_user_identifier(user_id)
    if not user_identifier:
        user_identifier = 'Desconocido'

    log_entry = APILog(
        user_id=user_id,
        user_identifier=user_identifier,
        operation=operation,
        container_name=container_name or '',
        object_name=object_name or '',
        status_code=status_code,
        error_message=error_message
    )
    db.session.add(log_entry)
    db.session.commit()
