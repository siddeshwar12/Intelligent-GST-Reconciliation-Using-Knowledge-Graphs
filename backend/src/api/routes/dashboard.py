"""Dashboard statistics API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import datetime, timedelta

from ..models.requests import DashboardStatsRequest
from ..models.responses import DashboardStatsResponse, ErrorResponse
from ..dependencies import get_neo4j_connection

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dashboard statistics",
    description="Get comprehensive dashboard statistics for GST reconciliation system"
)
async def get_dashboard_stats(
    taxpayer_gstin: Optional[str] = Query(None, description="Filter by taxpayer GSTIN"),
    period: Optional[str] = Query(None, description="Filter by tax period"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    include_trends: bool = Query(True, description="Include trend analysis"),
    neo4j_conn = Depends(get_neo4j_connection)
) -> DashboardStatsResponse:
    """
    Get dashboard statistics.
    
    This endpoint provides comprehensive statistics including:
    - Overview metrics (taxpayers, invoices, mismatches)
    - Reconciliation statistics
    - Mismatch analysis by type and severity
    - Vendor risk statistics
    - Compliance metrics
    - Trend analysis (optional)
    
    Args:
        taxpayer_gstin: Filter by specific taxpayer
        period: Filter by tax period
        start_date: Start date for date range
        end_date: End date for date range
        include_trends: Include trend analysis
        neo4j_conn: Injected Neo4j connection
        
    Returns:
        Comprehensive dashboard statistics
        
    Raises:
        HTTPException: If query fails
    """
    try:
        # In production, query Neo4j for actual statistics
        # For now, return mock data
        
        # Overview statistics
        overview = {
            "total_taxpayers": 150,
            "total_invoices": 25000,
            "total_mismatches": 1250,
            "mismatch_rate": 5.0,
            "total_vendors": 800,
            "active_reconciliations": 45
        }
        
        # Reconciliation statistics
        reconciliation_stats = {
            "total_reconciliations": 200,
            "successful_reconciliations": 185,
            "failed_reconciliations": 15,
            "average_processing_time_ms": 1350.5,
            "reconciliations_today": 12,
            "reconciliations_this_week": 45,
            "reconciliations_this_month": 200
        }
        
        # Mismatch statistics
        mismatch_stats = {
            "by_type": {
                "AMOUNT_MISMATCH": 650,
                "MISSING_IN_GSTR2B": 350,
                "DATE_MISMATCH": 150,
                "GSTIN_MISMATCH": 75,
                "TAX_AMOUNT_MISMATCH": 25
            },
            "by_severity": {
                "CRITICAL": 125,
                "HIGH": 375,
                "MEDIUM": 500,
                "LOW": 250
            },
            "total_financial_impact": 12500000.0,
            "average_mismatch_amount": 10000.0,
            "resolved_mismatches": 450,
            "pending_mismatches": 800,
            "resolution_rate": 36.0
        }
        
        # Vendor statistics
        vendor_stats = {
            "total_vendors": 800,
            "high_risk_vendors": 80,
            "medium_risk_vendors": 240,
            "low_risk_vendors": 480,
            "average_risk_score": 35.5,
            "vendors_requiring_action": 120,
            "vendors_under_enhanced_monitoring": 80,
            "vendors_under_intensive_monitoring": 40
        }
        
        # Compliance statistics
        compliance_stats = {
            "itc_chain_valid_rate": 87.5,
            "on_time_filing_rate": 93.0,
            "compliance_score": 89.5,
            "gstr1_filing_rate": 95.0,
            "gstr2b_availability_rate": 92.0,
            "average_filing_delay_days": 3.5,
            "taxpayers_with_issues": 25,
            "compliance_violations": 15
        }
        
        # Trend analysis (if requested)
        trends = None
        if include_trends:
            # Generate last 7 days trend data
            today = datetime.now()
            daily_trends = []
            
            for i in range(7):
                date = today - timedelta(days=6-i)
                daily_trends.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "reconciliations": 25 + i*2,
                    "mismatches_found": 60 + i*5,
                    "mismatches_resolved": 40 + i*3,
                    "average_risk_score": 35.0 + i*0.5
                })
            
            trends = {
                "daily_trends": daily_trends,
                "mismatch_trend": "increasing",
                "compliance_trend": "stable",
                "risk_trend": "increasing",
                "period": "last_7_days"
            }
        
        response = DashboardStatsResponse(
            overview=overview,
            reconciliation_stats=reconciliation_stats,
            mismatch_stats=mismatch_stats,
            vendor_stats=vendor_stats,
            compliance_stats=compliance_stats,
            trends=trends,
            generated_at=datetime.now()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard statistics: {str(e)}"
        )


@router.get(
    "/stats/summary",
    response_model=dict,
    summary="Get dashboard summary",
    description="Get quick summary statistics for dashboard"
)
async def get_dashboard_summary(
    neo4j_conn = Depends(get_neo4j_connection)
) -> dict:
    """
    Get dashboard summary statistics.
    
    Returns quick summary metrics for dashboard overview.
    
    Args:
        neo4j_conn: Injected Neo4j connection
        
    Returns:
        Summary statistics
        
    Raises:
        HTTPException: If query fails
    """
    try:
        summary = {
            "total_taxpayers": 150,
            "total_invoices": 25000,
            "total_mismatches": 1250,
            "mismatch_rate": 5.0,
            "high_risk_vendors": 80,
            "compliance_score": 89.5,
            "pending_actions": 120,
            "last_updated": datetime.now().isoformat()
        }
        
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )


@router.get(
    "/stats/alerts",
    response_model=dict,
    summary="Get dashboard alerts",
    description="Get critical alerts and notifications"
)
async def get_dashboard_alerts(
    neo4j_conn = Depends(get_neo4j_connection)
) -> dict:
    """
    Get dashboard alerts.
    
    Returns critical alerts and notifications that require attention.
    
    Args:
        neo4j_conn: Injected Neo4j connection
        
    Returns:
        Alert information
        
    Raises:
        HTTPException: If query fails
    """
    try:
        alerts = {
            "critical_alerts": [
                {
                    "id": "alert-001",
                    "type": "HIGH_RISK_VENDOR",
                    "severity": "CRITICAL",
                    "message": "5 vendors flagged as critical risk",
                    "action_required": True,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "alert-002",
                    "type": "LARGE_MISMATCH",
                    "severity": "HIGH",
                    "message": "Mismatch detected: ₹500,000 variance",
                    "action_required": True,
                    "created_at": datetime.now().isoformat()
                }
            ],
            "warnings": [
                {
                    "id": "warn-001",
                    "type": "FILING_DELAY",
                    "severity": "MEDIUM",
                    "message": "15 vendors with filing delays > 10 days",
                    "action_required": False,
                    "created_at": datetime.now().isoformat()
                }
            ],
            "info": [
                {
                    "id": "info-001",
                    "type": "RECONCILIATION_COMPLETE",
                    "severity": "LOW",
                    "message": "Monthly reconciliation completed successfully",
                    "action_required": False,
                    "created_at": datetime.now().isoformat()
                }
            ],
            "total_alerts": 4,
            "action_required_count": 2
        }
        
        return alerts
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate alerts: {str(e)}"
        )
