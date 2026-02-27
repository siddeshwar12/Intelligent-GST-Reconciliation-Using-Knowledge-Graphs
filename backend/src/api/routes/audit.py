"""Audit trail API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from ..models.responses import AuditTrailResponse, ErrorResponse
from ..dependencies import get_audit_service
from audit.audit_service import AuditTrailService

router = APIRouter(
    prefix="/audit-trail",
    tags=["Audit Trail"],
    responses={
        404: {"model": ErrorResponse, "description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


@router.get(
    "/{invoice_id}",
    response_model=AuditTrailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get audit trail for invoice",
    description="Generate comprehensive audit trail showing graph traversal and ITC chain validation"
)
async def get_audit_trail(
    invoice_id: str,
    invoice_number: str,
    taxpayer_gstin: str,
    audit_service: AuditTrailService = Depends(get_audit_service)
) -> AuditTrailResponse:
    """
    Get audit trail for an invoice.
    
    This endpoint generates a comprehensive audit trail including:
    - Complete graph traversal path
    - Matched and mismatched nodes
    - Field-level comparisons
    - ITC chain validation results
    - Graph visualization data with coordinates
    
    Args:
        invoice_id: Invoice ID to audit
        invoice_number: Invoice number for reference
        taxpayer_gstin: Taxpayer GSTIN
        audit_service: Injected audit trail service
        
    Returns:
        Complete audit trail with graph visualization data
        
    Raises:
        HTTPException: If audit trail generation fails
    """
    try:
        # Generate audit trail
        audit_trail = audit_service.generate_audit_trail(
            invoice_id=invoice_id,
            invoice_number=invoice_number,
            taxpayer_gstin=taxpayer_gstin
        )
        
        # Convert to response format
        audit_dict = audit_trail.to_dict()
        
        response = AuditTrailResponse(
            audit_id=audit_dict["audit_id"],
            invoice_id=audit_dict["invoice_id"],
            invoice_number=audit_dict["invoice_number"],
            taxpayer_gstin=audit_dict["taxpayer_gstin"],
            created_at=audit_trail.created_at,
            graph=audit_dict["graph"],
            traversal_path=audit_dict["traversal_path"],
            analysis=audit_dict["analysis"],
            summary=audit_dict["summary"]
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate audit trail: {str(e)}"
        )


@router.get(
    "/{invoice_id}/graph",
    response_model=Dict[str, Any],
    summary="Get audit trail graph data",
    description="Get only the graph visualization data for an invoice"
)
async def get_audit_trail_graph(
    invoice_id: str,
    invoice_number: str,
    taxpayer_gstin: str,
    audit_service: AuditTrailService = Depends(get_audit_service)
) -> Dict[str, Any]:
    """
    Get audit trail graph visualization data.
    
    This endpoint returns only the graph structure (nodes and edges)
    optimized for frontend visualization libraries like D3.js.
    
    Args:
        invoice_id: Invoice ID
        invoice_number: Invoice number
        taxpayer_gstin: Taxpayer GSTIN
        audit_service: Injected audit trail service
        
    Returns:
        Graph visualization data
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        # Generate audit trail
        audit_trail = audit_service.generate_audit_trail(
            invoice_id=invoice_id,
            invoice_number=invoice_number,
            taxpayer_gstin=taxpayer_gstin
        )
        
        # Extract graph data
        audit_dict = audit_trail.to_dict()
        
        # Format for D3.js
        d3_data = {
            "nodes": audit_dict["graph"]["nodes"],
            "links": [
                {
                    "source": edge["source"],
                    "target": edge["target"],
                    "type": edge["type"],
                    "label": edge["label"],
                    "status": edge["status"]
                }
                for edge in audit_dict["graph"]["edges"]
            ],
            "metadata": {
                "audit_id": audit_dict["audit_id"],
                "invoice_number": audit_dict["invoice_number"],
                "itc_chain_valid": audit_dict["analysis"]["itc_chain_valid"]
            }
        }
        
        return d3_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate graph data: {str(e)}"
        )


@router.get(
    "/{invoice_id}/summary",
    response_model=Dict[str, Any],
    summary="Get audit trail summary",
    description="Get summary statistics for an audit trail"
)
async def get_audit_trail_summary(
    invoice_id: str,
    invoice_number: str,
    taxpayer_gstin: str,
    audit_service: AuditTrailService = Depends(get_audit_service)
) -> Dict[str, Any]:
    """
    Get audit trail summary.
    
    Args:
        invoice_id: Invoice ID
        invoice_number: Invoice number
        taxpayer_gstin: Taxpayer GSTIN
        audit_service: Injected audit trail service
        
    Returns:
        Audit trail summary
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        # Generate audit trail
        audit_trail = audit_service.generate_audit_trail(
            invoice_id=invoice_id,
            invoice_number=invoice_number,
            taxpayer_gstin=taxpayer_gstin
        )
        
        # Return summary
        return audit_trail.summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )
