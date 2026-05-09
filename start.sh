#!/bin/bash

# Fotograf Czeladnik - Linux/macOS Start Script
# Enhanced version with better error handling

cd "$(dirname "$0")/backend"

echo
echo "🎞️  Fotograf Czeladnik — uruchamianie..."
echo "📡 Adres: http://localhost:5000"
echo "⚙️  Panel admina: http://localhost:5000/admin"
echo
echo "⚠️  Aby zatrzymać aplikację, naciśnij Ctrl+C"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python nie jest zainstalowany!"
    echo "Uruchom ./install.sh aby zainstalować wymagane komponenty."
    exit 1
fi

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

# Check if Flask is installed
if ! $PYTHON_CMD -c "import flask" &> /dev/null; then
    echo "❌ Flask nie jest zainstalowany!"
    echo "Uruchom ./install.sh aby zainstalować wymagane komponenty."
    exit 1
fi

# Check if database exists
if [ ! -f "fotograf.db" ]; then
    echo "❌ Baza danych nie istnieje!"
    echo "Uruchom ./install.sh aby zainicjalizować bazę danych."
    exit 1
fi

echo "🚀 Uruchamianie serwera..."
$PYTHON_CMD app.py
