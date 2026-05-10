@echo off
cd /d "%~dp0backend"
echo.
echo  Fotograf Czeladnik - uruchamianie...
echo.

python -m pip install flask --quiet
if %errorlevel% neq 0 (
    echo  BLAD: Python nie jest zainstalowany lub nie jest w PATH.
    echo  Pobierz Python ze strony: https://www.python.org/downloads/
    echo  Podczas instalacji zaznacz "Add Python to PATH"!
    pause
    exit /b 1
)

echo  Adres: http://localhost:5000
echo  Panel admina: http://localhost:5000/admin
echo.
python app.py
pause
