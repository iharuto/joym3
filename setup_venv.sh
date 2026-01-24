#!/bin/bash

echo "Setting up Joy-Con virtual environment..."

# Remove old venv if it exists
if [ -d "joycon-venv" ]; then
    echo "Removing old virtual environment..."
    rm -rf joycon-venv
fi

# Create new virtual environment using Homebrew Python
echo "Creating new virtual environment..."
/opt/homebrew/bin/python3 -m venv joycon-venv

# Activate virtual environment
echo "Activating virtual environment..."
source joycon-venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install hid pyobjc

echo ""
echo "✓ Setup complete!"
echo ""
echo "To run the application:"
echo "  ./run_app.sh"
echo ""
