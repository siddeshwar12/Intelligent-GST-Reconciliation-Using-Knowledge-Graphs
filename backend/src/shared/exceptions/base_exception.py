"""Base exception classes for the application."""


class GSTReconciliationException(Exception):
    """Base exception for all application exceptions."""
    
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ValidationException(GSTReconciliationException):
    """Exception for validation errors."""
    
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class NotFoundException(GSTReconciliationException):
    """Exception for resource not found errors."""
    
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, "NOT_FOUND")
        self.resource = resource
        self.identifier = identifier


class DuplicateException(GSTReconciliationException):
    """Exception for duplicate resource errors."""
    
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with identifier '{identifier}' already exists"
        super().__init__(message, "DUPLICATE_ERROR")
        self.resource = resource
        self.identifier = identifier
