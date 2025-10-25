from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os, threading, time
from app.encryption import generate_key

db = SQLAlchemy()
login_manager = LoginManager()

def key_rotation_job(interval=300):
    """Rotate encryption key every 5 min (default)"""
    while True:
        generate_key()
        print("[KeyRotation] Generated new key.")
        time.sleep(interval)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'supersecretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vault.db'

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from app.routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()

    # start background key rotation
    t = threading.Thread(target=key_rotation_job, daemon=True)
    t.start()

    return app
