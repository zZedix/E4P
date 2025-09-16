#!/bin/bash

# E4P - Encryption 4 People - One Line Installation Script
# Usage: curl -sSL https://raw.githubusercontent.com/zZedix/E4P/main/install.sh | bash

set -euo pipefail

# -----------------------------
# Helper functions
# -----------------------------
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

set_env_var() {
    local key="$1"
    local value="$2"
    if grep -q "^${key}=" ".env"; then
        if sed --version >/dev/null 2>&1; then
            sed -i "s#^${key}=.*#${key}=${value}#" ".env"
        else
            sed -i '' "s#^${key}=.*#${key}=${value}#" ".env"
        fi
    else
        printf '%s=%s\n' "$key" "$value" >> ".env"
    fi
}

get_env_var() {
    local key="$1"
    local default_value="${2-}"
    if grep -q "^${key}=" ".env"; then
        grep "^${key}=" ".env" | tail -n1 | cut -d'=' -f2-
    else
        printf '%s' "$default_value"
    fi
}

# -----------------------------
# Begin installation
# -----------------------------
echo "🔐 Installing Encryption 4 People (E4P)..."
echo "=========================================="

if [[ -z "${HOME:-}" ]]; then
    echo "❌ HOME environment variable is not set. Cannot determine installation directory."
    exit 1
fi

INSTALL_DIR="${E4P_INSTALL_DIR:-$HOME/.e4p}"
REPO_URL="https://github.com/zZedix/E4P.git"

# Ensure git, python3, and pip3 exist
if ! command -v git &> /dev/null; then
    install_git
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3 first."
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    install_pip3
fi

# Clone or update repository
echo "📥 Preparing installation directory at $INSTALL_DIR"
if [[ -d "$INSTALL_DIR/.git" ]]; then
    echo "🔄 Existing installation detected. Updating..."
    git -C "$INSTALL_DIR" pull --ff-only
else
    if [[ -e "$INSTALL_DIR" ]]; then
        BACKUP_DIR="${INSTALL_DIR}.bak.$(date +%s)"
        echo "⚠️  Existing path found at $INSTALL_DIR (not a git repo). Moving to $BACKUP_DIR"
        mv "$INSTALL_DIR" "$BACKUP_DIR"
    fi
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# Install dependencies
echo "📦 Installing Python dependencies..."
python3 -m pip install -r requirements.txt --quiet

# Ensure .env exists
if [[ ! -f .env ]]; then
    echo "⚙️  Creating configuration file..."
    cp env.example .env
fi

# Generate a secure secret key if placeholder is present
SECRET_KEY_VALUE="$(get_env_var SECRET_KEY)"
if [[ -z "$SECRET_KEY_VALUE" || "$SECRET_KEY_VALUE" == "change_me_to_random_base64" ]]; then
    NEW_SECRET_KEY="$(python3 - <<'PY'
import secrets
import base64
print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())
PY
)"
    set_env_var SECRET_KEY "$NEW_SECRET_KEY"
fi

# Prompt for domain to enable HTTPS
read -r -p "Enter your domain to enable HTTPS (leave blank for HTTP only): " DOMAIN
DOMAIN="${DOMAIN//[[:space:]]/}"

if [[ -n "$DOMAIN" ]]; then
    ENABLE_SSL=true
    read -r -p "Enter email for Let's Encrypt notifications [admin@${DOMAIN}]: " EMAIL_FOR_LETSENCRYPT
    if [[ -z "$EMAIL_FOR_LETSENCRYPT" ]]; then
        EMAIL_FOR_LETSENCRYPT="admin@${DOMAIN}"
    fi
else
    ENABLE_SSL=false
    EMAIL_FOR_LETSENCRYPT=""
fi

set_env_var DOMAIN "$DOMAIN"
set_env_var ENABLE_SSL "$ENABLE_SSL"
set_env_var EMAIL_FOR_LETSENCRYPT "$EMAIL_FOR_LETSENCRYPT"
set_env_var APP_HOST "$(get_env_var APP_HOST 0.0.0.0)"
set_env_var APP_PORT "$(get_env_var APP_PORT 8080)"
set_env_var APP_HTTP_PORT "$(get_env_var APP_HTTP_PORT 8080)"
set_env_var GUNICORN_WORKERS "$(get_env_var GUNICORN_WORKERS 2)"

# Install CLI wrapper
chmod +x E4P
CLI_LINK_CREATED=false
if [[ -w /usr/local/bin ]]; then
    TARGET_BIN="/usr/local/bin/E4P"
    ln -sf "$INSTALL_DIR/E4P" "$TARGET_BIN"
    chmod +x "$TARGET_BIN"
    CLI_LINK_CREATED=true
    echo "✅ E4P CLI linked to $TARGET_BIN"
else
    LOCAL_BIN="$HOME/.local/bin"
    mkdir -p "$LOCAL_BIN"
    TARGET_BIN="$LOCAL_BIN/E4P"
    ln -sf "$INSTALL_DIR/E4P" "$TARGET_BIN"
    chmod +x "$TARGET_BIN"
    CLI_LINK_CREATED=true
    echo "✅ E4P CLI linked to $TARGET_BIN"
    if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
        echo "💡 Add $LOCAL_BIN to your PATH to use the 'E4P' command."
    fi
fi

if [[ "$CLI_LINK_CREATED" == false ]]; then
    echo "⚠️  Could not install CLI globally. You can run './E4P' from $INSTALL_DIR."
fi

# Ensure temp directory exists
mkdir -p /tmp/e4p

HTTPS_DEPLOYED=false
if [[ "$ENABLE_SSL" == true ]]; then
    if command -v docker &> /dev/null; then
        echo "🐳 Docker detected."
        read -r -p "Would you like to run the Docker-based HTTPS deployment now? [Y/n]: " RUN_HTTPS
        RUN_HTTPS=${RUN_HTTPS:-Y}
        if [[ "$RUN_HTTPS" =~ ^[Yy]$ ]]; then
            echo "🚀 Starting HTTPS deployment via setup.sh"
            chmod +x setup.sh
            printf '%s\n%s\n' "$DOMAIN" "$EMAIL_FOR_LETSENCRYPT" | ./setup.sh
            HTTPS_DEPLOYED=true
        else
            echo "ℹ️  You can run './setup.sh' later to enable HTTPS."
        fi
    else
        echo "⚠️  Docker is required to enable HTTPS automatically. Install Docker and run './setup.sh' later."
    fi
fi

if [[ "$HTTPS_DEPLOYED" == false ]]; then
    echo
    echo "🚀 Starting E4P server..."
    echo "=========================================="
    echo "🌐 HTTP enabled - Access at: http://localhost:8080"
    echo "Press Ctrl+C to stop the server"
    echo "=========================================="
    python3 run.py
else
    echo "✅ HTTPS deployment initiated. Containers are running via Docker Compose."
    echo "Use 'docker compose ps' from $INSTALL_DIR to check status."
fi
