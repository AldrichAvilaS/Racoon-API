import subprocess

def create_openstack_project(project_name):
    try:
        # Definir el comando para crear el proyecto en OpenStack
        command = [
            "openstack", "project", "create",
            project_name,
            "--domain", "default",
            "--description", project_name
        ]
        
        # Ejecutar el comando
        subprocess.run(command, check=True)
        print(f"Proyecto '{project_name}' creado exitosamente con la descripción: Espacio privado para'{project_name}'.")
    except subprocess.CalledProcessError as e:
        print(f"Error al crear el proyecto: {e}")

def create_openstack_student(student_id, password, project_description="Espacio privado para el alumno"):
    try:
        # Crear el usuario (alumno)
        subprocess.run([
            "openstack", "user", "create",
            student_id,
            "--domain", "default",
            "--password", password,
            "--project", student_id
        ], check=True)
        print(f"Usuario '{student_id}' creado exitosamente.")

        # Asignar el rol al usuario en su proyecto privado
        subprocess.run([
            "openstack", "role", "add",
            "--project", student_id,
            "--user", student_id,
            "alumno"  
        ], check=True)
        print(f"Rol 'alumno' asignado exitosamente a '{student_id}' en el proyecto '{student_id}'.")

    except subprocess.CalledProcessError as e:
        print(f"Error en el proceso: {e}")

# Ejemplo de uso
#create_openstack_student(Boleta, password)
#create_openstack_student("2019301521", "password123")
#create_openstack_project(Boleta)
#create_openstack_project("2019301521")