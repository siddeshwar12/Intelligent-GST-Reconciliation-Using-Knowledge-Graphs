from abc import ABC, abstractmethod
from uuid import UUID

from ..value_objects import RiskScore


class IMLService(ABC):
    """Interface for ML operations."""
    
    @abstractmethod
    async def predict_vendor_risk(
        self,
        vendor_id: UUID
    ) -> RiskScore:
        """Predict vendor compliance risk score."""
        pass
    
    @abstractmethod
    async def detect_anomalies(
        self,
        taxpayer_id: UUID,
        period: str
    ) -> list:
        """Detect anomalies in transactions."""
        pass
