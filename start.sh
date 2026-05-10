#!/bin/bash
cd "$(dirname "$0")/backend"
echo "🎞️  Fotograf Czeladnik — uruchamianie..."
echo "📡 Adres: http://localhost:5000"
echo "⚙️  Panel admina: http://localhost:5000/admin"
echo ""
python3 app.py
