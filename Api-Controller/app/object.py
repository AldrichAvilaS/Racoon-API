import subprocess
from flask import Blueprint, json, request
from .auth import authorization_with_user

object_bp = Blueprint('object', __name__)

#ruta para listar los objetos
#como se mandan los datos
#curl -X GET http://192.168.1.104:5000/object/1

#listar los objetos de un usuario
@object_bp.route('/', methods = ['GET'])
def list_objects():

    data = request.get_json()
    user_id = str(data["user_id"])
    project = str(data["project"])

    print("user_id: ", user_id)
    print("project: ", project)
    # project_name = str(data["project_name"])
    try:
        authorization_with_user(user_id, project)  # Crear la autorización para el usuario en ese proyecto
        # Listar los objetos en el contenedor
        # Ejecutar el comando openstack con captura de stdout y stderr
        user_data = subprocess.run(
            [
                "openstack", 
                "object", 
                "list",
                "--long",
                "-f",
                "json",
                user_id
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  # Esto decodifica automáticamente la salida a cadena de texto
        )
        # user_data.stdout ya es una cadena de texto gracias a text=True
        user_info = json.loads(user_data.stdout)

        return {"message": "objetos listados con exito", "data": user_info}
    
    except subprocess.CalledProcessError as e:
        print(f"Error al listar objetos: {e}")
        return {"error": "Error al listar objetos"}

#ruta para listar los objetos de una carpeta    
@object_bp.route('/path', methods = ['POST'])
def list_object_by_path():
    #swift list 2018630522 -l  --prefix /home -j
    data = request.get_json()
    user_id = str(data["user_id"])
    project = str(data["project"])
    path = str(data["path"])
    # project_name = str(data["project_name"])
    try:
        authorization_with_user(user_id, project)  # Crear la autorización para el usuario en ese proyecto
        # Listar los objetos en el contenedor
        # Ejecutar el comando openstack con captura de stdout y stderr
        user_data = subprocess.run(
            [
                "swift", 
                "list", 
                user_id,
                "-l",
                "--prefix",
                path,
                "-j"
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  # Esto decodifica automáticamente la salida a cadena de texto
        )
        # user_data.stdout ya es una cadena de texto gracias a text=True
        user_info = json.loads(user_data.stdout)

        return {"message": "objetos de la carpeta {path} listados con exito", "data": user_info}
    
    except subprocess.CalledProcessError as e:
        print(f"Error al listar objetos: {e}")
        return {"error": "Error al listar objetos"}