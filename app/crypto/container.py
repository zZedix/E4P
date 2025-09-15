"""E4P container format implementation."""

import json
import struct
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from app.config import settings


# E4P magic bytes
E4P_MAGIC = b"E4P1"


@dataclass
class E4PHeader:
    """E4P file header structure."""
    
    algorithm: str
    kdf: str
    kdf_params: Dict[str, int]
    salt: str  # base64 encoded
    nonce: str  # base64 encoded
    original_name: str
    original_size: int
    timestamp: str  # RFC3339 format
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert header to dictionary."""
        return {
            "alg": self.algorithm,
            "kdf": self.kdf,
            "kdf_params": self.kdf_params,
            "salt": self.salt,
            "nonce": self.nonce,
            "orig_name": self.original_name,
            "orig_size": self.original_size,
            "ts": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "E4PHeader":
        """Create header from dictionary."""
        return cls(
            algorithm=data["alg"],
            kdf=data["kdf"],
            kdf_params=data["kdf_params"],
            salt=data["salt"],
            nonce=data["nonce"],
            original_name=data["orig_name"],
            original_size=data["orig_size"],
            timestamp=data["ts"]
        )


class E4PContainer:
    """E4P container format handler."""
    
    def __init__(self, algorithm: str = "AES-256-GCM"):
        self.algorithm = algorithm
        self.nonce_size = 12 if algorithm == "AES-256-GCM" else 24
    
    def create_header(
        self,
        salt: bytes,
        nonce: bytes,
        original_name: str,
        original_size: int
    ) -> E4PHeader:
        """Create a new E4P header."""
        import base64
        
        return E4PHeader(
            algorithm=self.algorithm,
            kdf="argon2id",
            kdf_params={
                "m": settings.argon2_memory_mb * 1024,  # Convert to KB
                "t": settings.argon2_time_cost,
                "p": settings.argon2_parallelism
            },
            salt=base64.b64encode(salt).decode('utf-8'),
            nonce=base64.b64encode(nonce).decode('utf-8'),
            original_name=original_name,
            original_size=original_size,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    
    def serialize_header(self, header: E4PHeader) -> bytes:
        """Serialize header to bytes."""
        # Convert header to JSON
        header_json = json.dumps(header.to_dict(), separators=(',', ':')).encode('utf-8')
        header_len = len(header_json)
        
        # Create the complete header: magic + length + JSON
        return E4P_MAGIC + struct.pack('<I', header_len) + header_json
    
    def deserialize_header(self, data: bytes) -> Tuple[E4PHeader, int]:
        """
        Deserialize header from bytes.
        
        Returns:
            Tuple of (header, bytes_consumed)
        """
        if len(data) < 8:  # magic + length
            raise ValueError("Invalid E4P file: too short")
        
        # Check magic bytes
        if data[:4] != E4P_MAGIC:
            raise ValueError("Invalid E4P file: wrong magic bytes")
        
        # Read header length
        header_len = struct.unpack('<I', data[4:8])[0]
        
        if len(data) < 8 + header_len:
            raise ValueError("Invalid E4P file: incomplete header")
        
        # Parse header JSON
        header_json = data[8:8 + header_len].decode('utf-8')
        header_data = json.loads(header_json)
        
        header = E4PHeader.from_dict(header_data)
        return header, 8 + header_len
    
    def validate_header(self, header: E4PHeader) -> bool:
        """Validate header structure and parameters."""
        # Check algorithm
        if header.algorithm not in ["AES-256-GCM", "XCHACHA20-POLY1305"]:
            return False
        
        # Check KDF
        if header.kdf != "argon2id":
            return False
        
        # Check KDF parameters
        required_params = {"m", "t", "p"}
        if not all(param in header.kdf_params for param in required_params):
            return False
        
        # Check parameter ranges
        if (header.kdf_params["m"] < 1024 or  # At least 1MB
            header.kdf_params["t"] < 1 or
            header.kdf_params["p"] < 1):
            return False
        
        # Check salt and nonce are base64 encoded
        try:
            import base64
            base64.b64decode(header.salt)
            base64.b64decode(header.nonce)
        except Exception:
            return False
        
        # Check original size is reasonable
        if header.original_size < 0 or header.original_size > settings.max_file_size_mb * 1024 * 1024:
            return False
        
        return True
    
    def get_expected_nonce_size(self, algorithm: str) -> int:
        """Get expected nonce size for algorithm."""
        if algorithm == "AES-256-GCM":
            return 12
        elif algorithm == "XCHACHA20-POLY1305":
            return 24
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
