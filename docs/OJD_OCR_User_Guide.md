# OJD OCR Processor - User Guide

## Introduction

OJD OCR Processor is a desktop application that extracts text from PDF documents using Google's Document AI technology. This standalone application requires no command line knowledge or Python installation.

## Installation

No installation is required. Simply double-click the application to run it.

- **macOS**: Open the `OJD OCR Processor.app` file
- **Windows**: Run the `OJD OCR Processor.exe` file

When you first run the application, you might see security warnings because the application is not signed with a recognized developer certificate. Follow your operating system's instructions to bypass these warnings.

## Interface Overview

The application has a simple, intuitive interface:

- **Select File**: Choose a single PDF file to process
- **Batch Process**: Select multiple PDF files to process in sequence
- **Save Text**: Save the extracted text to a file
- **Clear**: Clear the current results and start a new operation
- **About**: View application information and version details

## Processing PDFs

### Single File Processing

1. Click the "Select File" button
2. Browse to and select your PDF file
3. Click "Open"
4. The application will begin processing immediately
5. Progress will be shown in the status bar
6. When complete, the extracted text will appear in the main window

### Batch Processing

1. Click the "Batch Process" button
2. Browse to and select multiple PDF files (use Ctrl/Cmd+Click to select multiple files)
3. Click "Open"
4. Files will be processed in sequence
5. Progress information will show which file is currently being processed
6. Results will be displayed for each file as processing completes

## Saving Results

1. After processing a document, click the "Save Text" button
2. Choose a location and filename to save the extracted text
3. Select the file format (.txt is recommended)
4. Click "Save"

## Advanced Features

### Large Document Handling

Documents with more than 15 pages are automatically split into smaller chunks for processing. This is done to optimize OCR accuracy and respect Google Cloud API limits. The results from all chunks are combined seamlessly.

### Rate Limiting

The application includes built-in rate limiting to prevent exceeding Google Cloud API quotas. This ensures reliable operation even when processing multiple large documents.

## Troubleshooting

### Authentication Issues

If you encounter errors related to Google Cloud authentication:

1. Click the "About" button
2. In the dialog that appears, check that your credentials are valid
3. If needed, use the credentials dialog to update your settings

### Processing Errors

If a document fails to process:

1. Check that the PDF is not password-protected
2. Ensure the PDF contains actual text or images (not just blank pages)
3. Try processing a smaller portion of the document if it's very large

### Application Not Responding

If the application appears to freeze:

1. Give it some time - processing large documents can take several minutes
2. Check the status bar for progress information
3. If no progress is made for more than 5 minutes, you may need to restart the application

## Known Limitations

- PDFs with complex layouts may have text extracted in a different order than visually appears on the page
- Very large documents (hundreds of pages) may take significant time to process
- Handwritten text recognition accuracy varies depending on handwriting clarity
- Some special characters or symbols might not be recognized correctly

## Version History

- **1.0.0**: Initial release with basic text extraction functionality

## Support

This application is for personal use. If you encounter issues, please check this guide for troubleshooting tips.

---

*OJD OCR Processor is powered by Google Document AI technology* 