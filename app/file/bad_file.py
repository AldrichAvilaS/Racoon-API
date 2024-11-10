# files.py
# Módulo para el manejo de archivos y directorios

import os
import base64
import hashlib
import threading
import time
import uuid
import zipfile
from flask import Blueprint, after_this_request, request, jsonify, send_file
from pathlib import Path
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..db.db import Role, db, User, Student, Teacher, Academy
from ..db.path import store_path, zip_path
from ..logs.logs import log_api_request

# Crear un Blueprint para las rutas relacionadas con archivos
file_bp = Blueprint('file_bp', __name__)

# Tamaño máximo permitido para archivos/chunks (en bytes)
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB

# Función para obtener el ID del rol basado en su nombre
def get_role_id_by_name(role_name):
    role = Role.query.filter_by(name=role_name).first()
    if role:
        return role.role_id
    return None  # O puedes lanzar una excepción si el rol no existe

# Función auxiliar para obtener el usuario actual basado en su identificador
def get_current_user():
    identifier = get_jwt_identity()
    user = None
    print(identifier)
    # Buscar al usuario según el identificador
    student = Student.query.filter_by(boleta=identifier).first()
    if student:
        user = student.user
    else:
        teacher = Teacher.query.filter_by(rfc=identifier).first()
        if teacher:
            user = teacher.user 
        else:
            academy = Academy.query.filter_by(academy_id=identifier).first()
            if academy:
                user = academy.main_teacher.user
            else:
                # Asumimos que los administradores se autentican con user.id
                user = User.query.filter_by(id=identifier, role_id=get_role_id_by_name('Administrador')).first()

    return user

# Función para obtener el identificador del usuario basado en su rol
def get_user_identifier(user_id):
    user = User.query.get(user_id)
    if not user:
        return None

    if user.role.name == 'Estudiante':
        student = Student.query.filter_by(user_id=user_id).first()
        return student.boleta if student else None
    elif user.role.name == 'Profesor':
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        return teacher.rfc if teacher else None
    elif user.role.name == 'Administrador':
        return f'admin_{user.id}'
    elif user.role.name == 'Academia':
        academy = Academy.query.filter_by(main_teacher_id=user_id).first()
        return academy.academy_id if academy else None
    else:
        return None

# Función para obtener el directorio base del usuario
def get_user_directory(user):
    return os.path.join(store_path, str(get_user_identifier(user.user_id)))

# Función para asegurar rutas y prevenir path traversal
def secure_path(user_directory, relative_path):
    # Combinar y normalizar la ruta
    full_path = os.path.normpath(os.path.join(user_directory, relative_path))
    # Verificar que la ruta esté dentro del directorio del usuario
    if os.path.commonprefix([full_path, user_directory]) != user_directory:
        raise ValueError("Intento de acceso no autorizado fuera del directorio asignado")
    return full_path

# Función para verificar si un archivo ya existe y asignar un nuevo nombre si es necesario
def get_unique_file_path(directory, file_name):
    base_name, extension = os.path.splitext(file_name)
    counter = 1
    new_file_path = os.path.join(directory, file_name)

    # Itera hasta encontrar un nombre de archivo único
    while os.path.exists(new_file_path):
        new_file_name = f"{base_name}({counter}){extension}"
        new_file_path = os.path.join(directory, new_file_name)
        counter += 1

    return new_file_path

# Función que obtiene la estructura de directorios y archivos recursivamente
def get_directory_structure(root_dir):
    structure = {'folders': [], 'files': []}

    for item in root_dir.iterdir():
        if item.is_dir():
            structure['folders'].append(item.name)
        elif item.is_file():
            structure['files'].append(item.name)

    return structure

# Ruta para subir un solo archivo
@file_bp.route('/upload/single', methods=['POST'])
@jwt_required()
def upload_file():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401

    data = request.get_json()
    if not data or 'file' not in data or 'filename' not in data:
        log_api_request(get_jwt_identity(), "Subida de archivo fallida - Datos incompletos", "uploads", "unknown", 400)
        return jsonify({"error": "Datos incompletos"}), 400

    file_data = data['file']
    file_name = data['filename']
    file_path = data.get('path', '')

    try:
        # Decodificar los datos del archivo desde base64
        file_bytes = base64.b64decode(file_data)
        # Verificar el tamaño del archivo
        if len(file_bytes) > MAX_FILE_SIZE:
            log_api_request(get_jwt_identity(), "Archivo demasiado grande", file_path, file_name, 400)
            return jsonify({"error": "El archivo es demasiado grande"}), 400

        # Obtener y asegurar el directorio donde se guardará el archivo
        user_directory = get_user_directory(user)
        save_directory = secure_path(user_directory, file_path)
        os.makedirs(save_directory, exist_ok=True)

        save_path = os.path.join(save_directory, file_name)

        # Verificar si el archivo ya existe y obtener una ruta única
        save_path = get_unique_file_path(save_directory, file_name)

        # Guardar el archivo en el sistema
        with open(save_path, 'wb') as file:
            file.write(file_bytes)

        log_api_request(get_jwt_identity(), "Subida de archivo exitosa", file_path, file_name, 200)
        return jsonify({"message": "Archivo cargado correctamente"}), 200

    except ValueError as ve:
        # Manejo de errores de seguridad en la ruta
        log_api_request(get_jwt_identity(), "Intento de acceso no autorizado", file_path, file_name, 403)
        return jsonify({"error": str(ve)}), 403
    except Exception as e:
        # Manejo de errores generales
        log_api_request(get_jwt_identity(), "Error en la subida de archivo", file_path, file_name, 500, error_message=str(e))
        return jsonify({"error": "Error interno del servidor"}), 500

