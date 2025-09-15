#!/usr/bin/env python3
"""Dedicated certbot setup script for E4P with enhanced error handling."""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import argparse
import time


def command_exists(command):
    """Check if a command exists in the system."""
    return shutil.which(command) is not None


def install_certbot():
    """Install certbot using various methods."""
    print("📦 Installing certbot...")
    
    # Try different installation methods
    install_methods = [
        # Method 1: snap (universal, recommended)
        (['sudo', 'snap', 'install', 'core'], ['sudo', 'snap', 'install', '--classic', 'certbot']),
        # Method 2: apt (Ubuntu/Debian)
        (['sudo', 'apt-get', 'update'], ['sudo', 'apt-get', 'install', 'certbot', 'python3-certbot-nginx', '-y']),
        # Method 3: pip
        (['pip3', 'install', '--upgrade', 'pip'], ['pip3', 'install', 'certbot']),
        # Method 4: yum (CentOS/RHEL)
        (['sudo', 'yum', 'install', 'epel-release', '-y'], ['sudo', 'yum', 'install', 'certbot', '-y']),
        # Method 5: dnf (Fedora)
        (['sudo', 'dnf', 'install', 'epel-release', '-y'], ['sudo', 'dnf', 'install', 'certbot', '-y']),
    ]
    
    for prep_cmd, install_cmd in install_methods:
        try:
            print(f"🔧 Trying: {' '.join(install_cmd)}")
            
            # Run preparation command if needed
            if prep_cmd:
                prep_result = subprocess.run(prep_cmd, capture_output=True, text=True)
                if prep_result.returncode != 0:
                    print(f"⚠️  Prep command failed: {prep_result.stderr}")
                    continue
            
            # Run installation command
            install_result = subprocess.run(install_cmd, capture_output=True, text=True)
            if install_result.returncode == 0:
                print(f"✅ Certbot installed successfully using: {' '.join(install_cmd)}")
                
                # If using snap, create symlink for easier access
                if 'snap' in install_cmd:
                    subprocess.run(['sudo', 'ln', '-sf', '/snap/bin/certbot', '/usr/local/bin/certbot'], capture_output=True)
                
                return True
            else:
                print(f"⚠️  Installation failed: {install_result.stderr}")
                continue
                
        except Exception as e:
            print(f"⚠️  Installation method failed: {e}")
            continue
    
    print("❌ All certbot installation methods failed")
    return False


def check_certbot():
    """Check if certbot is installed and working."""
    print("🔍 Checking certbot installation...")
    
    if not command_exists('certbot'):
        print("❌ Certbot not found. Attempting to install...")
        return install_certbot()
    
    # Test certbot
    test_result = subprocess.run(['certbot', '--version'], capture_output=True, text=True)
    if test_result.returncode == 0:
        print(f"✅ Certbot version: {test_result.stdout.strip()}")
        return True
    else:
        print(f"❌ Certbot not working: {test_result.stderr}")
        print("🔧 Attempting to reinstall...")
        return install_certbot()


def stop_web_servers():
    """Stop any running web servers on port 80."""
    print("🛑 Stopping web servers on port 80...")
    
    servers = ['python.*run.py', 'uvicorn', 'nginx', 'apache', 'httpd']
    for server in servers:
        subprocess.run(['sudo', 'pkill', '-f', server], capture_output=True)
    
    # Wait for processes to stop
    time.sleep(3)
    
    # Check if port 80 is free
    port_check = subprocess.run(['sudo', 'netstat', '-tlnp'], capture_output=True, text=True)
    if ':80 ' in port_check.stdout:
        print("⚠️  Port 80 still in use. Force killing...")
        subprocess.run(['sudo', 'fuser', '-k', '80/tcp'], capture_output=True)
        time.sleep(2)


