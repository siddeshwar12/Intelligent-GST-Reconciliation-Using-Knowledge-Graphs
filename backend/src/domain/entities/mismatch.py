from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from ..enums import MismatchType, RiskLevel, MismatchStatus
from ..value_objects import Amount


@dataclass
class Mismatch:
    """
    Mismatch entity representing a discrepancy found during reconciliation.
    """
    
    id: UUID = field(default_factory=uuid4)
    
    # Related entities
    invoice_id_1: Optional[UUID] = field(default=None)  # Primary invoice
    invoice_id_2: Optional[UUID] = field(default=None)  # Matching invoice (if exists)
    taxpayer_id: UUID = field(default=None)
    
    # Mismatch details
    mismatch_type: MismatchType = field(default=MismatchType.AMOUNT_MISMATCH)
    risk_level: RiskLevel = field(default=RiskLevel.MEDIUM)
    status: MismatchStatus = field(default=MismatchStatus.OPEN)
    
    # Financial impact
    amount_difference: Amount = field(default_factory=Amount.zero)
    tax_impact: Amount = field(default_factory=Amount.zero)
    itc_impact: Amount = field(default_factory=Amount.zero)
    
    # Description and root cause
    description: str = field(default="")
    root_cause: str = field(default="")
    recommendation: str = field(default="")
    
    # Additional details
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Reconciliation metadata
    reconciliation_run_id: Optional[UUID] = field(default=None)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = field(default=None)
    resolved_by: Optional[str] = field(default=None)
    resolution_notes: Optional[str] = field(default=None)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_resolved(self) -> bool:
        """Check if mismatch is resolved."""
        return self.status in [MismatchStatus.RESOLVED, MismatchStatus.CLOSED]
    
    @property
    def is_critical(self) -> bool:
        """Check if mismatch is critical."""
        return self.risk_level == RiskLevel.CRITICAL
    
    @property
    def is_high_risk(self) -> bool:
        """Check if mismatch is high risk."""
        return self.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]
    
    @property
    def days_open(self) -> int:
        """Calculate days since mismatch was detected."""
        if self.resolved_at:
            return (self.resolved_at - self.detected_at).days
        return (datetime.utcnow() - self.detected_at).days
    
    def resolve(self, resolved_by: str, notes: Optional[str] = None) -> None:
        """Mark mismatch as resolved."""
        self.status = MismatchStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.resolved_by = resolved_by
        self.resolution_notes = notes
        self.updated_at = datetime.utcnow()
    
    def accept(self, accepted_by: str, notes: Optional[str] = None) -> None:
        """Accept mismatch as valid difference."""
        self.status = MismatchStatus.ACCEPTED
        self.resolved_at = datetime.utcnow()
        self.resolved_by = accepted_by
        self.resolution_notes = notes
        self.updated_at = datetime.utcnow()
    
    def dispute(self, notes: Optional[str] = None) -> None:
        """Mark mismatch as disputed."""
        self.status = MismatchStatus.DISPUTED
        self.resolution_notes = notes
        self.updated_at = datetime.utcnow()
    
    def update_risk_level(self, risk_level: RiskLevel) -> None:
        """Update risk level."""
        self.risk_level = risk_level
        self.updated_at = datetime.utcnow()
    
    def add_detail(self, key: str, value: Any) -> None:
        """Add additional detail."""
        self.details[key] = value
        self.updated_at = datetime.utcnow()
    
    def __str__(self) -> str:
        return f"Mismatch {self.mismatch_type.value} - {self.risk_level.value} ({self.status.value})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Mismatch):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
