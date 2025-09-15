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
    sudo apt-get install -y certbot openssl
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    sudo yum install -y certbot openssl
elif command -v dnf &> /dev/null; then
    # Fedora
    sudo dnf install -y certbot openssl
elif command -v brew &> /dev/null; then
    # macOS
    brew install certbot openssl
else
    echo "⚠️  Could not install SSL dependencies automatically. You may need to install certbot and openssl manually for HTTPS support."
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

# Ask about HTTPS setup
echo ""
echo "🔐 HTTPS Configuration (Optional)"
echo "=================================="
read -p "Do you want to set up HTTPS with SSL certificate? (y/N): " setup_https

if [[ $setup_https =~ ^[Yy]$ ]]; then
    echo ""
    read -p "Enter your domain name (e.g., example.com): " domain
    read -p "Enter your email address for Let's Encrypt: " email
    
    if [ -n "$domain" ] && [ -n "$email" ]; then
        echo "🔒 Setting up SSL certificate..."
        python3 setup_ssl.py --domain "$domain" --email "$email"
        
        if [ $? -eq 0 ]; then
            echo "✅ HTTPS setup complete!"
            echo "🌐 Your application will be available at: https://$domain"
        else
            echo "⚠️  HTTPS setup failed, continuing with HTTP..."
        fi
    else
        echo "⚠️  Invalid domain or email, continuing with HTTP..."
    fi
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
