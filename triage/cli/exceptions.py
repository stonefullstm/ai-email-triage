"""Custom exceptions for the triage CLI."""


class TriageCliException(Exception):
    """Base exception for CLI errors."""

    exit_code: int = 1
    message: str = "An error occurred"

    def __init__(self, message: str = None):
        if message:
            self.message = message
        super().__init__(self.message)


class IMAPConnectionError(TriageCliException):
    """Raised when IMAP connection fails."""

    exit_code = 2
    message = "Failed to connect to IMAP server"


class ConfigError(TriageCliException):
    """Raised when configuration is missing or invalid."""

    exit_code = 3
    message = "Configuration error"


class ValidationError(TriageCliException):
    """Raised when input validation fails."""

    exit_code = 4
    message = "Input validation failed"


class ResourceNotFoundError(TriageCliException):
    """Raised when a required resource is not found."""

    exit_code = 5
    message = "Resource not found"