# Ruta para subir múltiples archivos
@file_bp.route('/upload/lot', methods=['POST'])
@jwt_required()
def upload_multiple_files():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401

    data = request.get_json()
    if not data or 'files' not in data:
        log_api_request(get_jwt_identity(), "Subida múltiple fallida - No se encontraron archivos", "uploads", "none", 400)
        return jsonify({"error": "No se encontraron archivos"}), 400

    files = data['files']
    file_path = data.get('path', '')

    try:
        user_directory = get_user_directory(user)
        save_directory = secure_path(user_directory, file_path)
        os.makedirs(save_directory, exist_ok=True)

        for file_info in files:
            if not file_info.get('file') or not file_info.get('filename'):
                log_api_request(get_jwt_identity(), "Subida múltiple fallida - Datos incompletos en un archivo", file_path, "unknown", 400)
                return jsonify({"error": "Datos incompletos en uno de los archivos"}), 400

            file_data = file_info['file']
            file_name = file_info['filename']

            # Decodificar y verificar el tamaño del archivo
            file_bytes = base64.b64decode(file_data)
            if len(file_bytes) > MAX_FILE_SIZE:
                log_api_request(get_jwt_identity(), f"Archivo demasiado grande - {file_name}", file_path, file_name, 400)
                return jsonify({"error": f"El archivo {file_name} es demasiado grande"}), 400

            save_path = os.path.join(save_directory, file_name)
            save_path = get_unique_file_path(save_directory, file_name)

            # Guardar el archivo
            with open(save_path, 'wb') as file:
                file.write(file_bytes)

            log_api_request(get_jwt_identity(), "Subida múltiple exitosa", file_path, file_name, 200)

        return jsonify({"message": "Archivos cargados correctamente"}), 200

    except ValueError as ve:
        log_api_request(get_jwt_identity(), "Intento de acceso no autorizado", file_path, "unknown", 403)
        return jsonify({"error": str(ve)}), 403
    except Exception as e:
        log_api_request(get_jwt_identity(), "Error en la subida múltiple", file_path, "unknown", 500, error_message=str(e))
        return jsonify({"error": "Error interno del servidor"}), 500

# Ruta para listar los archivos y carpetas en una ruta específica
@file_bp.route('/list', methods=['GET'])
@jwt_required()
def list_files_and_folders():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401

    dir_path = request.args.get('dirPath', '')

    try:
        user_directory = get_user_directory(user)
        target_directory = secure_path(user_directory, dir_path)

        if not os.path.exists(target_directory):
            return jsonify({"error": "El directorio no existe"}), 404

        # Obtener la estructura de directorios y archivos
        directory_structure = get_directory_structure(Path(target_directory))

        return jsonify({"message": "Estructura obtenida correctamente", "structure": directory_structure}), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 403
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500

# Ruta para descargar un archivo
@file_bp.route('/download', methods=['GET'])
@jwt_required()
def download_file():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401

    file_path = request.args.get('file_path')
    if not file_path:
        return jsonify({"error": "No se proporcionó la ruta del archivo"}), 400

    try:
        user_directory = get_user_directory(user)
        full_file_path = secure_path(user_directory, file_path)

        if not os.path.exists(full_file_path):
            return jsonify({"error": "El archivo no existe"}), 404

        # Enviar el archivo al cliente
        return send_file(full_file_path, as_attachment=True)

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 403
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500

# Función para eliminar un archivo después de un retraso
def delayed_file_deletion(filepath, delay=180):
    time.sleep(delay)
    try:
        os.remove(filepath)
        print(f"Archivo {filepath} eliminado del servidor después de {delay} segundos.")
    except Exception as e:
        print(f"Error al eliminar el archivo {filepath}: {e}")

