@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0backend"

echo.
echo 🎞️  Fotograf Czeladnik — uruchamianie...
echo 📡 Adres: http://localhost:5000
echo ⚙️  Panel admina: http://localhost:5000/admin
echo.
echo ⚠️  Aby zatrzymać aplikację, naciśnij Ctrl+C
echo.

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python nie jest zainstalowany lub nie jest w PATH!
    echo Uruchom install.bat aby zainstalować wymagane komponenty.
    pause
    exit /b 1
)

:: Check if Flask is installed
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Flask nie jest zainstalowany!
    echo Uruchom install.bat aby zainstalować wymagane komponenty.
    pause
    exit /b 1
)

:: Check if database exists
if not exist "fotograf.db" (
    echo ❌ Baza danych nie istnieje!
    echo Uruchom install.bat aby zainicjalizować bazę danych.
    pause
    exit /b 1
)

echo 🚀 Uruchamianie serwera...
python app.py

pause
