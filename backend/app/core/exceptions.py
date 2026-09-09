"""
Custom application exception classes for SIH26103 Backend.
"""


class AppException(Exception):
    """Base exception for all application-specific exceptions."""
    def __init__(self, message: str = "An unexpected error occurred"):
        self.message = message
        super().__init__(self.message)


class NotFoundException(AppException):
    """Raised when a requested resource is not found."""
    pass


class ValidationException(AppException):
    """Raised when custom business validation fails."""
    pass
