from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from ..value_objects import GSTIN


@dataclass
class Taxpayer:
    """
    Taxpayer entity representing a GST registered entity.
    Can be both buyer and supplier.
    """
    
    id: UUID = field(default_factory=uuid4)
    gstin: GSTIN = field(default=None)
    legal_name: str = field(default="")
    trade_name: Optional[str] = field(default=None)
    taxpayer_type: str = field(default="Regular")  # Regular, Composition, ISD, etc.
    registration_date: Optional[datetime] = field(default=None)
    state_code: str = field(default="")
    is_active: bool = field(default=True)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate taxpayer data."""
        if self.gstin and not self.state_code:
            self.state_code = self.gstin.state_code
    
    @property
    def display_name(self) -> str:
        """Get display name (trade name or legal name)."""
        return self.trade_name or self.legal_name
    
    def update_details(
        self,
        legal_name: Optional[str] = None,
        trade_name: Optional[str] = None,
        taxpayer_type: Optional[str] = None
    ) -> None:
        """Update taxpayer details."""
        if legal_name:
            self.legal_name = legal_name
        if trade_name:
            self.trade_name = trade_name
        if taxpayer_type:
            self.taxpayer_type = taxpayer_type
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate taxpayer."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate taxpayer."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def __str__(self) -> str:
        return f"{self.display_name} ({self.gstin})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Taxpayer):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
