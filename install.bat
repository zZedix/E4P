@echo off
REM E4P - Encryption 4 People - Windows Installation Script
REM This script installs and runs the E4P secure file encryption web application

echo 🔐 Installing Encryption 4 People (E4P)...
echo ==========================================

REM Clone the repository if not already present
if not exist "E4P" (
    echo 📥 Cloning E4P repository...
    git clone https://github.com/zZedix/E4P.git
    if errorlevel 1 (
        echo ❌ Failed to clone repository. Please check your internet connection.
        pause
        exit /b 1
    )
)

REM Change to the E4P directory
cd E4P

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed. Please install Python first.
    pause
    exit /b 1
)

REM Check if pip is installed, install if missing
pip --version >nul 2>&1
if errorlevel 1 (
    echo 📦 pip not found, attempting to install...
    
    REM Try to install pip using ensurepip
    python -m ensurepip --upgrade >nul 2>&1
    if errorlevel 1 (
        echo ❌ Failed to install pip automatically. Please install pip manually.
        echo You can download Python from https://python.org which includes pip.
        pause
        exit /b 1
    )
    
    echo ✅ pip installed successfully!
)

REM Install dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist .env (
    echo ⚙️  Creating configuration file...
    copy env.example .env
    echo ✅ Configuration file created. You can edit .env to customize settings.
)

REM Create temp directory
if not exist "C:\tmp\e4p" mkdir "C:\tmp\e4p"

REM Start the application
echo.
echo 🚀 Starting E4P server...
echo ==========================================
echo 🌐 HTTP enabled - Access at: http://localhost:8080
echo Press Ctrl+C to stop the server
echo ==========================================

python run.py
pause