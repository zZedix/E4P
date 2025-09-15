"""Tests for key derivation functions."""

import pytest
from app.crypto.kdf import derive_key, generate_salt, verify_key_derivation


class TestKDF:
    """Test key derivation functionality."""
    
    def test_generate_salt(self):
        """Test salt generation."""
        salt1 = generate_salt()
        salt2 = generate_salt()
        
        assert len(salt1) == 32
        assert len(salt2) == 32
        assert salt1 != salt2  # Should be different each time
    
    def test_derive_key_deterministic(self):
        """Test that key derivation is deterministic with same inputs."""
        password = "test_password_123"
        salt = b"test_salt_32_bytes_long_12345"
        
        key1 = derive_key(password, salt)
        key2 = derive_key(password, salt)
        
        assert key1 == key2
        assert len(key1) == 32  # Should be 32 bytes
    
    def test_derive_key_different_salts(self):
        """Test that different salts produce different keys."""
        password = "test_password_123"
        salt1 = b"test_salt_1_32_bytes_long_1234"
        salt2 = b"test_salt_2_32_bytes_long_1234"
        
        key1 = derive_key(password, salt1)
        key2 = derive_key(password, salt2)
        
        assert key1 != key2
    
    def test_derive_key_different_passwords(self):
        """Test that different passwords produce different keys."""
        password1 = "password1"
        password2 = "password2"
        salt = b"same_salt_32_bytes_long_12345"
        
        key1 = derive_key(password1, salt)
        key2 = derive_key(password2, salt)
        
        assert key1 != key2
    
    def test_verify_key_derivation_correct(self):
        """Test key verification with correct password."""
        password = "test_password_123"
        salt = generate_salt()
        expected_key = derive_key(password, salt)
        
        assert verify_key_derivation(password, salt, expected_key) is True
    
    def test_verify_key_derivation_incorrect(self):
        """Test key verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        salt = generate_salt()
        expected_key = derive_key(password, salt)
        
        assert verify_key_derivation(wrong_password, salt, expected_key) is False
    
    def test_derive_key_empty_password(self):
        """Test key derivation with empty password."""
        password = ""
        salt = generate_salt()
        
        # Should not raise an exception
        key = derive_key(password, salt)
        assert len(key) == 32
    
    def test_derive_key_unicode_password(self):
        """Test key derivation with Unicode password."""
        password = "پسورد_فارسی_123"
        salt = generate_salt()
        
        key = derive_key(password, salt)
        assert len(key) == 32
    
    def test_derive_key_long_password(self):
        """Test key derivation with very long password."""
        password = "a" * 1000  # Very long password
        salt = generate_salt()
        
        key = derive_key(password, salt)
        assert len(key) == 32
