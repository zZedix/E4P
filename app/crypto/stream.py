"""Streaming encryption/decryption utilities."""

import os
import aiofiles
from typing import AsyncGenerator, Tuple, Optional
from pathlib import Path

from .aead import create_encryptor, encrypt_stream, decrypt_stream
from .kdf import derive_key, generate_salt
from .container import E4PContainer, E4PHeader


class StreamProcessor:
    """Handles streaming encryption and decryption operations."""
    
    def __init__(self, chunk_size: int = 1024 * 1024):  # 1MB chunks
        self.chunk_size = chunk_size
    
    async def encrypt_file(
        self,
        input_path: Path,
        output_path: Path,
        password: str,
        algorithm: str = "AES-256-GCM"
    ) -> E4PHeader:
        """
        Encrypt a file using streaming approach.
        
        Args:
            input_path: Path to input file
            output_path: Path to output encrypted file
            password: User password
            algorithm: Encryption algorithm
            
        Returns:
            E4P header with metadata
        """
        # Generate random salt and nonce
        salt = generate_salt()
        nonce = os.urandom(12 if algorithm == "AES-256-GCM" else 24)
        
        # Derive key from password
        key = derive_key(password, salt)
        
        # Create encryptor
        encryptor = create_encryptor(algorithm, key)
        
        # Create container
        container = E4PContainer(algorithm)
        
        # Create header
        header = container.create_header(
            salt=salt,
            nonce=nonce,
            original_name=input_path.name,
            original_size=input_path.stat().st_size
        )
        
        # Serialize header
        header_bytes = container.serialize_header(header)
        
        # Write header to output file
        async with aiofiles.open(output_path, 'wb') as out_file:
            await out_file.write(header_bytes)
            
            # Encrypt and write file content
            async with aiofiles.open(input_path, 'rb') as in_file:
                while True:
                    chunk = await in_file.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    # Encrypt chunk
                    encrypted_chunk = encryptor.encrypt_chunk(chunk, nonce)
                    await out_file.write(encrypted_chunk)
        
        return header
    
    async def decrypt_file(
        self,
        input_path: Path,
        output_path: Path,
        password: str
    ) -> bool:
        """
        Decrypt an E4P file.
        
        Args:
            input_path: Path to encrypted E4P file
            output_path: Path to output decrypted file
            password: User password
            
        Returns:
            True if decryption successful, False otherwise
        """
        try:
            # Read and parse header
            async with aiofiles.open(input_path, 'rb') as file:
                # Read enough data for header
                header_data = await file.read(8192)  # Read first 8KB
                
                container = E4PContainer()
                header, header_offset = container.deserialize_header(header_data)
                
                # Validate header
                if not container.validate_header(header):
                    return False
                
                # Decode salt and nonce
                import base64
                salt = base64.b64decode(header.salt)
                nonce = base64.b64decode(header.nonce)
                
                # Derive key
                key = derive_key(password, salt)
                
                # Create decryptor
                encryptor = create_encryptor(header.algorithm, key)
                
                # Seek to start of encrypted data
                await file.seek(header_offset)
                
                # Decrypt and write file content
                async with aiofiles.open(output_path, 'wb') as out_file:
                    while True:
                        chunk = await file.read(self.chunk_size)
                        if not chunk:
                            break
                        
                        # Decrypt chunk
                        decrypted_chunk = encryptor.decrypt_chunk(chunk, nonce)
                        await out_file.write(decrypted_chunk)
            
            return True
            
        except Exception:
            return False
    
    async def get_file_info(self, input_path: Path) -> Optional[E4PHeader]:
        """
        Get file information from E4P header without decryption.
        
        Args:
            input_path: Path to E4P file
            
        Returns:
            E4P header or None if invalid
        """
        try:
            async with aiofiles.open(input_path, 'rb') as file:
                header_data = await file.read(8192)
                
                container = E4PContainer()
                header, _ = container.deserialize_header(header_data)
                
                if container.validate_header(header):
                    return header
                return None
                
        except Exception:
            return None
