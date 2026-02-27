"""Vendor risk assessment API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from datetime import datetime

from ..models.requests import VendorRiskRequest
from ..models.responses import VendorRiskResponse, VendorRiskDetail, ErrorResponse
from ..dependencies import get_vendor_risk_predictor

try:
    from ml.vendor_risk import VendorRiskPredictor, VendorMetrics
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

router = APIRouter(
    prefix="/vendors",
    tags=["Vendors"],
    responses={
        404: {"model": ErrorResponse, "description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"}
    }
)


@router.get(
    "/risk-score",
    response_model=VendorRiskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vendor risk scores",
    description="Assess vendor risk using ML-based prediction and rule-based scoring"
)
async def get_vendor_risk_scores(
    vendor_gstin: Optional[str] = Query(None, description="Specific vendor GSTIN"),
    taxpayer_gstin: Optional[str] = Query(None, description="Taxpayer GSTIN for all vendors"),
    period: Optional[str] = Query(None, description="Tax period"),
    min_risk_level: Optional[str] = Query(None, description="Minimum risk level filter"),
    predictor: VendorRiskPredictor = Depends(get_vendor_risk_predictor)
) -> VendorRiskResponse:
    """
    Get vendor risk scores.
    
    This endpoint provides comprehensive vendor risk assessment including:
    - Rule-based risk scoring (0-100)
    - ML-based predictions (mismatch probability, compliance score)
    - Anomaly detection
    - Vendor clustering
    - Monitoring level recommendations
    - Actionable recommendations
    
    Args:
        vendor_gstin: Specific vendor to assess
        taxpayer_gstin: Get all vendors for a taxpayer
        period: Filter by tax period
        min_risk_level: Minimum risk level to include
        predictor: Injected vendor risk predictor
        
    Returns:
        Vendor risk assessment results
        
    Raises:
        HTTPException: If assessment fails
    """
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vendor risk assessment service not available. Install ML dependencies."
        )
    
    try:
        # Create sample vendor metrics
        # In production, fetch from database based on filters
        sample_vendors = []
        
        if vendor_gstin:
            # Single vendor assessment
            vendor_metrics = VendorMetrics(
                vendor_gstin=vendor_gstin,
                vendor_name=f"Vendor {vendor_gstin[:10]}",
                total_transactions=100,
                total_transaction_value=1000000.0,
                average_transaction_value=10000.0,
                transaction_frequency=8.3,
                mismatch_count=5,
                mismatch_rate=5.0,
                missing_invoice_count=2,
                late_filing_count=3,
                amount_variance_avg=3.5,
                amount_variance_max=8.0,
                amount_variance_std=2.5,
                average_filing_delay_days=5.0,
                max_filing_delay_days=15,
                months_active=12,
                first_transaction_date="2023-01-15",
                last_transaction_date="2024-01-15",
                gstin_change_count=0,
                cross_state_transaction_rate=0.2,
                reverse_charge_rate=0.1
            )
            sample_vendors.append(vendor_metrics)
        else:
            # Multiple vendors (mock data)
            for i in range(5):
                vendor_metrics = VendorMetrics(
                    vendor_gstin=f"VENDOR{i:010d}",
                    vendor_name=f"Sample Vendor {i+1}",
                    total_transactions=100 + i*20,
                    total_transaction_value=1000000.0 + i*500000,
                    average_transaction_value=10000.0 + i*1000,
                    transaction_frequency=8.3 + i,
                    mismatch_count=i*2,
                    mismatch_rate=i*2.0,
                    missing_invoice_count=i,
                    late_filing_count=i,
                    amount_variance_avg=i*1.5,
                    amount_variance_max=i*3.0,
                    amount_variance_std=i*0.8,
                    average_filing_delay_days=i*2.0,
                    max_filing_delay_days=i*5,
                    months_active=12,
                    first_transaction_date="2023-01-15",
                    last_transaction_date="2024-01-15",
                    gstin_change_count=0,
                    cross_state_transaction_rate=0.1 + i*0.1,
                    reverse_charge_rate=0.05 + i*0.05
                )
                sample_vendors.append(vendor_metrics)
        
        # Assess vendors
        assessments = predictor.batch_assess_vendors(sample_vendors)
        
        # Convert to response format
        vendor_details = []
        risk_distribution = {}
        
        for assessment in assessments:
            # Filter by minimum risk level if specified
            if min_risk_level:
                risk_levels = ["VERY_LOW", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
                min_index = risk_levels.index(min_risk_level)
                current_index = risk_levels.index(assessment.risk_level.value)
                if current_index < min_index:
                    continue
            
            vendor_detail = VendorRiskDetail(
                vendor_gstin=assessment.vendor_gstin,
                vendor_name=assessment.vendor_name,
                risk_score=assessment.risk_score,
                risk_level=assessment.risk_level.value,
                confidence_score=assessment.confidence_score,
                risk_factors=[rf.value for rf in assessment.risk_factors],
                risk_factor_scores=assessment.risk_factor_scores,
                predicted_mismatch_probability=assessment.predicted_mismatch_probability,
                predicted_compliance_score=assessment.predicted_compliance_score,
                anomaly_score=assessment.anomaly_score,
                monitoring_level=assessment.monitoring_level,
                recommended_actions=assessment.recommended_actions,
                vendor_cluster=assessment.vendor_cluster,
                cluster_description=assessment.cluster_description,
                assessment_date=assessment.assessment_date
            )
            vendor_details.append(vendor_detail)
            
            # Update risk distribution
            level = assessment.risk_level.value
            risk_distribution[level] = risk_distribution.get(level, 0) + 1
        
        # Calculate summary statistics
        total_vendors = len(vendor_details)
        average_risk_score = sum(v.risk_score for v in vendor_details) / total_vendors if total_vendors > 0 else 0
        high_risk_count = sum(1 for v in vendor_details if v.risk_level in ["HIGH", "CRITICAL"])
        vendors_requiring_action = sum(1 for v in vendor_details if v.monitoring_level in ["ENHANCED", "INTENSIVE"])
        
        summary = {
            "average_risk_score": round(average_risk_score, 2),
            "high_risk_count": high_risk_count,
            "vendors_requiring_action": vendors_requiring_action,
            "assessment_date": datetime.now().isoformat()
        }
        
        response = VendorRiskResponse(
            total_vendors=total_vendors,
            vendors=vendor_details,
            risk_distribution=risk_distribution,
            summary=summary
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assess vendor risk: {str(e)}"
        )


@router.get(
    "/{vendor_gstin}/risk-score",
    response_model=VendorRiskDetail,
    summary="Get specific vendor risk score",
    description="Get detailed risk assessment for a specific vendor"
)
async def get_specific_vendor_risk(
    vendor_gstin: str,
    predictor: VendorRiskPredictor = Depends(get_vendor_risk_predictor)
) -> VendorRiskDetail:
    """
    Get risk score for a specific vendor.
    
    Args:
        vendor_gstin: Vendor GSTIN
        predictor: Injected vendor risk predictor
        
    Returns:
        Detailed vendor risk assessment
        
    Raises:
        HTTPException: If assessment fails
    """
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vendor risk assessment service not available"
        )
    
    try:
        # Create vendor metrics (in production, fetch from database)
        vendor_metrics = VendorMetrics(
            vendor_gstin=vendor_gstin,
            vendor_name=f"Vendor {vendor_gstin[:10]}",
            total_transactions=100,
            total_transaction_value=1000000.0,
            average_transaction_value=10000.0,
            transaction_frequency=8.3,
            mismatch_count=5,
            mismatch_rate=5.0,
            missing_invoice_count=2,
            late_filing_count=3,
            amount_variance_avg=3.5,
            amount_variance_max=8.0,
            amount_variance_std=2.5,
            average_filing_delay_days=5.0,
            max_filing_delay_days=15,
            months_active=12,
            first_transaction_date="2023-01-15",
            last_transaction_date="2024-01-15",
            gstin_change_count=0,
            cross_state_transaction_rate=0.2,
            reverse_charge_rate=0.1
        )
        
        # Assess vendor
        assessment = predictor.assess_vendor_risk(vendor_metrics)
        
        # Convert to response format
        vendor_detail = VendorRiskDetail(
            vendor_gstin=assessment.vendor_gstin,
            vendor_name=assessment.vendor_name,
            risk_score=assessment.risk_score,
            risk_level=assessment.risk_level.value,
            confidence_score=assessment.confidence_score,
            risk_factors=[rf.value for rf in assessment.risk_factors],
            risk_factor_scores=assessment.risk_factor_scores,
            predicted_mismatch_probability=assessment.predicted_mismatch_probability,
            predicted_compliance_score=assessment.predicted_compliance_score,
            anomaly_score=assessment.anomaly_score,
            monitoring_level=assessment.monitoring_level,
            recommended_actions=assessment.recommended_actions,
            vendor_cluster=assessment.vendor_cluster,
            cluster_description=assessment.cluster_description,
            assessment_date=assessment.assessment_date
        )
        
        return vendor_detail
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assess vendor risk: {str(e)}"
        )
