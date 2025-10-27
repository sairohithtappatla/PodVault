from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, AuditLog, User
from app.podman_manager import create_user_vault, list_user_files
from app.key_rotation import encrypt_file_for_vault, decrypt_file_from_vault
import os

main = Blueprint('main', __name__)

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
    logs = AuditLog.query.filter_by(user=current_user.username).order_by(AuditLog.timestamp.desc()).all()
    
    # Get files from user's vault container
    vault_files = list_user_files(current_user.vault_name)
    
    return render_template('index.html', logs=logs, user=current_user, vault_files=vault_files)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('main.register'))
        
        # Create user vault container
        vault_name = create_user_vault(username)
        
        # Create user in database
        user = User(username=username, password=password, vault_name=vault_name)
        db.session.add(user)
        db.session.commit()
        
        # Log vault creation
        db.session.add(AuditLog(
            action="vault_created",
            filename=None,
            user=username,
            vault_name=vault_name,
            ip_address=request.remote_addr
        ))
        db.session.commit()
        
        flash(f'Account created! Your vault: {vault_name}')
        return redirect(url_for('main.login'))
    
    return render_template('register.html')

@main.route('/upload', methods=['POST'])
@login_required
def upload():
    file = request.files['file']
    if file:
        # Save temporarily
        temp_path = os.path.join("/tmp", file.filename)
        file.save(temp_path)
        
        # Encrypt and store in user's vault
        vault_name = current_user.vault_name
        try:
            enc_filename = encrypt_file_for_vault(temp_path, vault_name)
            
            # Log action
            db.session.add(AuditLog(
                action="Encrypted Upload",
                filename=file.filename,
                user=current_user.username,
                vault_name=vault_name,
                ip_address=request.remote_addr,
                status='success'
            ))
            db.session.commit()
            
            flash(f"✅ File '{file.filename}' encrypted in vault {vault_name}!")
        except Exception as e:
            db.session.add(AuditLog(
                action="Upload Failed",
                filename=file.filename,
                user=current_user.username,
                vault_name=vault_name,
                ip_address=request.remote_addr,
                status='failed'
            ))
            db.session.commit()
            flash(f"❌ Upload failed: {str(e)}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    return redirect(url_for('main.index'))

@main.route('/decrypt/<filename>')
@login_required
def decrypt(filename):
    vault_name = current_user.vault_name
    
    try:
        # Decrypt from user's vault
        dec_path = decrypt_file_from_vault(filename, vault_name)
        
        # Log action
        db.session.add(AuditLog(
            action="Decrypted Download",
            filename=filename,
            user=current_user.username,
            vault_name=vault_name,
            ip_address=request.remote_addr,
            status='success'
        ))
        db.session.commit()
        
        return send_file(dec_path, as_attachment=True)
    
    except Exception as e:
        db.session.add(AuditLog(
            action="Decrypt Failed",
            filename=filename,
            user=current_user.username,
            vault_name=vault_name,
            ip_address=request.remote_addr,
            status='failed'
        ))
        db.session.commit()
        flash(f"❌ Decryption failed: {str(e)}")
        return redirect(url_for('main.index'))

@main.route('/dashboard')
@login_required
def dashboard():
    # Get all vaults count
    total_vaults = User.query.count()
    
    # Get all logs
    total_logs = AuditLog.query.count()
    
    # Get user's file count
    total_files = len(list_user_files(current_user.vault_name))
    
    # Recent logs across all users (admin view)
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    return render_template('dashboard.html',
                         total_logs=total_logs, 
                         total_files=total_files,
                         total_vaults=total_vaults,
                         logs=recent_logs)
