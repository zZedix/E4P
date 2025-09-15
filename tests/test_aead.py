"""Tests for AEAD encryption implementations."""

import pytest
from app.crypto.aead import (
    AESGCMEncryptor, 
    XChaCha20Poly1305Encryptor, 
    create_encryptor,
    encrypt_stream,
    decrypt_stream
)
import asyncio


class TestAESGCMEncryptor:
    """Test AES-256-GCM encryption."""
    
    def test_encryptor_creation(self):
        """Test encryptor creation with valid key."""
        key = b"a" * 32  # 32 bytes for AES-256
        encryptor = AESGCMEncryptor(key)
        assert encryptor.get_algorithm_name() == "AES-256-GCM"
    
    def test_encryptor_invalid_key(self):
        """Test encryptor creation with invalid key length."""
        with pytest.raises(ValueError):
            AESGCMEncryptor(b"short_key")
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test encrypt/decrypt roundtrip."""
        key = b"a" * 32
        encryptor = AESGCMEncryptor(key)
        data = b"Hello, World! This is test data."
        
        # Encrypt
        nonce = encryptor.generate_nonce()
        encrypted = encryptor.encrypt_chunk(data, nonce)
        
        # Decrypt
        decrypted = encryptor.decrypt_chunk(encrypted, nonce)
        
        assert decrypted == data
        assert encrypted != data  # Should be different
    
    def test_nonce_generation(self):
        """Test nonce generation."""
        key = b"a" * 32
        encryptor = AESGCMEncryptor(key)
        
        nonce1 = encryptor.generate_nonce()
        nonce2 = encryptor.generate_nonce()
        
        assert len(nonce1) == 12  # AES-GCM nonce size
        assert len(nonce2) == 12
        assert nonce1 != nonce2  # Should be different
    
    def test_invalid_nonce_size(self):
        """Test with invalid nonce size."""
        key = b"a" * 32
        encryptor = AESGCMEncryptor(key)
        data = b"test data"
        
        with pytest.raises(ValueError):
            encryptor.encrypt_chunk(data, b"short_nonce")
        
        with pytest.raises(ValueError):
            encryptor.decrypt_chunk(data, b"short_nonce")


class TestXChaCha20Poly1305Encryptor:
    """Test XChaCha20-Poly1305 encryption."""
    
    def test_encryptor_creation(self):
        """Test encryptor creation with valid key."""
        key = b"a" * 32  # 32 bytes for XChaCha20
        encryptor = XChaCha20Poly1305Encryptor(key)
        assert encryptor.get_algorithm_name() == "XCHACHA20-POLY1305"
    
    def test_encryptor_invalid_key(self):
        """Test encryptor creation with invalid key length."""
        with pytest.raises(ValueError):
            XChaCha20Poly1305Encryptor(b"short_key")
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test encrypt/decrypt roundtrip."""
        key = b"a" * 32
        encryptor = XChaCha20Poly1305Encryptor(key)
        data = b"Hello, World! This is test data."
        
        # Encrypt
        nonce = encryptor.generate_nonce()
        encrypted = encryptor.encrypt_chunk(data, nonce)
        
        # Decrypt
        decrypted = encryptor.decrypt_chunk(encrypted, nonce)
        
        assert decrypted == data
        assert encrypted != data  # Should be different
    
    def test_nonce_generation(self):
        """Test nonce generation."""
        key = b"a" * 32
        encryptor = XChaCha20Poly1305Encryptor(key)
        
        nonce1 = encryptor.generate_nonce()
        nonce2 = encryptor.generate_nonce()
        
        assert len(nonce1) == 24  # XChaCha20 nonce size
        assert len(nonce2) == 24
        assert nonce1 != nonce2  # Should be different
    
    def test_invalid_nonce_size(self):
        """Test with invalid nonce size."""
        key = b"a" * 32
        encryptor = XChaCha20Poly1305Encryptor(key)
        data = b"test data"
        
        with pytest.raises(ValueError):
            encryptor.encrypt_chunk(data, b"short_nonce")
        
        with pytest.raises(ValueError):
            encryptor.decrypt_chunk(data, b"short_nonce")


