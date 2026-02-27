from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from ..enums import ReturnType
from ..value_objects import GSTIN, Amount


@dataclass
class GSTReturn:
    """
    GST Return entity representing filed returns.
    """
    
    id: UUID = field(default_factory=uuid4)
    taxpayer_id: UUID = field(default=None)
    gstin: GSTIN = field(default=None)
    
    # Return details
    return_type: ReturnType = field(default=ReturnType.GSTR3B)
    return_period: str = field(default="")  # Format: MMYYYY (e.g., "032024")
    financial_year: str = field(default="")  # Format: YYYY-YY (e.g., "2023-24")
    
    # Filing details
    filing_date: Optional[datetime] = field(default=None)
    due_date: Optional[datetime] = field(default=None)
    status: str = field(default="FILED")  # FILED, NOT_FILED, LATE_FILED
    arn: Optional[str] = field(default=None)  # Acknowledgement Reference Number
    
    # Summary amounts (for GSTR-3B)
    total_outward_supply: Amount = field(default_factory=Amount.zero)
    total_inward_supply: Amount = field(default_factory=Amount.zero)
    total_itc_claimed: Amount = field(default_factory=Amount.zero)
    total_tax_liability: Amount = field(default_factory=Amount.zero)
    total_tax_paid: Amount = field(default_factory=Amount.zero)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_filed(self) -> bool:
        """Check if return is filed."""
        return self.status == "FILED"
    
    @property
    def is_late_filed(self) -> bool:
        """Check if return was filed late."""
        if not self.filing_date or not self.due_date:
            return False
        return self.filing_date > self.due_date
    
    @property
    def days_late(self) -> int:
        """Calculate days late if filed late."""
        if not self.is_late_filed:
            return 0
        return (self.filing_date - self.due_date).days
    
    def mark_as_filed(self, filing_date: datetime, arn: str) -> None:
        """Mark return as filed."""
        self.status = "LATE_FILED" if self.is_late_filed else "FILED"
        self.filing_date = filing_date
        self.arn = arn
        self.updated_at = datetime.utcnow()
    
    def __str__(self) -> str:
        return f"{self.return_type.value} for {self.return_period} - {self.status}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, GSTReturn):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
