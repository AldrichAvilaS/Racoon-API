# lógica de manejo de archivos
# Versión 0.4 - Proporcionar directorios y rutas
from io import BytesIO
import os, base64, hashlib
import shutil
import threading
import time
import uuid
import zipfile
from flask import Blueprint, after_this_request, request, jsonify, send_file, abort
from pathlib import Path
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..db.db import User 
from ..db.path import store_path, zip_path
from ..logs.logs import log_api_request
from .path_functions import *

file_bp = Blueprint('file', __name__)

# Tamaño máximo permitido para archivos/chunks (en bytes)
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB

# Ruta para recibir un solo archivo
@file_bp.route('/upload/single', methods=['POST'])
@jwt_required()  # Proteger con JWT
def upload_file():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401

    data = request.get_json()
    if not data or 'file' not in data or 'filename' not in data:
        log_api_request(get_jwt_identity(), "Subida de archivo fallida - Datos incompletos", "uploads", "unknown", 400)
        return jsonify({"error": "Datos incompletos"}), 400
    
    file_data = data['file']  # Archivo codificado en base64
    file_name = data['filename']  # Nombre del archivo
    file_path = data.get('path', '')  # Opcionalmente, se recibe una ruta para guardar el archivo
    
    try:
        # Decodificar el archivo base64
        file_bytes = base64.b64decode(file_data)

        # Verificar el tamaño del archivo
        if len(file_bytes) > MAX_FILE_SIZE:
            log_api_request(get_jwt_identity(), "Archivo demasiado grande", file_path, file_name, 400)
            return jsonify({"error": "El archivo es demasiado grande"}), 400
        
        # Generar la ruta completa donde se guardará el archivo
        save_directory = get_save_directory(user, file_path)
        print("save_directory con solo limpieza de espacios: ", save_directory)
        
        # Obtener y asegurar el directorio donde se guardará el archivo
        user_directory = get_user_directory(get_user_identifier(user.id))
        print("user_directory: ", user_directory)
        save_directory = secure_path(user_directory, file_path)
        print("save_directory: ", save_directory)

        
        os.makedirs(save_directory, exist_ok=True)  # Crear el directorio si no existe
        
        save_path = os.path.join(save_directory, file_name)
        
        # Guardar el archivo
        with open(save_path, 'wb') as file:
            file.write(file_bytes)
            
        log_api_request(get_jwt_identity(), "Subida de archivo exitosa", file_path, file_name, 200)
        return jsonify({"message": "Archivo cargado correctamente"}), 200
    except base64.binascii.Error:
        return jsonify({"error": "Error al decodificar el archivo base64"}), 400
    except OSError as e:
        return jsonify({"error": f"Error de sistema: {str(e)}"}), 500
    except Exception as e:
        log_api_request(get_jwt_identity(), "Error en la subida de archivo", file_path, file_name, 500, error_message=str(e))
        return jsonify({"error": str(e)}), 500

