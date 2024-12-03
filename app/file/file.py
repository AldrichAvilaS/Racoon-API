# lógica de manejo de archivos
# Versión 0.4 - Proporcionar directorios y rutas seguras
import os, base64
import shutil
import threading
import uuid
import zipfile
from flask import Blueprint, after_this_request, request, jsonify, send_file, abort
from pathlib import Path
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..db.db import User 
from ..db.path import store_path, zip_path
from ..logs.logs import log_api_request
from .path_functions import *
from ..openstack.load import download_file_openstack, download_path_openstack, upload_file_openstack
from ..openstack.object import get_object_list, delete, move_data
from ..openstack.conteners import create_path

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
    file_project = data.get('project_id', get_user_identifier(user.id))

    print("file_path: ", file_path)
    print("file_project: ", file_project)
    print("file_name: ", file_name)
     
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
        print("save_path: ", save_path)
        print("file_path: ", file_path)
        # Guardar el archivo
        with open(save_path, 'wb') as file:
            file.write(file_bytes)
            print("si se escribio: ")
        

        upload_file_openstack(get_user_identifier(user.id), user.openstack_id, file_project, file_path , save_path, file_name)


        log_api_request(get_jwt_identity(), "Subida de archivo exitosa", file_path, file_name, 200)
        return jsonify({"message": "Archivo cargado correctamente"}), 200
    except base64.binascii.Error:
        return jsonify({"error": "Error al decodificar el archivo base64"}), 400
    except OSError as e:
        return jsonify({"error": f"Error de sistema: {str(e)}"}), 500
    except Exception as e:
        log_api_request(get_jwt_identity(), "Error en la subida de archivo", file_path, file_name, 500, error_message=str(e))
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
    file_project = request.headers.get('X-Project', get_user_identifier(user.id))  # Opcional, ruta proporcionada por el usuario
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
            
            upload_file_openstack(get_user_identifier(user.id), user.openstack_id, file_project, file_path , save_directory, file_name)

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
        
        #mandar a descargar el archivo desde openstack
        if not request.args.get('flag'):
            download_file_openstack(get_user_identifier(user.id), user.openstack_id, get_user_identifier(user.id), file_path, file_path, user_directory)
        else: 
            download_file_openstack(get_user_identifier(user.id), user.openstack_id, request.args.get('project_id'), file_path, file_path, user_directory)
        
        print("full_file_path en funcion: ", full_file_path)
        if not os.path.exists(full_file_path):
            return jsonify({"error": "El archivo no existe"}), 404

        # Enviar el archivo al cliente
        return send_file(full_file_path, as_attachment=True)

    except ValueError as ve:
        print("error: ", ve)
        return jsonify({"error": str(ve)}), 403
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500

# Ruta para eliminar un archivo o carpeta
@file_bp.route('/delete', methods=['POST'])
@jwt_required()
def delete_file_or_folder():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401
    user_identifier = get_user_identifier(user.id)
    data = request.get_json()
    target_path = data.get('target_path')
    if data.get('project_id') is not None: 
        project_id = data.get('project_id') 
    else: 
        project_id = user_identifier
    

    if not target_path:
        return jsonify({"error": "No se proporcionó la ruta del archivo o carpeta a eliminar"}), 400

    try:
        print("intentar eliminar")
        print("target_path: ", target_path)
        print("project_id: ", project_id)
        delete(user_identifier, user.openstack_id, project_id, target_path, target_path)

        log_api_request(get_jwt_identity(), "Eliminación exitosa", "delete", target_path, 200)
        return jsonify({"message": f"'{target_path}' eliminado exitosamente"}), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 403
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500

