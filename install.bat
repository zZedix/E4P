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

REM Install SSL dependencies for HTTPS setup
echo 🔒 Installing SSL dependencies...
echo Installing OpenSSL Python bindings...
pip install --upgrade pyOpenSSL cryptography

REM Test OpenSSL compatibility
echo 🧪 Testing OpenSSL compatibility...
python -c "from OpenSSL import crypto; print('✅ OpenSSL works')" 2>nul
if errorlevel 1 (
    echo ⚠️  OpenSSL compatibility issue detected, trying to fix...
    pip install --upgrade --force-reinstall pyOpenSSL cryptography
    python -c "from OpenSSL import crypto; print('✅ OpenSSL works')" 2>nul
    if errorlevel 1 (
        echo ❌ OpenSSL compatibility issues remain. HTTPS setup may fail.
    ) else (
        echo ✅ OpenSSL compatibility fixed!
    )
) else (
    echo ✅ OpenSSL compatibility confirmed!
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

REM HTTPS Configuration (Mandatory)
echo.
echo 🔐 HTTPS Configuration (Required)
echo =================================
echo E4P requires HTTPS for security. Please provide your domain information:
echo.

:get_domain
set /p domain="Enter your domain name (e.g., example.com): "
if "%domain%"=="" (
    echo ❌ Domain name is required. Please try again.
    goto get_domain
)

:get_email
set /p email="Enter your email address for Let's Encrypt: "
if "%email%"=="" (
    echo ❌ Email address is required. Please try again.
    goto get_email
)

echo.
echo 🔒 Setting up SSL certificate for %domain%...
python setup_ssl.py --domain "%domain%" --email "%email%"

if errorlevel 1 (
    echo ⚠️  Let's Encrypt failed, trying self-signed certificate...
    python setup_ssl.py --domain "%domain%" --email "%email%" --self-signed
    
    if errorlevel 1 (
        echo ❌ SSL certificate setup failed. Please check your domain and try again.
        echo You can run: setup_https_interactive.sh to try again later.
        pause
        exit /b 1
    ) else (
        echo ✅ Self-signed certificate setup complete!
        echo 🌐 Your application will be available at: https://%domain%
        echo ⚠️  Note: Browsers will show a security warning for self-signed certificates.
    )
) else (
    echo ✅ HTTPS setup complete!
    echo 🌐 Your application will be available at: https://%domain%
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
