"""Mapper for Invoice entity to/from graph nodes."""

from typing import Dict, Any
from datetime import datetime

from ....domain.entities import Invoice
from ....domain.value_objects import GSTIN, IRN, Amount, TaxComponent


class InvoiceMapper:
    """Maps Invoice entities to/from Neo4j nodes."""
    
    def to_dict(self, invoice: Invoice) -> Dict[str, Any]:
        """
        Convert Invoice entity to dictionary for Neo4j.
        
        Args:
            invoice: Invoice entity
            
        Returns:
            Dictionary representation
        """
        return {
            "id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.isoformat(),
            "taxable_value": float(invoice.taxable_value.value),
            "total_tax": float(invoice.total_tax.value),
            "total_amount": float(invoice.total_amount.value),
            "irn": str(invoice.irn) if invoice.irn else None,
            "place_of_supply": invoice.place_of_supply,
            "reverse_charge": invoice.reverse_charge,
            "invoice_type": invoice.invoice_type,
            "source_type": invoice.source_type,
            "source_period": invoice.source_period,
            "created_at": invoice.created_at.isoformat(),
            "updated_at": invoice.updated_at.isoformat(),
            "supplier_gstin": str(invoice.supplier_gstin) if invoice.supplier_gstin else None,
            "recipient_gstin": str(invoice.recipient_gstin) if invoice.recipient_gstin else None,
        }
    
    def from_node(self, node: Dict[str, Any]) -> Invoice:
        """
        Convert Neo4j node to Invoice entity.
        
        Args:
            node: Neo4j node data
            
        Returns:
            Invoice entity
        """
        # Parse tax components (simplified - would need full implementation)
        tax_amount = TaxComponent.zero()
        
        return Invoice(
            id=node.get("id"),
            invoice_number=node.get("invoice_number", ""),
            invoice_date=datetime.fromisoformat(node.get("invoice_date")),
            supplier_gstin=GSTIN(node["supplier_gstin"]) if node.get("supplier_gstin") else None,
            recipient_gstin=GSTIN(node["recipient_gstin"]) if node.get("recipient_gstin") else None,
            taxable_value=Amount.from_float(node.get("taxable_value", 0.0)),
            tax_amount=tax_amount,
            total_amount=Amount.from_float(node.get("total_amount", 0.0)),
            irn=IRN(node["irn"]) if node.get("irn") else None,
            place_of_supply=node.get("place_of_supply", ""),
            reverse_charge=node.get("reverse_charge", False),
            invoice_type=node.get("invoice_type", "B2B"),
            source_type=node.get("source_type", ""),
            source_period=node.get("source_period"),
            created_at=datetime.fromisoformat(node.get("created_at")),
            updated_at=datetime.fromisoformat(node.get("updated_at"))
        )
