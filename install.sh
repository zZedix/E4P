#!/bin/bash

# E4P - Encryption 4 People - One Line Installation Script
# Usage: curl -sSL https://raw.githubusercontent.com/zZedix/E4P/main/install.sh | bash

set -e  # Exit on any error

echo "🔐 Installing Encryption 4 People (E4P)..."
echo "=========================================="

# Function to install git
install_git() {
    echo "📦 Installing git..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq
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
}

# Function to install pip3
install_pip3() {
    echo "📦 Installing pip3..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update -qq
            sudo apt-get install -y python3-pip python3-venv
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3-pip python3-venv
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y python3-pip python3-venv
        else
            echo "❌ Cannot install pip3 automatically. Please install pip3 manually."
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install python3
        else
            echo "❌ Homebrew not found. Please install pip3 manually or install Homebrew first."
            exit 1
        fi
    else
        echo "❌ Unsupported operating system. Please install pip3 manually."
        exit 1
    fi
}

# Check if git is installed, install if missing
if ! command -v git &> /dev/null; then
    install_git
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3 first."
    echo "   On Ubuntu/Debian: sudo apt-get install python3"
    echo "   On CentOS/RHEL: sudo yum install python3"
    echo "   On Fedora: sudo dnf install python3"
    echo "   On macOS: brew install python3"
    exit 1
fi

# Check if pip3 is installed, install if missing
if ! command -v pip3 &> /dev/null; then
    install_pip3
fi

# Create a temporary directory for installation
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Clone the repository
echo "📥 Cloning E4P repository..."
git clone https://github.com/zZedix/E4P.git
cd E4P

# Install dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt --quiet

# Create .env file
echo "⚙️  Creating configuration file..."
cp env.example .env

# Create temp directory
mkdir -p /tmp/e4p

# Start the application
echo ""
echo "🚀 Starting E4P server..."
echo "=========================================="
echo "🌐 HTTP enabled - Access at: http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo "=========================================="

# Run the application
python3 run.py