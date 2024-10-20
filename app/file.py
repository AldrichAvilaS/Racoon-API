# logica de manejo de archivos
# Version 0.2
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from .db import db, User, APILog
import os, base64

file_bp = Blueprint('file', __name__)


# Ruta para recibir un solo archivo
@file_bp.route('/upload/single', methods=['POST'])
@jwt_required()  # Proteger con JWT
def upload_file():
    current_boleta = get_jwt_identity()
    user = User.query.get(current_boleta)
    data = request.get_json()  # Recibe JSON
    if 'file' not in data or 'filename' not in data:
        return jsonify({"error": "No se recibió archivo o nombre de archivo"}), 400
    
    file_data = data['file']  # Archivo codificado en base64
    file_name = data['filename']  # Nombre del archivo
    file_path = data.get('path', '')  # Opcionalmente, se recibe una ruta para guardar el archivo
    
    try:
        # Decodificar el archivo base64
        file_bytes = base64.b64decode(file_data)
        
        # Generar la ruta completa donde se guardará el archivo
        save_directory = os.path.join('F:/files/'+str(user.get_boleta())+ file_path+'/')
        os.makedirs(save_directory, exist_ok=True)  # Crear el directorio si no existe
        print(save_directory)
        
        save_path = os.path.join(save_directory, file_name)
        
        # Guardar el archivo
        with open(save_path, 'wb') as file:
            file.write(file_bytes)
        
        return jsonify({"message": "Archivo cargado correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@file_bp.route('/upload/lot', methods=['POST'])
@jwt_required()  # Proteger con JWT
def upload_multiple_files():
    current_boleta = get_jwt_identity()
    user = User.query.get(current_boleta)
    data = request.get_json()  # Recibe JSON
    if 'files' not in data:
        return jsonify({"error": "No se encontraron archivos"}), 400
    
    files = data['files']  # Lista de archivos, cada uno con 'file' y 'filename'
    file_path = data.get('path', '')  # Opcionalmente, se recibe una ruta para guardar los archivos
    
    try:
        for file_info in files:
            file_data = file_info['file']  # Archivo codificado en base64
            file_name = file_info['filename']  # Nombre del archivo
            
            # Decodificar el archivo base64
            file_bytes = base64.b64decode(file_data)
            
            # Generar la ruta completa donde se guardará cada archivo
            save_directory = os.path.join('F:/files/'+str(user.get_boleta())+ file_path+'/')
            print(save_directory)
            os.makedirs(save_directory, exist_ok=True)  # Crear el directorio si no existe
            
            save_path = os.path.join(save_directory, file_name)
            
            # Guardar el archivo
            with open(save_path, 'wb') as file:
                file.write(file_bytes)
        
        return jsonify({"message": "Archivos cargados correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
