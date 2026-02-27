from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..entities import Invoice, Taxpayer, Vendor, Mismatch, GSTReturn


class IGraphRepository(ABC):
    """Interface for graph database operations."""
    
    @abstractmethod
    async def create_invoice(self, invoice: Invoice) -> Invoice:
        """Create invoice node in graph."""
        pass
    
    @abstractmethod
    async def get_invoice(self, invoice_id: UUID) -> Optional[Invoice]:
        """Get invoice by ID."""
        pass
    
    @abstractmethod
    async def create_taxpayer(self, taxpayer: Taxpayer) -> Taxpayer:
        """Create taxpayer node in graph."""
        pass
    
    @abstractmethod
    async def get_taxpayer_by_gstin(self, gstin: str) -> Optional[Taxpayer]:
        """Get taxpayer by GSTIN."""
        pass
    
    @abstractmethod
    async def create_relationship(
        self,
        from_id: UUID,
        to_id: UUID,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create relationship between nodes."""
        pass
    
    @abstractmethod
    async def find_matching_invoices(
        self,
        invoice: Invoice,
        source_types: List[str]
    ) -> List[Invoice]:
        """Find matching invoices from different sources."""
        pass
