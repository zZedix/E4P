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

# Create temp directory
mkdir -p /tmp/e4p

# Start the application
echo "🚀 Starting E4P server..."
echo "=========================================="
echo "Access the application at: http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo "=========================================="

python3 run.py
