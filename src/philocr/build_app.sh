#!/bin/bash
# Script to build a standalone macOS application with PyInstaller

echo "=== Building standalone macOS application ==="

# Check if PyInstaller is installed
if ! pip show pyinstaller > /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Create spec file
echo "Creating PyInstaller spec file..."
pyinstaller --name "OJD_OCR_Processor" \
    --windowed \
    --log-level INFO \
    --add-data "philocr_icons:philocr_icons" \
    --hidden-import PyQt6.QtCore \
    --hidden-import PyQt6.QtGui \
    --hidden-import PyQt6.QtWidgets \
    --hidden-import PyQt6.sip \
    --osx-bundle-identifier "com.ojd.ocrprocessor" \
    main.py

# Build the application
echo "Building application bundle..."
pyinstaller --clean OJD_OCR_Processor.spec

echo "=== Build complete ==="
echo "Application bundle saved to ./dist/OJD_OCR_Processor.app"
echo "To run the application, open dist/OJD_OCR_Processor.app" 