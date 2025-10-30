from cryptography.fernet import Fernet
import os
import subprocess
from datetime import datetime

def get_vault_key_path(vault_name):
    """Get key file path for specific vault"""
    return f"/vault/keys/{vault_name}/master.key"

def generate_vault_key(vault_name):
    """Generate key for specific vault"""
    key = Fernet.generate_key()
    
    # Store inside Podman container
    subprocess.run([
        "podman", "exec", vault_name,
        "sh", "-c", f"mkdir -p /vault/keys && echo '{key.decode()}' > /vault/keys/master.key"
    ])
    return key

def load_vault_key(vault_name):
    """Load key from specific vault container"""
    result = subprocess.run([
        "podman", "exec", vault_name,
        "cat", "/vault/keys/master.key"
    ], capture_output=True, text=True)
    
    return result.stdout.strip().encode()

def encrypt_file_for_vault(filepath, vault_name):
    """Encrypt file using vault-specific key"""
    key = load_vault_key(vault_name)
    f = Fernet(key)
    
    with open(filepath, "rb") as f_in:
        data = f_in.read()
    
    encrypted = f.encrypt(data)
    
    # Store in vault's container
    enc_filename = os.path.basename(filepath) + ".enc"
    subprocess.run([
        "podman", "exec", vault_name,
        "sh", "-c", f"cat > /vault/data/{enc_filename}"
    ], input=encrypted)
    
    return enc_filename

def decrypt_file_from_vault(filename, vault_name):
    """Decrypt file from specific vault"""
    key = load_vault_key(vault_name)
    f = Fernet(key)
    
    # Read encrypted file from container
    result = subprocess.run([
        "podman", "exec", vault_name,
        "cat", f"/vault/data/{filename}"
    ], capture_output=True, check=True)
    
    # Decrypt the file
    decrypted = f.decrypt(result.stdout)
    
    # Save temporarily for download
    dec_path = f"/tmp/{filename.replace('.enc', '')}"
    with open(dec_path, "wb") as f_out:
        f_out.write(decrypted)
    
    return dec_path

# ============ KEY ROTATION WITH RE-ENCRYPTION ============

def rotate_vault_key(vault_name):
    """Rotate encryption key for specific vault and re-encrypt all files"""
    
    print(f"🔄 Starting key rotation for {vault_name}...")
    
    # 1. Load old key
    try:
        old_key_data = subprocess.run([
            "podman", "exec", vault_name,
            "cat", "/vault/keys/master.key"
        ], capture_output=True, text=True, check=True).stdout.strip()
        
        old_key = old_key_data.encode()
        old_fernet = Fernet(old_key)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to load key for {vault_name}: {e}")
        return False
    
    # 2. Generate new key
    new_key = Fernet.generate_key()
    new_fernet = Fernet(new_key)
    
    # 3. Get all encrypted files
    try:
        files_output = subprocess.run([
            "podman", "exec", vault_name,
            "ls", "/vault/data"
        ], capture_output=True, text=True, check=True).stdout.strip()
        
        if not files_output:
            print(f"⚠️ No files in {vault_name}, skipping re-encryption")
            files = []
        else:
            files = [f for f in files_output.split('\n') if f.strip()]
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to list files in {vault_name}: {e}")
        return False
    
    # 4. Re-encrypt each file
    re_encrypted_count = 0
    for filename in files:
        if not filename.endswith('.enc'):
            continue
        
        try:
            # Read encrypted file
            encrypted_data = subprocess.run([
                "podman", "exec", vault_name,
                "cat", f"/vault/data/{filename}"
            ], capture_output=True, check=True).stdout
            
            if not encrypted_data:
                print(f"  ⚠️ Empty file: {filename}, skipping")
                continue
            
            # Decrypt with old key
            plaintext = old_fernet.decrypt(encrypted_data)
            
            # Re-encrypt with new key
            new_encrypted = new_fernet.encrypt(plaintext)
            
            # Write back to container
            subprocess.run([
                "podman", "exec", vault_name,
                "sh", "-c", f"cat > /vault/data/{filename}"
            ], input=new_encrypted, check=True)
            
            re_encrypted_count += 1
            print(f"  ✅ Re-encrypted: {filename}")
            
        except Exception as e:
            print(f"  ❌ Error re-encrypting {filename}: {e}")
            continue
    
    # 5. Archive old key
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        subprocess.run([
            "podman", "exec", vault_name,
            "sh", "-c", 
            f"mkdir -p /vault/keys/archive && "
            f"echo '{old_key_data}' > /vault/keys/archive/key_{timestamp}.old"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Failed to archive old key for {vault_name}: {e}")
    
    # 6. Save new key as active
    try:
        subprocess.run([
            "podman", "exec", vault_name,
            "sh", "-c", f"echo '{new_key.decode()}' > /vault/keys/master.key"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to save new key for {vault_name}: {e}")
        return False
    
    print(f"✅ Key rotation completed for {vault_name} ({re_encrypted_count} files re-encrypted)")
    return True

def rotate_all_vaults():
    """Rotate keys for all active vaults"""
    print("\n🔄 Starting key rotation for all vaults...")
    
    try:
        result = subprocess.run([
            "podman", "ps", 
            "--filter", "name=vault_",
            "--format", "{{.Names}}"
        ], capture_output=True, text=True, check=True)
        
        # FIXED: Proper list comprehension syntax
        vault_names = [v.strip() for v in result.stdout.strip().split('\n') 
                      if v.strip() and v.strip().startswith('vault_')]
        
        if not vault_names:
            print("⚠️ No active vaults found")
            return
        
        print(f"📦 Found {len(vault_names)} active vaults")
        
        success_count = 0
        for vault_name in vault_names:
            if rotate_vault_key(vault_name):
                success_count += 1
        
        print(f"\n✅ Key rotation completed: {success_count}/{len(vault_names)} vaults successful")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to list vaults: {e}")