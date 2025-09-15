"""Key derivation functions using Argon2id."""

import os
from typing import Tuple
from argon2 import PasswordHasher, Type
from argon2.exceptions import HashingError

from app.config import settings


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive encryption key from password using Argon2id.
    
    Args:
        password: User-provided password
        salt: Random salt bytes
        
    Returns:
        Derived key bytes
        
    Raises:
        HashingError: If key derivation fails
    """
    try:
        # Convert memory cost from MB to KB
        memory_cost = settings.argon2_memory_mb * 1024
        
        ph = PasswordHasher(
            memory_cost=memory_cost,
            time_cost=settings.argon2_time_cost,
            parallelism=settings.argon2_parallelism,
            hash_len=settings.argon2_key_len,
            type=Type.ID
        )
        
        # Hash the password with the salt
        hash_result = ph.hash(password, salt=salt)
        
        # Extract the raw hash bytes from the encoded format
        # The hash result contains the raw hash bytes after the encoded header
        import base64
        # Split by $ to get the parts: $argon2id$v=19$m=262144,t=3,p=2$salt$hash
        parts = hash_result.split('$')
        if len(parts) >= 6:
            # The last part is the base64-encoded hash
            hash_b64 = parts[-1]
            # Add padding if needed
            missing_padding = len(hash_b64) % 4
            if missing_padding:
                hash_b64 += '=' * (4 - missing_padding)
            hash_bytes = base64.b64decode(hash_b64)
            return hash_bytes[:settings.argon2_key_len]
        else:
            # Fallback: use the hash string as bytes
            return hash_result.encode('utf-8')[:settings.argon2_key_len]
        
    except HashingError as e:
        raise HashingError(f"Key derivation failed: {e}")


def generate_salt() -> bytes:
    """Generate a cryptographically secure random salt."""
    return os.urandom(32)  # 32 bytes = 256 bits


def verify_key_derivation(password: str, salt: bytes, expected_key: bytes) -> bool:
    """
    Verify that a password and salt produce the expected key.
    
    Args:
        password: User-provided password
        salt: Salt used for key derivation
        expected_key: Expected derived key
        
    Returns:
        True if key derivation matches expected result
    """
    try:
        derived_key = derive_key(password, salt)
        return derived_key == expected_key
    except HashingError:
        return False
