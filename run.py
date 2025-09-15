#!/usr/bin/env python3
"""E4P Application Runner"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import settings

if __name__ == "__main__":
    print("🔐 Encryption 4 People (E4P)")
    print("=" * 40)
    print(f"Starting server on {settings.app_host}:{settings.app_port}")
    print(f"Max file size: {settings.max_file_size_mb}MB")
    print(f"Max concurrency: {settings.max_concurrency}")
    print(f"Argon2id memory: {settings.argon2_memory_mb}MB")
    print(f"Temp directory: {settings.temp_dir}")
    print("=" * 40)
    print()
    print("Access the application at:")
    print(f"  http://{settings.app_host}:{settings.app_port}")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        uvicorn.run(
            "app.main:app",
            host=settings.app_host,
            port=settings.app_port,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)
