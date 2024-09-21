from flask import Flask, jsonify, request
from app import create_app

app = create_app() #para declarar que este es el servidor

if __name__ == '__main__': #si lo que se ejecuta es el main, si corre en modo debug
    app.run(debug=True)