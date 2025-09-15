#!/bin/bash

# E4P - Encryption 4 People - One Line Installation Script
# This script installs and runs the E4P secure file encryption web application

echo "🔐 Installing Encryption 4 People (E4P)..."
echo "=========================================="

# Check if git is installed, install if missing
if ! command -v git &> /dev/null; then
    echo "📦 git not found, installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y git
    elif command -v yum &> /dev/null; then
        sudo yum install -y git
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y git
    elif command -v brew &> /dev/null; then
        brew install git
    else
        echo "❌ Cannot install git automatically. Please install git manually."
        exit 1
    fi
fi

# Clone the repository if not already present
if [ ! -d "E4P" ]; then
    echo "📥 Cloning E4P repository..."
    git clone https://github.com/zZedix/E4P.git
    if [ $? -ne 0 ]; then
        echo "❌ Failed to clone repository. Please check your internet connection."
        exit 1
    fi
fi

# Change to the E4P directory
cd E4P

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip3 is installed, install if missing
if ! command -v pip3 &> /dev/null; then
    echo "📦 pip3 not found, installing..."
    
    # Detect OS and install pip3
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            echo "Installing pip3 via apt-get..."
            sudo apt-get update
            sudo apt-get install -y python3-pip python3-venv
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL
            echo "Installing pip3 via yum..."
            sudo yum install -y python3-pip python3-venv
        elif command -v dnf &> /dev/null; then
            # Fedora
            echo "Installing pip3 via dnf..."
            sudo dnf install -y python3-pip python3-venv
        else
            echo "❌ Cannot install pip3 automatically. Please install pip3 manually."
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            echo "Installing pip3 via Homebrew..."
            brew install python3
        else
            echo "❌ Homebrew not found. Please install pip3 manually or install Homebrew first."
            exit 1
        fi
    else
        echo "❌ Unsupported operating system. Please install pip3 manually."
        exit 1
    fi
    
    # Verify pip3 installation
    if ! command -v pip3 &> /dev/null; then
        echo "❌ Failed to install pip3. Please install it manually."
        exit 1
    fi
    
    echo "✅ pip3 installed successfully!"
fi

# Install SSL dependencies for HTTPS setup
echo "🔒 Installing SSL dependencies..."
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    echo "Installing certbot and OpenSSL via apt-get..."
    sudo apt-get install -y certbot openssl python3-openssl python3-cryptography
    
    # Fix OpenSSL compatibility issues
    echo "🔧 Fixing OpenSSL compatibility issues..."
    sudo apt-get install --reinstall python3-openssl python3-cryptography -y
    pip3 install --upgrade pyOpenSSL
    
    # Test OpenSSL compatibility
    echo "🧪 Testing OpenSSL compatibility..."
    if ! python3 -c "from OpenSSL import crypto; print('OpenSSL works')" 2>/dev/null; then
        echo "⚠️  OpenSSL compatibility issue detected, trying alternative installation..."
        
        # Try installing certbot via snap as fallback
        if command -v snap &> /dev/null; then
            echo "Installing certbot via snap..."
            sudo snap install --classic certbot
            sudo ln -sf /snap/bin/certbot /usr/bin/certbot
        else
            echo "Installing certbot via pip..."
            pip3 install certbot
        fi
    fi
    
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    sudo yum install -y certbot openssl python3-pyOpenSSL python3-cryptography
    pip3 install --upgrade pyOpenSSL
elif command -v dnf &> /dev/null; then
    # Fedora
    sudo dnf install -y certbot openssl python3-pyOpenSSL python3-cryptography
    pip3 install --upgrade pyOpenSSL
elif command -v brew &> /dev/null; then
    # macOS
    brew install certbot openssl
    pip3 install --upgrade pyOpenSSL
else
    echo "⚠️  Could not install SSL dependencies automatically. You may need to install certbot and openssl manually for HTTPS support."
fi

# Final OpenSSL compatibility test
echo "🔍 Final OpenSSL compatibility test..."
if python3 -c "from OpenSSL import crypto; print('✅ OpenSSL works')" 2>/dev/null; then
    echo "✅ OpenSSL compatibility confirmed!"
else
    echo "❌ OpenSSL compatibility issues remain. HTTPS setup may fail."
    echo "   You can try running: ./fix_openssl.sh after installation"
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating configuration file..."
    cp env.example .env
    echo "✅ Configuration file created. You can edit .env to customize settings."
fi

# HTTPS Configuration (Mandatory)
echo ""
echo "🔐 HTTPS Configuration (Required)"
echo "================================="
echo "E4P requires HTTPS for security. Please provide your domain information:"
echo ""

# Check if running interactively
if [ -t 0 ]; then
    # Interactive mode - ask for domain and email
    while true; do
        read -p "Enter your domain name (e.g., example.com): " domain
        if [ -n "$domain" ]; then
            break
        else
            echo "❌ Domain name is required. Please try again."
        fi
    done
    
    while true; do
        read -p "Enter your email address for Let's Encrypt: " email
        if [ -n "$email" ]; then
            break
        else
            echo "❌ Email address is required. Please try again."
        fi
    done
    
    echo ""
    echo "🔒 Setting up SSL certificate for $domain..."
    python3 setup_ssl.py --domain "$domain" --email "$email"
    
    if [ $? -eq 0 ]; then
        echo "✅ HTTPS setup complete!"
        echo "🌐 Your application will be available at: https://$domain"
    else
        echo "⚠️  Let's Encrypt failed, trying self-signed certificate..."
        python3 setup_ssl.py --domain "$domain" --email "$email" --self-signed
        
        if [ $? -eq 0 ]; then
            echo "✅ Self-signed certificate setup complete!"
            echo "🌐 Your application will be available at: https://$domain"
            echo "⚠️  Note: Browsers will show a security warning for self-signed certificates."
        else
            echo "❌ SSL certificate setup failed. Please check your domain and try again."
            echo "You can run: ./setup_https_interactive.sh to try again later."
            exit 1
        fi
    fi
    
    # Verify HTTPS configuration
    echo ""
    echo "🔍 Verifying HTTPS configuration..."
    python3 test_https.py
    
    if [ $? -eq 0 ]; then
        echo "✅ HTTPS configuration verified!"
    else
        echo "⚠️  HTTPS configuration verification failed, but continuing..."
    fi
else
    # Non-interactive mode (piped from curl)
    echo "❌ HTTPS setup is mandatory but cannot be configured in non-interactive mode."
    echo ""
    echo "Please run the installation interactively:"
    echo "1. git clone https://github.com/zZedix/E4P.git"
    echo "2. cd E4P"
    echo "3. chmod +x install.sh"
    echo "4. ./install.sh"
    echo ""
    echo "Or set up HTTPS manually after installation:"
    echo "python3 setup_ssl.py --domain yourdomain.com --email your@email.com"
    exit 1
fi

# Create temp directory
mkdir -p /tmp/e4p

# Start the application
echo ""
echo "🚀 Starting E4P server..."
echo "=========================================="

# Check if HTTPS is enabled
if grep -q "USE_HTTPS=true" .env 2>/dev/null; then
    domain=$(grep "DOMAIN=" .env | cut -d'=' -f2)
    port=$(grep "APP_PORT=" .env | cut -d'=' -f2)
    echo "🔒 HTTPS enabled - Access at: https://$domain:$port"
else
    echo "🌐 HTTP enabled - Access at: http://localhost:8080"
fi

echo "Press Ctrl+C to stop the server"
echo "=========================================="

python3 run.py
