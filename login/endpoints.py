from flask_login import UserMixin
from flask_security import db

class User(db.Document, UserMixin):
    email = db.EmailField(unique=True)
    boleta = db.integerField(unique=True)
    password = db.StringField()
    nombre = db.StingField()
    active = db.BooleanField(default=True)
    confirmed_at = db.DateTimeField()
    roles = db.ListField(db.StringField(), default=[])