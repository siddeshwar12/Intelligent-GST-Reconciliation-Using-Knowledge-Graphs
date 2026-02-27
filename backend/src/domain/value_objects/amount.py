from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Union


@dataclass(frozen=True)
class Amount:
    """
    Immutable amount value object with precision handling.
    All GST amounts are stored with 2 decimal precision.
    """
    
    value: Decimal
    
    def __post_init__(self):
        """Ensure value is Decimal with 2 decimal places."""
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, 'value', Decimal(str(self.value)))
        
        # Round to 2 decimal places
        rounded = self.value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        object.__setattr__(self, 'value', rounded)
    
    @classmethod
    def from_float(cls, value: float) -> "Amount":
        """Create Amount from float."""
        return cls(Decimal(str(value)))
    
    @classmethod
    def from_string(cls, value: str) -> "Amount":
        """Create Amount from string."""
        return cls(Decimal(value))
    
    @classmethod
    def zero(cls) -> "Amount":
        """Create zero amount."""
        return cls(Decimal('0.00'))
    
    def add(self, other: "Amount") -> "Amount":
        """Add two amounts."""
        return Amount(self.value + other.value)
    
    def subtract(self, other: "Amount") -> "Amount":
        """Subtract two amounts."""
        return Amount(self.value - other.value)
    
    def multiply(self, multiplier: Union[int, float, Decimal]) -> "Amount":
        """Multiply amount by a number."""
        return Amount(self.value * Decimal(str(multiplier)))
    
    def divide(self, divisor: Union[int, float, Decimal]) -> "Amount":
        """Divide amount by a number."""
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        return Amount(self.value / Decimal(str(divisor)))
    
    def percentage_of(self, total: "Amount") -> Decimal:
        """Calculate what percentage this amount is of total."""
        if total.value == 0:
            return Decimal('0.00')
        return ((self.value / total.value) * 100).quantize(Decimal('0.01'))
    
    def variance_percent(self, other: "Amount") -> Decimal:
        """Calculate percentage variance between two amounts."""
        if self.value == 0:
            return Decimal('100.00') if other.value != 0 else Decimal('0.00')
        
        variance = ((other.value - self.value) / self.value * 100)
        return variance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def is_within_tolerance(self, other: "Amount", tolerance_percent: float) -> bool:
        """Check if two amounts are within tolerance percentage."""
        variance = abs(self.variance_percent(other))
        return variance <= Decimal(str(tolerance_percent))
    
    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.value == Decimal('0.00')
    
    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.value > Decimal('0.00')
    
    def is_negative(self) -> bool:
        """Check if amount is negative."""
        return self.value < Decimal('0.00')
    
    def __str__(self) -> str:
        return f"₹{self.value:,.2f}"
    
    def __float__(self) -> float:
        return float(self.value)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Amount):
            return False
        return self.value == other.value
    
    def __lt__(self, other: "Amount") -> bool:
        return self.value < other.value
    
    def __le__(self, other: "Amount") -> bool:
        return self.value <= other.value
    
    def __gt__(self, other: "Amount") -> bool:
        return self.value > other.value
    
    def __ge__(self, other: "Amount") -> bool:
        return self.value >= other.value
    
    def __hash__(self) -> int:
        return hash(self.value)
