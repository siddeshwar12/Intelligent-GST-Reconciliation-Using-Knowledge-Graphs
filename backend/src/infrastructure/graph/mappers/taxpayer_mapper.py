"""Mapper for Taxpayer entity to/from graph nodes."""

from typing import Dict, Any
from datetime import datetime

from ....domain.entities import Taxpayer
from ....domain.value_objects import GSTIN


class TaxpayerMapper:
    """Maps Taxpayer entities to/from Neo4j nodes."""
    
    def to_dict(self, taxpayer: Taxpayer) -> Dict[str, Any]:
        """Convert Taxpayer entity to dictionary for Neo4j."""
        return {
            "id": str(taxpayer.id),
            "gstin": str(taxpayer.gstin),
            "legal_name": taxpayer.legal_name,
            "trade_name": taxpayer.trade_name,
            "taxpayer_type": taxpayer.taxpayer_type,
            "state_code": taxpayer.state_code,
            "is_active": taxpayer.is_active,
            "created_at": taxpayer.created_at.isoformat(),
            "updated_at": taxpayer.updated_at.isoformat(),
        }
    
    def from_node(self, node: Dict[str, Any]) -> Taxpayer:
        """Convert Neo4j node to Taxpayer entity."""
        return Taxpayer(
            id=node.get("id"),
            gstin=GSTIN(node["gstin"]),
            legal_name=node.get("legal_name", ""),
            trade_name=node.get("trade_name"),
            taxpayer_type=node.get("taxpayer_type", "Regular"),
            state_code=node.get("state_code", ""),
            is_active=node.get("is_active", True),
            created_at=datetime.fromisoformat(node.get("created_at")),
            updated_at=datetime.fromisoformat(node.get("updated_at"))
        )
