# 🔐 PodVault - Secure Containerized File Storage

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Podman](https://img.shields.io/badge/Podman-4.0+-purple.svg)](https://podman.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Overview

PodVault is a **secure, multi-tenant file storage system** that demonstrates container-level isolation using Podman. Each user gets their own isolated Alpine container with a unique encryption key, showcasing how containerization can enhance data security beyond traditional cloud storage.

---

## ✨ Features

- ✅ **Per-User Container Isolation** - Each user gets their own Podman container
- ✅ **Unique Encryption Keys** - One Fernet key per vault (stored inside container)
- ✅ **Automatic Key Rotation** - Background scheduler rotates keys every 5 minutes
- ✅ **Web Interface** - Flask-based upload/download dashboard
- ✅ **Real-Time Analytics** - Chart.js visualization of vault activity
- ✅ **Comprehensive Audit Logs** - Track every action with timestamps and IP addresses

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  RHEL Host Machine                      │
│                                         │
│  Flask App (python3 run.py)            │
│  ├── SQLite DB (users, logs)           │
│  ├── Podman CLI access ✅               │
│  └── Port 8080                          │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Vault Containers (Alpine)       │   │
│  ├─────────────────────────────────┤   │
│  │ vault_alice                     │   │
│  │ ├── /vault/data/*.enc           │   │
│  │ └── /vault/keys/master.key      │   │
│  ├─────────────────────────────────┤   │
│  │ vault_bob                       │   │
│  │ ├── /vault/data/*.enc           │   │
│  │ └── /vault/keys/master.key      │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Key Design Decision:**
- Flask runs **on the host** (not containerized) to access Podman CLI
- User vault containers are created **dynamically** via `podman run`
- Each vault has **isolated storage volumes** and encryption keys

---

## 🚀 Prerequisites

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| **RHEL/Fedora/CentOS** | 8.0+ | `cat /etc/redhat-release` |
| **Podman** | 4.0+ | `podman --version` |
| **Python** | 3.9+ | `python3 --version` |
| **pip** | Latest | `pip3 --version` |

---

## 📦 Installation

### ⚠️ IMPORTANT: Run Flask on Host (NOT in Container)

**Why?** Flask needs access to the `podman` command to create vault containers.

### Step 1: Clone Repository

```bash
cd ~
git clone https://github.com/sairohithtappatta/PodVault.git
cd PodVault
```

### Step 2: Install Python Dependencies

```bash
pip3 install --user flask flask_sqlalchemy flask_login cryptography apscheduler
```

Or use requirements.txt:

```bash
pip3 install --user -r requirements.txt
```

### Step 3: Run Flask on Host

```bash
python3 run.py
```

**Expected Output:**
```
🔄 Key rotation scheduler started (every 5 minutes)
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:8080
```

### Step 4: Access Application

Open browser: **http://localhost:8080**

---

## 🎯 Usage Guide

### 1️⃣ Register New User

1. Navigate to **http://localhost:8080/register**
2. Enter username (min 3 chars) and password (min 6 chars)
3. Click **"Create Vault & Register"**
4. System creates isolated Podman container: `vault_username`

**Behind the Scenes:**
```bash
# Podman commands executed automatically
podman run -d --name vault_alice \
  -v vault_alice_data:/vault/data \
  -v vault_alice_keys:/vault/keys \
  alpine:latest sleep infinity

# Encryption key generated inside container
podman exec vault_alice sh -c "echo 'FERNET_KEY' > /vault/keys/master.key"
```

### 2️⃣ Login

1. Navigate to **http://localhost:8080/login**
2. Enter credentials
3. Redirected to home dashboard

### 3️⃣ Upload Files

1. Click **"Click to select file"** zone
2. Choose file → Automatically encrypted with vault's key
3. Stored in container: `/vault/data/filename.enc`

**Encryption Flow:**
```
File → /tmp/file.txt
     → Load vault key from container
     → Encrypt with Fernet
     → Store encrypted in container
     → Delete /tmp file
```

### 4️⃣ Download Files

1. Click **"Download"** button on file
2. File decrypted temporarily
3. Sent to browser
4. Temp file auto-deleted

### 5️⃣ View Analytics

Navigate to **http://localhost:8080/dashboard** to see:
- Total vaults
- Total files
- Recent actions chart

---

## 🔍 Verify Installation

### Check Flask Running

```bash
curl http://localhost:8080
# Should return HTML login page
```

### Check Vault Containers

```bash
# After registering user "alice"
podman ps | grep vault_alice

# Should show:
# vault_alice   alpine:latest   sleep infinity   Up 2 minutes
```

### Inspect Vault Structure

```bash
podman exec vault_alice ls -la /vault/
# Should show:
# drwxr-xr-x  data/
# drwxr-xr-x  keys/
```

### Check Encrypted Files

```bash
podman exec vault_alice ls -la /vault/data/
# Shows: file.txt.enc (encrypted)
```

### View Encryption Key

```bash
podman exec vault_alice cat /vault/keys/master.key
# Shows: 32-byte base64 encoded Fernet key
```

---

## 🐳 Docker/Registry Deployment (Optional)

### Build Image for Registry

```bash
podman build -t podvault:v1 .
podman tag podvault:v1 docker.io/YOUR_USERNAME/podvault:v1
```

### Login to Docker Hub

```bash
podman login docker.io
# Enter username & password
```

### Push to Registry

```bash
podman push docker.io/YOUR_USERNAME/podvault:v1
```

### Pull from Registry

```bash
podman pull docker.io/YOUR_USERNAME/podvault:v1
```

**⚠️ NOTE:** The containerized image is for **demonstration/registry purposes only**. For actual operation, run Flask on the host using `python3 run.py`.

---

## ❌ Common Errors & Solutions

### Error 1: `FileNotFoundError: 'podman'`

**Cause:** Running Flask inside a container (no Podman access)

**Solution:**
```bash
# DON'T DO THIS:
podman run -p 8080:8080 podvault:v1  ❌

# DO THIS:
python3 run.py  ✅
```

### Error 2: `Fernet key must be 32 url-safe base64-encoded bytes`

**Cause:** Vault container not created or key missing

**Solution:**
```bash
# Check container exists
podman ps -a | grep vault_username

# If missing, re-register user
# If exists but stopped:
podman start vault_username
```

### Error 3: `No active vaults found`

**Cause:** No vault containers running

**Solution:**
```bash
# Check running vaults
podman ps --filter "name=vault_"

# Start all stopped vaults
podman start $(podman ps -aq --filter "name=vault_")
```

### Error 4: Download returns 302 redirect

**Cause:** Decryption failed (likely key mismatch after rotation)

**Solution:**
```bash
# Re-upload the file after key rotation completes
# Or check logs for actual error:
python3 run.py  # Look for "DECRYPTION ERROR" in output
```

---

## 📂 Project Structure

```
PodVault/
├── app/
│   ├── __init__.py          # Flask app + APScheduler setup
│   ├── routes.py            # Web routes (login, upload, dashboard)
│   ├── models.py            # SQLAlchemy models (User, AuditLog)
│   ├── key_rotation.py      # Encryption & auto key rotation
│   ├── podman_manager.py    # Container lifecycle management
│   └── templates/
│       ├── base.html        # Base template with navbar
│       ├── login.html       # Login page
│       ├── register.html    # Registration page
│       ├── index.html       # Home dashboard
│       └── dashboard.html   # Analytics page
├── instance/
│   └── vault.db             # SQLite database (auto-created)
├── Dockerfile               # Container build (for demo/registry)
├── podman-compose.yml       # Multi-container config (not used)
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
└── README.md                # This file
```

---

## 🔐 Security Features

| Feature | Implementation | Benefit |
|---------|---------------|---------|
| **Container Isolation** | One Alpine container per user | Breach of one vault ≠ access to others |
| **Unique Keys** | Fernet key stored inside each container | No shared secrets |
| **Key Rotation** | APScheduler (every 5 min) | Re-encrypts all files with new key |
| **Audit Logging** | SQLite logs (user, IP, timestamp) | Track all actions |
| **No Key in DB** | Keys stored in containers, not SQLite | Database breach ≠ decrypt files |

---

## 🎓 For DO188 Presentation

### What to Demonstrate

1. **Containerization Skills**
   ```bash
   podman build -t podvault:v1 .
   podman push docker.io/username/podvault:v1
   ```

2. **Container Orchestration**
   ```bash
   # Show dynamic vault creation
   podman ps --filter "name=vault_"
   ```

3. **Volume Management**
   ```bash
   podman volume ls | grep vault_
   ```

4. **Security Isolation**
   ```bash
   # Show namespace isolation
   podman exec vault_alice ps aux
   podman exec vault_bob ps aux
   ```

### Architecture Explanation

**Key Points:**
- Flask runs on host (not containerized for operation)
- Each user gets their own Alpine container
- Containers share host kernel but isolated via namespaces
- Encryption keys stored inside containers (not on host)

---

## 🛠️ Technologies Used

| Technology | Version | Purpose |
|------------|---------|---------|
| **Podman** | 4.0+ | Container runtime (daemonless) |
| **Python** | 3.9+ | Backend language |
| **Flask** | 2.0+ | Web framework |
| **SQLAlchemy** | 1.4+ | ORM for SQLite |
| **Cryptography** | 40.0+ | Fernet symmetric encryption |
| **APScheduler** | 3.10+ | Background key rotation scheduler |
| **Chart.js** | 3.9+ | Dashboard visualization |
| **Alpine Linux** | latest | Base image for vault containers |

---

## 👥 Development Team

- **Sairohith Tappatta** - [@sairohithtappatta](https://github.com/sairohithtappatta)
- **Sahasra Peram** - Red Hat Academy Student

**Institution:** Red Hat Academy  
**Course:** DO188 - Red Hat OpenShift Development I: Containerizing Applications  
**Year:** 2025

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss proposed changes.

---

## 📞 Support

- **GitHub Issues:** [Report Bug](https://github.com/sairohithtappatta/PodVault/issues)
- **Email:** sairohith.tappatta@example.com

---

## 📚 References

- [Podman Documentation](https://docs.podman.io/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Cryptography Library](https://cryptography.io/)
- [DO188 Course Guide](https://www.redhat.com/en/services/training/do188-red-hat-openshift-development-i-containerizing-applications)

---

**Built with ❤️ for Red Hat Academy DO188**