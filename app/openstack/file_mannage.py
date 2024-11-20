#logica que recibe un archivo desde un endpoint para despues mandar el archivo por una request a los contenedores de openstack
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
import requests, json

openstack_auth_bp = Blueprint('openstack', __name__)

# @openstack_auth_bp.route('/', methods=['POST'])
def openstack_auth_token(user_identifier):
    # data = request.get_json()
    # user_identifier = data.get['user_identifier']
    print("get token", user_identifier)
    # Define los datos de autenticación
    auth_url = "http://192.168.1.104:5000/v3/auth/tokens"
    data = { 
            "auth": { 
            "identity": 
            { 
                "methods": ["password"],
                "password": 
                    {
                        "user": 
                        {
                            "domain": 
                            {
                                "name": "Default"
                            },
                            "name": user_identifier,
                            "password": user_identifier
                        } 
                    } 
                }, 
                "scope": 
                { 
                    "project": 
                    { 
                        "domain": 
                        { 
                            "name": "Default" 
                        }, 
                        "name":  user_identifier
                    } 
                } 
            }
        }

    # Realiza la solicitud de autenticación
    headers = {"Content-Type": "application/json"}
    response = requests.post(auth_url, headers=headers, data=json.dumps(data))

    # Comprueba si la solicitud fue exitosa
    if response.status_code == 201:
        token = response.headers["X-Subject-Token"]
        print("Token de autenticación obtenido:", token)
        id = get_id_scope(token, user_identifier)
        print("ID de usuario obtenido:", id)
        return {"token": token, "id": id}, 201
    else:
        print("Error en la autenticación:", response.status_code, response.text)
        return {"error": response.text}, response.status_code
    
import requests

def get_id_scope(token, nombre):
    auth_url = "http://192.168.1.104:5000/v3/users/"
    headers = {"X-Auth-Token": token}  # Corregido para usar el valor de la variable `token`

    try:
        response = requests.get(auth_url, headers=headers)
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud HTTP: {e}")
        return None

    if response.status_code != 200:
        print(f"Error al obtener el ID de usuario: {response.status_code} - {response.text}")
        return None

    try:
        respuesta = response.json()
    except ValueError as e:
        print(f"Error al decodificar JSON: {e}")
        return None

    # print("Respuesta JSON recibida:", respuesta)

    users = respuesta.get('users')
    if not users:
        print("La clave 'users' no se encontró en la respuesta.")
        return None

    # Buscar el usuario por nombre
    for usuario in users:
        if usuario.get('name') == nombre:
            user_id = usuario.get('id')
            print(f"ID de usuario obtenido: {user_id}")
            return user_id

    print(f"Usuario con nombre '{nombre}' no encontrado.")
    return None
