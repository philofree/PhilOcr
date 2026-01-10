#!/bin/bash
# Build script for OJD OCR Processor
# This script runs the full packaging process for the application

# Set error handling
set -e

# Clear the terminal
clear

echo "========================================================"
echo "OJD OCR Processor - Packaging Script"
echo "========================================================"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install required packages
echo "Installing required packages..."
pip install -r requirements.txt

# Run the packaging script
echo "Running packaging script..."
python package.py

# Check if the packaging was successful
if [ $? -eq 0 ]; then
    echo "Running package tests..."
    python test_package.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "========================================================"
        echo "Packaging completed successfully!"
        echo "========================================================"
        
        # Determine the platform and show appropriate path
        if [ "$(uname)" == "Darwin" ]; then
            # macOS
            echo "Application bundle created at:"
            echo "$(pwd)/dist/OJD OCR Processor.app"
            
            echo ""
            echo "You can run the application with:"
            echo "open \"$(pwd)/dist/OJD OCR Processor.app\""
        else
            # Linux or other
            echo "Executable created at:"
            echo "$(pwd)/dist/OJD OCR Processor/OJD OCR Processor"
            
            echo ""
            echo "You can run the application with:"
            echo "\"$(pwd)/dist/OJD OCR Processor/OJD OCR Processor\""
        fi
        
        echo ""
        echo "User guide is available at:"
        echo "$(pwd)/OJD_OCR_User_Guide.md"
    else
        echo ""
        echo "========================================================"
        echo "Package testing failed. Please check the errors above."
        echo "========================================================"
        exit 1
    fi
else
    echo ""
    echo "========================================================"
    echo "Packaging failed. Please check the errors above."
    echo "========================================================"
    exit 1
fi

# Deactivate virtual environment
deactivate

exit 0 