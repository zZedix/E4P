#!/usr/bin/env python3
"""Simple test script to verify E4P application works."""

import asyncio
import tempfile
from pathlib import Path
from app.crypto.stream import StreamProcessor
from app.crypto.kdf import derive_key, generate_salt
from app.crypto.aead import create_encryptor


async def test_basic_encryption():
    """Test basic encryption and decryption functionality."""
    print("Testing basic encryption/decryption...")
    
    # Create test file
    test_content = b"Hello, World! This is a test file for E4P encryption."
    
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
        
        # Test AES-256-GCM
        print("  Testing AES-256-GCM...")
        header = await processor.encrypt_file(
            input_path=input_path,
            output_path=encrypted_path,
            password=password,
            algorithm="AES-256-GCM"
        )
        
        print(f"    Original size: {len(test_content)} bytes")
        print(f"    Encrypted size: {encrypted_path.stat().st_size} bytes")
        print(f"    Algorithm: {header.algorithm}")
        print(f"    Original name: {header.original_name}")
        
        # Decrypt
        success = await processor.decrypt_file(
            input_path=encrypted_path,
            output_path=decrypted_path,
            password=password
        )
        
        if success:
            with open(decrypted_path, 'rb') as f:
                decrypted_content = f.read()
            
            if decrypted_content == test_content:
                print("    ✓ AES-256-GCM encryption/decryption successful")
            else:
                print("    ✗ AES-256-GCM decryption failed - content mismatch")
                return False
        else:
            print("    ✗ AES-256-GCM decryption failed")
            return False
        
        # Clean up
        encrypted_path.unlink()
        decrypted_path.unlink()
        
        # Test XChaCha20-Poly1305
        print("  Testing XChaCha20-Poly1305...")
        encrypted_path = Path(temp_file.name + "_xchacha.e4p")
        decrypted_path = Path(temp_file.name + "_xchacha_decrypted")
        
        header = await processor.encrypt_file(
            input_path=input_path,
            output_path=encrypted_path,
            password=password,
            algorithm="XCHACHA20-POLY1305"
        )
        
        print(f"    Algorithm: {header.algorithm}")
        
        success = await processor.decrypt_file(
            input_path=encrypted_path,
            output_path=decrypted_path,
            password=password
        )
        
        if success:
            with open(decrypted_path, 'rb') as f:
                decrypted_content = f.read()
            
            if decrypted_content == test_content:
                print("    ✓ XChaCha20-Poly1305 encryption/decryption successful")
            else:
                print("    ✗ XChaCha20-Poly1305 decryption failed - content mismatch")
                return False
        else:
            print("    ✗ XChaCha20-Poly1305 decryption failed")
            return False
        
        # Clean up
        encrypted_path.unlink()
        decrypted_path.unlink()
        
        return True
        
    finally:
        # Clean up input file
        if input_path.exists():
            input_path.unlink()


async def test_key_derivation():
    """Test key derivation functionality."""
    print("Testing key derivation...")
    
    password = "test_password_123"
    salt = generate_salt()
    
    # Test deterministic key derivation
    key1 = derive_key(password, salt)
    key2 = derive_key(password, salt)
    
    if key1 == key2 and len(key1) == 32:
        print("  ✓ Key derivation is deterministic and produces 32-byte keys")
    else:
        print("  ✗ Key derivation failed")
        return False
    
    # Test different salts produce different keys
    salt2 = generate_salt()
    key3 = derive_key(password, salt2)
    
    if key1 != key3:
        print("  ✓ Different salts produce different keys")
    else:
        print("  ✗ Different salts produced same key")
        return False
    
    return True


async def test_encryptors():
    """Test encryption algorithms."""
    print("Testing encryption algorithms...")
    
    key = b"a" * 32
    data = b"Test data for encryption"
    
    # Test AES-256-GCM
    aes_encryptor = create_encryptor("AES-256-GCM", key)
    nonce = aes_encryptor.generate_nonce()
    encrypted = aes_encryptor.encrypt_chunk(data, nonce)
    decrypted = aes_encryptor.decrypt_chunk(encrypted, nonce)
    
    if decrypted == data:
        print("  ✓ AES-256-GCM encryption/decryption successful")
    else:
        print("  ✗ AES-256-GCM encryption/decryption failed")
        return False
    
    # Test XChaCha20-Poly1305
    xchacha_encryptor = create_encryptor("XCHACHA20-POLY1305", key)
    nonce = xchacha_encryptor.generate_nonce()
    encrypted = xchacha_encryptor.encrypt_chunk(data, nonce)
    decrypted = xchacha_encryptor.decrypt_chunk(encrypted, nonce)
    
    if decrypted == data:
        print("  ✓ XChaCha20-Poly1305 encryption/decryption successful")
    else:
        print("  ✗ XChaCha20-Poly1305 encryption/decryption failed")
        return False
    
    return True


async def main():
    """Run all tests."""
    print("E4P Application Test Suite")
    print("=" * 40)
    
    try:
        # Test key derivation
        if not await test_key_derivation():
            return False
        
        print()
        
        # Test encryptors
        if not await test_encryptors():
            return False
        
        print()
        
        # Test full encryption flow
        if not await test_basic_encryption():
            return False
        
        print()
        print("=" * 40)
        print("✓ All tests passed! E4P is working correctly.")
        print()
        print("To start the application, run:")
        print("  uvicorn app.main:app --reload --port 8080")
        print()
        print("Then open http://localhost:8080 in your browser.")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
