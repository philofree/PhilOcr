"""
Custom exception hierarchy for the PhilOcr application.

This module provides a comprehensive exception hierarchy for better error handling
and to avoid catch-all exception handlers. All application-specific exceptions
should inherit from PhilOcrError.
"""

from __future__ import annotations


class PhilOcrError(Exception):
    """Base exception for all PhilOcr application errors."""


# Processing Errors
class DocumentProcessingError(PhilOcrError):
    """Exception raised when document processing fails."""


class PDFProcessingError(DocumentProcessingError):
    """Exception raised when PDF processing fails.

    Attributes:
        file_path: Path to the PDF file that failed to process
        reason: Reason for the failure
    """

    def __init__(self, file_path: str, reason: str = "Unknown error") -> None:
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"Failed to process PDF {file_path}: {reason}")


class PDFParseError(PDFProcessingError):
    """Exception raised when a PDF cannot be parsed (corrupted, password-protected, etc.)."""


class PDFPageCountError(PDFProcessingError):
    """Exception raised when page count cannot be determined."""


# API/Network Errors
class APIRateLimitError(PhilOcrError):
    """Exception raised when an API rate limit is hit."""


class APIConnectionError(PhilOcrError):
    """Exception raised when API connection fails."""


class APITimeoutError(PhilOcrError):
    """Exception raised when API request times out."""


class APIError(PhilOcrError):
    """Generic API error.

    Attributes:
        status_code: HTTP status code if applicable
        message: Error message from API
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)


# Configuration Errors
class ConfigurationError(PhilOcrError):
    """Exception raised when configuration is invalid or missing."""


class CredentialsError(ConfigurationError):
    """Exception raised when credentials are invalid or missing."""


class EnvironmentVariableError(ConfigurationError):
    """Exception raised when required environment variable is missing."""

    def __init__(self, var_name: str) -> None:
        self.var_name = var_name
        super().__init__(f"Required environment variable '{var_name}' is not set")


# File Operation Errors
class FileOperationError(PhilOcrError):
    """Base exception for file operation errors."""


class FileNotFoundError(FileOperationError):
    """Exception raised when a required file is not found.

    Note: This is different from built-in FileNotFoundError to avoid confusion.
    """

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        super().__init__(f"File not found: {file_path}")


class FilePermissionError(FileOperationError):
    """Exception raised when file permission is denied."""


class FileSaveError(FileOperationError):
    """Exception raised when file save operation fails."""

    def __init__(self, file_path: str, reason: str = "Unknown error") -> None:
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"Failed to save file {file_path}: {reason}")


class FileLoadError(FileOperationError):
    """Exception raised when file load operation fails."""

    def __init__(self, file_path: str, reason: str = "Unknown error") -> None:
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"Failed to load file {file_path}: {reason}")


# Validation Errors
class ValidationError(PhilOcrError):
    """Base exception for validation errors."""


class JSONValidationError(ValidationError):
    """Exception raised when JSON validation fails."""


class MarkdownConversionError(PhilOcrError):
    """Base exception for markdown conversion errors.

    Note: Kept for backward compatibility with existing markdown converter.
    """


class FormatDetectionError(MarkdownConversionError):
    """Raised when format detection fails."""


class AlternativeFormatError(MarkdownConversionError):
    """Raised when alternative format conversion fails."""


class ChunkProcessingError(MarkdownConversionError):
    """Raised when chunk processing fails."""


class HTMLConversionError(MarkdownConversionError):
    """Raised when HTML conversion fails."""


# Worker/Thread Errors
class WorkerError(PhilOcrError):
    """Base exception for worker thread errors."""


class WorkerCancelledError(WorkerError):
    """Exception raised when a worker is cancelled."""


class WorkerTimeoutError(WorkerError):
    """Exception raised when a worker operation times out."""