# Ruta para descargar una carpeta como ZIP
@file_bp.route('/download-folder', methods=['GET'])
@jwt_required()
def download_folder():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401

    folder_path = request.args.get('folder_path')
    if not folder_path:
        return jsonify({"error": "No se proporcionó la ruta de la carpeta"}), 400

    try:
        user_directory = get_user_directory(user)
        full_folder_path = secure_path(user_directory, folder_path)

        if not os.path.exists(full_folder_path):
            return jsonify({"error": "La carpeta no existe"}), 404

        # Crear directorio para ZIP si no existe
        if not os.path.exists(zip_path):
            os.makedirs(zip_path)

        # Nombre único para el archivo ZIP
        zip_filename = f"{os.path.basename(full_folder_path)}_{uuid.uuid4().hex}.zip"
        zip_filepath = os.path.join(zip_path, zip_filename)

        # Crear el archivo ZIP
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(full_folder_path):
                for file in files:
                    full_file_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_file_path, full_folder_path)
                    zf.write(full_file_path, arcname)

        # Programar eliminación del archivo ZIP después de su uso
        @after_this_request
        def schedule_file_deletion(response):
            threading.Thread(target=delayed_file_deletion, args=(zip_filepath, 60)).start()
            return response

        # Enviar el archivo ZIP al cliente
        return send_file(zip_filepath, as_attachment=True, download_name=os.path.basename(zip_filepath))

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 403
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500

# Ruta para crear una nueva carpeta
@file_bp.route('/create-folder', methods=['POST'])
@jwt_required()
def create_folder():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401

    data = request.get_json()
    folder_name = data.get('folder_name')
    parent_dir = data.get('parent_dir', '')

    if not folder_name:
        return jsonify({"error": "No se proporcionó el nombre de la carpeta"}), 400

    try:
        user_directory = get_user_directory(user)
        parent_directory = secure_path(user_directory, parent_dir)
        new_folder_path = os.path.join(parent_directory, folder_name)

        if os.path.exists(new_folder_path):
            return jsonify({"error": "La carpeta ya existe"}), 400

        # Crear la nueva carpeta
        os.makedirs(new_folder_path)
        return jsonify({"message": f"Carpeta '{folder_name}' creada exitosamente"}), 201

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 403
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500

# Ruta para mover archivos o carpetas
@file_bp.route('/move', methods=['POST'])
@jwt_required()
def move_file_or_folder():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401

    data = request.get_json()
    source_path = data.get('source_path')
    destination_path = data.get('destination_path')

    if not source_path or not destination_path:
        return jsonify({"error": "No se proporcionaron las rutas de origen o destino"}), 400

    try:
        user_directory = get_user_directory(user)
        full_source_path = secure_path(user_directory, source_path)
        full_destination_path = secure_path(user_directory, destination_path)

        if not os.path.exists(full_source_path):
            return jsonify({"error": "El archivo o carpeta de origen no existe"}), 404

        # Crear el directorio de destino si no existe
        os.makedirs(os.path.dirname(full_destination_path), exist_ok=True)
        # Mover el archivo o carpeta
        os.rename(full_source_path, full_destination_path)

        log_api_request(get_jwt_identity(), "Movimiento exitoso", "move", source_path, 200)
        return jsonify({"message": f"'{source_path}' movido exitosamente a '{destination_path}'"}), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 403
    except Exception as e:
        log_api_request(get_jwt_identity(), "Error al mover archivo/carpeta", "move", source_path, 500, error_message=str(e))
        return jsonify({"error": "Error interno del servidor"}), 500

# Ruta para eliminar un archivo o carpeta
@file_bp.route('/delete', methods=['POST'])
@jwt_required()
def delete_file_or_folder():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401

    data = request.get_json()
    target_path = data.get('target_path')

    if not target_path:
        return jsonify({"error": "No se proporcionó la ruta del archivo o carpeta a eliminar"}), 400

    try:
        user_directory = get_user_directory(user)
        full_target_path = secure_path(user_directory, target_path)

        if not os.path.exists(full_target_path):
            return jsonify({"error": "El archivo o carpeta no existe"}), 404

        if os.path.isfile(full_target_path):
            # Eliminar archivo
            os.remove(full_target_path)
        else:
            # Eliminar carpeta
            os.rmdir(full_target_path)

        log_api_request(get_jwt_identity(), "Eliminación exitosa", "delete", target_path, 200)
        return jsonify({"message": f"'{target_path}' eliminado exitosamente"}), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 403
    except Exception as e:
        log_api_request(get_jwt_identity(), "Error al eliminar archivo/carpeta", "delete", target_path, 500, error_message=str(e))
        return jsonify({"error": "Error interno del servidor"}), 500
