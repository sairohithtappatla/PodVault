# 🔐 PodVault - Secure Containerized File Storage

## Overview

PodVault is a secure, multi-tenant file storage system that uses Podman containers for per-user isolation, with automatic encryption key rotation.

## Features

- ✅ Per-user isolated Podman containers
- ✅ Unique encryption keys per vault
- ✅ Automatic key rotation every 5 minutes
- ✅ Web-based upload/download interface
- ✅ Real-time activity dashboard
- ✅ Comprehensive audit logging

## Architecture

```
Flask App ──→ SQLite DB (users, logs)
    │
    ├─→ Vault Container 1 (User A)
    │   ├── /vault/data/ (encrypted files)
    │   └── /vault/keys/master.key
    │
    └─→ Vault Container 2 (User B)
        ├── /vault/data/ (encrypted files)
        └── /vault/keys/master.key
```

## Prerequisites

- Podman 4.0+
- Python 3.9+
- Red Hat Enterprise Linux (or compatible)

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-username/Podvault.git
cd Podvault
```

### 2. Build Container Image

```bash
podman build -t podvault:v1 .
```

### 3. Run with Podman Compose

```bash
podman-compose up
```

### 4. Access Application

Open browser: `http://localhost:8080`

## Usage

### Register New User

1. Navigate to `/register`
2. Create account → Automatically creates isolated vault container
3. Login with credentials

### Upload Files

1. Go to home page
2. Select file and click "Upload & Encrypt"
3. File is encrypted with vault-specific key

### Download Files

1. View encrypted files list
2. Click "Download (Decrypt)"
3. File is temporarily decrypted and downloaded

### View Dashboard

1. Navigate to `/dashboard`
2. See total vaults, files, and activity logs
3. View Chart.js visualization of recent actions

## Container Registry

**Public Image**: `docker.io/your-username/podvault:v1.0`

Pull command:

```bash
podman pull docker.io/your-username/podvault:v1.0
```

## Project Structure

```
Podvault/
├── app/
│   ├── __init__.py           # Flask initialization + APScheduler
│   ├── routes.py             # Web routes (login, upload, dashboard)
│   ├── models.py             # User & AuditLog models
│   ├── key_rotation.py       # Encryption & key rotation
│   ├── podman_manager.py     # Container management
│   └── templates/            # HTML templates
├── Dockerfile                # Container build instructions
├── podman-compose.yml        # Multi-container orchestration
├── requirements.txt          # Python dependencies
└── run.py                    # Application entry point
```

## Key Technologies

- **Podman**: Container runtime
- **Flask**: Web framework
- **SQLAlchemy**: ORM for database
- **Cryptography**: Fernet encryption
- **APScheduler**: Background key rotation
- **Chart.js**: Dashboard visualization

## Security Features

1. **Isolation**: Each user's data in separate container
2. **Encryption**: Fernet symmetric encryption
3. **Key Rotation**: Automatic every 5 minutes
4. **Audit Trail**: All actions logged with timestamps
5. **No Shared Keys**: Breach of one vault ≠ access to others

## Development Team

- [ SAIROHITH TAPPATLA , SAHASRA PERAM ] - Red Hat Academy Student

## License

MIT License
