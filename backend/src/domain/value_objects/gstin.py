import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GSTIN:
    """
    GSTIN (Goods and Services Tax Identification Number) value object.
    Format: 22AAAAA0000A1Z5
    - 2 digits: State code
    - 10 characters: PAN
    - 1 digit: Entity number
    - 1 character: Z (default)
    - 1 character: Checksum
    """
    
    value: str
    
    GSTIN_PATTERN = re.compile(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$')
    
    def __post_init__(self):
        """Validate GSTIN format."""
        if not self.is_valid():
            raise ValueError(f"Invalid GSTIN format: {self.value}")
    
    def is_valid(self) -> bool:
        """Check if GSTIN is valid."""
        if not self.value or len(self.value) != 15:
            return False
        return bool(self.GSTIN_PATTERN.match(self.value))
    
    @property
    def state_code(self) -> str:
        """Extract state code from GSTIN."""
        return self.value[:2]
    
    @property
    def pan(self) -> str:
        """Extract PAN from GSTIN."""
        return self.value[2:12]
    
    @property
    def entity_number(self) -> str:
        """Extract entity number from GSTIN."""
        return self.value[12]
    
    @property
    def checksum(self) -> str:
        """Extract checksum from GSTIN."""
        return self.value[14]
    
    def __str__(self) -> str:
        return self.value
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, GSTIN):
            return False
        return self.value == other.value
    
    def __hash__(self) -> int:
        return hash(self.value)
