from dataclasses import dataclass
from typing import Optional
from .amount import Amount


@dataclass(frozen=True)
class TaxComponent:
    """
    Tax component breakdown for GST.
    Includes CGST, SGST, IGST, and Cess.
    """
    
    cgst: Amount
    sgst: Amount
    igst: Amount
    cess: Amount
    
    @classmethod
    def create(
        cls,
        cgst: float = 0.0,
        sgst: float = 0.0,
        igst: float = 0.0,
        cess: float = 0.0
    ) -> "TaxComponent":
        """Create TaxComponent from float values."""
        return cls(
            cgst=Amount.from_float(cgst),
            sgst=Amount.from_float(sgst),
            igst=Amount.from_float(igst),
            cess=Amount.from_float(cess)
        )
    
    @classmethod
    def zero(cls) -> "TaxComponent":
        """Create zero tax component."""
        return cls(
            cgst=Amount.zero(),
            sgst=Amount.zero(),
            igst=Amount.zero(),
            cess=Amount.zero()
        )
    
    @property
    def total_tax(self) -> Amount:
        """Calculate total tax amount."""
        return self.cgst.add(self.sgst).add(self.igst).add(self.cess)
    
    @property
    def is_intrastate(self) -> bool:
        """Check if transaction is intrastate (CGST + SGST)."""
        return self.cgst.is_positive() or self.sgst.is_positive()
    
    @property
    def is_interstate(self) -> bool:
        """Check if transaction is interstate (IGST)."""
        return self.igst.is_positive()
    
    def matches(self, other: "TaxComponent", tolerance_percent: float = 0.5) -> bool:
        """Check if tax components match within tolerance."""
        return (
            self.cgst.is_within_tolerance(other.cgst, tolerance_percent) and
            self.sgst.is_within_tolerance(other.sgst, tolerance_percent) and
            self.igst.is_within_tolerance(other.igst, tolerance_percent) and
            self.cess.is_within_tolerance(other.cess, tolerance_percent)
        )
    
    def __str__(self) -> str:
        parts = []
        if self.cgst.is_positive():
            parts.append(f"CGST: {self.cgst}")
        if self.sgst.is_positive():
            parts.append(f"SGST: {self.sgst}")
        if self.igst.is_positive():
            parts.append(f"IGST: {self.igst}")
        if self.cess.is_positive():
            parts.append(f"Cess: {self.cess}")
        
        return ", ".join(parts) if parts else "No Tax"
