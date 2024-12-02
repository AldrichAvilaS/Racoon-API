from flask import json, request, Blueprint, jsonify
from .auth import Get_id_with_project, authorization, Get_id
from .project import create_openstack_project
from .container import create_container
import subprocess

user_bp = Blueprint('user', __name__)

@user_bp.route('/student', methods = ['POST'])
def create_openstack_student():
    
    data = request.get_json() 
    
    student_id = str(data["student_id"])
    
    project_name = student_id
    
    # print(student_id)

    create_openstack_project(project_name)
    try:
        authorization()
        # Crear el usuario (alumno)
        subprocess.run([
            "openstack", "user", "create",
            student_id,
            "--domain", "default",
            "--password", student_id,
            "--project", student_id
        ], check=True)
        print(f"Usuario '{student_id}' creado exitosamente.")

        # Asignar el rol al usuario en su proyecto privado
        subprocess.run([
            "openstack", "role", "add",
            "--project", student_id,
            "--user", student_id,
            "Alumno"  
        ], check=True)

        create_container(student_id, student_id)

        user_id = Get_id_with_project(student_id, student_id)

        print("account ", user_id)
        print(f"Rol 'alumno' asignado exitosamente a '{student_id}' en el proyecto '{student_id}'.")
        return jsonify({"message": "usuario creado con exito", "id": str(user_id)})

    except subprocess.CalledProcessError as e:
        print(f"Error en el proceso: {e}")
        return jsonify({"error": "no se pudo crear el usuario"})

@user_bp.route('/teacher', methods = ['POST'])
def create_openstack_teacher():
    
    data = request.get_json() 
    
    teacher_id = str(data["student_id"])
    
    project_name = teacher_id
    
    # print(student_id)

    create_openstack_project(project_name)
    try:
        authorization()
        # Crear el usuario (alumno)
        subprocess.run([
            "openstack", "user", "create",
            teacher_id,
            "--domain", "default",
            "--password", teacher_id,
            "--project", teacher_id
        ], check=True)
        print(f"Usuario '{teacher_id}' creado exitosamente.")

        # Asignar el rol al usuario en su proyecto privado
        subprocess.run([
            "openstack", "role", "add",
            "--project", teacher_id,
            "--user", teacher_id,
            "Profesor"  
        ], check=True)

        create_container(teacher_id, teacher_id)

        user_id = Get_id_with_project(teacher_id, teacher_id)

        print("account ", user_id)
        print(f"Rol 'Teacher' asignado exitosamente a '{teacher_id}' en el proyecto '{teacher_id}'.")
        return jsonify({"message": "usuario creado con exito", "id": user_id})

    except subprocess.CalledProcessError as e:
        print(f"Error en el proceso: {e}")
        return jsonify({"error": "no se pudo crear el usuario"})

@user_bp.route('/academy', methods = ['POST'])
def create_openstack_academy():
    
    data = request.get_json() 
    
    academy_id = str(data["academy_id"])
    
    project_name = academy_id
    
    # print(student_id)

    create_openstack_project(project_name)
    try:
        authorization()
        # Crear el usuario (alumno)
        subprocess.run([
            "openstack", "user", "create",
            academy_id,
            "--domain", "default",
            "--password", academy_id,
            "--project", academy_id
        ], check=True)
        print(f"Usuario '{academy_id}' creado exitosamente.")

        # Asignar el rol al usuario en su proyecto privado
        subprocess.run([
            "openstack", "role", "add",
            "--project", academy_id,
            "--user", academy_id,
            "Academia"  
        ], check=True)

        create_container(academy_id, academy_id)

        user_id = Get_id_with_project(academy_id, academy_id)

        print("account ", id)
        print(f"Rol 'Academia' asignado exitosamente a '{academy_id}' en el proyecto '{academy_id}'.")
        return {"message": "usuario creado con exito", "id": user_id}

    except subprocess.CalledProcessError as e:
        print(f"Error en el proceso: {e}")
        return {"error": "no se pudo crear el usuario"}  

