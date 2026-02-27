"""Vendor repository for graph operations."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ....domain.entities import Vendor
from ....domain.value_objects import GSTIN, RiskScore
from ..neo4j_client import Neo4jClient


class VendorRepository:
    """Repository for vendor graph operations."""
    
    def __init__(self, client: Neo4jClient):
        self.client = client
    
    async def create(self, vendor: Vendor) -> Vendor:
        """
        Create vendor node in graph.
        
        Args:
            vendor: Vendor entity
            
        Returns:
            Created vendor
        """
        query = """
        CREATE (v:Vendor {
            id: $id,
            taxpayer_id: $taxpayer_id,
            gstin: $gstin,
            name: $name,
            compliance_score: $compliance_score,
            total_transactions: $total_transactions,
            total_mismatches: $total_mismatches,
            critical_mismatches: $critical_mismatches,
            on_time_filings: $on_time_filings,
            late_filings: $late_filings,
            missed_filings: $missed_filings,
            total_invoice_value: $total_invoice_value,
            total_mismatch_value: $total_mismatch_value,
            last_assessment_date: datetime($last_assessment_date),
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        RETURN v
        """
        
        params = {
            "id": str(vendor.id),
            "taxpayer_id": str(vendor.taxpayer_id),
            "gstin": str(vendor.gstin),
            "name": vendor.name,
            "compliance_score": float(vendor.compliance_score.value),
            "total_transactions": vendor.total_transactions,
            "total_mismatches": vendor.total_mismatches,
            "critical_mismatches": vendor.critical_mismatches,
            "on_time_filings": vendor.on_time_filings,
            "late_filings": vendor.late_filings,
            "missed_filings": vendor.missed_filings,
            "total_invoice_value": vendor.total_invoice_value,
            "total_mismatch_value": vendor.total_mismatch_value,
            "last_assessment_date": vendor.last_assessment_date.isoformat() if vendor.last_assessment_date else None,
            "created_at": vendor.created_at.isoformat(),
            "updated_at": vendor.updated_at.isoformat()
        }
        
        await self.client.execute_write(query, params)
        return vendor
    
    async def get_by_id(self, vendor_id: UUID) -> Optional[Vendor]:
        """Get vendor by ID."""
        query = """
        MATCH (v:Vendor {id: $id})
        RETURN v
        """
        
        result = await self.client.execute_query(query, {"id": str(vendor_id)})
        if not result:
            return None
        
        return self._map_from_node(result[0]["v"])
    
    async def get_by_gstin(self, gstin: GSTIN) -> Optional[Vendor]:
        """Get vendor by GSTIN."""
        query = """
        MATCH (v:Vendor {gstin: $gstin})
        RETURN v
        """
        
        result = await self.client.execute_query(query, {"gstin": str(gstin)})
        if not result:
            return None
        
        return self._map_from_node(result[0]["v"])
    
    async def update_compliance_score(
        self, 
        vendor_id: UUID, 
        score: RiskScore
    ) -> bool:
        """
        Update vendor compliance score.
        
        Args:
            vendor_id: Vendor UUID
            score: New compliance score
            
        Returns:
            True if successful
        """
        query = """
        MATCH (v:Vendor {id: $id})
        SET v.compliance_score = $score,
            v.last_assessment_date = datetime($assessment_date),
            v.updated_at = datetime($updated_at)
        RETURN v
        """
        
        params = {
            "id": str(vendor_id),
            "score": float(score.value),
            "assessment_date": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = await self.client.execute_write(query, params)
        return result["properties_set"] > 0
    
    async def get_high_risk_vendors(self, threshold: float = 40.0) -> List[Vendor]:
        """
        Get vendors with high risk (low compliance score).
        
        Args:
            threshold: Score threshold (below this is high risk)
            
        Returns:
            List of high-risk vendors
        """
        query = """
        MATCH (v:Vendor)
        WHERE v.compliance_score < $threshold
        RETURN v
        ORDER BY v.compliance_score ASC
        """
        
        result = await self.client.execute_query(query, {"threshold": threshold})
        return [self._map_from_node(record["v"]) for record in result]
    
    async def get_top_vendors_by_volume(self, limit: int = 10) -> List[Vendor]:
        """
        Get top vendors by transaction volume.
        
        Args:
            limit: Number of vendors to return
            
        Returns:
            List of top vendors
        """
        query = """
        MATCH (v:Vendor)
        RETURN v
        ORDER BY v.total_invoice_value DESC
        LIMIT $limit
        """
        
        result = await self.client.execute_query(query, {"limit": limit})
        return [self._map_from_node(record["v"]) for record in result]
    
    async def record_transaction(
        self, 
        vendor_id: UUID, 
        invoice_value: float
    ) -> bool:
        """
        Record a new transaction for vendor.
        
        Args:
            vendor_id: Vendor UUID
            invoice_value: Invoice amount
            
        Returns:
            True if successful
        """
        query = """
        MATCH (v:Vendor {id: $id})
        SET v.total_transactions = v.total_transactions + 1,
            v.total_invoice_value = v.total_invoice_value + $invoice_value,
            v.updated_at = datetime($updated_at)
        RETURN v
        """
        
        params = {
            "id": str(vendor_id),
            "invoice_value": invoice_value,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = await self.client.execute_write(query, params)
        return result["properties_set"] > 0
    
    async def record_mismatch(
        self, 
        vendor_id: UUID, 
        is_critical: bool,
        mismatch_value: float
    ) -> bool:
        """
        Record a mismatch for vendor.
        
        Args:
            vendor_id: Vendor UUID
            is_critical: Whether mismatch is critical
            mismatch_value: Mismatch amount
            
        Returns:
            True if successful
        """
        query = """
        MATCH (v:Vendor {id: $id})
        SET v.total_mismatches = v.total_mismatches + 1,
            v.critical_mismatches = v.critical_mismatches + $critical_increment,
            v.total_mismatch_value = v.total_mismatch_value + $mismatch_value,
            v.updated_at = datetime($updated_at)
        RETURN v
        """
        
        params = {
            "id": str(vendor_id),
            "critical_increment": 1 if is_critical else 0,
            "mismatch_value": mismatch_value,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = await self.client.execute_write(query, params)
        return result["properties_set"] > 0
    
    async def get_vendor_statistics(self) -> dict:
        """
        Get overall vendor statistics.
        
        Returns:
            Dictionary with statistics
        """
        query = """
        MATCH (v:Vendor)
        RETURN 
            count(v) as total_vendors,
            avg(v.compliance_score) as avg_compliance_score,
            sum(v.total_transactions) as total_transactions,
            sum(v.total_mismatches) as total_mismatches,
            count(CASE WHEN v.compliance_score < 40 THEN 1 END) as high_risk_count,
            count(CASE WHEN v.compliance_score >= 70 THEN 1 END) as low_risk_count
        """
        
        result = await self.client.execute_query(query)
        if not result:
            return {}
        
        return dict(result[0])
    
    def _map_from_node(self, node: dict) -> Vendor:
        """Map Neo4j node to Vendor entity."""
        return Vendor(
            id=UUID(node["id"]),
            taxpayer_id=UUID(node["taxpayer_id"]),
            gstin=GSTIN(node["gstin"]),
            name=node["name"],
            compliance_score=RiskScore.from_float(node["compliance_score"]),
            total_transactions=node["total_transactions"],
            total_mismatches=node["total_mismatches"],
            critical_mismatches=node["critical_mismatches"],
            on_time_filings=node["on_time_filings"],
            late_filings=node["late_filings"],
            missed_filings=node["missed_filings"],
            total_invoice_value=node["total_invoice_value"],
            total_mismatch_value=node["total_mismatch_value"],
            last_assessment_date=datetime.fromisoformat(node["last_assessment_date"]) if node.get("last_assessment_date") else None,
            created_at=datetime.fromisoformat(node["created_at"]),
            updated_at=datetime.fromisoformat(node["updated_at"])
        )
