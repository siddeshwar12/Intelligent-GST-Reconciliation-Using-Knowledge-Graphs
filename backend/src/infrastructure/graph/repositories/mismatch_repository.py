"""Mismatch repository for graph operations."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ....domain.entities import Mismatch
from ....domain.enums import MismatchType, RiskLevel, MismatchStatus
from ....domain.value_objects import Amount
from ..neo4j_client import Neo4jClient


class MismatchRepository:
    """Repository for mismatch graph operations."""
    
    def __init__(self, client: Neo4jClient):
        self.client = client
    
    async def create(self, mismatch: Mismatch) -> Mismatch:
        """
        Create mismatch node in graph.
        
        Args:
            mismatch: Mismatch entity
            
        Returns:
            Created mismatch
        """
        query = """
        CREATE (m:Mismatch {
            id: $id,
            invoice_id_1: $invoice_id_1,
            invoice_id_2: $invoice_id_2,
            taxpayer_id: $taxpayer_id,
            mismatch_type: $mismatch_type,
            risk_level: $risk_level,
            status: $status,
            amount_difference: $amount_difference,
            tax_impact: $tax_impact,
            itc_impact: $itc_impact,
            description: $description,
            root_cause: $root_cause,
            recommendation: $recommendation,
            reconciliation_run_id: $reconciliation_run_id,
            detected_at: datetime($detected_at),
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        RETURN m
        """
        
        params = {
            "id": str(mismatch.id),
            "invoice_id_1": str(mismatch.invoice_id_1) if mismatch.invoice_id_1 else None,
            "invoice_id_2": str(mismatch.invoice_id_2) if mismatch.invoice_id_2 else None,
            "taxpayer_id": str(mismatch.taxpayer_id),
            "mismatch_type": mismatch.mismatch_type.value,
            "risk_level": mismatch.risk_level.value,
            "status": mismatch.status.value,
            "amount_difference": float(mismatch.amount_difference.value),
            "tax_impact": float(mismatch.tax_impact.value),
            "itc_impact": float(mismatch.itc_impact.value),
            "description": mismatch.description,
            "root_cause": mismatch.root_cause,
            "recommendation": mismatch.recommendation,
            "reconciliation_run_id": str(mismatch.reconciliation_run_id) if mismatch.reconciliation_run_id else None,
            "detected_at": mismatch.detected_at.isoformat(),
            "created_at": mismatch.created_at.isoformat(),
            "updated_at": mismatch.updated_at.isoformat()
        }
        
        await self.client.execute_write(query, params)
        
        # Create relationships
        if mismatch.invoice_id_1:
            await self._link_to_invoice(mismatch.id, mismatch.invoice_id_1)
        if mismatch.taxpayer_id:
            await self._link_to_taxpayer(mismatch.id, mismatch.taxpayer_id)
        
        return mismatch
    
    async def get_by_id(self, mismatch_id: UUID) -> Optional[Mismatch]:
        """Get mismatch by ID."""
        query = """
        MATCH (m:Mismatch {id: $id})
        RETURN m
        """
        
        result = await self.client.execute_query(query, {"id": str(mismatch_id)})
        if not result:
            return None
        
        return self._map_from_node(result[0]["m"])
    
    async def find_by_taxpayer(
        self, 
        taxpayer_id: UUID,
        status: Optional[MismatchStatus] = None
    ) -> List[Mismatch]:
        """
        Find mismatches for a taxpayer.
        
        Args:
            taxpayer_id: Taxpayer UUID
            status: Optional status filter
            
        Returns:
            List of mismatches
        """
        if status:
            query = """
            MATCH (m:Mismatch {taxpayer_id: $taxpayer_id, status: $status})
            RETURN m
            ORDER BY m.detected_at DESC
            """
            params = {"taxpayer_id": str(taxpayer_id), "status": status.value}
        else:
            query = """
            MATCH (m:Mismatch {taxpayer_id: $taxpayer_id})
            RETURN m
            ORDER BY m.detected_at DESC
            """
            params = {"taxpayer_id": str(taxpayer_id)}
        
        result = await self.client.execute_query(query, params)
        return [self._map_from_node(record["m"]) for record in result]
    
    async def find_by_risk_level(self, risk_level: RiskLevel) -> List[Mismatch]:
        """
        Find mismatches by risk level.
        
        Args:
            risk_level: Risk level to filter
            
        Returns:
            List of mismatches
        """
        query = """
        MATCH (m:Mismatch {risk_level: $risk_level, status: 'OPEN'})
        RETURN m
        ORDER BY m.amount_difference DESC
        """
        
        result = await self.client.execute_query(query, {"risk_level": risk_level.value})
        return [self._map_from_node(record["m"]) for record in result]
    
    async def get_critical_mismatches(self, limit: int = 50) -> List[Mismatch]:
        """
        Get critical mismatches.
        
        Args:
            limit: Maximum results
            
        Returns:
            List of critical mismatches
        """
        query = """
        MATCH (m:Mismatch {risk_level: 'CRITICAL', status: 'OPEN'})
        RETURN m
        ORDER BY m.amount_difference DESC
        LIMIT $limit
        """
        
        result = await self.client.execute_query(query, {"limit": limit})
        return [self._map_from_node(record["m"]) for record in result]
    
    async def update_status(
        self, 
        mismatch_id: UUID, 
        status: MismatchStatus,
        resolved_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update mismatch status.
        
        Args:
            mismatch_id: Mismatch UUID
            status: New status
            resolved_by: User who resolved
            notes: Resolution notes
            
        Returns:
            True if successful
        """
        query = """
        MATCH (m:Mismatch {id: $id})
        SET m.status = $status,
            m.resolved_at = datetime($resolved_at),
            m.resolved_by = $resolved_by,
            m.resolution_notes = $notes,
            m.updated_at = datetime($updated_at)
        RETURN m
        """
        
        params = {
            "id": str(mismatch_id),
            "status": status.value,
            "resolved_at": datetime.utcnow().isoformat() if status in [MismatchStatus.RESOLVED, MismatchStatus.CLOSED] else None,
            "resolved_by": resolved_by,
            "notes": notes,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = await self.client.execute_write(query, params)
        return result["properties_set"] > 0
    
    async def get_statistics(self, taxpayer_id: Optional[UUID] = None) -> dict:
        """
        Get mismatch statistics.
        
        Args:
            taxpayer_id: Optional taxpayer filter
            
        Returns:
            Dictionary with statistics
        """
        if taxpayer_id:
            query = """
            MATCH (m:Mismatch {taxpayer_id: $taxpayer_id})
            RETURN 
                count(m) as total_mismatches,
                sum(CASE WHEN m.status = 'OPEN' THEN 1 ELSE 0 END) as open_mismatches,
                sum(CASE WHEN m.risk_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
                sum(CASE WHEN m.risk_level = 'HIGH' THEN 1 ELSE 0 END) as high_count,
                sum(CASE WHEN m.risk_level = 'MEDIUM' THEN 1 ELSE 0 END) as medium_count,
                sum(CASE WHEN m.risk_level = 'LOW' THEN 1 ELSE 0 END) as low_count,
                sum(m.amount_difference) as total_amount_difference,
                sum(m.itc_impact) as total_itc_impact
            """
            params = {"taxpayer_id": str(taxpayer_id)}
        else:
            query = """
            MATCH (m:Mismatch)
            RETURN 
                count(m) as total_mismatches,
                sum(CASE WHEN m.status = 'OPEN' THEN 1 ELSE 0 END) as open_mismatches,
                sum(CASE WHEN m.risk_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
                sum(CASE WHEN m.risk_level = 'HIGH' THEN 1 ELSE 0 END) as high_count,
                sum(CASE WHEN m.risk_level = 'MEDIUM' THEN 1 ELSE 0 END) as medium_count,
                sum(CASE WHEN m.risk_level = 'LOW' THEN 1 ELSE 0 END) as low_count,
                sum(m.amount_difference) as total_amount_difference,
                sum(m.itc_impact) as total_itc_impact
            """
            params = {}
        
        result = await self.client.execute_query(query, params)
        if not result:
            return {}
        
        return dict(result[0])
    
    async def _link_to_invoice(self, mismatch_id: UUID, invoice_id: UUID) -> bool:
        """Create relationship between mismatch and invoice."""
        query = """
        MATCH (m:Mismatch {id: $mismatch_id})
        MATCH (i:Invoice {id: $invoice_id})
        MERGE (i)-[r:HAS_MISMATCH]->(m)
        RETURN r
        """
        
        params = {
            "mismatch_id": str(mismatch_id),
            "invoice_id": str(invoice_id)
        }
        
        result = await self.client.execute_write(query, params)
        return result["relationships_created"] > 0
    
    async def _link_to_taxpayer(self, mismatch_id: UUID, taxpayer_id: UUID) -> bool:
        """Create relationship between mismatch and taxpayer."""
        query = """
        MATCH (m:Mismatch {id: $mismatch_id})
        MATCH (t:Taxpayer {id: $taxpayer_id})
        MERGE (m)-[r:DETECTED_FOR]->(t)
        RETURN r
        """
        
        params = {
            "mismatch_id": str(mismatch_id),
            "taxpayer_id": str(taxpayer_id)
        }
        
        result = await self.client.execute_write(query, params)
        return result["relationships_created"] > 0
    
    def _map_from_node(self, node: dict) -> Mismatch:
        """Map Neo4j node to Mismatch entity."""
        return Mismatch(
            id=UUID(node["id"]),
            invoice_id_1=UUID(node["invoice_id_1"]) if node.get("invoice_id_1") else None,
            invoice_id_2=UUID(node["invoice_id_2"]) if node.get("invoice_id_2") else None,
            taxpayer_id=UUID(node["taxpayer_id"]),
            mismatch_type=MismatchType(node["mismatch_type"]),
            risk_level=RiskLevel(node["risk_level"]),
            status=MismatchStatus(node["status"]),
            amount_difference=Amount.from_float(node["amount_difference"]),
            tax_impact=Amount.from_float(node["tax_impact"]),
            itc_impact=Amount.from_float(node["itc_impact"]),
            description=node["description"],
            root_cause=node["root_cause"],
            recommendation=node["recommendation"],
            reconciliation_run_id=UUID(node["reconciliation_run_id"]) if node.get("reconciliation_run_id") else None,
            detected_at=datetime.fromisoformat(node["detected_at"]),
            resolved_at=datetime.fromisoformat(node["resolved_at"]) if node.get("resolved_at") else None,
            resolved_by=node.get("resolved_by"),
            resolution_notes=node.get("resolution_notes"),
            created_at=datetime.fromisoformat(node["created_at"]),
            updated_at=datetime.fromisoformat(node["updated_at"])
        )
