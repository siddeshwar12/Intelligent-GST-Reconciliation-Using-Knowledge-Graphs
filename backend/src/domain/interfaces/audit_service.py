from abc import ABC, abstractmethod
from uuid import UUID

from ..entities import AuditTrail


class IAuditService(ABC):
    """Interface for audit trail operations."""
    
    @abstractmethod
    async def generate_audit_trail(
        self,
        invoice_id: UUID,
        reconciliation_run_id: UUID
    ) -> AuditTrail:
        """Generate audit trail for an invoice."""
        pass
    
    @abstractmethod
    async def get_audit_trail(
        self,
        audit_trail_id: UUID
    ) -> AuditTrail:
        """Get existing audit trail."""
        pass
