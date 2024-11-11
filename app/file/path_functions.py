
from datetime import datetime
import hashlib
import os
from pathlib import Path
import time

from flask_jwt_extended import get_jwt_identity

from ..db.path import store_path, zip_path
from ..db.db import Role, db, User, Student, Teacher, Academy
# Función para generar la ruta de guardado con limpieza de espacios en blanco
def get_save_directory(user, file_path):
    # Limpiar espacios en blanco no deseados
    store_path_clean = store_path.strip()
    boleta_clean = str(get_user_identifier(user.id)).strip()
    file_path_clean = file_path.strip() if file_path else ''
    
    return os.path.join(store_path_clean, boleta_clean, file_path_clean)

# Función para verificar si un archivo ya existe y asignar un nuevo nombre si es necesario
def get_unique_file_path(directory, file_name):
    base_name, extension = os.path.splitext(file_name)
    counter = 1
    new_file_path = os.path.join(directory, file_name)

    # Itera hasta encontrar un nombre de archivo único
    while os.path.exists(new_file_path):
        new_file_name = f"{base_name}({counter}){extension}"
        new_file_path = os.path.join(directory, new_file_name)
        counter += 1

    return new_file_path

# Función para verificar el hash de integridad del chunk
def verify_chunk_integrity(chunk_data, expected_hash):
    hash_object = hashlib.sha256()
    hash_object.update(chunk_data)
    return hash_object.hexdigest() == expected_hash

# Función que obtiene la estructura de directorios y archivos recursivamente
def get_directory_structure(root_dir):
    structure = {'': {'folders': [], 'files': []}}  # Estructura inicial para la raíz

    # Recorremos el directorio raíz con glob
    for path in root_dir.glob('**/*'):
        relative_path = path.relative_to(root_dir).as_posix()  # Convertimos la ruta a formato compatible ('/')

        if path.is_dir():
            # Si la carpeta está en la raíz, agregarla a 'folders' de la raíz
            parent_dir = '' if path.parent == root_dir else path.parent.relative_to(root_dir).as_posix()

            # Si el directorio no existe en la estructura, lo inicializamos
            if relative_path not in structure:
                structure[relative_path] = {'folders': [], 'files': []}

            # Añadir la carpeta al padre
            structure[parent_dir]['folders'].append(relative_path)

        elif path.is_file():
            # Obtener el tamaño y la fecha de modificación
            file_size = path.stat().st_size  # Tamaño del archivo en bytes
            mod_time = path.stat().st_mtime  # Fecha de última modificación en formato timestamp
            mod_time = datetime.fromtimestamp(mod_time).strftime('%d/%m/%Y')  # Convertir a formato legible

            # Si el archivo está en la raíz, agregarlo bajo la clave ''
            parent_dir = '' if path.parent == root_dir else path.parent.relative_to(root_dir).as_posix()

            # Si el directorio no existe en la estructura, lo inicializamos
            if parent_dir not in structure:
                structure[parent_dir] = {'folders': [], 'files': []}

            # Añadir el archivo con su tamaño y fecha de modificación
            structure[parent_dir]['files'].append({
                'path': relative_path,
                'size': bytes_to_megabytes(file_size),
                'date': mod_time
            })

    return structure

def bytes_to_megabytes(size_in_bytes):
    return round(size_in_bytes / (1024 * 1024), 2)  # 1 MB = 1024 * 1024 bytes


# Función que obtiene la estructura de directorios y archivos de una carpeta específica
def get_specific_directory_structure(dir_path):
    structure = {'folders': [], 'files': []}  # Inicializamos la estructura

    # Verificamos si la ruta es un directorio
    if not dir_path.is_dir():
        raise NotADirectoryError(f"{dir_path} no es un directorio válido.")
    
    # Recorremos los archivos y carpetas dentro del directorio proporcionado
    for path in dir_path.iterdir():
        relative_path = path.name  # Usamos solo el nombre del archivo/carpeta

        if path.is_dir():
            structure['folders'].append(relative_path)
        elif path.is_file():
            # Obtener el tamaño y la fecha de modificación
            file_size = path.stat().st_size  # Tamaño del archivo en bytes
            file_size_mb = bytes_to_megabytes(file_size)  # Convertir tamaño a megabytes
            mod_time = path.stat().st_mtime  # Fecha de última modificación en formato timestamp
            mod_time = datetime.fromtimestamp(mod_time).strftime('%d/%m/%Y') # Convertir a formato legible

            # Añadir el archivo con su tamaño y fecha de modificación
            structure['files'].append({
                'path': relative_path,
                'size': bytes_to_megabytes(file_size),
                'date': mod_time
            })

    return structure

