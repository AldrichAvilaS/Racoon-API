#logica que recibe un archivo desde un endpoint para despues mandar el archivo por una request a los contenedores de openstack
from flask import Blueprint
from flask_jwt_extended import jwt_required
import requests, json


#peticion a la api de openstack para crear un usuario
def create_user(user_id, role):
    print("Creando usuario en OpenStack")
    if role == "student":
        fetch_url = "http://localhost:10000/user/student"
    else:
        fetch_url = "http://localhost:10000/user/teacher"
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

def create_academy(user_id):
    try:
        fetch_url = "http://localhost:10000/user/academy"
        data = {"student_id": user_id}
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
