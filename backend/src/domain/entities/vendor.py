from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from ..value_objects import GSTIN, RiskScore


@dataclass
class Vendor:
    """
    Vendor entity with compliance tracking.
    Extends Taxpayer with vendor-specific attributes.
    """
    
    id: UUID = field(default_factory=uuid4)
    taxpayer_id: UUID = field(default=None)
    gstin: GSTIN = field(default=None)
    name: str = field(default="")
    
    # Compliance metrics
    compliance_score: RiskScore = field(default_factory=RiskScore.medium_risk)
    total_transactions: int = field(default=0)
    total_mismatches: int = field(default=0)
    critical_mismatches: int = field(default=0)
    
    # Filing behavior
    on_time_filings: int = field(default=0)
    late_filings: int = field(default=0)
    missed_filings: int = field(default=0)
    
    # Financial metrics
    total_invoice_value: float = field(default=0.0)
    total_mismatch_value: float = field(default=0.0)
    
    # Timestamps
    last_transaction_date: Optional[datetime] = field(default=None)
    last_assessment_date: Optional[datetime] = field(default=None)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def mismatch_rate(self) -> float:
        """Calculate mismatch rate percentage."""
        if self.total_transactions == 0:
            return 0.0
        return (self.total_mismatches / self.total_transactions) * 100
    
    @property
    def critical_mismatch_rate(self) -> float:
        """Calculate critical mismatch rate percentage."""
        if self.total_transactions == 0:
            return 0.0
        return (self.critical_mismatches / self.total_transactions) * 100
    
    @property
    def filing_punctuality_rate(self) -> float:
        """Calculate filing punctuality rate percentage."""
        total_filings = self.on_time_filings + self.late_filings + self.missed_filings
        if total_filings == 0:
            return 100.0
        return (self.on_time_filings / total_filings) * 100
    
    @property
    def is_high_risk(self) -> bool:
        """Check if vendor is high risk."""
        return self.compliance_score.is_high_risk
    
    @property
    def is_reliable(self) -> bool:
        """Check if vendor is reliable (low risk)."""
        return self.compliance_score.is_low_risk
    
    def update_compliance_score(self, score: RiskScore) -> None:
        """Update compliance score."""
        self.compliance_score = score
        self.last_assessment_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def record_transaction(self, invoice_value: float) -> None:
        """Record a new transaction."""
        self.total_transactions += 1
        self.total_invoice_value += invoice_value
        self.last_transaction_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def record_mismatch(self, is_critical: bool, mismatch_value: float) -> None:
        """Record a mismatch."""
        self.total_mismatches += 1
        if is_critical:
            self.critical_mismatches += 1
        self.total_mismatch_value += mismatch_value
        self.updated_at = datetime.utcnow()
    
    def record_filing(self, on_time: bool, missed: bool = False) -> None:
        """Record a filing event."""
        if missed:
            self.missed_filings += 1
        elif on_time:
            self.on_time_filings += 1
        else:
            self.late_filings += 1
        self.updated_at = datetime.utcnow()
    
    def __str__(self) -> str:
        return f"Vendor {self.name} ({self.gstin}) - Score: {self.compliance_score}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Vendor):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
