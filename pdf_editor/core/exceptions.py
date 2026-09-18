"""
Custom exception hierarchy for the PDF Editor.

Keeping a dedicated exception hierarchy lets the GUI layer catch specific,
predictable error types and show the user a friendly message instead of a
raw traceback, while still logging the full detail for debugging.
"""


class PDFEditorError(Exception):
    """Base class for all application-specific errors."""


class CorruptedPDFError(PDFEditorError):
    """Raised when a PDF file cannot be parsed / is structurally invalid."""


class EncryptedPDFError(PDFEditorError):
    """Raised when a PDF requires a password that was not supplied."""


class InvalidPasswordError(PDFEditorError):
    """Raised when a supplied password fails to open an encrypted PDF."""


class UnsupportedFileError(PDFEditorError):
    """Raised when a file's extension/content is not supported by an operation."""


class PageRangeError(PDFEditorError):
    """Raised when a requested page number/range is out of bounds."""


class EmptyInputError(PDFEditorError):
    """Raised when an operation is triggered without the required input files."""
