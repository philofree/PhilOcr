@echo off
REM Build script for OJD OCR Processor
REM This script runs the full packaging process for the application on Windows

cls
echo ========================================================
echo OJD OCR Processor - Packaging Script
echo ========================================================
echo.

REM Check for virtual environment
if exist venv (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
)

REM Install required packages
echo Installing required packages...
pip install -r requirements.txt

REM Run the packaging script
echo Running packaging script...
python package.py

REM Check if the packaging was successful
if %ERRORLEVEL% EQU 0 (
    echo Running package tests...
    python test_package.py
    
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo ========================================================
        echo Packaging completed successfully!
        echo ========================================================
        
        echo Executable created at:
        echo %CD%\dist\OJD OCR Processor\OJD OCR Processor.exe
        
        echo.
        echo You can run the application by double-clicking:
        echo OJD OCR Processor.exe in the dist folder
        
        echo.
        echo User guide is available at:
        echo %CD%\OJD_OCR_User_Guide.md
    ) else (
        echo.
        echo ========================================================
        echo Package testing failed. Please check the errors above.
        echo ========================================================
        exit /b 1
    )
) else (
    echo.
    echo ========================================================
    echo Packaging failed. Please check the errors above.
    echo ========================================================
    exit /b 1
)

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

echo.
pause
exit /b 0 