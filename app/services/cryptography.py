import os
from cryptography.fernet import Fernet
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

argon2_hasher = PasswordHasher()

def hash_password_argon2(password: str) -> str:
    return argon2_hasher.hash(password)

def verify_password_argon2(password_hash: str, password: str) -> bool:
    try:
        argon2_hasher.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False

def generate_aes_key() -> str:
    return Fernet.generate_key().decode("utf-8")

def get_aes_cipher(encryption_key: str | None = None) -> Fernet:
    key = encryption_key or os.getenv("DATA_ENCRYPTION_KEY")
    if not key:
        raise ValueError("DATA_ENCRYPTION_KEY não configurada")
    return Fernet(key.encode("utf-8"))

def encrypt_data_aes(data: str | None, encryption_key: str | None = None) -> str | None:
    if data is None:
        return None
    cipher = get_aes_cipher(encryption_key)
    return cipher.encrypt(str(data).encode("utf-8")).decode("utf-8")

def decrypt_data_aes(encrypted_data: str | None, encryption_key: str | None = None) -> str | None:
    if encrypted_data is None:
        return None
    cipher = get_aes_cipher(encryption_key)
    return cipher.decrypt(encrypted_data.encode("utf-8")).decode("utf-8")