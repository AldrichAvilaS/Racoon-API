from flask import request, Blueprint, jsonify

from app.container import create_container
from .auth import authorization, Get_id_with_project
import subprocess

project_bp = Blueprint('project', __name__)
#endopoind para crear un proyecto en openstack para materias que retorne el account de acceso
@project_bp.route('/', methods = ['POST'])
def create_openstack_project_endpoint():
    data = request.get_json()
    project_name = data["project"]
    try:
        authorization()
        # Definir el comando para crear el proyecto en OpenStack
        command = [
            "openstack", "project", "create",
            project_name,
            "--domain", "default",
            "--description", project_name
        ]
        
        # Ejecutar el comando
        subprocess.run(command, check=True)
        
        subprocess.run([
            "openstack", "role", "add",
            "--project", project_name,
            "--user", 'api_creator',
            "admin"  
        ], check=True)
        
        create_container('api_creator', project_name)

        account = Get_id_with_project('api_creator',project_name)

        print(f"Proyecto '{project_name}' creado exitosamente con la descripción: Espacio privado para'{project_name}'.")
        print("account: ",account)
        return jsonify({"message": "proyecto creado con exito", "account": account})
    
    except subprocess.CalledProcessError as e:
        print(f"Error al crear el proyecto: {e}")
        return jsonify({"error": "Error al crear proyecto"})

def create_openstack_project(project_name):
    print("project name:",project_name)
    project_name = str(project_name)
    try:
        authorization()
        # Definir el comando para crear el proyecto en OpenStack
        command = [
            "openstack", "project", "create",
            project_name,
            "--domain", "default",
            "--description", project_name
        ]
        # Ejecutar el comando
        subprocess.run(command, check=True)
        
        subprocess.run([
            "openstack", "role", "add",
            "--project", project_name,
            "--user", 'api_creator',
            "admin"  
        ], check=True)
        
        
        print(f"Proyecto '{project_name}' creado exitosamente con la descripción: Espacio privado para'{project_name}'.")
        return jsonify({"message": "proyecto creado con exito"})
    except subprocess.CalledProcessError as e:
        print(f"Error al crear el proyecto: {e}")
        return jsonify({"error": "Error al crear proyecto"})
