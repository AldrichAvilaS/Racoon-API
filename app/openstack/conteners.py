#logica de obtencio de elementos de los proyectos y contenedores de swift

from flask import Blueprint, after_this_request, request, jsonify, send_file, abort
from pathlib import Path
from flask_jwt_extended import get_jwt_identity, jwt_required
import requests

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