class TestCreateEncryptor:
    """Test encryptor factory function."""
    
    def test_create_aes_gcm(self):
        """Test creating AES-GCM encryptor."""
        key = b"a" * 32
        encryptor = create_encryptor("AES-256-GCM", key)
        assert isinstance(encryptor, AESGCMEncryptor)
    
    def test_create_xchacha20(self):
        """Test creating XChaCha20 encryptor."""
        key = b"a" * 32
        encryptor = create_encryptor("XCHACHA20-POLY1305", key)
        assert isinstance(encryptor, XChaCha20Poly1305Encryptor)
    
    def test_create_invalid_algorithm(self):
        """Test creating encryptor with invalid algorithm."""
        key = b"a" * 32
        with pytest.raises(ValueError):
            create_encryptor("INVALID_ALGORITHM", key)


class TestStreamEncryption:
    """Test streaming encryption functionality."""
    
    @pytest.mark.asyncio
    async def test_encrypt_stream_aes(self):
        """Test AES-GCM stream encryption."""
        key = b"a" * 32
        encryptor = AESGCMEncryptor(key)
        
        # Create test data
        test_data = [b"chunk1", b"chunk2", b"chunk3"]
        
        async def input_stream():
            for chunk in test_data:
                yield chunk
        
        # Encrypt stream
        encrypted_chunks = []
        async for chunk in encrypt_stream(encryptor, input_stream()):
            encrypted_chunks.append(chunk)
        
        assert len(encrypted_chunks) == 3
        assert all(len(chunk) > 0 for chunk in encrypted_chunks)
    
    @pytest.mark.asyncio
    async def test_encrypt_stream_xchacha20(self):
        """Test XChaCha20 stream encryption."""
        key = b"a" * 32
        encryptor = XChaCha20Poly1305Encryptor(key)
        
        # Create test data
        test_data = [b"chunk1", b"chunk2", b"chunk3"]
        
        async def input_stream():
            for chunk in test_data:
                yield chunk
        
        # Encrypt stream
        encrypted_chunks = []
        async for chunk in encrypt_stream(encryptor, input_stream()):
            encrypted_chunks.append(chunk)
        
        assert len(encrypted_chunks) == 3
        assert all(len(chunk) > 0 for chunk in encrypted_chunks)
    
    @pytest.mark.asyncio
    async def test_decrypt_stream_aes(self):
        """Test AES-GCM stream decryption."""
        key = b"a" * 32
        encryptor = AESGCMEncryptor(key)
        
        # Create test data
        test_data = [b"chunk1", b"chunk2", b"chunk3"]
        
        # Encrypt first
        encrypted_chunks = []
        async def input_stream():
            for chunk in test_data:
                yield chunk
        
        async for chunk in encrypt_stream(encryptor, input_stream()):
            encrypted_chunks.append(chunk)
        
        # Now decrypt
        async def encrypted_stream():
            for chunk in encrypted_chunks:
                yield chunk
        
        decrypted_chunks = []
        async for chunk in decrypt_stream(encryptor, encrypted_stream(), 12):  # 12 bytes nonce for AES-GCM
            decrypted_chunks.append(chunk)
        
        assert len(decrypted_chunks) == 3
        assert decrypted_chunks == test_data
    
    @pytest.mark.asyncio
    async def test_decrypt_stream_xchacha20(self):
        """Test XChaCha20 stream decryption."""
        key = b"a" * 32
        encryptor = XChaCha20Poly1305Encryptor(key)
        
        # Create test data
        test_data = [b"chunk1", b"chunk2", b"chunk3"]
        
        # Encrypt first
        encrypted_chunks = []
        async def input_stream():
            for chunk in test_data:
                yield chunk
        
        async for chunk in encrypt_stream(encryptor, input_stream()):
            encrypted_chunks.append(chunk)
        
        # Now decrypt
        async def encrypted_stream():
            for chunk in encrypted_chunks:
                yield chunk
        
        decrypted_chunks = []
        async for chunk in decrypt_stream(encryptor, encrypted_stream(), 24):  # 24 bytes nonce for XChaCha20
            decrypted_chunks.append(chunk)
        
        assert len(decrypted_chunks) == 3
        assert decrypted_chunks == test_data
