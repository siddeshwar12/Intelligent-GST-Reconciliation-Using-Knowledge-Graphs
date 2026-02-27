"""Taxpayer repository for graph operations."""

from typing import List, Optional
from uuid import UUID

from ....domain.entities import Taxpayer
from ....domain.value_objects import GSTIN
from ..neo4j_client import Neo4jClient
from ..mappers.taxpayer_mapper import TaxpayerMapper


class TaxpayerRepository:
    """Repository for taxpayer graph operations."""
    
    def __init__(self, client: Neo4jClient):
        self.client = client
        self.mapper = TaxpayerMapper()
    
    async def create(self, taxpayer: Taxpayer) -> Taxpayer:
        """
        Create taxpayer node in graph.
        
        Args:
            taxpayer: Taxpayer entity
            
        Returns:
            Created taxpayer
        """
        query = """
        CREATE (t:Taxpayer {
            id: $id,
            gstin: $gstin,
            legal_name: $legal_name,
            trade_name: $trade_name,
            taxpayer_type: $taxpayer_type,
            state_code: $state_code,
            is_active: $is_active,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        RETURN t
        """
        
        params = self.mapper.to_dict(taxpayer)
        await self.client.execute_write(query, params)
        return taxpayer
    
    async def get_by_id(self, taxpayer_id: UUID) -> Optional[Taxpayer]:
        """
        Get taxpayer by ID.
        
        Args:
            taxpayer_id: Taxpayer UUID
            
        Returns:
            Taxpayer entity or None
        """
        query = """
        MATCH (t:Taxpayer {id: $id})
        RETURN t
        """
        
        result = await self.client.execute_query(query, {"id": str(taxpayer_id)})
        if not result:
            return None
        
        return self.mapper.from_node(result[0]["t"])
    
    async def get_by_gstin(self, gstin: GSTIN) -> Optional[Taxpayer]:
        """
        Get taxpayer by GSTIN.
        
        Args:
            gstin: GSTIN value object
            
        Returns:
            Taxpayer entity or None
        """
        query = """
        MATCH (t:Taxpayer {gstin: $gstin})
        RETURN t
        """
        
        result = await self.client.execute_query(query, {"gstin": str(gstin)})
        if not result:
            return None
        
        return self.mapper.from_node(result[0]["t"])
    
    async def find_by_state(self, state_code: str) -> List[Taxpayer]:
        """
        Find taxpayers by state code.
        
        Args:
            state_code: State code (2 digits)
            
        Returns:
            List of taxpayers
        """
        query = """
        MATCH (t:Taxpayer {state_code: $state_code, is_active: true})
        RETURN t
        ORDER BY t.legal_name
        """
        
        result = await self.client.execute_query(query, {"state_code": state_code})
        return [self.mapper.from_node(record["t"]) for record in result]
    
    async def update(self, taxpayer: Taxpayer) -> Taxpayer:
        """
        Update taxpayer node.
        
        Args:
            taxpayer: Taxpayer entity with updated data
            
        Returns:
            Updated taxpayer
        """
        query = """
        MATCH (t:Taxpayer {id: $id})
        SET t.legal_name = $legal_name,
            t.trade_name = $trade_name,
            t.taxpayer_type = $taxpayer_type,
            t.is_active = $is_active,
            t.updated_at = datetime($updated_at)
        RETURN t
        """
        
        params = self.mapper.to_dict(taxpayer)
        await self.client.execute_write(query, params)
        return taxpayer
    
    async def get_suppliers_for_buyer(self, buyer_id: UUID) -> List[Taxpayer]:
        """
        Get all suppliers for a buyer.
        
        Args:
            buyer_id: Buyer taxpayer UUID
            
        Returns:
            List of supplier taxpayers
        """
        query = """
        MATCH (buyer:Taxpayer {id: $buyer_id})
        MATCH (buyer)<-[:RECEIVED_BY]-(inv:Invoice)-[:ISSUED_BY]->(supplier:Taxpayer)
        RETURN DISTINCT supplier
        ORDER BY supplier.legal_name
        """
        
        result = await self.client.execute_query(query, {"buyer_id": str(buyer_id)})
        return [self.mapper.from_node(record["supplier"]) for record in result]
    
    async def get_buyers_for_supplier(self, supplier_id: UUID) -> List[Taxpayer]:
        """
        Get all buyers for a supplier.
        
        Args:
            supplier_id: Supplier taxpayer UUID
            
        Returns:
            List of buyer taxpayers
        """
        query = """
        MATCH (supplier:Taxpayer {id: $supplier_id})
        MATCH (supplier)<-[:ISSUED_BY]-(inv:Invoice)-[:RECEIVED_BY]->(buyer:Taxpayer)
        RETURN DISTINCT buyer
        ORDER BY buyer.legal_name
        """
        
        result = await self.client.execute_query(query, {"supplier_id": str(supplier_id)})
        return [self.mapper.from_node(record["buyer"]) for record in result]
    
    async def search(self, search_term: str, limit: int = 20) -> List[Taxpayer]:
        """
        Search taxpayers by name or GSTIN.
        
        Args:
            search_term: Search string
            limit: Maximum results
            
        Returns:
            List of matching taxpayers
        """
        query = """
        MATCH (t:Taxpayer)
        WHERE t.legal_name CONTAINS $search_term 
           OR t.trade_name CONTAINS $search_term
           OR t.gstin CONTAINS $search_term
        RETURN t
        ORDER BY t.legal_name
        LIMIT $limit
        """
        
        result = await self.client.execute_query(
            query, 
            {"search_term": search_term.upper(), "limit": limit}
        )
        return [self.mapper.from_node(record["t"]) for record in result]
