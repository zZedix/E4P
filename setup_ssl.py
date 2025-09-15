#!/usr/bin/env python3
"""SSL setup script for E4P with automatic Let's Encrypt certificate generation."""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import argparse


def check_dependencies():
    """Check if required dependencies are installed."""
    required_commands = ['certbot', 'openssl']
    missing = []
    
    for cmd in required_commands:
        if not shutil.which(cmd):
            missing.append(cmd)
    
    if missing:
        print(f"❌ Missing required dependencies: {', '.join(missing)}")
        print("\n📦 Install them with:")
        print("  Ubuntu/Debian: sudo apt-get install certbot openssl")
        print("  CentOS/RHEL: sudo yum install certbot openssl")
        print("  macOS: brew install certbot openssl")
        return False
    
    return True


def generate_self_signed_cert(domain: str, email: str, cert_dir: Path):
    """Generate a self-signed certificate for testing."""
    print(f"🔧 Generating self-signed certificate for {domain}...")
    
    cert_path = cert_dir / f"{domain}.crt"
    key_path = cert_dir / f"{domain}.key"
    
    try:
        # Generate private key
        subprocess.run([
            'openssl', 'genrsa', '-out', str(key_path), '2048'
        ], check=True, capture_output=True)
        
        # Generate certificate
        subprocess.run([
            'openssl', 'req', '-new', '-x509', '-key', str(key_path),
            '-out', str(cert_path), '-days', '365',
            '-subj', f'/C=US/ST=State/L=City/O=Organization/CN={domain}/emailAddress={email}'
        ], check=True, capture_output=True)
        
        print(f"✅ Self-signed certificate generated:")
        print(f"   Certificate: {cert_path}")
        print(f"   Private Key: {key_path}")
        
        return str(cert_path), str(key_path)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating self-signed certificate: {e}")
        return None, None


def generate_letsencrypt_cert(domain: str, email: str, cert_dir: Path):
    """Generate Let's Encrypt certificate using certbot."""
    print(f"🔒 Generating Let's Encrypt certificate for {domain}...")
    
    try:
        # Stop any running web server on port 80
        print("🛑 Stopping any web server on port 80...")
        subprocess.run(['sudo', 'pkill', '-f', 'python.*run.py'], capture_output=True)
        subprocess.run(['sudo', 'pkill', '-f', 'uvicorn'], capture_output=True)
        
        # Generate certificate using standalone mode
        result = subprocess.run([
            'sudo', 'certbot', 'certonly',
            '--standalone',
            '--non-interactive',
            '--agree-tos',
            '--email', email,
            '--domains', domain,
            '--cert-path', str(cert_dir)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Find the generated certificate files
            letsencrypt_dir = Path('/etc/letsencrypt/live') / domain
            cert_path = letsencrypt_dir / 'fullchain.pem'
            key_path = letsencrypt_dir / 'privkey.pem'
            
            if cert_path.exists() and key_path.exists():
                # Copy to our cert directory
                local_cert = cert_dir / f"{domain}.crt"
                local_key = cert_dir / f"{domain}.key"
                
                shutil.copy2(cert_path, local_cert)
                shutil.copy2(key_path, local_key)
                
                # Set proper permissions
                os.chmod(local_cert, 0o644)
                os.chmod(local_key, 0o600)
                
                print(f"✅ Let's Encrypt certificate generated:")
                print(f"   Certificate: {local_cert}")
                print(f"   Private Key: {local_key}")
                
                return str(local_cert), str(local_key)
            else:
                print("❌ Certificate files not found after generation")
                return None, None
        else:
            print(f"❌ Error generating Let's Encrypt certificate:")
            print(f"   {result.stderr}")
            return None, None
            
    except Exception as e:
        print(f"❌ Error generating Let's Encrypt certificate: {e}")
        return None, None


def update_env_file(domain: str, email: str, cert_path: str, key_path: str, port: int = 443):
    """Update .env file with SSL configuration."""
    env_file = Path('.env')
    
    # Read existing .env content
    env_content = ""
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
    
    # Update or add SSL settings
    ssl_settings = f"""
# HTTPS Configuration
USE_HTTPS=true
DOMAIN={domain}
SSL_CERT_PATH={cert_path}
SSL_KEY_PATH={key_path}
EMAIL={email}
APP_PORT={port}
"""
    
    # Remove existing SSL settings if any
    lines = env_content.split('\n')
    filtered_lines = []
    skip_until_newline = False
    
    for line in lines:
        if any(line.strip().startswith(setting) for setting in ['USE_HTTPS', 'DOMAIN', 'SSL_CERT_PATH', 'SSL_KEY_PATH', 'EMAIL']):
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


def main():
    """Main SSL setup function."""
    parser = argparse.ArgumentParser(description='Setup SSL for E4P')
    parser.add_argument('--domain', required=True, help='Domain name for SSL certificate')
    parser.add_argument('--email', required=True, help='Email address for Let\'s Encrypt registration')
    parser.add_argument('--self-signed', action='store_true', help='Generate self-signed certificate instead of Let\'s Encrypt')
    parser.add_argument('--port', type=int, default=443, help='HTTPS port (default: 443)')
    
    args = parser.parse_args()
    
    print("🔐 E4P SSL Setup")
    print("=" * 50)
    
    # Create certificates directory
    cert_dir = Path('certs')
    cert_dir.mkdir(exist_ok=True)
    
    # Check dependencies
    if not args.self_signed and not check_dependencies():
        print("\n🔄 Falling back to self-signed certificate...")
        args.self_signed = True
    
    # Generate certificate
    if args.self_signed:
        cert_path, key_path = generate_self_signed_cert(args.domain, args.email, cert_dir)
    else:
        cert_path, key_path = generate_letsencrypt_cert(args.domain, args.email, cert_dir)
    
    if not cert_path or not key_path:
        print("❌ Failed to generate SSL certificate")
        sys.exit(1)
    
    # Update .env file
    update_env_file(args.domain, args.email, cert_path, key_path, args.port)
    
    print("\n🎉 SSL setup complete!")
    print(f"🌐 Your E4P application will be available at: https://{args.domain}:{args.port}")
    print("\n📝 Next steps:")
    print("1. Make sure your domain points to this server")
    print("2. Run: python run.py")
    print("3. Access your secure E4P application!")


if __name__ == "__main__":
    main()
