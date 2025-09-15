#!/bin/bash

# Interactive HTTPS setup script for E4P

echo "🔐 E4P HTTPS Setup"
echo "=================="
echo ""

# Check if we're in the E4P directory
if [ ! -f "setup_ssl.py" ]; then
    echo "❌ This script must be run from the E4P directory."
    echo "Please run: cd E4P && ./setup_https_interactive.sh"
    exit 1
fi

# Ask about HTTPS setup
echo "Do you want to set up HTTPS with SSL certificate?"
echo "1) Yes - Let's Encrypt (production)"
echo "2) Yes - Self-signed certificate (testing)"
echo "3) No - Continue with HTTP only"
echo ""
read -p "Choose an option (1-3): " choice

case $choice in
    1)
        echo ""
        read -p "Enter your domain name (e.g., example.com): " domain
        read -p "Enter your email address for Let's Encrypt: " email
        
        if [ -n "$domain" ] && [ -n "$email" ]; then
            echo "🔒 Setting up Let's Encrypt SSL certificate..."
            python3 setup_ssl.py --domain "$domain" --email "$email"
            
            if [ $? -eq 0 ]; then
                echo "✅ HTTPS setup complete!"
                echo "🌐 Your application will be available at: https://$domain"
            else
                echo "⚠️  Let's Encrypt setup failed, trying self-signed certificate..."
                python3 setup_ssl.py --domain "$domain" --email "$email" --self-signed
            fi
        else
            echo "⚠️  Invalid domain or email, skipping HTTPS setup..."
        fi
        ;;
    2)
        echo ""
        read -p "Enter your domain name or IP (e.g., localhost or 192.168.1.100): " domain
        read -p "Enter your email address: " email
        
        if [ -n "$domain" ] && [ -n "$email" ]; then
            echo "🔧 Setting up self-signed SSL certificate..."
            python3 setup_ssl.py --domain "$domain" --email "$email" --self-signed
            
            if [ $? -eq 0 ]; then
                echo "✅ Self-signed certificate setup complete!"
                echo "🌐 Your application will be available at: https://$domain"
                echo "⚠️  Note: Browsers will show a security warning for self-signed certificates."
            else
                echo "❌ Self-signed certificate setup failed, continuing with HTTP..."
            fi
        else
            echo "⚠️  Invalid domain or email, skipping HTTPS setup..."
        fi
        ;;
    3)
        echo "🌐 Continuing with HTTP only..."
        ;;
    *)
        echo "⚠️  Invalid choice, continuing with HTTP only..."
        ;;
esac

echo ""
echo "Setup complete! You can now run: python3 run.py"
