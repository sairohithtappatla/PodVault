from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50))
    filename = db.Column(db.String(100))
    user = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
