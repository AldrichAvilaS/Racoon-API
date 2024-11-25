import os
from flask import Blueprint,request, jsonify
from pathlib import Path
from .auth import openstack_auth_id
import requests

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/', methods=['POST'])
def upload_file_endpoint():
    
    data= request.get_json()
    user = data['user_id']
    file_path = data['file_path']
    token = openstack_auth_id(str(user))
    print(token)
    with open(file_path, 'rb') as f:
        data = f.read()
        #obtener nombre del archivo
        object_name = Path(file_path).name

    # url = f"192.168.1.104:5000/v1/{user}/{object_name}"
    url = f"http://192.168.1.104:8080/v1/AUTH_acd48220776d448ea82ea913032632d8/{user}/{object_name}"
    headers = {
        'X-Auth-Token': token,
    }

    response = requests.put(url, headers=headers, data=data)
    # response = requests.get(url, headers=headers)

    if response.status_code not in [201, 202, 204]:
        raise Exception(f"Error al subir el objeto: {response.status_code} - {response.text}")
    else:
        print(f"Objeto '{object_name}' subido exitosamente a '{user}'.")
        return jsonify({"message": f"Objeto '{object_name}' subido exitosamente a '{user}'."}), 201
    
@upload_bp.route('/', methods=['GET'])
def download_file_endpoint():
    
    data= request.get_json()
    user = data['user_id']
    file_path = data['file_path']
    token = openstack_auth_id(str(user))
    print(token)
    # with open(file_path, 'rb') as f:
    #     data = f.read()
    #     #obtener nombre del archivo
    #     object_name = Path(file_path).name
    object_name = data['file_path']
    # url = f"192.168.1.104:5000/v1/{user}/{object_name}"
    url = f"http://192.168.1.104:8080/v1/AUTH_acd48220776d448ea82ea913032632d8/{user}/{object_name}"
    headers = {
        'X-Auth-Token': token,
    }

    # response = requests.get(url, headers=headers, data=data)
    response = requests.get(url, headers=headers)

    if response.status_code not in [201, 202, 204]:
        raise Exception(f"Error al subir el objeto: {response.status_code} - {response.text}")
    else:
        print(f"Objeto '{object_name}' subido exitosamente a '{user}'.")
        return jsonify({"message": f"Objeto '{object_name}' subido exitosamente a '{user}'."}), 201


def upload_file_openstack(user, user_scope, project, file_path, full_path, file_name):
    
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
    url = f"http://192.168.1.104:8080/v1/{user_scope}/{user}/{file_name}"
    print(url)
    headers = {
        'X-Auth-Token': token,
    }

    response = requests.put(url, headers=headers, data=data)
    # response = requests.get(url, headers=headers)

    if response.status_code not in [201, 202, 204]:
        raise Exception(f"Error al subir el objeto: {response.status_code} - {response.text}")
    else:
        print(f"Objeto '{file_name}' subido exitosamente a '{user}'.")
        return jsonify({"message": f"Objeto '{file_name}' subido exitosamente a '{user}'."}), 201
    
def download_file(user, user_scope, project, file_path, file_name, save_directory):
    
  # Obtener el token de autenticación de OpenStack
    token = openstack_auth_id(str(user), project)

    # Construir la ruta completa del archivo en el contenedor
    file_full_path = f"{file_path}/{file_name}"
    print(f"Descargando archivo: {file_full_path}")

    # URL de descarga del archivo desde OpenStack Swift
    url = f"http://192.168.1.104:8080/v1/{user_scope}/{user}/{file_full_path}"
    headers = {
        'X-Auth-Token': token,
    }

    # Realizar la solicitud GET para descargar el archivo
    response = requests.get(url, headers=headers, stream=True)

    # Verificar el estado de la respuesta
    if response.status_code == 200:
        # Crear el directorio de destino si no existe
        os.makedirs(save_directory, exist_ok=True)

        # Ruta completa donde se guardará el archivo localmente
        local_file_path = os.path.join(save_directory, file_name)

        # Guardar el contenido del archivo en el sistema local
        with open(local_file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"Archivo '{file_name}' descargado exitosamente en '{local_file_path}'.")
        return jsonify({"message": f"Archivo '{file_name}' descargado exitosamente en '{local_file_path}'."}), 200
    else:
        raise Exception(f"Error al descargar el archivo: {response.status_code} - {response.text}")