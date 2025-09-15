@echo off
REM E4P - Encryption 4 People - Windows Installation Script
REM This script installs and runs the E4P secure file encryption web application

echo 🔐 Installing Encryption 4 People (E4P)...
echo ==========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed. Please install Python first.
    pause
    exit /b 1
)

REM Check if pip is installed
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip is required but not installed. Please install pip first.
    pause
    exit /b 1
)

REM Install dependencies
echo 📦 Installing dependencies...
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
echo 🚀 Starting E4P server...
echo ==========================================
echo Access the application at: http://localhost:8080
echo Press Ctrl+C to stop the server
echo ==========================================

python run.py
pause
