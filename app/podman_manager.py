import subprocess
from cryptography.fernet import Fernet

def create_user_vault(username):
    """Create isolated Podman container for user"""
    vault_name = f"vault_{username}"
    
    # Create volumes
    subprocess.run(["podman", "volume", "create", f"{vault_name}_data"])
    subprocess.run(["podman", "volume", "create", f"{vault_name}_keys"])
    
    # Create container
    subprocess.run([
        "podman", "run", "-d",
        "--name", vault_name,
        "-v", f"{vault_name}_data:/vault/data",
        "-v", f"{vault_name}_keys:/vault/keys",
        "alpine:latest",  # Lightweight base image
        "sleep", "infinity"  # Keep container running
    ])
    
    # Generate initial key
    key = Fernet.generate_key()
    subprocess.run([
        "podman", "exec", vault_name,
        "sh", "-c", 
        f"mkdir -p /vault/keys /vault/data && echo '{key.decode()}' > /vault/keys/master.key"
    ])
    
    return vault_name

def list_user_files(vault_name):
    """List all files in user's vault"""
    result = subprocess.run([
        "podman", "exec", vault_name,
        "ls", "/vault/data"
    ], capture_output=True, text=True)
    
    return result.stdout.strip().split('\n') if result.stdout else []

def delete_vault(vault_name):
    """Delete user's vault container and volumes"""
    subprocess.run(["podman", "stop", vault_name])
    subprocess.run(["podman", "rm", vault_name])
    subprocess.run(["podman", "volume", "rm", f"{vault_name}_data"])
    subprocess.run(["podman", "volume", "rm", f"{vault_name}_keys"])