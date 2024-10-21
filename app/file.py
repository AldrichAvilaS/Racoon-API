# lógica de manejo de archivos
# Versión 0.4 - Proporcionar directorios y rutas
import os, base64, hashlib
from flask import Blueprint, request, jsonify
from pathlib import Path
from flask_jwt_extended import get_jwt_identity, jwt_required
from .db import db, User, APILog
from .path import store_path
from .logs import log_api_request

file_bp = Blueprint('file', __name__)

# Tamaño máximo permitido para archivos/chunks (en bytes)
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB

# Función para generar la ruta de guardado con limpieza de espacios en blanco
def get_save_directory(user, file_path):
    # Limpiar espacios en blanco no deseados
    store_path_clean = store_path.strip()
    boleta_clean = str(user.get_boleta()).strip()
    file_path_clean = file_path.strip() if file_path else ''
    
    return os.path.join(store_path_clean, boleta_clean, file_path_clean)

# Función para verificar si un archivo ya existe y asignar un nuevo nombre si es necesario
def get_unique_file_path(directory, file_name):
    """
    Verifica si el archivo existe y, si es así, añade un índice para evitar sobrescribirlo.
    Devuelve una ruta única.
    """
    base_name, extension = os.path.splitext(file_name)
    counter = 1
    new_file_path = os.path.join(directory, file_name)

    # Itera hasta encontrar un nombre de archivo único
    while os.path.exists(new_file_path):
        new_file_name = f"{base_name}({counter}){extension}"
        new_file_path = os.path.join(directory, new_file_name)
        counter += 1

    return new_file_path

# Función para verificar el hash de integridad del chunk
def verify_chunk_integrity(chunk_data, expected_hash):
    hash_object = hashlib.sha256()
    hash_object.update(chunk_data)
    return hash_object.hexdigest() == expected_hash

# Función que obtiene la estructura de directorios y archivos recursivamente
def get_directory_structure(root_dir):
    structure = {}

    # Recorremos el directorio raíz con glob
    for path in root_dir.glob('**/*'):  # Utilizamos '**/*' para obtener todo recursivamente
        relative_path = path.relative_to(root_dir).as_posix()  # Convertimos la ruta a formato compatible ('/')
        
        if path.is_dir():
            # Inicializamos la carpeta en la estructura
            if relative_path not in structure:
                structure[relative_path] = {
                    'folders': [],
                    'files': []
                }
            
            # Añadimos las subcarpetas y archivos
            for subpath in path.iterdir():
                sub_relative_path = subpath.relative_to(root_dir).as_posix()
                if subpath.is_dir():
                    structure[relative_path]['folders'].append(sub_relative_path)
                elif subpath.is_file():
                    structure[relative_path]['files'].append(sub_relative_path)

        elif path.is_file():
            # Si es un archivo en la raíz o en cualquier otra carpeta
            if '' not in structure:
                structure[''] = {'folders': [], 'files': []}
            structure['']['files'].append(relative_path)

    return structure

# Ruta para recibir un solo archivo
@file_bp.route('/upload/single', methods=['POST'])
@jwt_required()  # Proteger con JWT
def upload_file():
    current_boleta = get_jwt_identity()
    user = User.query.get(current_boleta)
    data = request.get_json()  # Recibe JSON
    
    # Validar que los datos necesarios estén presentes
    if not data.get('file') or not data.get('filename'):
        log_api_request(user.boleta, "Subida de archivo fallida - Datos incompletos", "uploads", data.get('filename', 'unknown'), 400)
        return jsonify({"error": "No se recibió archivo o nombre de archivo"}), 400
    
    file_data = data['file']  # Archivo codificado en base64
    file_name = data['filename']  # Nombre del archivo
    file_path = data.get('path', '')  # Opcionalmente, se recibe una ruta para guardar el archivo
    
    try:
        # Decodificar el archivo base64
        file_bytes = base64.b64decode(file_data)

        # Validar tamaño de archivo
        if len(file_bytes) > MAX_FILE_SIZE:
            log_api_request(user.boleta, "Archivo demasiado grande", data.get('path', 'default_container'), data['filename'], 400)
            return jsonify({"error": "El archivo es demasiado grande"}), 400
        
        # Generar la ruta completa donde se guardará el archivo
        save_directory = get_save_directory(user, file_path)
        os.makedirs(save_directory, exist_ok=True)  # Crear el directorio si no existe
        
        save_path = os.path.join(save_directory, file_name)
        
        # Guardar el archivo
        with open(save_path, 'wb') as file:
            file.write(file_bytes)
        log_api_request(user.boleta, "Subida de archivo exitosa", data.get('path', 'default_container'), data['filename'], 200)
        return jsonify({"message": "Archivo cargado correctamente"}), 200
    except base64.binascii.Error:
        return jsonify({"error": "Error al decodificar el archivo base64"}), 400
    except OSError as e:
        return jsonify({"error": f"Error de sistema: {str(e)}"}), 500
    except Exception as e:
        log_api_request(user.boleta, "Error en la subida de archivo", data.get('path', 'default_container'), data.get('filename', 'unknown'), 500, error_message=str(e))
        return jsonify({"error": str(e)}), 500

