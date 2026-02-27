from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from ..entities import Invoice, Mismatch


class IReconciliationService(ABC):
    """Interface for reconciliation operations."""
    
    @abstractmethod
    async def reconcile_invoices(
        self,
        taxpayer_id: UUID,
        period: str
    ) -> List[Mismatch]:
        """Reconcile invoices for a taxpayer and period."""
        pass
    
    @abstractmethod
    async def validate_itc_chain(
        self,
        invoice: Invoice
    ) -> bool:
        """Validate ITC chain for an invoice."""
        pass
    
    @abstractmethod
    async def classify_mismatch(
        self,
        invoice1: Invoice,
        invoice2: Invoice
    ) -> Mismatch:
        """Classify mismatch between two invoices."""
        pass
