from enum import Enum


class ReconciliationStatus(str, Enum):
    """Status of reconciliation process."""
    
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"


class MismatchStatus(str, Enum):
    """Status of individual mismatch."""
    
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    ACCEPTED = "ACCEPTED"  # Accepted as valid difference
    DISPUTED = "DISPUTED"  # Disputed with vendor
    CLOSED = "CLOSED"
