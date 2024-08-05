#!/bin/bash
echo "Starting setup script..."

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate


if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment."
    exit 1
fi

echo "Virtual environment activated."

echo
echo "Updating pip..."
pip install --upgrade pip setuptools wheel
echo


echo
echo "Installing required packages..."
pip install -r requirements.txt > pip_install_log.txt 2>&1
cat pip_install_log.txt


echo "Setup complete."
