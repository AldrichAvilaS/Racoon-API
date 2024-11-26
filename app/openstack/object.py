#logica que recibe un archivo desde un endpoint para despues mandar el archivo por una request a los contenedores de openstack
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
import requests, json
from .auth import openstack_auth_id
openstack_auth_bp = Blueprint('openstack', __name__)

def get_object_list(user_id, project_id):
    fetch_url = "http://localhost:10000/object/"
    data = {"user_id": user_id, "project": project_id}
    try:
        response = requests.get(fetch_url, json=data)
        
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

def get_object_list_by_path(user_id, project_id, path):
    fetch_url = "http://localhost:10000/object/path"
    data = {"user_id": user_id, "project_id": project_id, "path": path}
    try:
        response = requests.post(fetch_url, json=data)
        
        # Verifica si la respuesta fue exitosa (código 200)
        response.raise_for_status()  # Lanza una excepción si la respuesta tiene un error

        #obtener user_info de response
        user_info = response.json()['user_info']
        
        # Retorna el contenido de la respuesta
        return user_info  # Usar .json() si la respuesta es en JSON, .text si es texto plano
    except requests.exceptions.HTTPError as errh:
        print("Error HTTP:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error de conexión:", errc)
    except requests.exceptions.Timeout as errt:
        print("Error de tiempo de espera:", errt)
    except requests.exceptions.RequestException as err:
        print("Error en la petición:", err)
    return response.json()


def delete(user, user_scope, project, file_path, file_name):
    token = openstack_auth_id(str(user), project)
    print(project)
    print(token)
    print("file_path_recibido", file_path)
    print("file_name_recibido", file_name)
    # print("full_path_recibido", full_path)
    if not file_path == '':
        file_name =  '/' + file_name

    # url = f"192.168.1.104:5000/v1/{user}/{object_name}"
    url = f"http://192.168.1.104:8080/v1/{user_scope}/{user}{file_name}"
    print(url)
    headers = {
        'X-Auth-Token': token,
    }

    response = requests.delete(url, headers=headers)
    # response = requests.get(url, headers=headers)

    if response.status_code not in [201, 202, 204]:
        raise Exception(f"Error al subir el objeto: {response.status_code} - {response.text}")
    else:
        print(f"Objeto '{file_name}' subido exitosamente a '{user}'.")
        return jsonify({"message": f"Objeto '{file_name}' subido exitosamente a '{user}'."}), 201
    
def move_data(user, user_scope, project, file_path, file_name, new_path):
    token = openstack_auth_id(str(user), project)
    print(token)
    print("file_path_recibido", file_path)
    print("file_name_recibido", file_name)
    # print("full_path_recibido", full_path)

    file_name = file_path + '/' + file_name

    # url = f"192.168.1.104:5000/v1/{user}/{object_name}"
    url = f"http://192.168.1.104:8080/v1/{user_scope}/{user}/{file_name}"
    print(url)
    headers = {
        'X-Auth-Token': token,
        'X-Object-Meta-name': new_path + '/' + file_name
    }

    response = requests.post(url, headers=headers)
    # response = requests.get(url, headers=headers)

    if response.status_code not in [201, 202, 204]:
        raise Exception(f"Error al subir el objeto: {response.status_code} - {response.text}")
    else:
        print(f"Objeto '{file_name}' subido exitosamente a '{user}'.")
        return jsonify({"message": f"Objeto '{file_name}' subido exitosamente a '{user}'."}), 201
    
