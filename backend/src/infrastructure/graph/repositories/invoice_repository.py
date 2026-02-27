"""Invoice repository for graph operations."""

from typing import List, Optional
from uuid import UUID

from ....domain.entities import Invoice
from ....domain.interfaces import IGraphRepository
from ..neo4j_client import Neo4jClient
from ..mappers.invoice_mapper import InvoiceMapper


class InvoiceRepository:
    """Repository for invoice graph operations."""
    
    def __init__(self, client: Neo4jClient):
        self.client = client
        self.mapper = InvoiceMapper()
    
    async def create(self, invoice: Invoice) -> Invoice:
        """
        Create invoice node in graph.
        
        Args:
            invoice: Invoice entity
            
        Returns:
            Created invoice
        """
        query = """
        CREATE (i:Invoice {
            id: $id,
            invoice_number: $invoice_number,
            invoice_date: datetime($invoice_date),
            taxable_value: $taxable_value,
            total_tax: $total_tax,
            total_amount: $total_amount,
            irn: $irn,
            place_of_supply: $place_of_supply,
            reverse_charge: $reverse_charge,
            invoice_type: $invoice_type,
            source_type: $source_type,
            source_period: $source_period,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        RETURN i
        """
        
        params = self.mapper.to_dict(invoice)
        await self.client.execute_write(query, params)
        return invoice
    
    async def get_by_id(self, invoice_id: UUID) -> Optional[Invoice]:
        """
        Get invoice by ID.
        
        Args:
            invoice_id: Invoice UUID
            
        Returns:
            Invoice entity or None
        """
        query = """
        MATCH (i:Invoice {id: $id})
        RETURN i
        """
        
        result = await self.client.execute_query(query, {"id": str(invoice_id)})
        if not result:
            return None
        
        return self.mapper.from_node(result[0]["i"])
    
    async def find_by_invoice_number(
        self,
        invoice_number: str,
        source_type: Optional[str] = None
    ) -> List[Invoice]:
        """
        Find invoices by invoice number.
        
        Args:
            invoice_number: Invoice number
            source_type: Optional source type filter
            
        Returns:
            List of matching invoices
        """
        if source_type:
            query = """
            MATCH (i:Invoice {invoice_number: $invoice_number, source_type: $source_type})
            RETURN i
            """
            params = {"invoice_number": invoice_number, "source_type": source_type}
        else:
            query = """
            MATCH (i:Invoice {invoice_number: $invoice_number})
            RETURN i
            """
            params = {"invoice_number": invoice_number}
        
        result = await self.client.execute_query(query, params)
        return [self.mapper.from_node(record["i"]) for record in result]
    
    async def find_matching_invoices(
        self,
        invoice: Invoice,
        source_types: List[str]
    ) -> List[Invoice]:
        """
        Find potential matching invoices from different sources.
        
        Args:
            invoice: Invoice to match
            source_types: List of source types to search
            
        Returns:
            List of potential matches
        """
        query = """
        MATCH (i:Invoice)
        WHERE i.invoice_number = $invoice_number
        AND i.source_type IN $source_types
        AND i.id <> $exclude_id
        AND abs(duration.between(i.invoice_date, datetime($invoice_date)).days) <= 30
        RETURN i
        ORDER BY abs(i.total_amount - $total_amount)
        LIMIT 10
        """
        
        params = {
            "invoice_number": invoice.invoice_number,
            "source_types": source_types,
            "exclude_id": str(invoice.id),
            "invoice_date": invoice.invoice_date.isoformat(),
            "total_amount": float(invoice.total_amount.value)
        }
        
        result = await self.client.execute_query(query, params)
        return [self.mapper.from_node(record["i"]) for record in result]
    
    async def link_to_taxpayer(
        self,
        invoice_id: UUID,
        taxpayer_id: UUID,
        relationship: str
    ) -> bool:
        """
        Create relationship between invoice and taxpayer.
        
        Args:
            invoice_id: Invoice UUID
            taxpayer_id: Taxpayer UUID
            relationship: Relationship type (ISSUED_BY or RECEIVED_BY)
            
        Returns:
            True if successful
        """
        query = f"""
        MATCH (i:Invoice {{id: $invoice_id}})
        MATCH (t:Taxpayer {{id: $taxpayer_id}})
        MERGE (i)-[r:{relationship}]->(t)
        RETURN r
        """
        
        params = {
            "invoice_id": str(invoice_id),
            "taxpayer_id": str(taxpayer_id)
        }
        
        result = await self.client.execute_write(query, params)
        return result["relationships_created"] > 0
