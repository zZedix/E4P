#!/bin/bash

# Fix OpenSSL compatibility issues for E4P

echo "🔧 Fixing OpenSSL compatibility issues..."
echo "=========================================="

# Update package list
echo "📦 Updating package list..."
sudo apt-get update

# Reinstall OpenSSL Python bindings
echo "🔧 Reinstalling OpenSSL Python bindings..."
sudo apt-get install --reinstall python3-openssl -y

# Upgrade pyOpenSSL
echo "⬆️  Upgrading pyOpenSSL..."
pip3 install --upgrade pyOpenSSL

# Install additional dependencies
echo "📦 Installing additional dependencies..."
sudo apt-get install python3-cryptography -y

# Test OpenSSL
echo "🧪 Testing OpenSSL compatibility..."
python3 -c "from OpenSSL import crypto; print('✅ OpenSSL crypto module works')"

if [ $? -eq 0 ]; then
    echo "✅ OpenSSL compatibility fixed!"
    echo ""
    echo "You can now try HTTPS setup again:"
    echo "python3 setup_ssl.py --domain yourdomain.com --email your@email.com"
else
    echo "❌ OpenSSL compatibility still has issues."
    echo "Try running: sudo apt-get install --reinstall python3-openssl python3-cryptography"
fi
