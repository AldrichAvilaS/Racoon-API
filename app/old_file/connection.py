from openstack import connection
import requests

conn = connection.Connection(
    auth_url="http://192.168.1.104:5000/v3",
    project_name="admin",
    username="api_creator",
    password="openpwd1",
    project_domain_name="Default",
    user_domain_name="Default",
    identity_api_version=3,
    image_api_version=2
)

def auth_openstack():
    response = requests.get("http://192.168.1.104:5000")
    print(response.status_code)  # Código de estado HTTP
    print(response.text)         # Contenido de la respuesta
    # Ejemplo: Listar instancias
    #for server in conn.compute.servers():
    #    print(server.name, server.status)