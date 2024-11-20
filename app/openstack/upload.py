from flask import Blueprint, after_this_request, request, jsonify, send_file, abort
from pathlib import Path

from .user_openstack import openstack_auth_id

from .file_mannage import openstack_auth_token
import requests

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/', methods=['PUT'])
def upload_file():
    
    data= request.get_json()
    user = data['user_id']
    file_path = data['file_path']
    token = openstack_auth_id(str(user))
    print(token)
    with open(file_path, 'rb') as f:
        data = f.read()
        #obtener nombre del archivo
        object_name = Path(file_path).name

    url = f"192.168.1.104:5000/{user}/{object_name}"
    headers = {
        'X-Auth-Token': token,
    }

    response = requests.put(url, headers=headers, data=data)

    if response.status_code not in [201, 202, 204]:
        raise Exception(f"Error al subir el objeto: {response.status_code} - {response.text}")
    else:
        print(f"Objeto '{object_name}' subido exitosamente a '{user}'.")
        return jsonify({"message": f"Objeto '{object_name}' subido exitosamente a '{user}'."}), 201