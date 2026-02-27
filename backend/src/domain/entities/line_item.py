from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from ..value_objects import Amount, TaxComponent


@dataclass
class LineItem:
    """
    Line item entity representing individual items in an invoice.
    """
    
    id: UUID = field(default_factory=uuid4)
    invoice_id: UUID = field(default=None)
    
    # Item details
    item_number: int = field(default=1)
    description: str = field(default="")
    hsn_code: str = field(default="")
    
    # Quantity and rate
    quantity: float = field(default=1.0)
    unit_of_measurement: str = field(default="NOS")
    rate: Amount = field(default_factory=Amount.zero)
    
    # Amounts
    taxable_value: Amount = field(default_factory=Amount.zero)
    discount: Amount = field(default_factory=Amount.zero)
    
    # Tax details
    tax_rate: float = field(default=0.0)  # Total GST rate (e.g., 18%)
    tax_amount: TaxComponent = field(default_factory=TaxComponent.zero)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def total_value(self) -> Amount:
        """Calculate total value including tax."""
        return self.taxable_value.add(self.tax_amount.total_tax)
    
    @property
    def gross_amount(self) -> Amount:
        """Calculate gross amount (quantity * rate)."""
        return self.rate.multiply(self.quantity)
    
    def calculate_taxable_value(self) -> Amount:
        """Calculate taxable value after discount."""
        return self.gross_amount.subtract(self.discount)
    
    def update_amounts(self) -> None:
        """Recalculate all amounts."""
        self.taxable_value = self.calculate_taxable_value()
        self.updated_at = datetime.utcnow()
    
    def __str__(self) -> str:
        return f"LineItem {self.item_number}: {self.description} - {self.total_value}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, LineItem):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
