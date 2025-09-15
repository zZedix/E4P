#!/usr/bin/env python3
"""Test HTTPS configuration for E4P"""

import os
import sys
from pathlib import Path

def test_env_file():
    """Test if .env file exists and has correct HTTPS settings."""
    print("🔍 Testing .env file configuration...")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    print("✅ .env file found")
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Check for required HTTPS settings
    required_settings = {
        'USE_HTTPS': 'true',
        'DOMAIN': None,  # Any value
        'SSL_CERT_PATH': None,  # Any value
        'SSL_KEY_PATH': None,  # Any value
        'APP_PORT': '443'
    }
    
    missing = []
    for setting, expected_value in required_settings.items():
        found = False
        for line in content.split('\n'):
            if line.startswith(f'{setting}='):
                value = line.split('=', 1)[1].strip()
                if expected_value is None or value == expected_value:
                    print(f"   ✅ {setting}: {value}")
                    found = True
                    break
                else:
                    print(f"   ⚠️  {setting}: {value} (expected: {expected_value})")
                    found = True
                    break
        
        if not found:
            print(f"   ❌ {setting}: Not found")
            missing.append(setting)
    
    if missing:
        print(f"❌ Missing required settings: {', '.join(missing)}")
        return False
    
    print("✅ All required HTTPS settings found")
    return True

def test_ssl_files():
    """Test if SSL certificate files exist and are valid."""
    print("\n🔍 Testing SSL certificate files...")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    # Read SSL file paths from .env
    cert_path = None
    key_path = None
    
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('SSL_CERT_PATH='):
                cert_path = line.split('=', 1)[1].strip()
            elif line.startswith('SSL_KEY_PATH='):
                key_path = line.split('=', 1)[1].strip()
    
    if not cert_path or not key_path:
        print("❌ SSL file paths not found in .env")
        return False
    
    cert_file = Path(cert_path)
    key_file = Path(key_path)
    
    if not cert_file.exists():
        print(f"❌ Certificate file not found: {cert_path}")
        return False
    
    if not key_file.exists():
        print(f"❌ Private key file not found: {key_path}")
        return False
    
    print(f"✅ Certificate file found: {cert_path}")
    print(f"✅ Private key file found: {key_path}")
    
    # Test certificate validity
    try:
        import subprocess
        result = subprocess.run([
            'openssl', 'x509', '-in', str(cert_file), '-text', '-noout'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Certificate is valid")
        else:
            print(f"❌ Certificate is invalid: {result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️  Could not validate certificate: {e}")
    
    return True

def test_config_loading():
    """Test if the application can load HTTPS configuration."""
    print("\n🔍 Testing configuration loading...")
    
    try:
        # Add the app directory to Python path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from app.config import settings
        
        print(f"   App Host: {settings.app_host}")
        print(f"   App Port: {settings.app_port}")
        print(f"   Use HTTPS: {settings.use_https}")
        print(f"   Domain: {settings.domain}")
        print(f"   SSL Cert Path: {settings.ssl_cert_path}")
        print(f"   SSL Key Path: {settings.ssl_key_path}")
        
        if settings.use_https and settings.ssl_cert_path and settings.ssl_key_path:
            print("✅ HTTPS configuration loaded correctly")
            return True
        else:
            print("❌ HTTPS configuration incomplete")
            return False
            
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False

def main():
    """Main test function."""
    print("🔐 E4P HTTPS Configuration Test")
    print("=" * 40)
    
    env_ok = test_env_file()
    ssl_ok = test_ssl_files()
    config_ok = test_config_loading()
    
    print("\n📊 Test Results:")
    print(f"   .env file: {'✅ OK' if env_ok else '❌ Issues'}")
    print(f"   SSL files: {'✅ OK' if ssl_ok else '❌ Issues'}")
    print(f"   Config loading: {'✅ OK' if config_ok else '❌ Issues'}")
    
    if env_ok and ssl_ok and config_ok:
        print("\n🎉 All tests passed! HTTPS should be working.")
        print("Run: python3 run.py")
    else:
        print("\n❌ Some tests failed. HTTPS may not work properly.")
        print("Try running: python3 setup_ssl.py --domain yourdomain.com --email your@email.com --self-signed")

if __name__ == "__main__":
    main()