# Ruta para listar las carpetas y archivos del espacio individual del usuario
@file_bp.route('/full-list', methods=['GET'])
@jwt_required()  # Protegido con JWT
def list_files_and_folders():
    print("entro a full-list")
    user = get_current_user()
    print("user: ", user)
    if not user:
        print("no user")
        return jsonify({"error": "Usuario no autenticado"}), 401

    user_identifier = get_user_identifier(user.id)
    print("user_identifier: ", user_identifier)
    try:
        # Obtener la estructura de archivos y carpetas
        object_list = get_object_list(user_identifier, user_identifier)
        object_list = object_list['data']
        object_list = transform_to_structure(object_list)
        # print(object_list)
        return jsonify({"message": "Estructura obtenida correctamente", "structure": object_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para listar las carpetas y archivos que contiene un alumno en un grupo
@file_bp.route('/list-student', methods=['POST'])
@jwt_required()  # Protegido con JWT
def list_files_and_folders_single():
    data = request.get_json()

    print("data: ", data)
    user = data['user_id']
    group = data['project_id']
    

    # user = User.query.filter_by(id=user).first()

    user_identifier = get_user_identifier(user)
    print("user_identifier: ", user_identifier)

    print("user a consultar: ", user)

    #obtener el usuario dependiendo del id
    

    print("user_directory: ")

    try:
        object_list = get_object_list(user, group)
        print(object_list)
        object_list = object_list['data']
        object_list = transform_to_structure(object_list)
        return jsonify({"message": "Estructura obtenida correctamente", "structure": object_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    project = data.get('project_id', get_user_identifier(user.id))

    if not folder_name:
        return jsonify({"error": "No se proporcionó el nombre de la carpeta"}), 400

    try:
        create_path(get_user_identifier(user.id), user.openstack_id , project, parent_dir, folder_name)
        return jsonify({"message": f"Carpeta '{folder_name}' creada exitosamente"}), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 403
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500
    
#--------------------------------------------------------------************--------------------------------------------------------------#

# Ruta para descargar una carpeta como ZIP
@file_bp.route('/download-folder', methods=['POST'])
@jwt_required()  # Proteger con JWT
def download_folder():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    data = request.get_json()

    #recibir la ruta por url
    folder_path = '/'+data['folder_path']
    print("folder_path: ", folder_path)
    # Recibir la ruta de la carpeta que se desea comprimir
    # folder_path = data.get('folder_path')
    if not folder_path:
        return jsonify({"error": "No se proporcionó la ruta de la carpeta"}), 400
    
    project = data.get('project_id', get_user_identifier(user.id))
    print("project: ", project)

    print(folder_path, ": esta es la ruta de la carpeta")
    # Generar la ruta completa donde se encuentra la carpeta del usuario
    full_folder_path = os.path.join(store_path + str(get_user_identifier(user.id)) )
    
    print("full: ",full_folder_path)
    
    
    # Verificar si la carpeta existe
    # if not os.path.exists(full_folder_path):
    #     return jsonify({"error": "La carpeta no existe"}), 404

    try:
        
        download_path_openstack(get_user_identifier(user.id), user.openstack_id, project, folder_path, full_folder_path)
        # # Definir el directorio donde se guardarán los archivos ZIP
        
        print("entrara a la compresion de los archivos")
        zip_dir = zip_path  # Usar la variable `zip_path` donde se guardarán los ZIP


        print("zip_dir: ", zip_dir)
        # Crear el directorio si no existe
        if not os.path.exists(zip_dir):
            print("no existe y se creara")
            os.makedirs(zip_dir)

        print("folder_path: ", folder_path)
        folder_path = os.path.normpath(folder_path)
        print("full_folder_path: ", full_folder_path)
        full_file_path = os.path.normpath(full_folder_path)
        folder_path = folder_path.lstrip("/\\")  # Eliminar cualquier barra inicial
        full_file_path = os.path.join(full_folder_path, folder_path)
        
        print("full_file_path: ", full_file_path)
        full_file_path = os.path.normpath(full_file_path)  # Normaliza la ruta según el sistema operativo
        # Verificar si la carpeta existe
        if not os.path.exists(full_file_path):
            return jsonify({"error": "La carpeta no existe"}), 404
        
        # # Generar un nombre único para el archivo ZIP para evitar colisiones
        zip_filename = f"{os.path.basename(full_folder_path)}_{uuid.uuid4().hex}.zip"
        zip_filepath = os.path.join(zip_dir, zip_filename)
        
        # Crear el archivo ZIP en el almacenamiento local
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            total_files = len([f for f in os.listdir(full_file_path) if os.path.isfile(os.path.join(full_file_path, f))])  # Solo archivos
            processed_files = 0

            print(f"Total archivos a comprimir: {total_files}")
            print(os.listdir(full_file_path))
            # Recorrer solo los archivos dentro de la carpeta, no subdirectorios
            for file in os.listdir(full_file_path):
                full_file_path = os.path.join(full_file_path, file)

                # Verificar si es un archivo (no un subdirectorio)
                if os.path.isfile(full_file_path):
                    print(f"Agregando archivo: {full_file_path}")
                    arcname = os.path.relpath(full_file_path, full_folder_path)  # Nombre relativo
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
        # return jsonify({"message": "Carpeta descargada exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": f"Error al comprimir la carpeta: {str(e)}"}), 500
    

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
    file_name = os.path.basename(source_path)

    print("source_path: ", source_path)
    print("destination_path: ", destination_path)
    print("file_name: ", file_name)

    if not source_path or not destination_path:
        return jsonify({"error": "No se proporcionaron las rutas de origen o destino"}), 400

    try:
        if not data.get('project_id'):
            project = get_user_identifier(user.id)
            user_scope = user.openstack_id
        else:
            project = data.get('project_id')
        print("user identifier: ", get_user_identifier(user.id))
        move_data(get_user_identifier(user.id), user_scope, project, source_path, file_name, destination_path)
       # user_directory = get_user_directory(get_user_identifier(user.id))
        # print("secure de full_source_path: ")
        # full_source_path = secure_path(user_directory, source_path)
        # print("secure de full_destination_path: ")
        # full_destination_path = secure_path(user_directory, destination_path)

        # if not os.path.exists(full_source_path):
        #     return jsonify({"error": "El archivo o carpeta de origen no existe"}), 404

        # # Crear el directorio de destino si no existe
        # os.makedirs(os.path.dirname(full_destination_path), exist_ok=True)
        # # Mover el archivo o carpeta
        # shutil.move(full_source_path, full_destination_path)

        # log_api_request(get_jwt_identity(), "Movimiento exitoso", "move", source_path, 200)
        return jsonify({"message": f"'{source_path}' movido exitosamente a '{destination_path}'"}), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 403
    except Exception as e:
        log_api_request(get_jwt_identity(), "Error al mover archivo/carpeta", "move", source_path, 500, error_message=str(e))
        return jsonify({"error": "Error interno del servidor"}), 500
   