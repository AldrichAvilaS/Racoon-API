#logica que recibe un archivo desde un endpoint para despues mandar el archivo por una request a los contenedores de openstack
from flask import Blueprint
from flask_jwt_extended import jwt_required
import requests, json

def openstack_auth_id(user_identifier):
    # Define los datos de autenticación
    user_identifier=str(user_identifier)
    print(user_identifier)
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
                        "name": user_identifier
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
        return {"token": token}, 201
    else:
        print("Error en la autenticación:", response.status_code, response.text)
        return {"error": response.text}, response.status_code

#funcion que obtiene el id de un usuario en openstack
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

#peticion a la api de openstack para crear un usuario
def create_user(user_id):
    print("Creando usuario en OpenStack")
    fetch_url = "http://localhost:10000/user/"
    data = {"student_id": user_id}
    try:
        response = requests.post(fetch_url, json=data)
        
        # Verifica si la respuesta fue exitosa (código 200)
        response.raise_for_status()  # Lanza una excepción si la respuesta tiene un error
        print("Usuario creado exitosamente", response.json())
        user_id = response.json()['id']
        print("ID de usuario:", user_id)
        # Retorna el contenido de la respuesta
        return user_id
    except requests.exceptions.HTTPError as errh:
        print("Error HTTP:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error de conexión:", errc)
    except requests.exceptions.Timeout as errt:
        print("Error de tiempo de espera:", errt)
    except requests.exceptions.RequestException as err:
        print("Error en la petición:", err)
    return response.json()

