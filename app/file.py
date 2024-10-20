# lógica de manejo de archivos
# Versión 0.3 - Con soporte para uploads en chunks y mejoras
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from .db import db, User, APILog
import os, base64, hashlib
from .path import store_path

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

# Ruta para recibir un solo archivo
@file_bp.route('/upload/single', methods=['POST'])
@jwt_required()  # Proteger con JWT
def upload_file():
    current_boleta = get_jwt_identity()
    user = User.query.get(current_boleta)
    data = request.get_json()  # Recibe JSON
    
    # Validar que los datos necesarios estén presentes
    if not data.get('file') or not data.get('filename'):
        return jsonify({"error": "No se recibió archivo o nombre de archivo"}), 400
    
    file_data = data['file']  # Archivo codificado en base64
    file_name = data['filename']  # Nombre del archivo
    file_path = data.get('path', '')  # Opcionalmente, se recibe una ruta para guardar el archivo
    
    try:
        # Decodificar el archivo base64
        file_bytes = base64.b64decode(file_data)

        # Validar tamaño de archivo
        if len(file_bytes) > MAX_FILE_SIZE:
            return jsonify({"error": "El archivo es demasiado grande"}), 400
        
        # Generar la ruta completa donde se guardará el archivo
        save_directory = get_save_directory(user, file_path)
        os.makedirs(save_directory, exist_ok=True)  # Crear el directorio si no existe
        
        save_path = os.path.join(save_directory, file_name)
        
        # Guardar el archivo
        with open(save_path, 'wb') as file:
            file.write(file_bytes)
        
        return jsonify({"message": "Archivo cargado correctamente"}), 200
    except base64.binascii.Error:
        return jsonify({"error": "Error al decodificar el archivo base64"}), 400
    except OSError as e:
        return jsonify({"error": f"Error de sistema: {str(e)}"}), 500
    except Exception as e:
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
        
        return jsonify({"message": "Archivos cargados correctamente"}), 200
    except base64.binascii.Error:
        return jsonify({"error": "Error al decodificar alguno de los archivos base64"}), 400
    except OSError as e:
        return jsonify({"error": f"Error de sistema: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Función para verificar el hash de integridad del chunk
def verify_chunk_integrity(chunk_data, expected_hash):
    hash_object = hashlib.sha256()
    hash_object.update(chunk_data)
    return hash_object.hexdigest() == expected_hash

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

    # Verificar si se recibieron las cabeceras correctas
    #print(f"Cabeceras recibidas: X-Chunk-Index: {chunk_index}, X-Total-Chunks: {total_chunks}, X-File-Name: {file_name}, X-File-Path: {file_path}")

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
        #print(f"Recibiendo chunk {chunk_index + 1}/{total_chunks}, tamaño: {len(chunk)} bytes")

        # Guardar el chunk en el archivo temporal
        with open(temp_file_path, 'ab') as temp_file:
            temp_file.write(chunk)

        # Verificar si es el último chunk
        if chunk_index == total_chunks - 1:
            # Generar la ruta final del archivo, evitando sobrescribir si ya existe
            final_file_path = get_unique_file_path(save_directory, file_name)
            
            os.rename(temp_file_path, final_file_path)
            #print(f"Archivo {file_name} completado y guardado como {final_file_path}")
            return jsonify({"message": "Archivo completo", "file_name": os.path.basename(final_file_path)}), 200

        return jsonify({"message": f"Chunk {chunk_index + 1} de {total_chunks} recibido"}), 200

    except OSError as e:
        return jsonify({"error": f"Error de sistema: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
# Ruta para listar las carpetas y archivos dentro de store_path
@file_bp.route('/list', methods=['GET'])
@jwt_required()  # Protegido con JWT
def list_files_and_folders():
    current_boleta = get_jwt_identity()
    user = User.query.get(current_boleta)
    
    # Directorio del usuario
    user_directory = os.path.join(store_path, str(user.get_boleta()))
    
    # Verificar si el directorio existe
    if not os.path.exists(user_directory):
        return jsonify({"error": "Directorio del usuario no encontrado"}), 404

    # Función recursiva para estructurar carpetas y archivos
    def get_directory_structure(root_dir):
        structure = {}
        for root, dirs, files in os.walk(root_dir):
            # Obtener la ruta relativa para evitar rutas absolutas en la estructura
            rel_path = os.path.relpath(root, root_dir)
            if rel_path == '.':
                rel_path = ''  # Raíz del directorio
                
            # Inicializar el objeto de directorio
            structure[rel_path] = {
                'folders': dirs,
                'files': files
            }
        return structure

    try:
        # Obtener la estructura de archivos y carpetas
        directory_structure = get_directory_structure(user_directory)
        return jsonify({"message": "Estructura obtenida correctamente", "structure": directory_structure}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
