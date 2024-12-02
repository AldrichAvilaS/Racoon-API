import subprocess
from .auth import authorization_with_user
from flask import Blueprint, jsonify, request

container_bp = Blueprint('container', __name__)

def create_container(user,project):
    """
    Crea un contenedor en OpenStack para un usuario dado su nombre de usuario.
    """
    try:
        authorization_with_user(user, project) # Crear la autorización para el usuario en ese proyecto
        # Crear el contenedor del usuario en su proyecto
        subprocess.run([
            "openstack", "container", "create", user
        ], check=True)
        print(f"Contenedor '{user}' creado exitosamente.")    

    except subprocess.CalledProcessError as e:
        print(f"Error en el proceso: {e}")
        


@container_bp.route('/', methods = ['POST'])
def create_container_endpoint():
    data = request.get_json()
    user = data["user"]
    project = data["project"]

    """
    Crea un contenedor en OpenStack para un usuario dado su nombre de usuario.
    """

    try:
        authorization_with_user(user, project) # Crear la autorización para el usuario en ese proyecto
        # Crear el contenedor del usuario en su proyecto
        subprocess.run([
            "openstack", "container", "create",
            "--name", user
        ], check=True)

        return {"message": "contenedor creado con exito"}

    except subprocess.CalledProcessError as e:
        print(f"Error en el proceso: {e}")
        return jsonify({"error": "no se pudo crear el contenedor"})