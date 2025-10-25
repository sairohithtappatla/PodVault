from cryptography.fernet import Fernet
import os

KEY_FILE = "vault.key"

def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key

def load_key():
    if not os.path.exists(KEY_FILE):
        return generate_key()
    return open(KEY_FILE, "rb").read()

def encrypt_file(filepath):
    key = load_key()
    f = Fernet(key)
    with open(filepath, "rb") as f_in:
        data = f_in.read()
    encrypted = f.encrypt(data)
    enc_path = filepath + ".enc"
    with open(enc_path, "wb") as f_out:
        f_out.write(encrypted)
    return enc_path

def decrypt_file(filepath):
    key = load_key()
    f = Fernet(key)
    with open(filepath, "rb") as f_in:
        data = f_in.read()
    decrypted = f.decrypt(data)
    dec_path = filepath.replace(".enc", "")
    with open(dec_path, "wb") as f_out:
        f_out.write(decrypted)
    return dec_path
