from flask import Flask, jsonify, request

app = Flask(__name__) #para declarar que este es el servidor

@app.route('/') #endpoint de raiz
def root():
        return "Home"
@app.route('/users/<user_id>') #endpoint de raiz
def get_user(user_id):
        user = {
            
        }


if __name__ == '__main__': #si lo que se ejecuta es el main, si corre en modo debug
    app.run(debug=True)