def generate_certificate(domain: str, email: str, cert_dir: Path):
    """Generate Let's Encrypt certificate using certbot."""
    print(f"🔒 Generating Let's Encrypt certificate for {domain}...")
    
    # Stop web servers
    stop_web_servers()
    
    # Fix OpenSSL compatibility
    print("🔧 Fixing OpenSSL compatibility...")
    try:
        subprocess.run(['pip3', 'install', '--upgrade', 'pyOpenSSL'], capture_output=True)
        
        if command_exists('apt-get'):
            subprocess.run(['sudo', 'apt-get', 'install', '--reinstall', 'python3-openssl', 'python3-cryptography', '-y'], capture_output=True)
        elif command_exists('yum'):
            subprocess.run(['sudo', 'yum', 'reinstall', 'python3-pyOpenSSL', 'python3-cryptography', '-y'], capture_output=True)
        elif command_exists('dnf'):
            subprocess.run(['sudo', 'dnf', 'reinstall', 'python3-pyOpenSSL', 'python3-cryptography', '-y'], capture_output=True)
    except:
        pass
    
    # Generate certificate
    print("🔐 Running certbot...")
    result = subprocess.run([
        'sudo', 'certbot', 'certonly',
        '--standalone',
        '--non-interactive',
        '--agree-tos',
        '--email', email,
        '--domains', domain,
        '--pre-hook', 'pkill -f "python.*run.py" || true; pkill -f "uvicorn" || true; pkill -f "nginx" || true; pkill -f "apache" || true',
        '--post-hook', 'echo "Certificate generation complete"',
        '--expand',
        '--force-renewal'
    ], capture_output=True, text=True)
    
    print(f"📋 Certbot result:")
    print(f"   Return code: {result.returncode}")
    if result.stdout:
        print(f"   Output: {result.stdout}")
    if result.stderr:
        print(f"   Error: {result.stderr}")
    
    if result.returncode == 0:
        # Find certificate files
        letsencrypt_dir = Path('/etc/letsencrypt/live') / domain
        cert_path = letsencrypt_dir / 'fullchain.pem'
        key_path = letsencrypt_dir / 'privkey.pem'
        
        if cert_path.exists() and key_path.exists():
            # Copy to local directory
            local_cert = cert_dir / f"{domain}.crt"
            local_key = cert_dir / f"{domain}.key"
            
            shutil.copy2(cert_path, local_cert)
            shutil.copy2(key_path, local_key)
            
            # Set permissions
            os.chmod(local_cert, 0o644)
            os.chmod(local_key, 0o600)
            
            print(f"✅ Certificate generated successfully!")
            print(f"   Certificate: {local_cert}")
            print(f"   Private Key: {local_key}")
            
            return str(local_cert), str(local_key)
        else:
            print("❌ Certificate files not found after generation")
            return None, None
    else:
        print("❌ Certificate generation failed")
        print("💡 Common issues:")
        print("   - Domain not pointing to this server")
        print("   - Port 80 not accessible")
        print("   - OpenSSL compatibility issues")
        print("   - Rate limiting from Let's Encrypt")
        return None, None


def update_env_file(domain: str, email: str, cert_path: str, key_path: str, port: int = 443):
    """Update .env file with SSL configuration."""
    env_file = Path('.env')
    
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
EMAIL={email}
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


def main():
    """Main certbot setup function."""
    parser = argparse.ArgumentParser(description='Setup SSL for E4P using certbot')
    parser.add_argument('--domain', required=True, help='Domain name for SSL certificate')
    parser.add_argument('--email', required=True, help='Email address for Let\'s Encrypt registration')
    parser.add_argument('--port', type=int, default=443, help='HTTPS port (default: 443)')
    
    args = parser.parse_args()
    
    print("🔐 E4P Certbot SSL Setup")
    print("=" * 40)
    
    # Create certificates directory
    cert_dir = Path('certs')
    cert_dir.mkdir(exist_ok=True)
    
    # Check certbot
    if not check_certbot():
        print("❌ Failed to install certbot")
        sys.exit(1)
    
    # Generate certificate
    cert_path, key_path = generate_certificate(args.domain, args.email, cert_dir)
    
    if not cert_path or not key_path:
        print("❌ Failed to generate SSL certificate")
        sys.exit(1)
    
    # Update .env file
    update_env_file(args.domain, args.email, cert_path, key_path, args.port)
    
    print("\n🎉 Certbot SSL setup complete!")
    print(f"🌐 Your E4P application will be available at: https://{args.domain}:{args.port}")
    print("\n📝 Next steps:")
    print("1. Make sure your domain points to this server")
    print("2. Run: python run.py")
    print("3. Access your secure E4P application!")


if __name__ == "__main__":
    main()
