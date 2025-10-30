import subprocess
from cryptography.fernet import Fernet

def create_user_vault(username):
    """Create isolated Podman container for user"""
    vault_name = f"vault_{username}"
    
    print(f"🔧 Creating vault: {vault_name}")
    
    # Check if vault already exists
    try:
        check_container = subprocess.run([
            "podman", "ps", "-a", "--filter", f"name={vault_name}", "--format", "{{.Names}}"
        ], capture_output=True, text=True, check=True)
        
        if vault_name in check_container.stdout:
            print(f"⚠️ Vault {vault_name} already exists, using existing vault")
            return vault_name
    except subprocess.CalledProcessError as e:
        print(f"❌ Error checking for existing vault: {e.stderr}")
        raise Exception(f"Podman check failed: {e.stderr}")
    
    # Create volumes (ignore if already exist)
    try:
        subprocess.run(["podman", "volume", "create", f"{vault_name}_data"], 
                       stderr=subprocess.DEVNULL, check=False)
        subprocess.run(["podman", "volume", "create", f"{vault_name}_keys"], 
                       stderr=subprocess.DEVNULL, check=False)
        print(f"✅ Volumes created for {vault_name}")
    except Exception as e:
        print(f"⚠️ Volume creation warning: {e}")
    
    # Create container
    try:
        result = subprocess.run([
            "podman", "run", "-d",
            "--name", vault_name,
            "-v", f"{vault_name}_data:/vault/data",
            "-v", f"{vault_name}_keys:/vault/keys",
            "alpine:latest",
            "sleep", "infinity"
        ], capture_output=True, text=True, check=True)
        print(f"✅ Container created: {vault_name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Container creation failed: {e.stderr}")
        raise Exception(f"Failed to create Podman container: {e.stderr}")
    
    # Generate initial key
    try:
        key = Fernet.generate_key()
        result = subprocess.run([
            "podman", "exec", vault_name,
            "sh", "-c", 
            f"mkdir -p /vault/keys /vault/data && echo '{key.decode()}' > /vault/keys/master.key"
        ], capture_output=True, text=True, check=True)
        print(f"✅ Encryption key generated for {vault_name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Key generation failed: {e.stderr}")
        raise Exception(f"Failed to generate encryption key: {e.stderr}")
    
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