"""Tests for E4P container format."""

import pytest
import json
from app.crypto.container import E4PContainer, E4PHeader, E4P_MAGIC


class TestE4PHeader:
    """Test E4P header functionality."""
    
    def test_header_creation(self):
        """Test header creation and serialization."""
        header = E4PHeader(
            algorithm="AES-256-GCM",
            kdf="argon2id",
            kdf_params={"m": 262144, "t": 3, "p": 2},
            salt="dGVzdF9zYWx0",
            nonce="dGVzdF9ub25jZQ==",
            original_name="test.txt",
            original_size=1024,
            timestamp="2024-01-01T00:00:00Z"
        )
        
        header_dict = header.to_dict()
        assert header_dict["alg"] == "AES-256-GCM"
        assert header_dict["kdf"] == "argon2id"
        assert header_dict["orig_name"] == "test.txt"
        assert header_dict["orig_size"] == 1024
    
    def test_header_from_dict(self):
        """Test header creation from dictionary."""
        data = {
            "alg": "AES-256-GCM",
            "kdf": "argon2id",
            "kdf_params": {"m": 262144, "t": 3, "p": 2},
            "salt": "dGVzdF9zYWx0",
            "nonce": "dGVzdF9ub25jZQ==",
            "orig_name": "test.txt",
            "orig_size": 1024,
            "ts": "2024-01-01T00:00:00Z"
        }
        
        header = E4PHeader.from_dict(data)
        assert header.algorithm == "AES-256-GCM"
        assert header.kdf == "argon2id"
        assert header.original_name == "test.txt"
        assert header.original_size == 1024


