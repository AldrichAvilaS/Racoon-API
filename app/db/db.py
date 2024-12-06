from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# Inicializa la instancia de SQLAlchemy
db = SQLAlchemy()

# Modelo de rol
class Role(db.Model):
    role_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))

    def __repr__(self):
        return f'<Role {self.name}>'

# Modelo de usuario
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    active = db.Column(db.Boolean, default=False)
    confirmed_at = db.Column(db.DateTime)
    storage_limit = db.Column(db.Integer)
    delete_date = db.Column(db.DateTime)
    openstack_id = db.Column(db.String(255),nullable=False)
    # Llave foránea para el rol
    role_id = db.Column(db.Integer, db.ForeignKey('role.role_id'), nullable=False)
    role = db.relationship('Role', backref='users')

    def __repr__(self):
        return f'<User {self.username}>'

# Modelo de estudiante
class Student(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    boleta = db.Column(db.Integer, unique=True, nullable=False)
    current_semester = db.Column(db.Integer)
    user = db.relationship('User', backref='student')

    def __repr__(self):
        return f'<Student {self.boleta}>'

# Modelo de profesor
class Teacher(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    rfc = db.Column(db.String(20), unique=True, nullable=False)
    user = db.relationship('User', backref='teacher')

    def __repr__(self):
        return f'<Teacher {self.user.username}>'

# Modelo de academia
class Academy(db.Model):
    academy_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    main_teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.user_id'))
    main_teacher = db.relationship('Teacher', backref='academies')
    password = db.Column(db.String(200), nullable=False)
    def __repr__(self):
        return f'<Academy {self.name}>'

# Modelo de materia
class Subject(db.Model):
    subject_id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    swift_scope = db.Column(db.String(255))

    # Llaves foráneas
    academy_id = db.Column(db.Integer, db.ForeignKey('academy.academy_id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.user_id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))

    academy = db.relationship('Academy', backref='subjects')
    teacher = db.relationship('Teacher', backref='subjects')
    group = db.relationship('Group', backref='subjects')

    def __repr__(self):
        return f'<Subject {self.subject_name}>'

# Modelo de grupo
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)  # e.g., 6CV1, 8CV12
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)
    semester = db.relationship('Semester', backref='groups')

    def __repr__(self):
        return f'<Group {self.name}>'

# Modelo de semestre
class Semester(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    semester = db.Column(db.String(10), nullable=False)  # e.g., 2024-01
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    finished_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Semester {self.semester}>'

# Modelo de inscripción
class Enrollment(db.Model):
    enrollment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    status = db.Column(db.String(50), nullable=False)

    user = db.relationship('User', backref='enrollments')
    subject = db.relationship('Subject', backref='enrollments')

    def __repr__(self):
        user = User.query.get(self.user_id)
        subject = Subject.query.get(self.subject_id)
        return f'<Enrollment {user.username} - {subject.subject_name}>'

# Modelo de aviso
class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    notice = db.Column(db.Text, nullable=False)
    date_at_publish = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_at_finish = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Notice {self.id}>'

# Modelo de registro de API
class APILog(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(255), nullable=False)
    user_identifier = db.Column(db.String(255), nullable=False)  
    operation = db.Column(db.String(50), nullable=False)
    container_name = db.Column(db.String(255), nullable=False)
    object_name = db.Column(db.String(255), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    error_message = db.Column(db.Text)

    def __repr__(self):
        return f'<APILog {self.id}>'

# Función para agregar datos por defecto
def insert_default_data():
    if Role.query.count() == 0:
        roles = [
            Role(name='Administrador', description='Funciones de Administrador'),
            Role(name='Academia', description='Funciones de Academia'),
            Role(name='Profesor', description='Funciones de Profesor'),
            Role(name='Estudiante', description='Funciones de Estudiante')
        ]
        db.session.add_all(roles)
        db.session.commit()
        print("Roles por defecto creados")

    if User.query.count() == 0:
        admin_user = User(
            username='admin',
            email='admin@example.com',
            password=generate_password_hash('root'),
            role_id=Role.query.filter_by(name='Administrador').first().role_id,
            openstack_id='00000000000000000000000000000000'
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Usuario administrador por defecto creado")

    if Teacher.query.count() == 0:
        admin_user = User(
            username='Default',
            email='Default@example.com',
            password=generate_password_hash('root'),
            role_id=Role.query.filter_by(name='Profesor').first().role_id,
            openstack_id='00000000000000000000000000000001'
        )
        db.session.add(admin_user)
        db.session.commit()
        teach_default= Teacher(
            user_id=admin_user.id,
            rfc='XXXX000000XX0'
        )
        db.session.add(teach_default)
        db.session.commit()
        print("Usuario administrador por defecto creado")
    if Semester.query.count() == 0:
        current_semester = Semester(
            semester = '2025-01',
            created_at = '2025-01-01 00:00:00',
            finished_at = '2025-06-30 23:59:59'
        )
        db.session.add_all(current_semester)
        db.session.commit()
        print("Semestres por defecto creados")

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        insert_default_data()

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
