#!/bin/bash

# E4P - Encryption 4 People - One Line Installation Script
# This script installs and runs the E4P secure file encryption web application

echo "🔐 Installing Encryption 4 People (E4P)..."
echo "=========================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed. Please install pip3 first."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
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
