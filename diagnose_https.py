#!/usr/bin/env python3
"""HTTPS diagnostic script for E4P"""

import os
import sys
from pathlib import Path
import subprocess

def check_ssl_files():
    """Check if SSL certificate files exist and are valid."""
    print("🔍 Checking SSL certificate files...")
    
    cert_dir = Path('certs')
    if not cert_dir.exists():
        print("❌ certs directory not found")
        return False
    
    # Look for certificate files
    cert_files = list(cert_dir.glob('*.crt'))
    key_files = list(cert_dir.glob('*.key'))
    
    if not cert_files:
        print("❌ No certificate files found in certs/")
        return False
    
    print(f"✅ Found {len(cert_files)} certificate file(s)")
    
    for cert_file in cert_files:
        print(f"   📄 Certificate: {cert_file}")
        
        # Check certificate details
        try:
            result = subprocess.run([
                'openssl', 'x509', '-in', str(cert_file), '-text', '-noout'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Extract subject and validity
                subject_result = subprocess.run([
                    'openssl', 'x509', '-in', str(cert_file), '-subject', '-noout'
                ], capture_output=True, text=True)
                
                not_after_result = subprocess.run([
                    'openssl', 'x509', '-in', str(cert_file), '-enddate', '-noout'
                ], capture_output=True, text=True)
                
                print(f"      Subject: {subject_result.stdout.strip()}")
                print(f"      Valid until: {not_after_result.stdout.strip()}")
            else:
                print(f"      ❌ Invalid certificate: {result.stderr}")
        except Exception as e:
            print(f"      ❌ Error reading certificate: {e}")
    
    return True

def check_env_config():
    """Check .env configuration."""
    print("\n🔍 Checking .env configuration...")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    print("✅ .env file found")
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Check for HTTPS settings
    https_settings = {
        'USE_HTTPS': 'USE_HTTPS=true' in content,
        'DOMAIN': 'DOMAIN=' in content,
        'SSL_CERT_PATH': 'SSL_CERT_PATH=' in content,
        'SSL_KEY_PATH': 'SSL_KEY_PATH=' in content,
        'EMAIL': 'EMAIL=' in content
    }
    
    for setting, present in https_settings.items():
        if present:
            # Extract the value
            for line in content.split('\n'):
                if line.startswith(f'{setting}='):
                    value = line.split('=', 1)[1]
                    print(f"   ✅ {setting}: {value}")
                    break
        else:
            print(f"   ❌ {setting}: Not set")
    
    return all(https_settings.values())

def check_port_availability():
    """Check if ports 80 and 443 are available."""
    print("\n🔍 Checking port availability...")
    
    ports = [80, 443, 8080]
    for port in ports:
        try:
            result = subprocess.run([
                'netstat', '-tuln'
            ], capture_output=True, text=True)
            
            if f':{port} ' in result.stdout:
                print(f"   ⚠️  Port {port}: In use")
            else:
                print(f"   ✅ Port {port}: Available")
        except Exception as e:
            print(f"   ❌ Error checking port {port}: {e}")

def check_openssl_compatibility():
    """Check OpenSSL compatibility."""
    print("\n🔍 Checking OpenSSL compatibility...")
    
    try:
        # Check OpenSSL version
        result = subprocess.run(['openssl', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ OpenSSL version: {result.stdout.strip()}")
        else:
            print(f"   ❌ OpenSSL not working: {result.stderr}")
            return False
        
        # Check if the problematic function exists
        result = subprocess.run([
            'python3', '-c', 
            'from OpenSSL import crypto; print("OpenSSL crypto module works")'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ OpenSSL Python bindings working")
        else:
            print(f"   ❌ OpenSSL Python bindings error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking OpenSSL: {e}")
        return False
    
    return True

def suggest_fixes():
    """Suggest fixes for common issues."""
    print("\n💡 Suggested fixes:")
    print("1. If OpenSSL compatibility issues:")
    print("   sudo apt-get update")
    print("   sudo apt-get install --reinstall python3-openssl")
    print("   pip3 install --upgrade pyOpenSSL")
    print("")
    print("2. If certificate files are missing:")
    print("   python3 setup_ssl.py --domain yourdomain.com --email your@email.com --self-signed")
    print("")
    print("3. If ports are in use:")
    print("   sudo pkill -f 'python.*run.py'")
    print("   sudo pkill -f 'uvicorn'")
    print("")
    print("4. To restart with HTTPS:")
    print("   python3 run.py")

def main():
    """Main diagnostic function."""
    print("🔐 E4P HTTPS Diagnostic Tool")
    print("=" * 40)
    
    ssl_ok = check_ssl_files()
    env_ok = check_env_config()
    check_port_availability()
    openssl_ok = check_openssl_compatibility()
    
    print("\n📊 Summary:")
    print(f"   SSL Files: {'✅ OK' if ssl_ok else '❌ Issues'}")
    print(f"   .env Config: {'✅ OK' if env_ok else '❌ Issues'}")
    print(f"   OpenSSL: {'✅ OK' if openssl_ok else '❌ Issues'}")
    
    if not (ssl_ok and env_ok and openssl_ok):
        suggest_fixes()
    else:
        print("\n✅ All checks passed! HTTPS should be working.")
        print("If you're still having issues, check:")
        print("1. Domain DNS points to this server")
        print("2. Firewall allows ports 80 and 443")
        print("3. Server is running: python3 run.py")

if __name__ == "__main__":
    main()
