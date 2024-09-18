from flask import Flask, request
from db import db, init_db

app = Flask(__name__)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/test'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa la base de datos
init_db(app)

# Modelo de ejemplo
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.get_json()
    new_user = User(email=data['email'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()  # Cierra la sesión después de hacer commit
    return {"message": "User added"}, 201


if __name__ == '__main__':
    app.run(debug=True)