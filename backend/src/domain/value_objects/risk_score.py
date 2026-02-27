from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RiskScore:
    """
    Risk score value object (0-100).
    0 = Highest risk
    100 = Lowest risk (most compliant)
    """
    
    value: Decimal
    
    def __post_init__(self):
        """Validate risk score range."""
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, 'value', Decimal(str(self.value)))
        
        if not (0 <= self.value <= 100):
            raise ValueError(f"Risk score must be between 0 and 100, got {self.value}")
        
        # Round to 2 decimal places
        rounded = self.value.quantize(Decimal('0.01'))
        object.__setattr__(self, 'value', rounded)
    
    @classmethod
    def from_float(cls, value: float) -> "RiskScore":
        """Create RiskScore from float."""
        return cls(Decimal(str(value)))
    
    @classmethod
    def high_risk(cls) -> "RiskScore":
        """Create high risk score (0)."""
        return cls(Decimal('0.00'))
    
    @classmethod
    def low_risk(cls) -> "RiskScore":
        """Create low risk score (100)."""
        return cls(Decimal('100.00'))
    
    @classmethod
    def medium_risk(cls) -> "RiskScore":
        """Create medium risk score (50)."""
        return cls(Decimal('50.00'))
    
    @property
    def is_high_risk(self) -> bool:
        """Check if score indicates high risk (<40)."""
        return self.value < Decimal('40.00')
    
    @property
    def is_medium_risk(self) -> bool:
        """Check if score indicates medium risk (40-70)."""
        return Decimal('40.00') <= self.value < Decimal('70.00')
    
    @property
    def is_low_risk(self) -> bool:
        """Check if score indicates low risk (>=70)."""
        return self.value >= Decimal('70.00')
    
    @property
    def risk_category(self) -> str:
        """Get risk category as string."""
        if self.is_high_risk:
            return "HIGH_RISK"
        elif self.is_medium_risk:
            return "MEDIUM_RISK"
        else:
            return "LOW_RISK"
    
    def __str__(self) -> str:
        return f"{self.value}/100 ({self.risk_category})"
    
    def __float__(self) -> float:
        return float(self.value)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, RiskScore):
            return False
        return self.value == other.value
    
    def __lt__(self, other: "RiskScore") -> bool:
        return self.value < other.value
    
    def __hash__(self) -> int:
        return hash(self.value)
