"""Tests for complete encryption/decryption flow."""

import pytest
import tempfile
import os
from pathlib import Path
from app.crypto.stream import StreamProcessor
from app.crypto.kdf import derive_key, generate_salt
from app.crypto.aead import create_encryptor


class TestEncryptFlow:
    """Test complete encryption and decryption flow."""
    
    @pytest.mark.asyncio
    async def test_encrypt_decrypt_roundtrip_aes(self):
        """Test complete encrypt/decrypt roundtrip with AES-256-GCM."""
        # Create test file
        test_content = b"Hello, World! This is a test file for encryption."
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file.flush()
            input_path = Path(temp_file.name)
        
        try:
            # Create output paths
            encrypted_path = Path(temp_file.name + ".e4p")
            decrypted_path = Path(temp_file.name + "_decrypted")
            
            processor = StreamProcessor()
            password = "test_password_123"
            
            # Encrypt file
            header = await processor.encrypt_file(
                input_path=input_path,
                output_path=encrypted_path,
                password=password,
                algorithm="AES-256-GCM"
            )
            
            # Verify header
            assert header.algorithm == "AES-256-GCM"
            assert header.kdf == "argon2id"
            assert header.original_name == input_path.name
            assert header.original_size == len(test_content)
            
            # Verify encrypted file exists and is different
            assert encrypted_path.exists()
            assert encrypted_path.stat().st_size > len(test_content)
            
            # Decrypt file
            success = await processor.decrypt_file(
                input_path=encrypted_path,
                output_path=decrypted_path,
                password=password
            )
            
            assert success is True
            assert decrypted_path.exists()
            
            # Verify decrypted content
            with open(decrypted_path, 'rb') as f:
                decrypted_content = f.read()
            
            assert decrypted_content == test_content
            
        finally:
            # Cleanup
            for path in [input_path, encrypted_path, decrypted_path]:
                if path.exists():
                    path.unlink()
    
    @pytest.mark.asyncio
    async def test_encrypt_decrypt_roundtrip_xchacha20(self):
        """Test complete encrypt/decrypt roundtrip with XChaCha20-Poly1305."""
        # Create test file
        test_content = b"Hello, World! This is a test file for XChaCha20 encryption."
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file.flush()
            input_path = Path(temp_file.name)
        
        try:
            # Create output paths
            encrypted_path = Path(temp_file.name + ".e4p")
            decrypted_path = Path(temp_file.name + "_decrypted")
            
            processor = StreamProcessor()
            password = "test_password_456"
            
            # Encrypt file
            header = await processor.encrypt_file(
                input_path=input_path,
                output_path=encrypted_path,
                password=password,
                algorithm="XCHACHA20-POLY1305"
            )
            
            # Verify header
            assert header.algorithm == "XCHACHA20-POLY1305"
            assert header.kdf == "argon2id"
            assert header.original_name == input_path.name
            assert header.original_size == len(test_content)
            
            # Decrypt file
            success = await processor.decrypt_file(
                input_path=encrypted_path,
                output_path=decrypted_path,
                password=password
            )
            
            assert success is True
            assert decrypted_path.exists()
            
            # Verify decrypted content
            with open(decrypted_path, 'rb') as f:
                decrypted_content = f.read()
            
            assert decrypted_content == test_content
            
        finally:
            # Cleanup
            for path in [input_path, encrypted_path, decrypted_path]:
                if path.exists():
                    path.unlink()
    
    @pytest.mark.asyncio
    async def test_encrypt_wrong_password(self):
        """Test decryption with wrong password."""
        # Create test file
        test_content = b"Secret data that should not be accessible with wrong password."
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file.flush()
            input_path = Path(temp_file.name)
        
        try:
            # Create output paths
            encrypted_path = Path(temp_file.name + ".e4p")
            decrypted_path = Path(temp_file.name + "_decrypted")
            
            processor = StreamProcessor()
            correct_password = "correct_password"
            wrong_password = "wrong_password"
            
            # Encrypt file
            await processor.encrypt_file(
                input_path=input_path,
                output_path=encrypted_path,
                password=correct_password,
                algorithm="AES-256-GCM"
            )
            
            # Try to decrypt with wrong password
            success = await processor.decrypt_file(
                input_path=encrypted_path,
                output_path=decrypted_path,
                password=wrong_password
            )
            
            assert success is False
            assert not decrypted_path.exists()
            
        finally:
            # Cleanup
            for path in [input_path, encrypted_path, decrypted_path]:
                if path.exists():
                    path.unlink()
    
    @pytest.mark.asyncio
    async def test_large_file_encryption(self):
        """Test encryption of a larger file."""
        # Create a larger test file (1MB)
        test_content = b"X" * (1024 * 1024)  # 1MB of data
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file.flush()
            input_path = Path(temp_file.name)
        
        try:
            # Create output paths
            encrypted_path = Path(temp_file.name + ".e4p")
            decrypted_path = Path(temp_file.name + "_decrypted")
            
            processor = StreamProcessor()
            password = "large_file_password"
            
            # Encrypt file
            header = await processor.encrypt_file(
                input_path=input_path,
                output_path=encrypted_path,
                password=password,
                algorithm="AES-256-GCM"
            )
            
            # Verify header
            assert header.original_size == len(test_content)
            
            # Decrypt file
            success = await processor.decrypt_file(
                input_path=encrypted_path,
                output_path=decrypted_path,
                password=password
            )
            
            assert success is True
            assert decrypted_path.exists()
            
            # Verify decrypted content
            with open(decrypted_path, 'rb') as f:
                decrypted_content = f.read()
            
            assert decrypted_content == test_content
            
        finally:
            # Cleanup
            for path in [input_path, encrypted_path, decrypted_path]:
                if path.exists():
                    path.unlink()
    
    @pytest.mark.asyncio
    async def test_get_file_info(self):
        """Test getting file information without decryption."""
        # Create test file
        test_content = b"Test file for info extraction."
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file.flush()
            input_path = Path(temp_file.name)
        
        try:
            # Create output path
            encrypted_path = Path(temp_file.name + ".e4p")
            
            processor = StreamProcessor()
            password = "info_test_password"
            
            # Encrypt file
            original_header = await processor.encrypt_file(
                input_path=input_path,
                output_path=encrypted_path,
                password=password,
                algorithm="AES-256-GCM"
            )
            
            # Get file info
            file_info = await processor.get_file_info(encrypted_path)
            
            assert file_info is not None
            assert file_info.algorithm == original_header.algorithm
            assert file_info.kdf == original_header.kdf
            assert file_info.original_name == original_header.original_name
            assert file_info.original_size == original_header.original_size
            
        finally:
            # Cleanup
            for path in [input_path, encrypted_path]:
                if path.exists():
                    path.unlink()
    
    @pytest.mark.asyncio
    async def test_invalid_e4p_file(self):
        """Test handling of invalid E4P file."""
        # Create invalid file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"This is not a valid E4P file")
            temp_file.flush()
            invalid_path = Path(temp_file.name)
        
        try:
            processor = StreamProcessor()
            
            # Try to get info from invalid file
            file_info = await processor.get_file_info(invalid_path)
            assert file_info is None
            
            # Try to decrypt invalid file
            decrypted_path = Path(temp_file.name + "_decrypted")
            success = await processor.decrypt_file(
                input_path=invalid_path,
                output_path=decrypted_path,
                password="any_password"
            )
            
            assert success is False
            assert not decrypted_path.exists()
            
        finally:
            # Cleanup
            for path in [invalid_path, decrypted_path]:
                if path.exists():
                    path.unlink()
