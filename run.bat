@echo off
chcp 65001 >nul

cd /d "%~dp0"
set PYTHONPATH=%CD%;%PYTHONPATH%

if not exist "venv" (
    python -m venv venv
)

call venv\Scripts\activate.bat

python -c "import flask" 2>nul
if errorlevel 1 (
    pip install --upgrade SQLAlchemy
    pip install -r requirements.txt
) else (
    echo.
)

echo Приложение запускается...
echo Откройте браузер: http://localhost:5001
echo Для остановки нажмите Ctrl+C

python app\startservice.py

pause

