from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from ..value_objects import GSTIN, IRN, Amount, TaxComponent


@dataclass
class Invoice:
    """
    Invoice entity representing a GST invoice.
    Can be from GSTR-1, GSTR-2B, Purchase Register, or e-Invoice.
    """
    
    id: UUID = field(default_factory=uuid4)
    invoice_number: str = field(default="")
    invoice_date: datetime = field(default_factory=datetime.utcnow)
    
    # Parties
    supplier_gstin: GSTIN = field(default=None)
    recipient_gstin: GSTIN = field(default=None)
    
    # Amounts
    taxable_value: Amount = field(default_factory=Amount.zero)
    tax_amount: TaxComponent = field(default_factory=TaxComponent.zero)
    total_amount: Amount = field(default_factory=Amount.zero)
    
    # Additional fields
    irn: Optional[IRN] = field(default=None)
    place_of_supply: str = field(default="")
    reverse_charge: bool = field(default=False)
    invoice_type: str = field(default="B2B")  # B2B, B2C, Export, etc.
    
    # Source tracking
    source_type: str = field(default="")  # GSTR-1, GSTR-2B, PURCHASE_REGISTER, E_INVOICE
    source_period: Optional[str] = field(default=None)  # e.g., "032024" for March 2024
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def total_tax(self) -> Amount:
        """Get total tax amount."""
        return self.tax_amount.total_tax
    
    @property
    def is_intrastate(self) -> bool:
        """Check if invoice is intrastate."""
        return self.tax_amount.is_intrastate
    
    @property
    def is_interstate(self) -> bool:
        """Check if invoice is interstate."""
        return self.tax_amount.is_interstate
    
    @property
    def has_irn(self) -> bool:
        """Check if invoice has IRN."""
        return self.irn is not None
    
    def calculate_total(self) -> Amount:
        """Calculate total invoice amount."""
        return self.taxable_value.add(self.total_tax)
    
    def matches_invoice(
        self,
        other: "Invoice",
        amount_tolerance: float = 0.5,
        date_tolerance_days: int = 7
    ) -> bool:
        """
        Check if this invoice matches another invoice.
        Used for reconciliation between GSTR-1 and GSTR-2B.
        """
        # Invoice number must match
        if self.invoice_number != other.invoice_number:
            return False
        
        # GSTIN must match (supplier in one should be recipient in other)
        if self.supplier_gstin != other.supplier_gstin:
            return False
        
        # Date should be within tolerance
        date_diff = abs((self.invoice_date - other.invoice_date).days)
        if date_diff > date_tolerance_days:
            return False
        
        # Amount should be within tolerance
        if not self.total_amount.is_within_tolerance(other.total_amount, amount_tolerance):
            return False
        
        return True
    
    def update_amounts(
        self,
        taxable_value: Amount,
        tax_amount: TaxComponent
    ) -> None:
        """Update invoice amounts."""
        self.taxable_value = taxable_value
        self.tax_amount = tax_amount
        self.total_amount = self.calculate_total()
        self.updated_at = datetime.utcnow()
    
    def __str__(self) -> str:
        return f"Invoice {self.invoice_number} dated {self.invoice_date.date()} - {self.total_amount}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Invoice):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