class TestE4PContainer:
    """Test E4P container functionality."""
    
    def test_container_creation(self):
        """Test container creation."""
        container = E4PContainer("AES-256-GCM")
        assert container.algorithm == "AES-256-GCM"
        assert container.nonce_size == 12
    
    def test_container_xchacha20(self):
        """Test container creation for XChaCha20."""
        container = E4PContainer("XCHACHA20-POLY1305")
        assert container.algorithm == "XCHACHA20-POLY1305"
        assert container.nonce_size == 24
    
    def test_create_header(self):
        """Test header creation."""
        container = E4PContainer("AES-256-GCM")
        salt = b"test_salt_32_bytes_long_12345"
        nonce = b"test_nonce_12"
        original_name = "test_file.txt"
        original_size = 1024
        
        header = container.create_header(salt, nonce, original_name, original_size)
        
        assert header.algorithm == "AES-256-GCM"
        assert header.kdf == "argon2id"
        assert header.original_name == original_name
        assert header.original_size == original_size
        assert len(header.salt) > 0
        assert len(header.nonce) > 0
    
    def test_serialize_header(self):
        """Test header serialization."""
        container = E4PContainer("AES-256-GCM")
        header = E4PHeader(
            algorithm="AES-256-GCM",
            kdf="argon2id",
            kdf_params={"m": 262144, "t": 3, "p": 2},
            salt="dGVzdF9zYWx0",
            nonce="dGVzdF9ub25jZQ==",
            original_name="test.txt",
            original_size=1024,
            timestamp="2024-01-01T00:00:00Z"
        )
        
        serialized = container.serialize_header(header)
        
        # Check magic bytes
        assert serialized[:4] == E4P_MAGIC
        
        # Check header length
        header_len = int.from_bytes(serialized[4:8], 'little')
        assert header_len > 0
        
        # Check JSON data
        json_data = serialized[8:8+header_len]
        header_data = json.loads(json_data.decode('utf-8'))
        assert header_data["alg"] == "AES-256-GCM"
        assert header_data["orig_name"] == "test.txt"
    
    def test_deserialize_header(self):
        """Test header deserialization."""
        container = E4PContainer("AES-256-GCM")
        header = E4PHeader(
            algorithm="AES-256-GCM",
            kdf="argon2id",
            kdf_params={"m": 262144, "t": 3, "p": 2},
            salt="dGVzdF9zYWx0",
            nonce="dGVzdF9ub25jZQ==",
            original_name="test.txt",
            original_size=1024,
            timestamp="2024-01-01T00:00:00Z"
        )
        
        # Serialize and then deserialize
        serialized = container.serialize_header(header)
        deserialized_header, bytes_consumed = container.deserialize_header(serialized)
        
        assert deserialized_header.algorithm == header.algorithm
        assert deserialized_header.kdf == header.kdf
        assert deserialized_header.original_name == header.original_name
        assert deserialized_header.original_size == header.original_size
        assert bytes_consumed == len(serialized)
    
    def test_deserialize_invalid_magic(self):
        """Test deserialization with invalid magic bytes."""
        container = E4PContainer("AES-256-GCM")
        invalid_data = b"INVALID_MAGIC" + b"\x00\x00\x00\x10" + b"{}"
        
        with pytest.raises(ValueError, match="wrong magic bytes"):
            container.deserialize_header(invalid_data)
    
    def test_deserialize_too_short(self):
        """Test deserialization with too short data."""
        container = E4PContainer("AES-256-GCM")
        short_data = b"E4P1"
        
        with pytest.raises(ValueError, match="too short"):
            container.deserialize_header(short_data)
    
    def test_validate_header_valid(self):
        """Test header validation with valid header."""
        container = E4PContainer("AES-256-GCM")
        header = E4PHeader(
            algorithm="AES-256-GCM",
            kdf="argon2id",
            kdf_params={"m": 262144, "t": 3, "p": 2},
            salt="dGVzdF9zYWx0",
            nonce="dGVzdF9ub25jZQ==",
            original_name="test.txt",
            original_size=1024,
            timestamp="2024-01-01T00:00:00Z"
        )
        
        assert container.validate_header(header) is True
    
    def test_validate_header_invalid_algorithm(self):
        """Test header validation with invalid algorithm."""
        container = E4PContainer("AES-256-GCM")
        header = E4PHeader(
            algorithm="INVALID_ALGORITHM",
            kdf="argon2id",
            kdf_params={"m": 262144, "t": 3, "p": 2},
            salt="dGVzdF9zYWx0",
            nonce="dGVzdF9ub25jZQ==",
            original_name="test.txt",
            original_size=1024,
            timestamp="2024-01-01T00:00:00Z"
        )
        
        assert container.validate_header(header) is False
    
    def test_validate_header_invalid_kdf(self):
        """Test header validation with invalid KDF."""
        container = E4PContainer("AES-256-GCM")
        header = E4PHeader(
            algorithm="AES-256-GCM",
            kdf="invalid_kdf",
            kdf_params={"m": 262144, "t": 3, "p": 2},
            salt="dGVzdF9zYWx0",
            nonce="dGVzdF9ub25jZQ==",
            original_name="test.txt",
            original_size=1024,
            timestamp="2024-01-01T00:00:00Z"
        )
        
        assert container.validate_header(header) is False
    
    def test_validate_header_invalid_params(self):
        """Test header validation with invalid KDF parameters."""
        container = E4PContainer("AES-256-GCM")
        header = E4PHeader(
            algorithm="AES-256-GCM",
            kdf="argon2id",
            kdf_params={"m": 100, "t": 0, "p": 0},  # Invalid parameters
            salt="dGVzdF9zYWx0",
            nonce="dGVzdF9ub25jZQ==",
            original_name="test.txt",
            original_size=1024,
            timestamp="2024-01-01T00:00:00Z"
        )
        
        assert container.validate_header(header) is False
    
    def test_validate_header_invalid_salt(self):
        """Test header validation with invalid salt."""
        container = E4PContainer("AES-256-GCM")
        header = E4PHeader(
            algorithm="AES-256-GCM",
            kdf="argon2id",
            kdf_params={"m": 262144, "t": 3, "p": 2},
            salt="invalid_base64!",
            nonce="dGVzdF9ub25jZQ==",
            original_name="test.txt",
            original_size=1024,
            timestamp="2024-01-01T00:00:00Z"
        )
        
        assert container.validate_header(header) is False
    
    def test_get_expected_nonce_size(self):
        """Test getting expected nonce size for algorithms."""
        container = E4PContainer("AES-256-GCM")
        
        assert container.get_expected_nonce_size("AES-256-GCM") == 12
        assert container.get_expected_nonce_size("XCHACHA20-POLY1305") == 24
        
        with pytest.raises(ValueError):
            container.get_expected_nonce_size("INVALID_ALGORITHM")
