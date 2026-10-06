"""Crypto functions"""

from cryptography.fernet import Fernet


def generate_key():
    """Generate a new key for encryption"""
    return Fernet.generate_key().decode()


def encrypt(data, key):
    """Encrypt data with a given key"""
    return Fernet(key).encrypt(data.encode()).decode() if data else None


def decrypt(data, key):
    """Decrypt data with a given key"""
    return Fernet(key).decrypt(data).decode() if data else None
