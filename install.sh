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

# Install dependencies
echo "📦 Installing Python dependencies..."
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
echo ""
echo "🚀 Starting E4P server..."
echo "=========================================="
echo "🌐 HTTP enabled - Access at: http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo "=========================================="

python3 run.py