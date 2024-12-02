# Ejecutar el archivo de configuración

import subprocess
import os

from flask import json, jsonify

def authorization():
    config_file = "app/api_admin.sh"
    abs_path = os.path.abspath(config_file)
    print("Directorio actual de ejecución:", os.getcwd())
    # Imprimir la ruta absoluta para verificarla
    print("Ruta absoluta esperada:", abs_path)

    # Comprobar si el archivo existe en la ruta esperada
    if not os.path.exists(abs_path):
        print("El archivo no existe en la ruta:", abs_path)
    else:
        print("El archivo existe en la ruta:", abs_path)


    config_file = abs_path
    command = f'source {config_file} && env'
    proc = subprocess.Popen(['bash', '-c', command], stdout=subprocess.PIPE, text=True)

    # Diccionario para almacenar las variables
    env_vars = {}
    for line in proc.stdout:
        key, _, value = line.partition("=")
        env_vars[key] = value.strip()

    proc.communicate()

    # Puedes ahora acceder a las variables como OS_PROJECT_NAME, OS_USERNAME, etc.
    # print(env_vars.get('OS_PROJECT_NAME'))  # Ejemplo para mostrar el valor de OS_PROJECT_NAME

    # Opcionalmente, puedes actualizar el entorno del programa Python
    os.environ.update(env_vars)

    # Acceso a la variable desde os.environ
    # print(os.getenv('OS_PROJECT_NAME'))

#Funcion para autenticar un usuario en un proyecto en especifico
def authorization_with_user(user, project): 
    print("intentando autenticar a", user, "en el proyecto", project)
    if not user == "api_creator":
        print("no es el usuario api_creator")
        env_vars = {
            "OS_PROJECT_DOMAIN_NAME": "Default",
            "OS_USER_DOMAIN_NAME": "Default",
            "OS_PROJECT_NAME": project,
            "OS_USERNAME": user,
            "OS_PASSWORD": user,
            "OS_AUTH_URL": "http://controller:5000/v3",
            "OS_IDENTITY_API_VERSION": "3",
            "OS_IMAGE_API_VERSION": "2",
        }
    else:
        print("es el usuario api_creator")
        env_vars = {
            "OS_PROJECT_DOMAIN_NAME": "Default",
            "OS_USER_DOMAIN_NAME": "Default",
            "OS_PROJECT_NAME": project,
            "OS_USERNAME": user,
            "OS_PASSWORD": 'openpwd1',
            "OS_AUTH_URL": "http://controller:5000/v3",
            "OS_IDENTITY_API_VERSION": "3",
            "OS_IMAGE_API_VERSION": "2",
        }

    # Mostrar las variables originales
    # print("Variables originales:")
    # for key, value in env_vars.items():
    #     print(f"{key}={value}")

    # Actualizar las variables de entorno del proceso actual
    os.environ.update(env_vars)

    # Verificar que las variables se han establecido
    # print("\nVariables de entorno actualizadas:")
    # for key in env_vars:
    #     print(f"{key}={os.getenv(key)}")

    # Ahora puedes usar estas variables en tu código o en subprocessos posteriores
    # Por ejemplo, ejecutar un comando que utilice estas variables
    # subprocess.run(['tu_comando'], env=os.environ)

def Get_id(container):

    try:
        print("intentando obtener la cuenta de", container)
        authorization_with_user('api_creator', container)
        # Ejecuta el comando OpenStack CLI para mostrar la información del usuario en formato JSON
        user_data = subprocess.run(
            ["openstack", "container", "show", "-f", "json", container],
            check=True,                # Lanza una excepción si el comando falla
            stdout=subprocess.PIPE,    # Captura la salida estándar
            stderr=subprocess.PIPE     # Captura los errores estándar
        )
        
        # Decodifica la salida de bytes a cadena de texto
        user_json_str = user_data.stdout.decode('utf-8')
        
        # Parsear el JSON a un diccionario de Python
        user_info = json.loads(user_json_str)
        
        # Extraer el campo 'id' del diccionario
        user_id = user_info['account'] 
        print("account ", user_id)  #se obtiene la cuenta
        
        if user_id:
            return user_id
        else:
            print("No se pudo obtener la cuenta del usuario.")
            return jsonify({"error": "No se pudo obtener el ID del usuario."}), 500
    except subprocess.CalledProcessError as e:
        # Maneja errores en la ejecución del comando
        error_message = e.stderr.decode('utf-8').strip()
        print(f"Error al ejecutar el comando: {error_message}")
        return jsonify({"error": f"Error al ejecutar el comando: {error_message}"}), 500
    except json.JSONDecodeError as e:
        # Maneja errores al parsear el JSON
        print(f"Error al decodificar el JSON: {e}")
        return jsonify({"error": "Error al procesar la respuesta JSON."}), 500
    except Exception as e:
        # Maneja cualquier otro tipo de error
        print(f"Ocurrió un error inesperado: {e}")
        return jsonify({"error": "Ocurrió un error inesperado."}), 500
    
def Get_id_with_project(user,project):
    try:
        authorization_with_user(user, project)
        # Ejecuta el comando OpenStack CLI para mostrar la información del usuario en formato JSON
        result = subprocess.run(
            ["openstack", "container", "show", "-f", "json", user],
            check=True,                # Lanza una excepción si el comando falla
            stdout=subprocess.PIPE,    # Captura la salida estándar
            stderr=subprocess.PIPE     # Captura los errores estándar
        )
        
         # Decodifica la salida JSON y extrae el campo 'account'
        output = result.stdout.decode('utf-8')
        user_info = json.loads(output)
        user_id = user_info['account']  # Se asume que siempre está presente
        
        if user_id:
            return user_id
        else:
            print("No se pudo obtener el ID del usuario.")
            return jsonify({"error": "No se pudo obtener el ID del usuario."}), 500
    except subprocess.CalledProcessError as e:
        # Maneja errores en la ejecución del comando
        error_message = e.stderr.decode('utf-8').strip()
        print(f"Error al ejecutar el comando: {error_message}")
        return jsonify({"error": f"Error al ejecutar el comando: {error_message}"}), 500
    except json.JSONDecodeError as e:
        # Maneja errores al parsear el JSON
        print(f"Error al decodificar el JSON: {e}")
        return jsonify({"error": "Error al procesar la respuesta JSON."}), 500
    except Exception as e:
        # Maneja cualquier otro tipo de error
        print(f"Ocurrió un error inesperado: {e}")
        return jsonify({"error": "Ocurrió un error inesperado."}), 500