# Ruta para recibir múltiples archivos
@file_bp.route('/upload/lot', methods=['POST'])
@jwt_required()  # Proteger con JWT
def upload_multiple_files():
    
    user = get_current_user()
    
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401
    data = request.get_json()  # Recibe JSON
    
    # Validar que se hayan recibido archivos
    if 'files' not in data:
        return jsonify({"error": "No se encontraron archivos"}), 400
    
    files = data['files']  # Lista de archivos, cada uno con 'file' y 'filename'
    file_path = data.get('path', '')  # Opcionalmente, se recibe una ruta para guardar los archivos
    
    try:
        for file_info in files:
            if not file_info.get('file') or not file_info.get('filename'):
                return jsonify({"error": "Falta archivo o nombre en uno de los archivos"}), 400

            file_data = file_info['file']  # Archivo codificado en base64
            file_name = file_info['filename']  # Nombre del archivo
            
            # Decodificar el archivo base64
            file_bytes = base64.b64decode(file_data)

            # Validar tamaño de archivo
            if len(file_bytes) > MAX_FILE_SIZE:
                return jsonify({"error": f"El archivo {file_name} es demasiado grande"}), 400
            
            # Generar la ruta completa donde se guardará cada archivo
            save_directory = get_save_directory(user, file_path)
            os.makedirs(save_directory, exist_ok=True)  # Crear el directorio si no existe
            
            save_path = os.path.join(save_directory, file_name)
            
            # Guardar el archivo
            with open(save_path, 'wb') as file:
                file.write(file_bytes)
            # Log exitoso para cada archivo subido
            log_api_request(get_jwt_identity(), "Subida de archivos multiples exitosa", file_path, file_name, 200)
            
        return jsonify({"message": "Archivos cargados correctamente"}), 200
    except base64.binascii.Error:
        return jsonify({"error": "Error al decodificar alguno de los archivos base64"}), 400
    except OSError as e:
        return jsonify({"error": f"Error de sistema: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para recibir archivos en partes (chunks)
@file_bp.route('/upload/chunk', methods=['POST'])
@jwt_required()  # Proteger con JWT
def upload_file_chunk():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    # Obtener las cabeceras necesarias
    chunk_index = request.headers.get('X-Chunk-Index')
    total_chunks = request.headers.get('X-Total-Chunks')
    file_name = request.headers.get('X-File-Name')
    file_path = request.headers.get('X-File-Path', '')  # Opcional, ruta proporcionada por el usuario

    if not chunk_index or not total_chunks or not file_name:
        return jsonify({"error": "Faltan cabeceras"}), 400

    try:
        chunk_index = int(chunk_index)
        total_chunks = int(total_chunks)

        # Generar la ruta donde se guardará el archivo temporalmente
        save_directory = get_save_directory(user, file_path)
        os.makedirs(save_directory, exist_ok=True)  # Crear el directorio si no existe
        
        temp_file_path = os.path.join(save_directory, f'temp_{file_name}')
        
        # Leer el chunk recibido
        chunk = request.data  # El chunk debería enviarse en binario

        # Guardar el chunk en el archivo temporal
        with open(temp_file_path, 'ab') as temp_file:
            temp_file.write(chunk)

        # Verificar si es el último chunk
        if chunk_index == total_chunks - 1:
            # Generar la ruta final del archivo, evitando sobrescribir si ya existe
            final_file_path = get_unique_file_path(save_directory, file_name)
            
            os.rename(temp_file_path, final_file_path)
            log_api_request(get_jwt_identity(), "Subida de archivo exitosa", file_path, file_name, 200)
            return jsonify({"message": "Archivo completo", "file_name": os.path.basename(final_file_path)}), 200

        return jsonify({"message": f"Chunk {chunk_index + 1} de {total_chunks} recibido"}), 200

    except OSError as e:
        return jsonify({"error": f"Error de sistema: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para descargar un archivo
@file_bp.route('/download', methods=['GET'])
@jwt_required()
def download_file():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401

    file_path = request.args.get('file_path')
    print("file_path: ", file_path)
    if not file_path:
        return jsonify({"error": "No se proporcionó la ruta del archivo"}), 400

    try:
        user_directory = get_user_directory(get_user_identifier(user.id))
        print("user_directory: ", user_directory)
        full_file_path = secure_path(user_directory, file_path)
        print("full_file_path: ", full_file_path)
        if not os.path.exists(full_file_path):
            return jsonify({"error": "El archivo no existe"}), 404

        # Enviar el archivo al cliente
        return send_file(full_file_path, as_attachment=True)

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 403
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500

# Ruta para descargar una carpeta como ZIP
@file_bp.route('/download-folder', methods=['GET'])
@jwt_required()  # Proteger con JWT
def download_folder():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    # Recibir la ruta de la carpeta que se desea comprimir
    folder_path = request.args.get('folder_path')
    if not folder_path:
        return jsonify({"error": "No se proporcionó la ruta de la carpeta"}), 400
    
    print(folder_path, ": esta es la ruta de la carpeta")
    # Generar la ruta completa donde se encuentra la carpeta del usuario
    full_folder_path = os.path.join(store_path + str(get_user_identifier(user.id)) +'/'+ folder_path)
    
    print("full: ",full_folder_path)
    
    
    # Verificar si la carpeta existe
    if not os.path.exists(full_folder_path):
        return jsonify({"error": "La carpeta no existe"}), 404

    try:
        # Definir el directorio donde se guardarán los archivos ZIP
        zip_dir = zip_path  # Usar la variable `zip_path` donde se guardarán los ZIP

        # Crear el directorio si no existe
        if not os.path.exists(zip_dir):
            os.makedirs(zip_dir)

        # Generar un nombre único para el archivo ZIP para evitar colisiones
        zip_filename = f"{os.path.basename(full_folder_path)}_{uuid.uuid4().hex}.zip"
        zip_filepath = os.path.join(zip_dir, zip_filename)
        
        # Crear el archivo ZIP en el almacenamiento local
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            total_files = sum([len(files) for _, _, files in os.walk(full_folder_path)])
            processed_files = 0
            
            # Recorrer todos los archivos dentro de la carpeta y agregarlos al ZIP
            for root, dirs, files in os.walk(full_folder_path):
                for file in files:
                    full_file_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_file_path, full_folder_path)
                    zf.write(full_file_path, arcname)

                    # Actualizar el progreso en la consola
                    processed_files += 1
                    progress = (processed_files / total_files) * 100
                    #print(f"Progreso: {progress:.2f}% ({processed_files}/{total_files} archivos)")

        # Programar la eliminación del archivo ZIP en un hilo separado con retraso
        @after_this_request
        def schedule_file_deletion(response):
            threading.Thread(target=delayed_file_deletion, args=(zip_filepath, 60)).start()  # 5 segundos de retraso
            return response

        # Enviar el archivo ZIP generado al cliente desde el disco
        return send_file(zip_filepath, as_attachment=True, download_name=os.path.basename(zip_filepath))

    except Exception as e:
        return jsonify({"error": f"Error al comprimir la carpeta: {str(e)}"}), 500
    
# Ruta para crear una nueva carpeta
@file_bp.route('/create-folder', methods=['POST'])
@jwt_required()
def create_folder():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401

    data = request.get_json()
    print("data: ", data)
    folder_name = data.get('folder_name')
    parent_dir = data.get('parent_dir', '')

    if not folder_name:
        return jsonify({"error": "No se proporcionó el nombre de la carpeta"}), 400

    try:
        user_directory = get_user_directory(get_user_identifier(user.id))
        print("user_directory: ", user_directory)
        parent_directory = secure_path(user_directory, parent_dir)
        print("parent_directory: ", parent_directory)
        new_folder_path = os.path.join(parent_directory, folder_name)
        print("new_folder_path: ", new_folder_path)

        if os.path.exists(new_folder_path):
            return jsonify({"error": "La carpeta ya existe"}), 400

        # Crear la nueva carpeta
        os.makedirs(new_folder_path)
        return jsonify({"message": f"Carpeta '{folder_name}' creada exitosamente"}), 200

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
        user_directory = get_user_directory(get_user_identifier(user.id))
        print("secure de full_source_path: ")
        full_source_path = secure_path(user_directory, source_path)
        print("secure de full_destination_path: ")
        full_destination_path = secure_path(user_directory, destination_path)

        if not os.path.exists(full_source_path):
            return jsonify({"error": "El archivo o carpeta de origen no existe"}), 404

        # Crear el directorio de destino si no existe
        os.makedirs(os.path.dirname(full_destination_path), exist_ok=True)
        # Mover el archivo o carpeta
        shutil.move(full_source_path, full_destination_path)

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
        user_directory = get_user_directory(get_user_identifier(user.id))
        full_target_path = secure_path(user_directory, target_path)

        print("full_target_path: ", full_target_path)
        
        if not os.path.exists(full_target_path):
            return jsonify({"error": "El archivo o carpeta no existe"}), 404

        if os.path.isfile(full_target_path):
            # Eliminar archivo
            print("Eliminando archivo")
            os.remove(full_target_path)
        else:
            # Eliminar carpeta
            print("Eliminando carpeta")
            shutil.rmtree(full_target_path)

        log_api_request(get_jwt_identity(), "Eliminación exitosa", "delete", target_path, 200)
        return jsonify({"message": f"'{target_path}' eliminado exitosamente"}), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 403
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500


# Ruta para listar las carpetas y archivos dentro de store_path
@file_bp.route('/full-list', methods=['GET'])
@jwt_required()  # Protegido con JWT
def list_files_and_folders():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401

    user_identifier = get_user_identifier(user.id)
    # Directorio del usuario
    user_directory = Path(store_path) / str(user_identifier)
    print("user_directory: ", user_directory)
    
    user_directory = get_user_directory(user_identifier)
    print("user_directory por get_user_directory: ", user_directory)
    # Verificar si el directorio existe
    if not user_directory.exists():
        return jsonify({"error": "Directorio del usuario no encontrado"}), 404

    try:
        # Obtener la estructura de archivos y carpetas
        directory_structure = get_directory_structure(user_directory)
        #print(directory_structure)
        return jsonify({"message": "Estructura obtenida correctamente", "structure": directory_structure}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para listar las carpetas y archivos dentro de una ruta especifica
@file_bp.route('/list', methods=['POST'])
@jwt_required()  # Protegido con JWT
def list_files_and_folders_single():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    data = request.get_json()
    relative_path = data.get('dirPath', '')  # Obtener la ruta desde el cuerpo de la solicitud
    user_identifier = get_user_identifier(user.id)
    specific_user_directory = str(user_identifier) + "/" + relative_path
    user_directory = Path(store_path) / specific_user_directory

    if not user_directory.exists():
        return jsonify({"error": "Directorio del usuario no encontrado"}), 404

    try:
        directory_structure = get_specific_directory_structure(user_directory)
        return jsonify({"message": "Estructura obtenida correctamente", "structure": directory_structure}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
