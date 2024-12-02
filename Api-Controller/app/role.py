import subprocess
from flask import Blueprint, Flask, jsonify, request
from .auth import authorization
from .container import create_container

role_bp = Blueprint('role', __name__)

@role_bp.route('/student', methods = ['POST'])
def association_student_project():
    data = request.get_json()
    user = data["user"]
    project = data["project"]
    try:
        authorization()
        # Asignar el rol al usuario en su proyecto privado
        subprocess.run([
            "openstack", "role", "add",
            "--project", project,
            "--user", user,
            "Alumno_Materia"  
        ], check=True)

        create_container(user, project)

        print(f"Rol 'alumno' asignado exitosamente a '{user}' en el proyecto '{project}'.")
        return {"message": "rol asignado con exito"}
    except subprocess.CalledProcessError as e:
        print(f"Error en el proceso: {e}")
        return {"error": "no se pudo asignar el rol"}

@role_bp.route('/teacher', methods = ['POST'])
def association_teacher_project():
    data = request.get_json()
    user = data["user"]
    project = data["project"]
    try:
        authorization()
        # Asignar el rol al usuario en su proyecto privado
        subprocess.run([
            "openstack", "role", "add",
            "--project", project,
            "--user", user,
            "Profesor_Materia"  
        ], check=True)
        print(f"Rol '' asignado exitosamente a '{user}' en el proyecto '{project}'.")
        return {"message": "rol asignado con exito"}
    except subprocess.CalledProcessError as e:
        print(f"Error en el proceso: {e}")
        return {"error": "no se pudo asignar el rol"}
    
@role_bp.route('/academy', methods = ['POST'])
def association_academia_project():
    data = request.get_json()
    user = data["user"]
    project = data["project"]
    try:
        authorization()
        # Asignar el rol al usuario en su proyecto privado
        subprocess.run([
            "openstack", "role", "add",
            "--project", project,
            "--user", user,
            "Academia"  
        ], check=True)
        print(f"Rol '' asignado exitosamente a '{user}' en el proyecto '{project}'.")
        return {"message": "rol asignado con exito"}
    except subprocess.CalledProcessError as e:
        print(f"Error en el proceso: {e}")
        return {"error": "no se pudo asignar el rol"}