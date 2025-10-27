from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from apscheduler.schedulers.background import BackgroundScheduler
import os

db = SQLAlchemy()
login_manager = LoginManager()

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

    # Start background key rotation scheduler
    from app.key_rotation import rotate_all_vaults
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=rotate_all_vaults,
        trigger="interval",
        minutes=5,  # Rotate every 5 minutes
        id='key_rotation_job',
        name='Rotate all vault keys',
        replace_existing=True
    )
    scheduler.start()
    
    print("🔄 Key rotation scheduler started (every 5 minutes)")

    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))
