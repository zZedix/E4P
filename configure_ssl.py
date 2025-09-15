#!/usr/bin/env python3
"""Manual SSL configuration script for E4P."""

import os
import sys
from pathlib import Path
import argparse


def show_current_config():
    """Show current SSL configuration."""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    print("🔍 Current SSL Configuration:")
    print("=" * 40)
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    ssl_settings = {
        'USE_HTTPS': 'Not set',
        'DOMAIN': 'Not set',
        'SSL_CERT_PATH': 'Not set',
        'SSL_KEY_PATH': 'Not set',
        'APP_PORT': 'Not set'
    }
    
    for line in content.split('\n'):
        for setting in ssl_settings:
            if line.startswith(f'{setting}='):
                ssl_settings[setting] = line.split('=', 1)[1].strip()
                break
    
    for setting, value in ssl_settings.items():
        status = "✅" if value != "Not set" else "❌"
        print(f"   {status} {setting}: {value}")
    
    return True


def configure_ssl(domain: str, cert_path: str, key_path: str, port: int = 443):
    """Configure SSL settings in .env file."""
    env_file = Path('.env')
    
    # Check if certificate files exist
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
    
    # Read existing .env content
    env_content = ""
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
    else:
        # Create basic .env if it doesn't exist
        env_content = """APP_HOST=0.0.0.0
APP_PORT=8080
MAX_FILE_SIZE_MB=2048
MAX_CONCURRENCY=2

# Argon2id
ARGON2_MEMORY_MB=256
ARGON2_TIME_COST=3
ARGON2_PARALLELISM=2
ARGON2_KEY_LEN=32

# Cleanup
CLEAN_INTERVAL_MIN=5
FILE_TTL_MIN=60

# Tokens
DOWNLOAD_TOKEN_TTL_S=900
SECRET_KEY=te8FqI6dbr4e8qzojgWNPAyvnPF5kdNoV10rioRcq2Q

# Security
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Temp directory
TEMP_DIR=/tmp/e4p
"""
    
    # Update or add SSL settings
    ssl_settings = f"""
# HTTPS Configuration
USE_HTTPS=true
DOMAIN={domain}
SSL_CERT_PATH={cert_path}
SSL_KEY_PATH={key_path}
EMAIL=admin@{domain}
APP_PORT={port}
"""
    
    # Remove existing SSL settings if any
    lines = env_content.split('\n')
    filtered_lines = []
    skip_until_newline = False
    
    for line in lines:
        if any(line.strip().startswith(setting) for setting in ['USE_HTTPS', 'DOMAIN', 'SSL_CERT_PATH', 'SSL_KEY_PATH', 'EMAIL', 'APP_PORT']):
            skip_until_newline = True
            continue
        elif skip_until_newline and line.strip() == '':
            skip_until_newline = False
            continue
        elif not skip_until_newline:
            filtered_lines.append(line)
    
    # Add new SSL settings
    new_content = '\n'.join(filtered_lines) + ssl_settings
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Updated .env file with SSL configuration")
    print(f"   Domain: {domain}")
    print(f"   Port: {port}")
    print(f"   Certificate: {cert_path}")
    print(f"   Private Key: {key_path}")
    
    return True


def main():
    """Main configuration function."""
    parser = argparse.ArgumentParser(description='Configure SSL for E4P')
    parser.add_argument('--show', action='store_true', help='Show current SSL configuration')
    parser.add_argument('--domain', help='Domain name for SSL certificate')
    parser.add_argument('--cert', help='Path to certificate file')
    parser.add_argument('--key', help='Path to private key file')
    parser.add_argument('--port', type=int, default=443, help='HTTPS port (default: 443)')
    
    args = parser.parse_args()
    
    print("🔐 E4P SSL Configuration")
    print("=" * 30)
    
    if args.show:
        show_current_config()
        return
    
    if not args.domain or not args.cert or not args.key:
        print("❌ Missing required arguments")
        print("Usage: python configure_ssl.py --domain example.com --cert certs/example.com.crt --key certs/example.com.key")
        print("       python configure_ssl.py --show  # Show current configuration")
        sys.exit(1)
    
    # Configure SSL
    if configure_ssl(args.domain, args.cert, args.key, args.port):
        print("\n🎉 SSL configuration complete!")
        print(f"🌐 Your E4P application will be available at: https://{args.domain}:{args.port}")
        print("\n📝 Next steps:")
        print("1. Run: python run.py")
        print("2. Access your secure E4P application!")
    else:
        print("❌ SSL configuration failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
