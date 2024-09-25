from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# Inicializa la instancia de SQLAlchemy
db = SQLAlchemy()

# Modelo de rol
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))

    def __repr__(self):
        return f'<Role {self.name}>'

# Modelo de usuario
class User(db.Model, UserMixin):
    boleta = db.Column(db.Integer, unique=True, primary_key=True)  # Cambiado para que boleta sea la clave primaria
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, default=True)
    confirmed_at = db.Column(db.DateTime)

    # Llave foránea para el rol
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    role = db.relationship('Role', backref='users')  # Relación con Role

    def __repr__(self):
        return f'<User {self.email}>'
    
    def get_id(self):
        return self.boleta  # Devuelve el ID del usuario
    def get_role(self):
        return self.role_id
    def get_email(self):
        return self.email
    def get_name(self):
        return self.nombre

def init_db(app):
    """Inicializa la base de datos con la aplicación."""
    db.init_app(app)
    with app.app_context():
        db.create_all()  # Crea las tablas en la base de datos
