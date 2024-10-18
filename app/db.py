from flask_sqlalchemy import SQLAlchemy

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
class User(db.Model):
    boleta = db.Column(db.Integer, unique=True, primary_key=True)  # Cambiado para que boleta sea la clave primaria
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    current_semester = db.Column(db.Integer, default=1)
    nombre = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, default=False)
    confirmed_at = db.Column(db.DateTime)
    storage_limit = db.Column(db.Integer)
    delete_date = db.Column(db.DateTime)
    
    # Llave foránea para el rol
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    role = db.relationship('Role', backref='users')  # Relación con Role

    def __repr__(self):
        return f'<User {self.email}>'
    def get_id(self):
        return self.boleta  # Devuelve el ID del usuario
    def get_boleta(self):
        return self.boleta  # Devuelve el ID del usuario
    def get_role(self):
        return self.role_id
    def get_email(self):
        return self.email
    def get_name(self):
        return self.nombre


class Subject(db.Model):
    subject_id = db.Column(db.Integer, primary_key=True)
    academy_id = db.Column(db.Integer, db.ForeignKey('academy.id'))  # Relación con Academy
    subject_name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.boleta'))  # Relación con User (profesor)
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='subjects')  # Relación con el profesor
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))  # Relación con Group
    group = db.relationship('Group', backref='subjects')
    description = db.Column(db.Text)
    swift_scope = db.Column(db.String(255))


class Enrollment(db.Model):
    enrollment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.boleta'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    status = db.Column(db.String(50), nullable=False)

class Academy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    main_teacher_id = db.Column(db.Integer, db.ForeignKey('user.boleta'))  # Llave foránea hacia User (profesor)
    main_teacher = db.relationship('User', foreign_keys=[main_teacher_id], backref='academies')  # Relación con profesor

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    semester = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    finished_at = db.Column(db.DateTime)

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    notice = db.Column(db.Text, nullable=False)
    date_at_publish = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_at_finish = db.Column(db.DateTime)

class APILog(db.Model):
    __tablename__ = 'api_logs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Identificador único
    user_id = db.Column(db.String(255), nullable=False)                # ID del usuario
    operation = db.Column(db.String(50), nullable=False)               # Tipo de operación
    container_name = db.Column(db.String(255), nullable=False)         # Nombre del contenedor
    object_name = db.Column(db.String(255), nullable=False)            # Nombre del objeto
    status_code = db.Column(db.Integer, nullable=False)                # Código de estado HTTP
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())  # Marca de tiempo    status_code = db.Column(db.Integer, nullable=False)                # Código de estado HTTP
    error_message = db.Column(db.Text)                                 # Mensaje de error, si lo hay

def init_db(app):
    """Inicializa la base de datos con la aplicación."""
    db.init_app(app)
    with app.app_context():
        db.create_all()  # Crea las tablas en la base de datos
