from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
import os
import base64
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

argon2_hasher = PasswordHasher()

# ==================== ARGON2 HASHING ====================

def hash_password_argon2(password: str) -> str:
    return argon2_hasher.hash(password)

def verify_password_argon2(password_hash: str, password: str) -> bool:
    try:
        argon2_hasher.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False

# ==================== AES-256 ENCRYPTION ====================

def generate_aes_key() -> str:
    key = Fernet.generate_key()
    return key.decode('utf-8')

def get_aes_cipher(encryption_key: str) -> Fernet:
    return Fernet(encryption_key.encode('utf-8'))

def encrypt_data_aes(data: str, encryption_key: str) -> str:
    cipher = get_aes_cipher(encryption_key)
    encrypted = cipher.encrypt(data.encode('utf-8'))
    return encrypted.decode('utf-8')

def decrypt_data_aes(encrypted_data: str, encryption_key: str) -> str:
    cipher = get_aes_cipher(encryption_key)
    decrypted = cipher.decrypt(encrypted_data.encode('utf-8'))
    return decrypted.decode('utf-8')