"""Token management for secure downloads."""

import base64
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.config import settings


class TokenManager:
    """Manages secure download tokens."""
    
    def __init__(self):
        self.secret_key = settings.secret_key.encode('utf-8')
        self.token_ttl = settings.download_token_ttl_s
    
    def create_download_token(self, file_path: str, filename: str) -> str:
        """
        Create a secure download token.
        
        Args:
            file_path: Path to the file to download
            filename: Original filename
            
        Returns:
            Base64 encoded token
        """
        # Create token data
        token_data = {
            "file_path": file_path,
            "filename": filename,
            "expires": int(time.time()) + self.token_ttl,
            "timestamp": int(time.time())
        }
        
        # Serialize token data
        import json
        data_json = json.dumps(token_data, separators=(',', ':'))
        data_bytes = data_json.encode('utf-8')
        
        # Create HMAC signature
        signature = hmac.new(
            self.secret_key,
            data_bytes,
            hashlib.sha256
        ).digest()
        
        # Combine data and signature
        token_bytes = data_bytes + b'|' + signature
        
        # Encode as base64
        return base64.urlsafe_b64encode(token_bytes).decode('utf-8')
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate and decode a download token.
        
        Args:
            token: Base64 encoded token
            
        Returns:
            Token data if valid, None if invalid
        """
        try:
            # Decode token
            token_bytes = base64.urlsafe_b64decode(token.encode('utf-8'))
            
            # Split data and signature
            if b'|' not in token_bytes:
                return None
            
            data_bytes, signature = token_bytes.split(b'|', 1)
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key,
                data_bytes,
                hashlib.sha256
            ).digest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return None
            
            # Parse token data
            import json
            token_data = json.loads(data_bytes.decode('utf-8'))
            
            # Check expiration
            current_time = int(time.time())
            expires_time = token_data.get("expires", 0)
            if expires_time < current_time:
                return None
            
            return token_data
            
        except Exception:
            return None
    
    def is_token_valid(self, token: str) -> bool:
        """Check if token is valid without returning data."""
        return self.validate_token(token) is not None
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get token information without validation."""
        try:
            token_bytes = base64.urlsafe_b64decode(token.encode('utf-8'))
            
            if b'.' not in token_bytes:
                return None
            
            data_bytes = token_bytes.split(b'.', 1)[0]
            
            import json
            token_data = json.loads(data_bytes.decode('utf-8'))
            
            return {
                "filename": token_data.get("filename"),
                "expires": token_data.get("expires"),
                "timestamp": token_data.get("timestamp"),
                "is_expired": token_data.get("expires", 0) < int(time.time())
            }
            
        except Exception:
            return None
