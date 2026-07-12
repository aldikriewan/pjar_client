@echo off
REM PJAR Client Setup Script for Windows
REM Usage: Run this batch file

echo ======================================
echo PJAR Client - Windows Setup
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python 3.10+ is required but not installed
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo Python found!
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Create .env if it doesn't exist
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo.
    echo ** IMPORTANT: Edit .env with your server configuration **
)

echo.
echo ===== Setup Complete! =====
echo.
echo To run the WEB client (browser-based):
echo 1. Open Command Prompt in this folder
echo 2. Run: venv\Scripts\activate
echo 3. Run: python web_app.py
echo 4. Buka browser: http://localhost:5001
echo.
echo Before first run:
echo - Edit .env with your server URL
echo - Make sure server is running on Ubuntu
echo.
pause
