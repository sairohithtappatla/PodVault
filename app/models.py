from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    vault_name = db.Column(db.String(100))  # NEW: Track user's vault container
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # NEW

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50))
    filename = db.Column(db.String(100))
    user = db.Column(db.String(50))
    vault_name = db.Column(db.String(100))  # NEW: Track which vault
    ip_address = db.Column(db.String(50))  # NEW: Security audit
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='success')  # NEW: Track failures
