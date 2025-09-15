"""Authenticated Encryption with Associated Data (AEAD) implementations."""

import os
from abc import ABC, abstractmethod
from typing import Tuple, AsyncGenerator
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from nacl.secret import SecretBox
from nacl.utils import random


class AEADEncryptor(ABC):
    """Abstract base class for AEAD encryption."""
    
    @abstractmethod
    def encrypt_chunk(self, data: bytes, nonce: bytes) -> bytes:
        """Encrypt a chunk of data."""
        pass
    
    @abstractmethod
    def decrypt_chunk(self, data: bytes, nonce: bytes) -> bytes:
        """Decrypt a chunk of data."""
        pass
    
    @abstractmethod
    def generate_nonce(self) -> bytes:
        """Generate a new nonce."""
        pass
    
    @abstractmethod
    def get_algorithm_name(self) -> str:
        """Get the algorithm name."""
        pass


class AESGCMEncryptor(AEADEncryptor):
    """AES-256-GCM encryption implementation."""
    
    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("AES-256-GCM requires a 32-byte key")
        self.key = key
        self.cipher = AESGCM(key)
    
    def encrypt_chunk(self, data: bytes, nonce: bytes) -> bytes:
        """Encrypt data using AES-256-GCM."""
        if len(nonce) != 12:
            raise ValueError("AES-GCM requires a 12-byte nonce")
        return self.cipher.encrypt(nonce, data, None)
    
    def decrypt_chunk(self, data: bytes, nonce: bytes) -> bytes:
        """Decrypt data using AES-256-GCM."""
        if len(nonce) != 12:
            raise ValueError("AES-GCM requires a 12-byte nonce")
        return self.cipher.decrypt(nonce, data, None)
    
    def generate_nonce(self) -> bytes:
        """Generate a 12-byte nonce for AES-GCM."""
        return os.urandom(12)
    
    def get_algorithm_name(self) -> str:
        """Get algorithm name."""
        return "AES-256-GCM"


class XChaCha20Poly1305Encryptor(AEADEncryptor):
    """XChaCha20-Poly1305 encryption implementation."""
    
    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("XChaCha20-Poly1305 requires a 32-byte key")
        self.key = key
        self.box = SecretBox(key)
    
    def encrypt_chunk(self, data: bytes, nonce: bytes) -> bytes:
        """Encrypt data using XChaCha20-Poly1305."""
        if len(nonce) != 24:
            raise ValueError("XChaCha20-Poly1305 requires a 24-byte nonce")
        # XChaCha20-Poly1305 encrypts and returns nonce + ciphertext + tag
        # We need to prepend our own nonce to match the expected format
        encrypted = self.box.encrypt(data, nonce)
        return nonce + encrypted[24:]  # Remove the nonce from encrypted data and add our own
    
    def decrypt_chunk(self, data: bytes, nonce: bytes) -> bytes:
        """Decrypt data using XChaCha20-Poly1305."""
        if len(nonce) != 24:
            raise ValueError("XChaCha20-Poly1305 requires a 24-byte nonce")
        # For XChaCha20-Poly1305, the data contains nonce + ciphertext + tag
        # We need to extract just the ciphertext + tag part
        if len(data) < 24:
            raise ValueError("Invalid encrypted data length")
        # Remove the nonce from the beginning
        ciphertext = data[24:]
        return self.box.decrypt(ciphertext, nonce)
    
    def generate_nonce(self) -> bytes:
        """Generate a 24-byte nonce for XChaCha20-Poly1305."""
        return random(24)
    
    def get_algorithm_name(self) -> str:
        """Get algorithm name."""
        return "XCHACHA20-POLY1305"


def create_encryptor(algorithm: str, key: bytes) -> AEADEncryptor:
    """
    Create an encryptor instance based on algorithm name.
    
    Args:
        algorithm: Algorithm name ("AES-256-GCM" or "XCHACHA20-POLY1305")
        key: Encryption key
        
    Returns:
        AEADEncryptor instance
        
    Raises:
        ValueError: If algorithm is not supported
    """
    if algorithm == "AES-256-GCM":
        return AESGCMEncryptor(key)
    elif algorithm == "XCHACHA20-POLY1305":
        return XChaCha20Poly1305Encryptor(key)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


async def encrypt_stream(
    encryptor: AEADEncryptor, 
    input_stream: AsyncGenerator[bytes, None],
    chunk_size: int = 1024 * 1024  # 1MB chunks
) -> AsyncGenerator[bytes, None]:
    """
    Encrypt a stream of data using the specified encryptor.
    
    Args:
        encryptor: AEAD encryptor instance
        input_stream: Async generator yielding data chunks
        chunk_size: Size of chunks to process
        
    Yields:
        Encrypted data chunks
    """
    async for chunk in input_stream:
        if len(chunk) == 0:
            continue
            
        # Generate nonce for this chunk
        nonce = encryptor.generate_nonce()
        
        # Encrypt the chunk
        encrypted_chunk = encryptor.encrypt_chunk(chunk, nonce)
        
        # Yield nonce + encrypted data
        yield nonce + encrypted_chunk


async def decrypt_stream(
    encryptor: AEADEncryptor,
    input_stream: AsyncGenerator[bytes, None],
    nonce_size: int
) -> AsyncGenerator[bytes, None]:
    """
    Decrypt a stream of data using the specified encryptor.
    
    Args:
        encryptor: AEAD encryptor instance
        input_stream: Async generator yielding encrypted data chunks
        nonce_size: Size of nonce in bytes
        
    Yields:
        Decrypted data chunks
    """
    async for chunk in input_stream:
        if len(chunk) <= nonce_size:
            continue
            
        # Split nonce and encrypted data
        nonce = chunk[:nonce_size]
        encrypted_data = chunk[nonce_size:]
        
        # Decrypt the chunk
        decrypted_chunk = encryptor.decrypt_chunk(encrypted_data, nonce)
        
        yield decrypted_chunk
