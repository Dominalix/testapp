@echo off
cd /d "%~dp0backend"
echo.
echo  Fotograf Czeladnik - uruchamianie...
echo  Adres: http://localhost:5000
echo  Panel admina: http://localhost:5000/admin
echo.
python app.py
pause
