# lógica de manejo de archivos
# Versión 0.4 - Proporcionar directorios y rutas seguras
import json
import os, base64
import shutil
import threading
import uuid
import zipfile
from flask import Blueprint, after_this_request, request, jsonify, send_file, abort
from pathlib import Path
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..db.db import Subject, User 
from ..db.path import store_path, zip_path
from ..logs.logs import log_api_request
from .path_functions import *
from ..openstack.load import delete_path_openstack, download_file_openstack, download_path_openstack, upload_file_openstack
from ..openstack.object import get_object_list, delete, move_data, move_path_to_path
from ..openstack.conteners import create_path, size_container

file_bp = Blueprint('file', __name__)

# Tamaño máximo permitido para archivos/chunks (en bytes)
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB

# Ruta para recibir un solo archivo
#ejemplo de entrada y salida
#entrada 
# {
# 	"file": "base64",
# 	"filename": "nombre del archivo",
# 	"path": "ruta del archivo",
# 	"project_id": "id del proyecto"
# }
#salida
# "message": "Archivo cargado correctamente"
# "message": "Archivo demasiado grande"
# "error": "Datos incompletos"
# "error": "Error al decodificar el archivo base64"
# "error": "Error de sistema: {str(e)}"
# "error": str(e)

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
        
        if data.get('project_id') is not None:
            project_id = data.get('project_id')
            scope = Subject.query.filter_by(subject_name=project_id).first()
            scope = scope.swift_scope
        else:
            scope = user.openstack_id

        upload_file_openstack(get_user_identifier(user.id), scope, file_project, file_path , save_path, file_name)


        # log_api_request(get_jwt_identity(), "Subida de archivo exitosa", file_path, file_name, 200)
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
            
            if request.headers.get('X-Project') is not None:
                project_id = request.headers.get('X-Project')
                scope = Subject.query.filter_by(subject_name=project_id).first()
                scope = scope.swift_scope
            else:
                scope = user.openstack_id

            upload_file_openstack(get_user_identifier(user.id), scope, file_project, file_path , save_directory, file_name)

            log_api_request(get_jwt_identity(), "Subida de archivo exitosa", file_path, file_name, 200)
            return jsonify({"message": "Archivo completo", "file_name": os.path.basename(final_file_path)}), 200

        return jsonify({"message": f"Chunk {chunk_index + 1} de {total_chunks} recibido"}), 200

    except OSError as e:
        return jsonify({"error": f"Error de sistema: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para descargar un archivo
#ejemplo de entrada y salida
# entrada
# {
# 	"token": "token del usuario",
# 	"file_path": "ruta del archivo",
# 	"flag": "bandera de proyecto"
# }
# salida
# "message": "Estructura obtenida correctamente"
# "error": "El archivo no existe"
# "error": "Error interno del servidor"
# "error": str(ve)
# "error": "No se proporcionó la ruta del archivo"
# "error": "Usuario no autenticado"
@file_bp.route('/download', methods=['POST'])
@jwt_required()
def download_file():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    data = request.get_json()
    print("data: ", data)
    file_path = data['file_path']

    print("file_path: ", file_path)
    if not file_path:
        return jsonify({"error": "No se proporcionó la ruta del archivo"}), 400
    
    project_id = data.get('project_id', get_user_identifier(user.id))
    #print(data['project_id'])
    if project_id != get_user_identifier(user.id):
        print("si hay proyecto a donde apuntar project_id")
        scope = Subject.query.filter_by(subject_name=project_id).first()
        scope = scope.swift_scope
    else:
        print("no hay proyecto a donde apuntar project_id por lo que sera el del usuarios")
        scope = user.openstack_id
    print("scope: ", scope)
    try:
        user_directory = get_user_directory(get_user_identifier(user.id))
        print("user_directory: ", user_directory)
        full_file_path = secure_path(user_directory, '/'+file_path)
        print("full_file_path: ", full_file_path)
        
        #mandar a descargar el archivo desde openstack
        if project_id == get_user_identifier(user.id):
            print("no project_id")
            download_file_openstack(get_user_identifier(user.id), scope, get_user_identifier(user.id), file_path, file_path, user_directory)
        else:
            print("si project_id")
            download_file_openstack(get_user_identifier(user.id), scope, project_id, file_path, file_path, user_directory)
        
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


# Ruta para descargar un archivo
#ejemplo de entrada y salida
# entrada
# {
# 	"token": "token del usuario",
# 	"file_path": "ruta del archivo",
# 	"flag": "bandera de proyecto"
# }
# salida
# "message": "Estructura obtenida correctamente"
# "error": "El archivo no existe"
# "error": "Error interno del servidor"
# "error": str(ve)
# "error": "No se proporcionó la ruta del archivo"
# "error": "Usuario no autenticado"
@file_bp.route('/download-student', methods=['POST'])
@jwt_required()
def download_file_for_student():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    data = request.get_json()
    print("data: ", data)
    file_path = data['file_path']

    print("file_path: ", file_path)
    if not file_path:
        return jsonify({"error": "No se proporcionó la ruta del archivo"}), 400
    
    student_container = data.get('student_id')
    print("student_container: ", student_container)
    project_id = data.get('project_id', get_user_identifier(user.id))
    #print(data['project_id'])
    if project_id != get_user_identifier(user.id):
        print("si hay proyecto a donde apuntar project_id")
        scope = Subject.query.filter_by(subject_name=project_id).first()
        scope = scope.swift_scope
    else:
        print("no hay proyecto a donde apuntar project_id por lo que sera el del usuarios")
        scope = user.openstack_id
    print("scope: ", scope)
    try:
        user_directory = get_user_directory(get_user_identifier(user.id))
        print("user_directory: ", user_directory)
        full_file_path = secure_path(user_directory, '/'+file_path)
        print("full_file_path: ", full_file_path)
        
        #mandar a descargar el archivo desde openstack
        if project_id == get_user_identifier(user.id):
            print("no project_id")
            download_file_openstack(student_container, scope, get_user_identifier(user.id), file_path, file_path, user_directory)
        else:
            print("si project_id")
            download_file_openstack(student_container, scope, project_id, file_path, file_path, user_directory)
        
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
#ejemplo de entrada y salida
# entrada
# {
# 	"token": "token del usuario",
# 	"target_path": "ruta del archivo o carpeta",
# 	"project_id": "id del proyecto"
# }
# salida
# "message": "'{target_path}' eliminado exitosamente"
# "error": "No se proporcionó la ruta del archivo o carpeta a eliminar"
# "error": str(ve)
# "error": "Error interno del servidor"
# "error": "Usuario no autenticado"

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

        if data.get('project_id') is not None:
            project_id = data.get('project_id')
            scope = Subject.query.filter_by(subject_name=project_id).first()
            scope = scope.swift_scope
        else:
            scope = user.openstack_id

        #si el target_path es un archivo si tiene extension
        if target_path.find(".") != -1:
            print("es un archivo")
            delete(user_identifier, scope, project_id, target_path, target_path)
        else:
            print("es una carpeta")
            delete_path_openstack(user_identifier, scope, project_id, target_path)
        

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
    # print("entro a full-list")
    user = get_current_user()
    # print("user: ", user)
    if not user:
        # print("no user")
        return jsonify({"error": "Usuario no autenticado"}), 401

    user_identifier = get_user_identifier(user.id)
    # print("user_identifier: ", user_identifier)
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

    # print("data: ", data)
    user = data['user_id']
    group = data['project_id']
    

    # user = User.query.filter_by(id=user).first()

    user_identifier = get_user_identifier(user)
    # print("user_identifier: ", user_identifier)

    # print("user a consultar: ", user)

    #obtener el usuario dependiendo del id
    

    # print("user_directory: ")

    try:
        object_list = get_object_list(user, group)
        #print(object_list)
        object_list = object_list['data']
        object_list = transform_to_structure(object_list)
        #imprimir la estructura como json
        #json.dumps(object_list)
        # print(json.dumps(object_list))
        return jsonify({"message": "Estructura obtenida correctamente", "structure": object_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Ruta para listar las carpetas y archivos que contiene un alumno en un grupo
@file_bp.route('/list-subject', methods=['POST'])
@jwt_required()  # Protegido con JWT
def list_files_and_folders_by_subject():

    # print("entro a list-subject")
    user = get_current_user()
    # print("user: ", user)
    data = request.get_json()
    user = get_user_identifier(user.id)
    # print("data: ", data)
    group = data['project_id']
    

    # user = User.query.filter_by(id=user).first()

    user_identifier = get_user_identifier(user)
    # print("user_identifier: ", user_identifier)

    # print("user a consultar: ", user)

    #obtener el usuario dependiendo del id
    

    # print("user_directory: ")

    try:
        object_list = get_object_list(user, group)
        #print(object_list)
        object_list = object_list['data']
        object_list = transform_to_structure(object_list)
        #imprimir la estructura como json
        #json.dumps(object_list)
        # print(json.dumps(object_list))
        return jsonify({"message": "Estructura obtenida correctamente", "structure": object_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para crear una nueva carpeta
#ejemplo de entrada y salida
# entrada
# {
# 	"token": "token del usuario",
# 	"folder_name": "nombre de la carpeta",
# 	"parent_dir": "ruta de la carpeta padre",
# 	"project_id": "id del proyecto"
# }
# salida
# "message": "Carpeta '{folder_name}' creada exitosamente"
# "error": "No se proporcionó el nombre de la carpeta"
# "error": str(ve)
# "error": "Error interno del servidor"

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
        if data.get('project_id') is not None:
            project_id = data.get('project_id')
            scope = Subject.query.filter_by(subject_name=project_id).first()
            scope = scope.swift_scope
        else:
            scope = user.openstack_id

        create_path(get_user_identifier(user.id), scope , project, parent_dir, folder_name)
        return jsonify({"message": f"Carpeta '{folder_name}' creada exitosamente"}), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 403
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500
    
    
#--------------------------------------------------------------************--------------------------------------------------------------#

# Ruta para descargar una carpeta como ZIP
#ejemplo de entrada y salida
# entrada
# {
# 	"token":
# 	"folder_path": "ruta de la carpeta",
# 	"project_id": "id del proyecto"
# }
# salida
# "message": "Carpeta descargada exitosamente"
# "error": "No se proporcionó la ruta de la carpeta"
# "error": "La carpeta no existe"
# "error": f"Error al comprimir la carpeta: {str(e)}"
# "error": "Usuario no autenticado"

@file_bp.route('/download-folder', methods=['POST'])
@jwt_required()  # Proteger con JWT
def download_folder():
    print("Iniciando el proceso de descarga de carpeta...")  # Depuración inicial
    
    user = get_current_user()
    if not user:
        print("Error: Usuario no autenticado")  # Depuración de autenticación
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    data = request.get_json()
    print(f"Datos recibidos: {data}")  # Depuración de los datos recibidos

    # Recibir la ruta por URL
    folder_path = '/' + data['folder_path']
    print("Ruta proporcionada por el cliente:", folder_path)  # Depuración de ruta
    
    if not folder_path:
        print("Error: No se proporcionó la ruta de la carpeta")  # Depuración de validación de ruta
        return jsonify({"error": "No se proporcionó la ruta de la carpeta"}), 400
    
    project = data.get('project_id', get_user_identifier(user.id))
    print("Proyecto identificado:", project)  # Depuración de project_id

    full_folder_path = os.path.join(store_path + str(get_user_identifier(user.id)))
    print("Ruta completa de la carpeta del usuario:", full_folder_path)  # Depuración de ruta completa
    
    try:
        print("Iniciando descarga desde OpenStack...")  # Depuración del inicio de descarga
        if data.get('project_id') is not None:
            project_id = data.get('project_id')
            scope = Subject.query.filter_by(subject_name=project_id).first()
            scope = scope.swift_scope
        else:
            scope = user.openstack_id

        download_path_openstack(get_user_identifier(user.id), scope, project, folder_path, full_folder_path)
        
        zip_dir = zip_path
        print("Directorio para ZIP definido:", zip_dir)  # Depuración de directorio ZIP

        if not os.path.exists(zip_dir):
            print("El directorio ZIP no existe, creando:", zip_dir)  # Depuración de creación de directorio
            os.makedirs(zip_dir)

        folder_path = os.path.normpath(folder_path)
        full_file_path = os.path.join(full_folder_path, folder_path.lstrip("/\\"))
        full_file_path = os.path.normpath(full_file_path)
        print("Ruta normalizada de la carpeta a comprimir:", full_file_path)  # Depuración de ruta final
        
        if not os.path.exists(full_file_path):
            print(f"Error: La carpeta no existe en {full_file_path}")  # Depuración de existencia
            return jsonify({"error": "La carpeta no existe"}), 404

        zip_filename = f"{os.path.basename(full_folder_path)}_{uuid.uuid4().hex}.zip"
        zip_filepath = os.path.join(zip_dir, zip_filename)
        print("Ruta del archivo ZIP a generar:", zip_filepath)  # Depuración de nombre ZIP

        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            processed_files = 0
            total_files = 0

            # Usar os.walk para recorrer recursivamente
            for root, dirs, files in os.walk(full_file_path):
                for file in files:
                    total_files += 1

            print(f"Archivos totales a comprimir: {total_files}")  # Depuración del conteo de archivos

            # Agregar archivos al ZIP
            for root, dirs, files in os.walk(full_file_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, full_folder_path)  # Ruta relativa dentro del ZIP
                    print(f"Agregando archivo al ZIP: {file_path} como {arcname}")  # Depuración del archivo agregado
                    zf.write(file_path, arcname)

                    # Actualizar progreso
                    processed_files += 1
                    progress = (processed_files / total_files) * 100
                    print(f"Progreso de compresión: {progress:.2f}% ({processed_files}/{total_files})")

        @after_this_request
        def schedule_file_deletion(response):
            print(f"Programando eliminación del archivo ZIP: {zip_filepath}")  # Depuración de eliminación
            threading.Thread(target=delayed_file_deletion, args=(zip_filepath, 60)).start()
            return response

        print("Enviando archivo ZIP al cliente...")  # Depuración de envío
        return send_file(zip_filepath, as_attachment=True, download_name=os.path.basename(zip_filepath))

    except Exception as e:
        print(f"Error al procesar la carpeta: {str(e)}")  # Depuración de errores
        return jsonify({"error": f"Error al comprimir la carpeta: {str(e)}"}), 500


# Ruta para descargar una carpeta como ZIP
#ejemplo de entrada y salida
# entrada
# {
# 	"token":
# 	"folder_path": "ruta de la carpeta",
# 	"project_id": "id del proyecto"
# }
# salida
# "message": "Carpeta descargada exitosamente"
# "error": "No se proporcionó la ruta de la carpeta"
# "error": "La carpeta no existe"
# "error": f"Error al comprimir la carpeta: {str(e)}"
# "error": "Usuario no autenticado"

@file_bp.route('/download-folder-student', methods=['POST'])
@jwt_required()  # Proteger con JWT
def download_folder_student():
    print("Iniciando el proceso de descarga de carpeta...")  # Depuración inicial
    
    user = get_current_user()
    if not user:
        print("Error: Usuario no autenticado")  # Depuración de autenticación
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    data = request.get_json()
    print(f"Datos recibidos: {data}")  # Depuración de los datos recibidos

    # Recibir la ruta por URL
    folder_path = '/' + data['folder_path']
    print("Ruta proporcionada por el cliente:", folder_path)  # Depuración de ruta
    
    if not folder_path:
        print("Error: No se proporcionó la ruta de la carpeta")  # Depuración de validación de ruta
        return jsonify({"error": "No se proporcionó la ruta de la carpeta"}), 400
    
    project = data.get('project_id', get_user_identifier(user.id))
    print("Proyecto identificado:", project)  # Depuración de project_id

    full_folder_path = os.path.join(store_path + str(get_user_identifier(user.id)))
    print("Ruta completa de la carpeta del usuario:", full_folder_path)  # Depuración de ruta completa
    
    try:
        student_container = data.get('student_id')
        print("student_container: ", student_container)

        print("Iniciando descarga desde OpenStack...")  # Depuración del inicio de descarga
        if data.get('project_id') is not None:
            project_id = data.get('project_id')
            scope = Subject.query.filter_by(subject_name=project_id).first()
            scope = scope.swift_scope
        else:
            scope = user.openstack_id

        download_path_openstack(student_container, scope, project, folder_path, full_folder_path)
        
        zip_dir = zip_path
        print("Directorio para ZIP definido:", zip_dir)  # Depuración de directorio ZIP

        if not os.path.exists(zip_dir):
            print("El directorio ZIP no existe, creando:", zip_dir)  # Depuración de creación de directorio
            os.makedirs(zip_dir)

        folder_path = os.path.normpath(folder_path)
        full_file_path = os.path.join(full_folder_path, folder_path.lstrip("/\\"))
        full_file_path = os.path.normpath(full_file_path)
        print("Ruta normalizada de la carpeta a comprimir:", full_file_path)  # Depuración de ruta final
        
        if not os.path.exists(full_file_path):
            print(f"Error: La carpeta no existe en {full_file_path}")  # Depuración de existencia
            return jsonify({"error": "La carpeta no existe"}), 404

        zip_filename = f"{os.path.basename(full_folder_path)}_{uuid.uuid4().hex}.zip"
        zip_filepath = os.path.join(zip_dir, zip_filename)
        print("Ruta del archivo ZIP a generar:", zip_filepath)  # Depuración de nombre ZIP

        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            processed_files = 0
            total_files = 0

            # Usar os.walk para recorrer recursivamente
            for root, dirs, files in os.walk(full_file_path):
                for file in files:
                    total_files += 1

            print(f"Archivos totales a comprimir: {total_files}")  # Depuración del conteo de archivos

            # Agregar archivos al ZIP
            for root, dirs, files in os.walk(full_file_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, full_folder_path)  # Ruta relativa dentro del ZIP
                    print(f"Agregando archivo al ZIP: {file_path} como {arcname}")  # Depuración del archivo agregado
                    zf.write(file_path, arcname)

                    # Actualizar progreso
                    processed_files += 1
                    progress = (processed_files / total_files) * 100
                    print(f"Progreso de compresión: {progress:.2f}% ({processed_files}/{total_files})")

        @after_this_request
        def schedule_file_deletion(response):
            print(f"Programando eliminación del archivo ZIP: {zip_filepath}")  # Depuración de eliminación
            threading.Thread(target=delayed_file_deletion, args=(zip_filepath, 60)).start()
            return response

        print("Enviando archivo ZIP al cliente...")  # Depuración de envío
        return send_file(zip_filepath, as_attachment=True, download_name=os.path.basename(zip_filepath))

    except Exception as e:
        print(f"Error al procesar la carpeta: {str(e)}")  # Depuración de errores
        return jsonify({"error": f"Error al comprimir la carpeta: {str(e)}"}), 500


# Ruta para mover archivos o carpetas
#ejemplo de entrada y salida
# entrada
# {
# 	"token": "token del usuario",
# 	"source_path": "ruta del archivo o carpeta de origen",
# 	"destination_path": "ruta de destino",
# 	"project_id": "id del proyecto"
# }
# salida
# "message": "'{source_path}' movido exitosamente a '{destination_path}'"
# "error": "No se proporcionaron las rutas de origen o destino"
# "error": str(ve)
# "error": "Error interno del servidor"
# "error": "Usuario no autenticado"

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
            user_scope = Subject.query.filter_by(subject_name=project).first()
            user_scope = user_scope.swift_scope
        print("user identifier: ", get_user_identifier(user.id))




        #si no tiene una extension es un directorio
        if "." in file_name:
            print("es un archivo el que se mueve")
            move_data(get_user_identifier(user.id), user_scope, project, source_path, file_name, destination_path)
        else:
            print("es un directorio el que se mueve")
            move_path_to_path(get_user_identifier(user.id), user_scope, project, source_path, destination_path)
            
        return jsonify({"message": f"'{source_path}' movido exitosamente a '{destination_path}'"}), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 403
    except Exception as e:
        log_api_request(get_jwt_identity(), "Error al mover archivo/carpeta", "move", source_path, 500, error_message=str(e))
        return jsonify({"error": "Error interno del servidor"}), 500


@file_bp.route('/space', methods=['GET'])
@jwt_required()
def get_space():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado"}), 401

    user_identifier = get_user_identifier(user.id)
    # user_directory = get_user_directory(user_identifier)
    size = size_container(user_identifier, user.openstack_id, user_identifier)
    total_size = user.storage_limit
    #pasar de gb a mb
    total_size = total_size * 1024

    used_size = size 
    free_space = total_size - used_size
    #solo 2 decimales

    return jsonify({
        "total_space": total_size,
        "used_space": round(used_size,2),
        "free_space": round(free_space,2)
    }), 200