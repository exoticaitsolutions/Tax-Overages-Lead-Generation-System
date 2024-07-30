@echo off
echo "Starting setup script..."

echo "Creating virtual environment..."
python.exe -m venv venv

echo "Activating virtual environment in directory: %cd%"
echo "Activating virtual environment..."
call .\venv\Scripts\activate.bat

if %errorlevel% neq 0 (
    echo "Failed to activate virtual environment."
    pause
    exit /b 1
)

echo "Virtual environment activated in directory: %cd%"

echo.
echo "Installing required packages..."
pip install -r requirements.txt > pip_install_log.txt 2>&1
type pip_install_log.txt


echo.
echo "Installing required packages..."
python.exe -m pip install --upgrade pip
echo.
echo "Setup complete."
pause
