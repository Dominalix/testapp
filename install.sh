#!/bin/bash

# Fotograf Czeladnik - Universal Installation Script
# Works on Linux, macOS, and Windows (with Git Bash)

echo "📷 Fotograf Czeladnik - Instalator"
echo "=================================="
echo ""

# Detect operating system
OS="Unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="Windows"
fi

echo "🔍 Wykryto system: $OS"
echo ""

# Check Python installation
echo "🐍 Sprawdzanie instalacji Pythona..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "✅ Znaleziono Python 3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "✅ Znaleziono Python"
else
    echo "❌ Python nie jest zainstalowany!"
    echo ""
    echo "Proszę zainstalować Python 3.8+ z:"
    echo "  • Linux: sudo apt install python3 python3-pip (Ubuntu/Debian)"
    echo "  • macOS: brew install python3"
    echo "  • Windows: https://www.python.org/downloads/"
    echo ""
    echo "⚠️  Podczas instalacji na Windows zaznacz 'Add Python to PATH'!"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "📌 Wersja Pythona: $PYTHON_VERSION"

# Check if version is 3.8+
if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    echo "✅ Wersja Pythona jest kompatybilna"
else
    echo "❌ Wymagany Python 3.8+ (obecna: $PYTHON_VERSION)"
    exit 1
fi

# Check pip
echo ""
echo "📦 Sprawdzanie pip..."
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
    echo "✅ Znaleziono pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
    echo "✅ Znaleziono pip"
else
    echo "❌ pip nie jest zainstalowany!"
    echo "Proszę zainstalować pip:"
    echo "  • Linux: sudo apt install python3-pip"
    echo "  • macOS: python3 -m ensurepip --upgrade"
    exit 1
fi

# Install Flask
echo ""
echo "🔧 Instalowanie Flask..."
$PIP_CMD install flask --quiet

if [ $? -eq 0 ]; then
    echo "✅ Flask zainstalowany pomyślnie"
else
    echo "❌ Błąd instalacji Flask"
    exit 1
fi

# Create database if it doesn't exist
echo ""
echo "🗄️  Inicjalizacja bazy danych..."
cd "$(dirname "$0")/backend"

if [ ! -f "fotograf.db" ]; then
    echo "📝 Tworzenie bazy danych..."
    $PYTHON_CMD build_db.py
    if [ $? -eq 0 ]; then
        echo "✅ Baza danych utworzona pomyślnie"
    else
        echo "❌ Błąd tworzenia bazy danych"
        exit 1
    fi
else
    echo "✅ Baza danych już istnieje"
fi

echo ""
echo "🎉 Instalacja zakończona pomyślnie!"
echo ""
echo "🚀 Uruchamianie aplikacji:"
echo "   • Linux/macOS: ./start.sh"
echo "   • Windows: start.bat"
echo ""
echo "📡 Adresy:"
echo "   • Aplikacja: http://localhost:5000"
echo "   • Panel admina: http://localhost:5000/admin"
echo ""
echo "📖 Więcej informacji w README.md"

# Ask if user wants to start the app now
echo ""
read -p "🚀 Czy uruchomić aplikację teraz? (t/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Tt]$ ]]; then
    echo "🎞️  Uruchamianie Fotograf Czeladnik..."
    echo "📡 Adres: http://localhost:5000"
    echo "⚙️  Panel admina: http://localhost:5000/admin"
    echo ""
    echo "⚠️  Aby zatrzymać aplikację, naciśnij Ctrl+C"
    echo ""
    $PYTHON_CMD app.py
fi
