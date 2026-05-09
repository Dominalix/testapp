@echo off
setlocal enabledelayedexpansion

:: Fotograf Czeladnik - Windows Installation Script
:: Enhanced version with better error handling and user feedback

echo.
echo 📷 Fotograf Czeladnik - Instalator Windows
echo ==========================================
echo.

:: Check if Python is installed
echo 🐍 Sprawdzanie instalacji Pythona...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python nie jest zainstalowany lub nie jest w PATH!
    echo.
    echo Proszę zainstalować Python 3.8+ z: https://www.python.org/downloads/
    echo ⚠️  Podczas instalacji zaznacz "Add Python to PATH"!
    echo.
    pause
    exit /b 1
)

:: Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Znaleziono Python %PYTHON_VERSION%

:: Check if Python version is 3.8+
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% lss 3 (
    echo ❌ Wymagany Python 3.8+ (obecna: %PYTHON_VERSION%)
    pause
    exit /b 1
)

if %MAJOR% equ 3 if %MINOR% lss 8 (
    echo ❌ Wymagany Python 3.8+ (obecna: %PYTHON_VERSION%)
    pause
    exit /b 1
)

echo ✅ Wersja Pythona jest kompatybilna

:: Check if pip is available
echo.
echo 📦 Sprawdzanie pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip nie jest dostępny!
    echo Proszę zainstalować pip lub użyć alternatywnej instalacji Pythona.
    pause
    exit /b 1
)

:: Get pip version
for /f "tokens=2" %%i in ('pip --version 2^>^&1') do set PIP_VERSION=%%i
echo ✅ Znaleziono pip %PIP_VERSION%

:: Install Flask
echo.
echo 🔧 Instalowanie Flask...
python -m pip install flask --quiet
if %errorlevel% neq 0 (
    echo ❌ Błąd instalacji Flask!
    echo Spróbuj zainstalować ręcznie: python -m pip install flask
    pause
    exit /b 1
)

echo ✅ Flask zainstalowany pomyślnie

:: Change to backend directory
cd /d "%~dp0backend"

:: Create database if it doesn't exist
echo.
echo 🗄️  Inicjalizacja bazy danych...
if not exist "fotograf.db" (
    echo 📝 Tworzenie bazy danych...
    python build_db.py
    if %errorlevel% neq 0 (
        echo ❌ Błąd tworzenia bazy danych!
        pause
        exit /b 1
    )
    echo ✅ Baza danych utworzona pomyślnie
) else (
    echo ✅ Baza danych już istnieje
)

echo.
echo 🎉 Instalacja zakończona pomyślnie!
echo.
echo 🚀 Uruchamianie aplikacji:
echo    • Windows: start.bat
echo.
echo 📡 Adresy:
echo    • Aplikacja: http://localhost:5000
echo    • Panel admina: http://localhost:5000/admin
echo.
echo 📖 Więcej informacji w README.md

:: Ask if user wants to start the app now
echo.
set /p "start_app=🚀 Czy uruchomić aplikację teraz? (t/n): "
if /i "%start_app%"=="t" (
    echo.
    echo 🎞️  Uruchamianie Fotograf Czeladnik...
    echo 📡 Adres: http://localhost:5000
    echo ⚙️  Panel admina: http://localhost:5000/admin
    echo.
    echo ⚠️  Aby zatrzymać aplikację, naciśnij Ctrl+C
    echo.
    python app.py
)

echo.
pause
