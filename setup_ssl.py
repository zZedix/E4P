#!/usr/bin/env python3
"""SSL setup script for E4P with automatic Let's Encrypt certificate generation."""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import argparse


def command_exists(command):
    """Check if a command exists in the system."""
    return shutil.which(command) is not None


def install_certbot():
    """Install certbot using various methods."""
    print("📦 Installing certbot...")
    
    # Try different installation methods
    install_methods = [
        # Method 1: apt (Ubuntu/Debian)
        (['sudo', 'apt-get', 'update'], ['sudo', 'apt-get', 'install', 'certbot', 'python3-certbot-nginx', '-y']),
        # Method 2: snap (universal)
        (['sudo', 'snap', 'install', 'core'], ['sudo', 'snap', 'install', '--classic', 'certbot']),
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
                    continue
            
            # Run installation command
            install_result = subprocess.run(install_cmd, capture_output=True, text=True)
            if install_result.returncode == 0:
                print(f"✅ Certbot installed successfully using: {' '.join(install_cmd)}")
                return True
            else:
                print(f"⚠️  Installation failed: {install_result.stderr}")
                continue
                
        except Exception as e:
            print(f"⚠️  Installation method failed: {e}")
            continue
    
    print("❌ All certbot installation methods failed")
    return False


def check_dependencies():
    """Check if required dependencies are installed."""
    required_commands = ['certbot', 'openssl']
    missing = []
    
    for cmd in required_commands:
        if not shutil.which(cmd):
            missing.append(cmd)
    
    if missing:
        print(f"❌ Missing required dependencies: {', '.join(missing)}")
        
        # Try to install certbot automatically
        if 'certbot' in missing:
            print("\n🔧 Attempting to install certbot automatically...")
            if install_certbot():
                # Check again after installation
                if shutil.which('certbot'):
                    print("✅ Certbot installed successfully!")
                    missing.remove('certbot')
                else:
                    print("❌ Certbot installation failed")
        
        if missing:
            print(f"\n📦 Please install missing dependencies manually:")
            print("  Ubuntu/Debian: sudo apt-get install certbot openssl")
            print("  CentOS/RHEL: sudo yum install certbot openssl")
            print("  macOS: brew install certbot openssl")
            print("  Or try: sudo snap install --classic certbot")
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
        # Check if certbot is working properly first
        print("🔍 Checking certbot installation...")
        test_result = subprocess.run(['certbot', '--version'], capture_output=True, text=True)
        if test_result.returncode != 0:
            print(f"❌ Certbot is not working properly: {test_result.stderr}")
            return None, None
        
        print(f"✅ Certbot version: {test_result.stdout.strip()}")
        
        # Stop any running web server on port 80
        print("🛑 Stopping any web server on port 80...")
        subprocess.run(['sudo', 'pkill', '-f', 'python.*run.py'], capture_output=True)
        subprocess.run(['sudo', 'pkill', '-f', 'uvicorn'], capture_output=True)
        subprocess.run(['sudo', 'pkill', '-f', 'nginx'], capture_output=True)
        subprocess.run(['sudo', 'pkill', '-f', 'apache'], capture_output=True)
        
        # Wait a moment for processes to stop
        import time
        time.sleep(2)
        
        # Try to fix OpenSSL compatibility issue
        print("🔧 Attempting to fix OpenSSL compatibility...")
        try:
            # Try to install/upgrade pyOpenSSL
            subprocess.run(['pip3', 'install', '--upgrade', 'pyOpenSSL'], capture_output=True)
            
            # Try to reinstall OpenSSL Python bindings
            if command_exists('apt-get'):
                subprocess.run(['sudo', 'apt-get', 'install', '--reinstall', 'python3-openssl', 'python3-cryptography', '-y'], capture_output=True)
            elif command_exists('yum'):
                subprocess.run(['sudo', 'yum', 'reinstall', 'python3-pyOpenSSL', 'python3-cryptography', '-y'], capture_output=True)
            elif command_exists('dnf'):
                subprocess.run(['sudo', 'dnf', 'reinstall', 'python3-pyOpenSSL', 'python3-cryptography', '-y'], capture_output=True)
        except:
            pass
        
        # Check if port 80 is available
        print("🔍 Checking if port 80 is available...")
        port_check = subprocess.run(['sudo', 'netstat', '-tlnp'], capture_output=True, text=True)
        if ':80 ' in port_check.stdout:
            print("⚠️  Port 80 is still in use. Trying to free it...")
            subprocess.run(['sudo', 'fuser', '-k', '80/tcp'], capture_output=True)
            time.sleep(3)
        
        # Generate certificate using standalone mode
        print("🔐 Running certbot to generate certificate...")
        result = subprocess.run([
            'sudo', 'certbot', 'certonly',
            '--standalone',
            '--non-interactive',
            '--agree-tos',
            '--email', email,
            '--domains', domain,
            '--pre-hook', 'pkill -f "python.*run.py" || true; pkill -f "uvicorn" || true; pkill -f "nginx" || true; pkill -f "apache" || true',
            '--post-hook', 'echo "Certificate generation complete"',
            '--expand',  # Allow expanding existing certificates
            '--force-renewal'  # Force renewal if certificate exists
        ], capture_output=True, text=True)
        
        print(f"📋 Certbot output:")
        print(f"   Return code: {result.returncode}")
        if result.stdout:
            print(f"   stdout: {result.stdout}")
        if result.stderr:
            print(f"   stderr: {result.stderr}")
        
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
                
                # Verify certificate
                verify_result = subprocess.run([
                    'openssl', 'x509', '-in', str(local_cert), '-text', '-noout'
                ], capture_output=True, text=True)
                
                if verify_result.returncode == 0:
                    print("✅ Certificate verification successful")
                else:
                    print("⚠️  Certificate verification failed")
                
                return str(local_cert), str(local_key)
            else:
                print("❌ Certificate files not found after generation")
                print(f"   Expected cert: {cert_path}")
                print(f"   Expected key: {key_path}")
                return None, None
        else:
            print(f"❌ Error generating Let's Encrypt certificate:")
            print(f"   {result.stderr}")
            print("💡 Common issues:")
            print("   - Domain not pointing to this server")
            print("   - Port 80 not accessible")
            print("   - OpenSSL compatibility issues")
            print("   - Rate limiting from Let's Encrypt")
            print("   The system will fall back to self-signed certificate.")
            return None, None
            
    except Exception as e:
        print(f"❌ Error generating Let's Encrypt certificate: {e}")
        print("💡 This might be due to OpenSSL compatibility issues.")
        print("   The system will fall back to self-signed certificate.")
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
    
    # Verify the .env file was written correctly
    print(f"\n🔍 Verifying .env configuration...")
    with open(env_file, 'r') as f:
        content = f.read()
        if f"DOMAIN={domain}" in content and f"USE_HTTPS=true" in content:
            print("✅ .env file configured correctly")
        else:
            print("❌ .env file configuration failed")
            return False
    
    return True


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
