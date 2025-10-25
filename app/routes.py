from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, AuditLog, User
from app.encryption import encrypt_file, decrypt_file
import os

main = Blueprint('main', __name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            flash('Login successful!')
            return redirect(url_for('main.index'))
        flash('Invalid credentials!')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out!')
    return redirect(url_for('main.login'))

@main.route('/')
@login_required
def index():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return render_template('index.html', logs=logs, user=current_user)

@main.route('/upload', methods=['POST'])
@login_required
def upload():
    file = request.files['file']
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        enc_path = encrypt_file(filepath)
        db.session.add(AuditLog(action="Encrypted Upload",
                                filename=file.filename,
                                user=current_user.username))
        db.session.commit()
        flash(f"File '{file.filename}' encrypted successfully!")
    return redirect(url_for('main.index'))

@main.route('/decrypt/<filename>')
@login_required
def decrypt(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        flash("File not found!")
        return redirect(url_for('main.index'))
    dec_path = decrypt_file(filepath)
    db.session.add(AuditLog(action="Decrypted Download",
                            filename=filename,
                            user=current_user.username))
    db.session.commit()
    return send_file(dec_path, as_attachment=True)

@main.route('/dashboard')
@login_required
def dashboard():
    total_logs = AuditLog.query.count()
    total_files = len(os.listdir(UPLOAD_FOLDER))
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(5).all()
    return render_template('dashboard.html',total_logs=total_logs, total_files=total_files,logs=recent_logs)
