#logica de obtencio de elementos de los proyectos y contenedores de swift

from flask import Blueprint, after_this_request, request, jsonify, send_file, abort
from pathlib import Path
from flask_jwt_extended import get_jwt_identity, jwt_required
import requests
from app.openstack.auth import openstack_auth_id

def create_project(user_id):
    fetch_url = "http://localhost:10000/project/"
    data = {"user_id": user_id}
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

def create_path(user, user_scope, project, full_path, path_name):
    token = openstack_auth_id(str(user), project)
    
    print("full_path_recibido", full_path)
    print("path_name_recibido", path_name) 
     
    path_name = full_path + '/' + path_name
    
    # Crear un archivo temporal vacío que sirva de ancla para crear el directorio
    
    with open(path_name, 'w') as file:
        pass  # Esto crea un archivo vacío

    # url = f"192.168.1.104:5000/v1/{user}/{object_name}"
    url = f"http://192.168.1.104:8080/v1/{user_scope}/{user}/{path_name}"
    print(url)
    headers = {
        'X-Auth-Token': token,
    }

    response = requests.put(url, headers=headers, data=file)
    # response = requests.get(url, headers=headers)

    if response.status_code not in [201, 202, 204]:
        raise Exception(f"Error al subir el objeto: {response.status_code} - {response.text}")
    else:
        return jsonify({"message": f"Carpeta '{path_name}' creada exitosamente '."}), 201