#funcion para crear directorio de usuario por identificador
def create_user_directory(user):
    user_directory = os.path.join(store_path, str(user.get_boleta()).strip())
    if not os.path.exists(user_directory):
        os.makedirs(user_directory)
    return user_directory


# Función para asegurar rutas y prevenir path traversal
def secure_path(user_directory, relative_path):
    # Convertir user_directory y relative_path a cadenas
    user_directory = str(user_directory)
    relative_path = os.path.normpath(relative_path)

    # Si el relative_path es '.' (directorio actual), no se necesita ningún ajuste
    if relative_path == '.':
        full_path = user_directory
    else:
        full_path = os.path.normpath(os.path.join(user_directory, relative_path))

    # Normalizar las rutas para asegurar consistencia en las barras invertidas
    print(f"Relative Path: {relative_path}")
    print(f"Full Path: {full_path}")
    print(f"User Directory: {user_directory}")

    # Verificar que la ruta esté dentro del directorio del usuario
    common_path = os.path.commonpath([full_path, user_directory])
    print(f"Common Path: {common_path}")

    # Convertimos ambas rutas a rutas absolutas
    user_directory_abs = os.path.abspath(user_directory)
    full_path_abs = os.path.abspath(full_path)
    
    # Comparamos las rutas absolutas
    print(f"User Directory (Absoluta): {user_directory_abs}")
    print(f"Full Path (Absoluto): {full_path_abs}")

    if not full_path_abs.startswith(user_directory_abs):
        print("Acceso no autorizado: la ruta no está dentro del directorio asignado")
        raise ValueError("Intento de acceso no autorizado fuera del directorio asignado")

    return full_path


# Función para obtener el directorio base del usuario
def get_user_directory(user_identifier):
    return Path(store_path) / str(user_identifier)

# Función para obtener el ID del rol basado en su nombre
def get_role_id_by_name(role_name):
    role = Role.query.filter_by(name=role_name).first()
    if role:
        return role.role_id
    return None  # O puedes lanzar una excepción si el rol no existe

# Función auxiliar para obtener el usuario actual basado en su identificador
def get_current_user():
    identifier = get_jwt_identity()
    user = None
    print(identifier)
    # Buscar al usuario según el identificador
    student = Student.query.filter_by(boleta=identifier).first()
    if student:
        user = student.user
    else:
        teacher = Teacher.query.filter_by(rfc=identifier).first()
        if teacher:
            user = teacher.user 
        else:
            academy = Academy.query.filter_by(academy_id=identifier).first()
            if academy:
                user = academy.main_teacher.user
            else:
                # Asumimos que los administradores se autentican con user.id
                user = User.query.filter_by(id=identifier, role_id=get_role_id_by_name('Administrador')).first()

    return user

# Función para obtener el identificador del usuario basado en su rol
def get_user_identifier(user_id):
    user = User.query.get(user_id)
    if not user:
        return None

    if user.role.name == 'Estudiante':
        student = Student.query.filter_by(user_id=user_id).first()
        return student.boleta if student else None
    elif user.role.name == 'Profesor':
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        return teacher.rfc if teacher else None
    elif user.role.name == 'Administrador':
        return f'admin_{user.id}'
    elif user.role.name == 'Academia':
        academy = Academy.query.filter_by(main_teacher_id=user_id).first()
        return academy.academy_id if academy else None
    else:
        return None

# Función para eliminar un archivo después de un retraso
def delayed_file_deletion(filepath, delay=180):
    time.sleep(delay)
    try:
        os.remove(filepath)
        print(f"Archivo {filepath} eliminado del servidor después de {delay} segundos.")
    except Exception as e:
        print(f"Error al eliminar el archivo {filepath}: {e}")
