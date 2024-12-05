import json
import os
from flask import Blueprint,request, jsonify
from pathlib import Path

from app.openstack.object import get_object_list_by_path
from .auth import openstack_auth_id
import requests

upload_bp = Blueprint('upload', __name__)

#subir archivo a un contenedor en openstack
def upload_file_openstack(user, user_scope, project, file_path, full_path, file_name):
    
    print("project", project)
    token = openstack_auth_id(str(user), project)
    print(token)
    print("file_path_recibido", file_path)
    print("file_name_recibido", file_name)
    print("full_path_recibido", full_path)

    with open(full_path, 'rb') as f:
        data = f.read()
        
    
    print("file_name ",file_name)
    # Contar las barras diagonales (considerando ambas / y \)
    count_slashes = file_name.count("/") + file_name.count("\\")
    # url = f"192.168.1.104:5000/v1/{user}/{object_name}"
    if file_path == '':
        url = f"http://192.168.1.104:8080/v1/{user_scope}/{user}/{file_name}"
    else:
        file_name = file_path + '/' + file_name
        url = f"http://192.168.1.104:8080/v1/{user_scope}/{user}//{file_name}"

    # url = f"http://192.168.1.104:8080/v1/{user_scope}/{user}{file_name}"
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

#descargar archivo de un contenedor en openstack    
def download_file_openstack(user, user_scope, project, file_path, file_name, save_directory):
    
  # Obtener el token de autenticación de OpenStack
    print("user", user)
    print("user_scope", user_scope)
    print("project", project)

    token = openstack_auth_id(str(user), project)

    # Construir la ruta completa del archivo en el contenedor
    file_full_path = f"{file_path}/{file_name}"
    print(f"Descargando archivo: {file_name}")
    print("file_path", file_path)
    print("file_name", file_name)
    # Asegurarte de limpiar barras iniciales en file_name
    #saber si un file_name tiene una barra al inicio
    
    # Contar las barras diagonales (considerando ambas / y \)
    count_slashes = file_name.count("/") + file_name.count("\\")

    # URL de descarga del archivo desde OpenStack Swift
    #si file name tiene extension
    if file_name.find(".") != -1:
        url = f"http://192.168.1.104:8080/v1/{user_scope}/{user}/{file_name}"
    else:
        url = f"http://192.168.1.104:8080/v1/{user_scope}/{user}{file_name}"
    print(url)

    headers = {
        'X-Auth-Token': token,
    }

    # Realizar la solicitud GET para descargar el archivo
    response = requests.get(url, headers=headers, stream=True)
    print(response.status_code)
    # Verificar el estado de la respuesta
    if response.status_code == 200:
        # Crear el directorio de destino si no existe
        print("save_directory", save_directory)
        os.makedirs(save_directory, exist_ok=True)

        # Asegurarte de limpiar barras iniciales en file_name
        file_name = file_name.lstrip("/\\")  # Eliminar cualquier barra inicial
        print("file_name", file_name)

        print("save_directory", save_directory)
          # Normalizar la ruta para asegurar el formato correcto del sistema operativo
        local_file_path = os.path.join(save_directory, file_name)
        local_file_path = os.path.normpath(local_file_path)  # Normaliza la ruta según el sistema operativo
        only_path = os.path.dirname(local_file_path)
        os.makedirs(only_path, exist_ok=True)
        print(f"Guardando archivo en: {local_file_path}")

        # Guardar el contenido del archivo en el sistema local
        with open(local_file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"Archivo '{file_name}' descargado exitosamente en '{local_file_path}'.")
        return jsonify({"message": f"Archivo '{file_name}' descargado exitosamente en '{local_file_path}'."}), 200
    else:
        raise Exception(f"Error al descargar el archivo: {response.status_code} - {response.text}")
    
    # Descargar archivos de un directorio virtual dentro de un contenedor de OpenStack

#descargar archivos de un directorio virtual dentro de un contenedor de OpenStack
def download_path_openstack(user, user_scope, project, file_path, save_directory):
    try:
        # Obtener el token de autenticación de OpenStack
        token = openstack_auth_id(user, project)

        # Obtener la lista de archivos en un directorio
        objects = get_object_list_by_path(user, project, file_path)
        # objects = objects.get('data', [])
        
        if not objects:
            raise Exception("No se encontraron archivos en el directorio especificado.")
        # print("objects", objects)
        #imprimir con formato json
        print(json.dumps(objects, indent=4))
        # Iterar sobre los archivos y descargarlos
        for obj in objects:
            file_name = obj['name'].lstrip("/\\")
            if file_name.endswith("/"):
                continue
            url = f"http://192.168.1.104:8080/v1/{user_scope}/{user}//{file_name}"
            print('\nurl: ',url)

            headers = {'X-Auth-Token': token}

            # Solicitar el archivo al servidor
            response = requests.get(url, headers=headers, stream=True)
            if response.status_code == 200:
                # Crear directorios locales según sea necesario
                save_directory = os.path.normpath(save_directory)
                file_name = os.path.normpath(file_name)
                
                print("save_directory", save_directory)
                print("file_name", file_name)

                # common_path = os.path.commonpath([save_directory, file_name])
                
                # print("common_path", common_path)

                #obtener nombre del archivo
                # file_name = os.path.basename(file_name)

                print("file_name", file_name)

                local_file_path = os.path.join(save_directory, file_name)
                local_file_path = os.path.normpath(local_file_path)
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                print(f"Guardando archivo en: {local_file_path}\n")   
                # Guardar el archivo
                with open(local_file_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)

                print(f"Archivo '{file_name}' descargado exitosamente en '{local_file_path}'.")
            else:
                print(f"Error al descargar '{file_name}': {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error en el proceso de descarga: {e}")

#Eliminar carpeta y su contenido de un contenedor en openstack 
def delete_path_openstack(user, user_scope, project, file_path):
    try:
        # Obtener el token de autenticación de OpenStack
        token = openstack_auth_id(user, project)

        # Obtener la lista de archivos en un directorio
        objects = get_object_list_by_path(user, project, file_path)
        # objects = objects.get('data', [])
        
        if not objects:
            raise Exception("No se encontraron archivos en el directorio especificado.")
        # print("objects", objects)
        #imprimir con formato json
        print(json.dumps(objects, indent=4))
        # Iterar sobre los archivos y descargarlos
        for obj in objects:
            file_name = obj['name'].lstrip("/\\")
            url = f"http://192.168.1.104:8080/v1/{user_scope}/{user}//{file_name}"
            print('\nurl: ',url)

            headers = {'X-Auth-Token': token}

            # Solicitar el archivo al servidor
            response = requests.delete(url, headers=headers, stream=True)
            print(response.status_code)
            if response.status_code == 200 or response.status_code == 204:

                print(f"Archivo '{file_name}' eliminado exitosamente")
            else:
                print(f"Error al eliminar '{file_name}': {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error en el proceso de eliminacion: {e}")