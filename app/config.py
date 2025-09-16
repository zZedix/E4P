"""Configuration settings for E4P application."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server settings
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    
    # File handling
    max_file_size_mb: int = 2048
    max_concurrency: int = 2
    
    # Argon2id parameters
    argon2_memory_mb: int = 256
    argon2_time_cost: int = 3
    argon2_parallelism: int = 2
    argon2_key_len: int = 32
    
    # Cleanup settings
    clean_interval_min: int = 5
    file_ttl_min: int = 60
    
    # Token settings
    download_token_ttl_s: int = 900
    secret_key: str = "te8FqI6dbr4e8qzojgWNPAyvnPF5kdNoV10rioRcq2Q"
    
    # Security
    rate_limit_requests_per_minute: int = 60
    
    # Temp directory
    temp_dir: str = "/tmp/e4p"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()

# Ensure temp directory exists
os.makedirs(settings.temp_dir, exist_ok=True)
