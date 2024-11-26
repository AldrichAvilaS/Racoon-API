import os
from flask import Blueprint,request, jsonify
from pathlib import Path
from .auth import openstack_auth_id
import requests

upload_bp = Blueprint('upload', __name__)


def upload_file_openstack(user, user_scope, project, file_path, full_path, file_name):
    
    print("project", project)
    token = openstack_auth_id(str(user), project)
    print(token)
    print("file_path_recibido", file_path)
    print("file_name_recibido", file_name)
    print("full_path_recibido", full_path)
    with open(full_path, 'rb') as f:
        data = f.read()
        
    file_name = file_path + '/' + file_name
    print(file_name)
    # url = f"192.168.1.104:5000/v1/{user}/{object_name}"
    url = f"http://192.168.1.104:8080/v1/{user_scope}/{user}{file_name}"
    print(url)
    headers = {
        'X-Auth-Token': token,
    }

    response = requests.put(url, headers=headers, data=data)
    # response = requests.get(url, headers=headers)
    print(response.status_code)
    if response.status_code not in [201, 202, 204]:
        raise Exception(f"Error al subir el objeto: {response.status_code} - {response.text}")
    else:
        print(f"Objeto '{file_name}' subido exitosamente a '{user}'.")
        return jsonify({"message": f"Objeto '{file_name}' subido exitosamente a '{user}'."}), 201
    
def download_file_openstack(user, user_scope, project, file_path, file_name, save_directory):
    
  # Obtener el token de autenticación de OpenStack
    print("user", user)
    print("user_scope", user_scope)
    print("project", project)

    token = openstack_auth_id(str(user), project)

    # Construir la ruta completa del archivo en el contenedor
    file_full_path = f"{file_path}/{file_name}"
    print(f"Descargando archivo: {file_name}")

    # URL de descarga del archivo desde OpenStack Swift
    url = f"http://192.168.1.104:8080/v1/{user_scope}/{user}{file_path}"
    print(url)

    headers = {
        'X-Auth-Token': token,
    }

    # Realizar la solicitud GET para descargar el archivo
    response = requests.get(url, headers=headers, stream=True)

    # Verificar el estado de la respuesta
    if response.status_code == 200:
        # Crear el directorio de destino si no existe
        print("save_directory", save_directory)
        os.makedirs(save_directory, exist_ok=True)

        # Asegurarte de limpiar barras iniciales en file_name
        file_name = file_name.lstrip("/\\")  # Eliminar cualquier barra inicial
        print("file_name", file_name)

        # Ruta completa donde se guardará el archivo localmente
        local_file_path = os.path.join(save_directory, file_name)

        print(f"Guardando archivo en: {local_file_path}")

        # Guardar el contenido del archivo en el sistema local
        with open(local_file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"Archivo '{file_name}' descargado exitosamente en '{local_file_path}'.")
        return jsonify({"message": f"Archivo '{file_name}' descargado exitosamente en '{local_file_path}'."}), 200
    else:
        raise Exception(f"Error al descargar el archivo: {response.status_code} - {response.text}")