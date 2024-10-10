#logica de manejo de logs 
#Version 0.1
from flask import Flask, request, jsonify
from .db import Role, db, User, APILog

def log_api_request(user_id, operation, container_name, object_name, status_code, error_message=None):
    new_log = APILog(
        user_id=user_id,
        operation=operation,
        container_name=container_name,
        object_name=object_name,
        status_code=status_code,
        error_message=error_message
    )
    db.session.add(new_log)  # Agregar el nuevo log a la sesión
    db.session.commit()      # Confirmar la transacción

def new_user_log(user, operation, status_code=None, error_message=None):
    # Ejemplo de uso
    log_api_request(
        user_id=user,
        operation=operation,
        container_name='none',
        object_name='none',
        status_code=status_code,
        error_message = error_message
        )
