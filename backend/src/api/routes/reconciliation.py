"""Reconciliation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import time
from datetime import datetime
import uuid

from ..models.requests import ReconcileRequest
from ..models.responses import ReconcileResponse, MismatchDetail, ErrorResponse
from ..dependencies import get_reconciliation_service, get_risk_classifier
from reconciliation.reconcile_service import GSTReconciliationService
from reconciliation.classification import FinancialRiskClassifier

router = APIRouter(
    prefix="/reconcile",
    tags=["Reconciliation"],
    responses={
        404: {"model": ErrorResponse, "description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


@router.post(
    "",
    response_model=ReconcileResponse,
    status_code=status.HTTP_200_OK,
    summary="Reconcile GST invoices",
    description="Perform GST reconciliation for a taxpayer and period with ITC chain validation"
)
async def reconcile_taxpayer(
    request: ReconcileRequest,
    reconciliation_service: GSTReconciliationService = Depends(get_reconciliation_service),
    risk_classifier: FinancialRiskClassifier = Depends(get_risk_classifier)
) -> ReconcileResponse:
    """
    Reconcile GST invoices for a taxpayer.
    
    This endpoint performs comprehensive GST reconciliation including:
    - Multi-hop ITC chain validation
    - Mismatch detection (Amount, Date, GSTIN, Missing invoices)
    - Risk classification (if requested)
    - Detailed mismatch analysis
    
    Args:
        request: Reconciliation request parameters
        reconciliation_service: Injected reconciliation service
        risk_classifier: Injected risk classifier
        
    Returns:
        Comprehensive reconciliation results
        
    Raises:
        HTTPException: If reconciliation fails
    """
    start_time = time.time()
    
    try:
        # Perform reconciliation
        result = reconciliation_service.reconcile_taxpayer(
            taxpayer_gstin=request.taxpayer_gstin,
            period=request.period,
            validate_itc_chains=request.validate_itc_chains
        )
        
        # Convert mismatches to response format
        mismatch_details = []
        for mismatch in result.mismatches:
            mismatch_detail = MismatchDetail(
                mismatch_id=str(uuid.uuid4()),
                mismatch_type=mismatch.mismatch_type,
                severity=mismatch.severity,
                description=mismatch.description,
                invoice_number=mismatch.invoice_number,
                supplier_gstin=mismatch.supplier_gstin,
                amount_difference=mismatch.amount_difference,
                percentage_variance=mismatch.percentage_variance,
                detected_at=mismatch.detected_at,
                resolved=False
            )
            mismatch_details.append(mismatch_detail)
        
        # Perform risk assessment if requested
        risk_assessment = None
        if request.include_risk_assessment and result.mismatches:
            try:
                # Create mismatch contexts for classification
                mismatch_contexts = []
                for mismatch in result.mismatches:
                    context = {
                        "mismatch_type": mismatch.mismatch_type,
                        "amount_difference": mismatch.amount_difference,
                        "base_amount": mismatch.base_amount if hasattr(mismatch, 'base_amount') else 0,
                        "supplier_gstin": mismatch.supplier_gstin,
                        "buyer_gstin": request.taxpayer_gstin,
                        "invoice_date": mismatch.detected_at
                    }
                    mismatch_contexts.append(context)
                
                # Classify mismatches
                assessments = risk_classifier.classify_batch(mismatch_contexts)
                distribution = risk_classifier.get_risk_distribution(assessments)
                
                risk_assessment = {
                    "total_assessed": len(assessments),
                    "risk_distribution": distribution["risk_distribution"],
                    "financial_impact": distribution["financial_impact"],
                    "urgency_summary": distribution["urgency_summary"]
                }
            except Exception as e:
                # Risk assessment is optional, don't fail the whole request
                risk_assessment = {"error": f"Risk assessment failed: {str(e)}"}
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Build response
        response = ReconcileResponse(
            reconciliation_id=str(uuid.uuid4()),
            taxpayer_gstin=request.taxpayer_gstin,
            period=request.period,
            total_invoices_processed=result.total_invoices_processed,
            matched_invoices=result.matched_invoices,
            mismatches_found=len(result.mismatches),
            itc_chain_valid_count=result.itc_chain_valid_count if hasattr(result, 'itc_chain_valid_count') else 0,
            itc_chain_invalid_count=result.itc_chain_invalid_count if hasattr(result, 'itc_chain_invalid_count') else 0,
            mismatches=mismatch_details,
            summary=result.summary,
            risk_assessment=risk_assessment,
            processing_time_ms=processing_time_ms,
            timestamp=datetime.now()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reconciliation failed: {str(e)}"
        )


@router.get(
    "/status/{reconciliation_id}",
    response_model=Dict[str, Any],
    summary="Get reconciliation status",
    description="Get the status of a reconciliation job"
)
async def get_reconciliation_status(
    reconciliation_id: str
) -> Dict[str, Any]:
    """
    Get reconciliation status by ID.
    
    Args:
        reconciliation_id: Reconciliation job ID
        
    Returns:
        Reconciliation status
        
    Raises:
        HTTPException: If reconciliation not found
    """
    # TODO: Implement reconciliation status tracking
    # For now, return a placeholder response
    return {
        "reconciliation_id": reconciliation_id,
        "status": "completed",
        "message": "Reconciliation completed successfully"
    }
