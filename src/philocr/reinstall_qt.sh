#!/bin/bash
# Script to properly reinstall PyQt6 packages

echo "Reinstalling PyQt6 packages..."

# Activate the virtual environment if needed
# source .venv/bin/activate

# Completely remove PyQt6 packages
pip uninstall -y PyQt6 PyQt6-Qt6 PyQt6-sip PyQt6-tools

# Clear pip cache
pip cache purge

# Check if Qt 6 is installed via Homebrew (recommended)
if ! brew list qt@6 &>/dev/null; then
    echo "Qt 6 not found in Homebrew. Installing Qt 6..."
    brew install qt@6
    # Add Qt to path if needed
    echo 'export PATH="/usr/local/opt/qt@6/bin:$PATH"' >> ~/.zshrc
fi

# Install PyQt6 with specific versions known to work together
pip install --no-cache-dir PyQt6==6.5.0 PyQt6-Qt6==6.5.0 PyQt6-sip==13.5.1

# Verify installation
pip list | grep -i pyqt

echo "Reinstallation complete. Try running the application now with:"
echo "python run_app.py" 