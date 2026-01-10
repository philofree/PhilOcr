# Prompt for Cursor AI: Document AI OCR Application Implementation

I need you to implement a Document AI OCR application that extracts text from PDF documents using Google Cloud's Document AI service. I'm not an experienced developer, so please handle the implementation autonomously while guiding me through the process with clear explanations.

## Core Requirements

Create a desktop application that:
1. Allows users to select PDF files
2. Processes these files using Google Document AI OCR
3. Displays the extracted text in a scrollable window
4. Provides status updates and progress indication during processing
5. Allows saving the extracted text to a file

## Technical Specifications

The application should:
- Be built with Python using Tkinter for the GUI
- Use Google Cloud Document AI API for OCR processing
- Use threading for UI responsiveness
- Have a clean, intuitive interface
- Include proper error handling
- Be well-documented with comments

## The Implementation Should Include

1. **Main application file (`main.py`)** with:
   - A simple Tkinter interface with:
     - A "Select PDF" button at the top
     - A status label showing processing state
     - A progress bar that appears during processing
     - A scrollable text area to display extracted text
     - A "Save Text" button to export the results
   - Background processing using threading to keep the UI responsive
   - Clear error handling with user-friendly messages
   - Environment variable configuration for Google Cloud settings

2. **Requirements file (`requirements.txt`)** listing all dependencies

3. **Documentation (`README.md`)** with:
   - Installation instructions
   - Instructions for setting up Google Cloud Document AI
   - Configuration guidance
   - Usage instructions
   - Troubleshooting tips

## Implementation Guidelines

1. **For the PDF processing:**
   - Connect to Google Document AI using the provided project ID, location, and processor ID
   - Process PDF documents and extract all text content
   - Handle potential errors gracefully

2. **For the user interface:**
   - Keep the UI responsive during processing by using threading
   - Show processing status with both text and a progress indicator
   - Enable/disable buttons appropriately during processing
   - Provide clear feedback about the processing result

3. **For error handling:**
   - Validate configuration before attempting to process documents
   - Catch and display meaningful error messages
   - Provide recovery options when possible

## Starting Point

Below is a skeleton of the implementation that needs to be completed:

```python
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
from google.cloud import documentai_v1 as documentai

# Google Cloud configuration details.
# Set these as environment variables or replace the default values
PROJECT_ID = os.getenv("DOCUMENT_AI_PROJECT_ID", "your-project-id")
LOCATION = os.getenv("DOCUMENT_AI_LOCATION", "your-processor-location")
PROCESSOR_ID = os.getenv("DOCUMENT_AI_PROCESSOR_ID", "your-processor-id")

def process_pdf(file_path):
    """
    Process the given PDF using Google Document AI OCR and return the extracted text.
    
    Args:
        file_path (str): The path to the PDF file.
    
    Returns:
        str: The text extracted from the PDF.
    
    Raises:
        Exception: Propagates any exception that occurs during processing.
    """
    # TODO: Implement PDF processing with Document AI
    pass

def process_and_update(file_path):
    """
    Worker function to process the PDF and update the UI.
    
    Args:
        file_path (str): The path to the PDF file.
    """
    # TODO: Implement threaded processing with UI updates
    pass

def update_text_box(text):
    """Update the text box with the given text."""
    # TODO: Implement text box update
    pass

def select_file():
    """Handle file selection and initiate processing."""
    # TODO: Implement file selection
    pass

def save_text():
    """Save the extracted text to a file."""
    # TODO: Implement save functionality
    pass

# TODO: Set up the main Tkinter window and UI components

# TODO: Start the Tkinter event loop
```

Please complete the implementation, ensuring it's well-documented and user-friendly. I need a production-ready application that requires minimal technical knowledge to use beyond the initial Google Cloud setup.

## Additional Notes

- The application should run on Windows, macOS, and Linux
- Error messages should be informative but not overly technical
- The UI should be clean and intuitive for non-technical users
- Configuration should use my existing ENV.local file (see below)
- The README should provide complete setup instructions

## ENV.local File Integration

I already have all the required environmental variables set up in an ENV.local file with the following structure:

```
DOCUMENT_AI_PROJECT_ID=my-project-id
DOCUMENT_AI_LOCATION=my-processor-location
DOCUMENT_AI_PROCESSOR_ID=my-processor-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/my-credentials.json
```

Instead of using system environment variables, please modify the implementation to:

1. Look for this ENV.local file in the application directory
2. Load the variables from this file if it exists
3. Fall back to system environment variables if the file isn't found
4. Use default values only as a last resort

This will make the application more portable and easier to configure. You'll need to implement a function to parse this .env file format.

Thank you for implementing this solution. Please explain your implementation choices as you go, and ensure the final product is both functional and user-friendly.
