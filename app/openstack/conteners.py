#logica de obtencio de elementos de los proyectos y contenedores de swift

import io
from flask import Blueprint, after_this_request, request, jsonify, send_file, abort
from pathlib import Path
from flask_jwt_extended import get_jwt_identity, jwt_required
import requests
from app.openstack.auth import openstack_auth_id
from ..db.path import *

#crear proyecto en openstack
def create_project(project_id):
    fetch_url = "http://192.168.1.104:10000/project/"
    data = {"project": project_id}
    try:
        response = requests.post(fetch_url, json=data)
        
        # Verifica si la respuesta fue exitosa (código 200)
        response.raise_for_status()  # Lanza una excepción si la respuesta tiene un error

        # Retorna el contenido de la respuesta
        return response.json()  # Usar .json() si la respuesta es en JSON, .text si es texto plano
    except requests.exceptions.HTTPError as errh:
        print("Error HTTP:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error de conexión:", errc)
    except requests.exceptions.Timeout as errt:
        print("Error de tiempo de espera:", errt)
    except requests.exceptions.RequestException as err:
        print("Error en la petición:", err)
    return response.json()

#asignar rol en una proyecto referido en una materia de openstack
def assigment_role(user_id, project_id, role):

    print("Asignando rol en OpenStack")
    print
    if role == "student":
        fetch_url = "http://192.168.1.104:10000/role/student"
    elif role == "teacher":
        fetch_url = "http://192.168.1.104:10000/role/teacher"
    elif role == "academy":
        fetch_url = "http://192.168.1.104:10000/role/academy"

    data = {"user": user_id, "project": project_id}
    try:
        print("Se intentará asignar el rol")
        print("data", data)
        response = requests.post(fetch_url, json=data)
        
        # Verifica si la respuesta fue exitosa (código 200)
        response.raise_for_status()  # Lanza una excepción si la respuesta tiene un error

        # Retorna el contenido de la respuesta
        return response.json()  # Usar .json() si la respuesta es en JSON, .text si es texto plano
    except requests.exceptions.HTTPError as errh:
        print("Error HTTP:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error de conexión:", errc)
    except requests.exceptions.Timeout as errt:
        print("Error de tiempo de espera:", errt)
    except requests.exceptions.RequestException as err:
        print("Error en la petición:", err)
    return response.json()

#obtener tamaño del contenedor en openstack
def size_container(user, user_scope, project):
    token = openstack_auth_id(str(user), project)
    if token:
        print("Token de autenticación obtenido:")

    print(project)

    url = f"http://192.168.1.104:8080/v1/{user_scope}/{user}/"
    print(url)
    headers = {
        'X-Auth-Token': token,
    }
    #metodo head en el request para obtener el tamaño del contenedor
    response = requests.get(url, headers=headers)
    #obtener Content-Length del header
    try:
        size = response.headers.get('X-Container-Bytes-Used')
        #Bytes to MB
        size = int(size) / 1024 / 1024
        print("Tamaño del contenedor:", size)

        if response.status_code not in [200, 201, 202, 204]:
            print("Error al obtener el tamaño del contenedor")
        else:
            return size
    except Exception as e:
        print("Error al obtener el tamaño del contenedor:", e)
        return 0    



#crear carpeta virtual en openstack
def create_path(user, user_scope, project, full_path, path_name):
    token = openstack_auth_id(str(user), project)
    if token:
        print("Token de autenticación obtenido:")

    print(project)
    print("full_path_recibido", full_path)
    print("path_name_recibido", path_name) 
    path_name = path_name+"/"
    if not full_path == '/': 
        path_name = full_path + '/' + path_name
    else:
        path_name = full_path+path_name
        
    print("path_name", path_name)
    # Crear un archivo temporal vacío que sirva de ancla para crear el directorio
    print(store_path+path_name)
    # Crear un archivo vacío en memoria
    empty_file = io.BytesIO()
    print("Creando archivo vacío en memoria")
    
    # url = f"192.168.1.104:5000/v1/{user}/{object_name}"
    url = f"http://192.168.1.104:8080/v1/{user_scope}/{user}/{path_name}"
    print(url)
    headers = {
        'X-Auth-Token': token,
    }

    response = requests.put(url, headers=headers, data=empty_file.getvalue())
    # response = requests.get(url, headers=headers)
    print(response.status_code)
    if response.status_code not in [201, 202, 204]:
        raise Exception(f"Error al subir el objeto: {response.status_code} - {response.text}")
    else:
        return jsonify({"message": f"Carpeta '{path_name}' creada exitosamente '."}), 201