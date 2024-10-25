# lógica de manejo de archivos
# Versión 0.4 - Proporcionar directorios y rutas
from io import BytesIO
import os, base64, hashlib
import threading
import time
import uuid
import zipfile
import shutil
from flask import Blueprint, after_this_request, request, jsonify, send_file, abort
from pathlib import Path
from flask_jwt_extended import get_jwt_identity, jwt_required
from .db import User
from .path import store_path, zip_path
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
    structure = {'': {'folders': [], 'files': []}}  # Estructura inicial para la raíz

    # Recorremos el directorio raíz con glob
    for path in root_dir.glob('**/*'):
        relative_path = path.relative_to(root_dir).as_posix()  # Convertimos la ruta a formato compatible ('/')
        
        if path.is_dir():
            # Si la carpeta está en la raíz, agregarla a 'folders' de la raíz
            parent_dir = '' if path.parent == root_dir else path.parent.relative_to(root_dir).as_posix()
            
            # Si el directorio no existe en la estructura, lo inicializamos
            if relative_path not in structure:
                structure[relative_path] = {'folders': [], 'files': []}
            
            # Añadir la carpeta al padre
            structure[parent_dir]['folders'].append(relative_path)

        elif path.is_file():
            # Si el archivo está en la raíz, agregarlo bajo la clave ''
            parent_dir = '' if path.parent == root_dir else path.parent.relative_to(root_dir).as_posix()

            # Si el directorio no existe en la estructura, lo inicializamos
            if parent_dir not in structure:
                structure[parent_dir] = {'folders': [], 'files': []}

            # Añadir el archivo
            structure[parent_dir]['files'].append(relative_path)

    return structure

# Función que obtiene la estructura de directorios y archivos de una carpeta específica
def get_specific_directory_structure(dir_path):
    structure = {'folders': [], 'files': []}  # Inicializamos la estructura

    # Verificamos si la ruta es un directorio
    if not dir_path.is_dir():
        raise NotADirectoryError(f"{dir_path} no es un directorio válido.")
    
    # Recorremos los archivos y carpetas dentro del directorio proporcionado
    for path in dir_path.iterdir():
        relative_path = path.name  # Usamos solo el nombre del archivo/carpeta

        if path.is_dir():
            structure['folders'].append(relative_path)
        elif path.is_file():
            structure['files'].append(relative_path)

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
@file_bp.route('/full-list', methods=['GET'])
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
        #print(directory_structure)
        return jsonify({"message": "Estructura obtenida correctamente", "structure": directory_structure}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para listar las carpetas y archivos dentro de una ruta especifica
@file_bp.route('/list', methods=['GET'])
@jwt_required()  # Protegido con JWT
def list_files_and_folders_single():
    current_boleta = get_jwt_identity()
    user = User.query.get(current_boleta)
    
    # Recibimos la ruta proporcionada desde el front (por ejemplo, ?dir_path=subcarpeta)
    relative_path = request.args.get('dirPath', '')  # Si no se proporciona, usa la raíz
    
    # Directorio del usuario
    user_directory = Path(store_path) / str(user.get_boleta())  / relative_path
    
    # Verificar si el directorio existe
    if not user_directory.exists():
        return jsonify({"error": "Directorio del usuario no encontrado"}), 404

    try:
        # Obtener la estructura de archivos y carpetas
        directory_structure = get_specific_directory_structure(user_directory)
        #print(directory_structure)
        return jsonify({"message": "Estructura obtenida correctamente", "structure": directory_structure}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Ruta para descargar un archivo
@file_bp.route('/download', methods=['GET'])
@jwt_required()  # Proteger con JWT
def download_file():
    current_boleta = get_jwt_identity()
    user = User.query.get(current_boleta)
    
    # Recibir la ruta del archivo a descargar desde el front
    file_path = request.args.get('file_path')
    
    if not file_path:
        return jsonify({"error": "No se proporcionó la ruta del archivo"}), 400
    
    # Generar la ruta completa donde se encuentra el archivo del usuario
    full_path = os.path.join(store_path, str(user.get_boleta()), file_path)
    
    # Verificar si el archivo existe
    if not os.path.exists(full_path):
        return jsonify({"error": "El archivo no existe"}), 404
    
    try:
        # Usar send_file para enviar el archivo al cliente
        return send_file(full_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"Error al descargar el archivo: {str(e)}"}), 500

# Función para eliminar un archivo después de un retraso
def delayed_file_deletion(filepath, delay=180):
    """Elimina un archivo después de un retraso de 'delay' segundos."""
    time.sleep(delay)
    try:
        os.remove(filepath)
        print(f"Archivo {filepath} eliminado del servidor después de {delay} segundos.")
    except Exception as e:
        print(f"Error al eliminar el archivo {filepath}: {e}")

# Ruta para descargar una carpeta como ZIP
@file_bp.route('/download-folder', methods=['GET'])
@jwt_required()  # Proteger con JWT
def download_folder():
    current_boleta = get_jwt_identity()
    user = User.query.get(current_boleta)
    
    # Recibir la ruta de la carpeta que se desea comprimir
    folder_path = request.args.get('folder_path')
    
    # Generar la ruta completa donde se encuentra la carpeta del usuario
    full_folder_path = os.path.join(store_path, str(user.get_boleta()), folder_path)
    
    print(full_folder_path, ": esta es la ruta de la carpeta")
    
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
                    print(f"Progreso: {progress:.2f}% ({processed_files}/{total_files} archivos)")

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
@jwt_required()  # Proteger con JWT
def create_folder():
    current_boleta = get_jwt_identity()
    user = User.query.get(current_boleta)
    
    # Obtener los datos del front-end
    data = request.get_json()
    folder_name = data.get('folder_name')
    parent_dir = data.get('parent_dir', '')  # Si no se proporciona, se crea en la raíz del directorio del usuario

    if not folder_name:
        return jsonify({"error": "No se proporcionó el nombre de la carpeta"}), 400

    # Directorio donde se creará la carpeta
    user_directory = os.path.join(store_path, str(user.get_boleta()), parent_dir)
    
    # Asegurarse de que el directorio del usuario existe
    if not os.path.exists(user_directory):
        return jsonify({"error": "El directorio padre no existe"}), 404
    
    # Ruta completa de la nueva carpeta
    new_folder_path = os.path.join(user_directory, folder_name)

    # Verificar si la carpeta ya existe
    if os.path.exists(new_folder_path):
        return jsonify({"error": "La carpeta ya existe"}), 400

    try:
        # Crear la nueva carpeta
        os.makedirs(new_folder_path)
        return jsonify({"message": f"Carpeta '{folder_name}' creada exitosamente en '{parent_dir}'"}), 201
    except Exception as e:
        return jsonify({"error": f"Error al crear la carpeta: {str(e)}"}), 500