#logica que recibe un archivo desde un endpoint para despues mandar el archivo por una request a los contenedores de openstack
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
import requests, json
from .auth import openstack_auth_id
openstack_auth_bp = Blueprint('openstack', __name__)

def get_object_list(user_id):
    token = openstack_auth_id(str(user_id))
    url = f"http://" 
    