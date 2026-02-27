"""Reconciliation related exceptions."""

from .base_exception import GSTReconciliationException


class ReconciliationException(GSTReconciliationException):
    """Base exception for reconciliation errors."""
    
    def __init__(self, message: str):
        super().__init__(message, "RECONCILIATION_ERROR")


class ITCValidationException(ReconciliationException):
    """Exception for ITC validation errors."""
    
    def __init__(self, message: str):
        super().__init__(f"ITC validation failed: {message}")


class MismatchClassificationException(ReconciliationException):
    """Exception for mismatch classification errors."""
    
    def __init__(self, message: str):
        super().__init__(f"Mismatch classification failed: {message}")
