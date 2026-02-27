"""Payment entity for GST tax payments."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from ..value_objects import Amount


@dataclass
class Payment:
    """
    Payment entity representing GST tax payments.
    """
    
    id: UUID = field(default_factory=uuid4)
    taxpayer_id: UUID = field(default=None)
    return_id: Optional[UUID] = field(default=None)
    
    # Payment details
    payment_id: str = field(default="")
    payment_date: datetime = field(default_factory=datetime.utcnow)
    payment_mode: str = field(default="ONLINE")  # ONLINE, CHALLAN, etc.
    
    # Amounts
    cgst_paid: Amount = field(default_factory=Amount.zero)
    sgst_paid: Amount = field(default_factory=Amount.zero)
    igst_paid: Amount = field(default_factory=Amount.zero)
    cess_paid: Amount = field(default_factory=Amount.zero)
    interest: Amount = field(default_factory=Amount.zero)
    penalty: Amount = field(default_factory=Amount.zero)
    
    # Reference
    challan_number: Optional[str] = field(default=None)
    bank_reference: Optional[str] = field(default=None)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def total_tax_paid(self) -> Amount:
        """Calculate total tax paid."""
        return (
            self.cgst_paid
            .add(self.sgst_paid)
            .add(self.igst_paid)
            .add(self.cess_paid)
        )
    
    @property
    def total_amount(self) -> Amount:
        """Calculate total payment including interest and penalty."""
        return (
            self.total_tax_paid
            .add(self.interest)
            .add(self.penalty)
        )
    
    def __str__(self) -> str:
        return f"Payment {self.payment_id} - {self.total_amount} on {self.payment_date.date()}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Payment):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