# Ruta para recibir múltiples archivos
@file_bp.route('/upload/lot', methods=['POST'])
@jwt_required()  # Proteger con JWT
def upload_multiple_files():
    current_boleta = get_jwt_identity()
    user = User.query.get(current_boleta)
    data = request.get_json()  # Recibe JSON
    
    # Validar que se hayan recibido archivos
    if 'files' not in data:
        log_api_request(user.boleta, "Subida múltiple fallida - No se encontraron archivos", "uploads", "none", 400)
        return jsonify({"error": "No se encontraron archivos"}), 400
    
    files = data['files']  # Lista de archivos, cada uno con 'file' y 'filename'
    file_path = data.get('path', '')  # Opcionalmente, se recibe una ruta para guardar los archivos
    
    try:
        for file_info in files:
            if not file_info.get('file') or not file_info.get('filename'):
                log_api_request(user.boleta, "Subida múltiple fallida - Falta archivo o nombre en uno de los archivos", file_path, "unknown", 400)
                return jsonify({"error": "Falta archivo o nombre en uno de los archivos"}), 400

            file_data = file_info['file']  # Archivo codificado en base64
            file_name = file_info['filename']  # Nombre del archivo
            
            # Decodificar el archivo base64
            file_bytes = base64.b64decode(file_data)

            # Validar tamaño de archivo
            if len(file_bytes) > MAX_FILE_SIZE:
                log_api_request(user.boleta, f"Archivo demasiado grande en subida múltiple - {file_name}", file_path, file_name, 400)
                return jsonify({"error": f"El archivo {file_name} es demasiado grande"}), 400
            
            # Generar la ruta completa donde se guardará cada archivo
            save_directory = get_save_directory(user, file_path)
            os.makedirs(save_directory, exist_ok=True)  # Crear el directorio si no existe
            
            save_path = os.path.join(save_directory, file_name)
            
            # Guardar el archivo
            with open(save_path, 'wb') as file:
                file.write(file_bytes)
            # Log exitoso para cada archivo subido
            log_api_request(user.boleta, f"Subida de archivo múltiple exitosa", file_path, file_name, 200)
            
        return jsonify({"message": "Archivos cargados correctamente"}), 200
    except base64.binascii.Error:
        log_api_request(user.boleta, "Error al decodificar algún archivo en la subida múltiple", file_path, "unknown", 400)
        return jsonify({"error": "Error al decodificar alguno de los archivos base64"}), 400
    except OSError as e:
        log_api_request(user.boleta, f"Error de sistema en subida múltiple: {str(e)}", file_path, "unknown", 500)
        return jsonify({"error": f"Error de sistema: {str(e)}"}), 500
    except Exception as e:
        log_api_request(user.boleta, f"Error general en subida múltiple: {str(e)}", file_path, "unknown", 500)
        return jsonify({"error": str(e)}), 500

# Ruta para recibir archivos en partes (chunks)
@file_bp.route('/upload/chunk', methods=['POST'])
@jwt_required()  # Proteger con JWT
def upload_file_chunk():
    current_boleta = get_jwt_identity()
    user = User.query.get(current_boleta)
    
    # Obtener las cabeceras necesarias
    chunk_index = request.headers.get('X-Chunk-Index')
    total_chunks = request.headers.get('X-Total-Chunks')
    file_name = request.headers.get('X-File-Name')
    file_path = request.headers.get('X-File-Path', '')  # Opcional, ruta proporcionada por el usuario

    if not chunk_index or not total_chunks or not file_name:
        log_api_request(user.boleta, "Subida de chunk fallida - Faltan cabeceras", file_path, file_name, 400)
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
            log_api_request(user.boleta, "Subida de archivo por chunks exitosa", file_path, file_name, 200)
            return jsonify({"message": "Archivo completo", "file_name": os.path.basename(final_file_path)}), 200

        return jsonify({"message": f"Chunk {chunk_index + 1} de {total_chunks} recibido"}), 200

    except OSError as e:
        return jsonify({"error": f"Error de sistema: {str(e)}"}), 500
    except Exception as e:
        log_api_request(user.boleta, "Error en la subida de chunk", file_path, file_name, 500, error_message=str(e))
        return jsonify({"error": str(e)}), 500

# Ruta para listar las carpetas y archivos dentro de store_path
@file_bp.route('/list', methods=['GET'])
@jwt_required()  # Protegido con JWT
def list_files_and_folders():
    current_boleta = get_jwt_identity()
    user = User.query.get(current_boleta)
    
    # Directorio del usuario
    user_directory = Path(store_path) / str(user.get_boleta())
    
    # Verificar si el directorio existe
    if not user_directory.exists():
        return jsonify({"error": "Directorio del usuario no encontrado"}), 404

    try:
        # Obtener la estructura de archivos y carpetas
        directory_structure = get_directory_structure(user_directory)
        print(directory_structure)
        return jsonify({"message": "Estructura obtenida correctamente", "structure": directory_structure}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500