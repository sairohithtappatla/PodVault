import subprocess
from cryptography.fernet import Fernet

def create_user_vault(username):
    """Create isolated Podman container for user"""
    vault_name = f"vault_{username}"
    
    print(f"🔧 Creating vault: {vault_name}")
    
    # Check if vault already exists
    try:
        check_container = subprocess.run([
            "podman", "ps", "-a", "--filter", f"name=^{vault_name}$", "--format", "{{.Names}}"
        ], capture_output=True, text=True, check=True)
        
        if vault_name in check_container.stdout:
            print(f"⚠️ Vault {vault_name} already exists, using existing vault")
            # Make sure it's running
            subprocess.run(["podman", "start", vault_name], stderr=subprocess.DEVNULL)
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
    
    # Create container - FIXED: Use proper list format
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
        print(f"   Container ID: {result.stdout.strip()[:12]}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Container creation failed:")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
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
        print(f"❌ Key generation failed:")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        # Clean up the container if key generation fails
        subprocess.run(["podman", "rm", "-f", vault_name], stderr=subprocess.DEVNULL)
        raise Exception(f"Failed to generate encryption key: {e.stderr}")
    
    return vault_name

def list_user_files(vault_name):
    """List all files in user's vault"""
    try:
        result = subprocess.run([
            "podman", "exec", vault_name,
            "ls", "/vault/data"
        ], capture_output=True, text=True, check=True)
        
        files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        return files if files else []
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error listing files in {vault_name}: {e.stderr}")
        return []

def delete_vault(vault_name):
    """Delete user's vault container and volumes"""
    try:
        subprocess.run(["podman", "stop", vault_name], 
                      stderr=subprocess.DEVNULL, check=False)
        subprocess.run(["podman", "rm", vault_name], 
                      stderr=subprocess.DEVNULL, check=False)
        subprocess.run(["podman", "volume", "rm", f"{vault_name}_data"], 
                      stderr=subprocess.DEVNULL, check=False)
        subprocess.run(["podman", "volume", "rm", f"{vault_name}_keys"], 
                      stderr=subprocess.DEVNULL, check=False)
        print(f"✅ Vault {vault_name} deleted successfully")
    except Exception as e:
        print(f"⚠️ Error deleting vault {vault_name}: {e}")