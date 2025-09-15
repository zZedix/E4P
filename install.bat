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
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist .env (
    echo ⚙️  Creating configuration file...
    copy env.example .env
    echo ✅ Configuration file created. You can edit .env to customize settings.
)

REM Ask about HTTPS setup
echo.
echo 🔐 HTTPS Configuration (Optional)
echo ==================================
set /p setup_https="Do you want to set up HTTPS with SSL certificate? (y/N): "

if /i "%setup_https%"=="y" (
    echo.
    set /p domain="Enter your domain name (e.g., example.com): "
    set /p email="Enter your email address for Let's Encrypt: "
    
    if not "%domain%"=="" if not "%email%"=="" (
        echo 🔒 Setting up SSL certificate...
        python setup_ssl.py --domain "%domain%" --email "%email%"
        
        if errorlevel 1 (
            echo ⚠️  HTTPS setup failed, continuing with HTTP...
        ) else (
            echo ✅ HTTPS setup complete!
            echo 🌐 Your application will be available at: https://%domain%
        )
    ) else (
        echo ⚠️  Invalid domain or email, continuing with HTTP...
    )
)

REM Create temp directory
if not exist "C:\tmp\e4p" mkdir "C:\tmp\e4p"

REM Start the application
echo.
echo 🚀 Starting E4P server...
echo ==========================================

REM Check if HTTPS is enabled
findstr /C:"USE_HTTPS=true" .env >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=2 delims==" %%a in ('findstr "DOMAIN=" .env') do set domain=%%a
    for /f "tokens=2 delims==" %%a in ('findstr "APP_PORT=" .env') do set port=%%a
    echo 🔒 HTTPS enabled - Access at: https://%domain%:%port%
) else (
    echo 🌐 HTTP enabled - Access at: http://localhost:8080
)

echo Press Ctrl+C to stop the server
echo ==========================================

python run.py
pause
