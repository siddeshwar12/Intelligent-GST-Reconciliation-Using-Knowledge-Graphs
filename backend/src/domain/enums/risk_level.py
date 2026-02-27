from enum import Enum


class RiskLevel(str, Enum):
    """Financial risk levels for mismatches."""
    
    CRITICAL = "CRITICAL"  # >10% variance or missing invoices with high value
    HIGH = "HIGH"  # 5-10% variance or significant ITC impact
    MEDIUM = "MEDIUM"  # 2-5% variance or moderate impact
    LOW = "LOW"  # <2% variance or minimal impact
    
    @classmethod
    def from_amount_variance(cls, variance_percent: float) -> "RiskLevel":
        """Determine risk level based on amount variance percentage."""
        abs_variance = abs(variance_percent)
        
        if abs_variance > 10:
            return cls.CRITICAL
        elif abs_variance > 5:
            return cls.HIGH
        elif abs_variance > 2:
            return cls.MEDIUM
        else:
            return cls.LOW
