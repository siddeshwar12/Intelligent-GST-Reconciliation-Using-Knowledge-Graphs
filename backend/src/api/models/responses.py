"""Response Pydantic models for API endpoints."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid GSTIN format",
                "details": {"field": "taxpayer_gstin", "value": "INVALID"},
                "timestamp": "2024-01-15T10:30:00"
            }
        }


class SuccessResponse(BaseModel):
    """Standard success response model."""
    
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {}
            }
        }


class MismatchDetail(BaseModel):
    """Mismatch detail model."""
    
    mismatch_id: str
    mismatch_type: str
    severity: str
    description: str
    invoice_number: str
    supplier_gstin: str
    amount_difference: float
    percentage_variance: Optional[float] = None
    detected_at: datetime
    resolved: bool = False
    resolution_notes: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "mismatch_id": "mismatch-001",
                "mismatch_type": "AMOUNT_MISMATCH",
                "severity": "HIGH",
                "description": "Amount mismatch: PR=10000.00, GSTR-2B=10500.00",
                "invoice_number": "INV-001",
                "supplier_gstin": "27AABCU9603R1ZM",
                "amount_difference": 500.0,
                "percentage_variance": 5.0,
                "detected_at": "2024-01-15T10:30:00",
                "resolved": False
            }
        }


class ReconcileResponse(BaseModel):
    """Response model for reconciliation endpoint."""
    
    reconciliation_id: str
    taxpayer_gstin: str
    period: str
    total_invoices_processed: int
    matched_invoices: int
    mismatches_found: int
    itc_chain_valid_count: int
    itc_chain_invalid_count: int
    
    mismatches: List[MismatchDetail]
    
    summary: Dict[str, Any] = Field(
        ...,
        description="Summary statistics"
    )
    
    risk_assessment: Optional[Dict[str, Any]] = Field(
        None,
        description="Risk assessment results if requested"
    )
    
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        schema_extra = {
            "example": {
                "reconciliation_id": "recon-12345",
                "taxpayer_gstin": "27AABCU9603R1ZM",
                "period": "032024",
                "total_invoices_processed": 150,
                "matched_invoices": 125,
                "mismatches_found": 25,
                "itc_chain_valid_count": 120,
                "itc_chain_invalid_count": 5,
                "mismatches": [],
                "summary": {
                    "total_mismatches": 25,
                    "mismatch_types": {"AMOUNT_MISMATCH": 15, "MISSING_IN_GSTR2B": 10},
                    "severity_distribution": {"CRITICAL": 3, "HIGH": 12, "MEDIUM": 10}
                },
                "processing_time_ms": 1250.5,
                "timestamp": "2024-01-15T10:30:00"
            }
        }


class MismatchResponse(BaseModel):
    """Response model for mismatch list endpoint."""
    
    total_count: int
    page: int
    page_size: int
    total_pages: int
    
    mismatches: List[MismatchDetail]
    
    filters_applied: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "total_count": 250,
                "page": 1,
                "page_size": 100,
                "total_pages": 3,
                "mismatches": [],
                "filters_applied": {"severity": "HIGH", "resolved": False}
            }
        }


class GraphNode(BaseModel):
    """Graph node model for audit trail."""
    
    id: str
    type: str
    label: str
    properties: Dict[str, Any]
    status: str
    coordinates: Optional[Dict[str, float]] = None


class GraphEdge(BaseModel):
    """Graph edge model for audit trail."""
    
    id: str
    source: str
    target: str
    type: str
    label: str
    properties: Dict[str, Any]
    status: str


class TraversalStep(BaseModel):
    """Traversal step model for audit trail."""
    
    step: str
    description: str
    query_executed: str
    nodes_found: List[GraphNode]
    relationships_created: List[GraphEdge]
    success: bool
    error_message: Optional[str] = None
    execution_time_ms: float


class FieldComparison(BaseModel):
    """Field comparison model."""
    
    field_name: str
    source_value: Any
    target_value: Any
    is_match: bool
    variance_percentage: Optional[float] = None
    tolerance_applied: Optional[float] = None


class MismatchAnalysis(BaseModel):
    """Mismatch analysis model."""
    
    mismatch_type: str
    severity: str
    description: str
    field_comparisons: List[FieldComparison]
    financial_impact: float
    compliance_impact: str
    recommendation: str


class AuditTrailResponse(BaseModel):
    """Response model for audit trail endpoint."""
    
    audit_id: str
    invoice_id: str
    invoice_number: str
    taxpayer_gstin: str
    created_at: datetime
    
    graph: Dict[str, Any] = Field(
        ...,
        description="Graph structure with nodes and edges"
    )
    
    traversal_path: List[TraversalStep]
    
    analysis: Dict[str, Any] = Field(
        ...,
        description="Analysis results including ITC chain validity and mismatches"
    )
    
    summary: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "audit_id": "audit-12345",
                "invoice_id": "inv-001",
                "invoice_number": "INV-001001",
                "taxpayer_gstin": "27AABCU9603R1ZM",
                "created_at": "2024-01-15T10:30:00",
                "graph": {
                    "nodes": [],
                    "edges": []
                },
                "traversal_path": [],
                "analysis": {
                    "itc_chain_valid": True,
                    "mismatches_found": []
                },
                "summary": {}
            }
        }


class VendorRiskDetail(BaseModel):
    """Vendor risk detail model."""
    
    vendor_gstin: str
    vendor_name: str
    risk_score: float
    risk_level: str
    confidence_score: float
    
    risk_factors: List[str]
    risk_factor_scores: Dict[str, float]
    
    predicted_mismatch_probability: float
    predicted_compliance_score: float
    anomaly_score: float
    
    monitoring_level: str
    recommended_actions: List[str]
    
    vendor_cluster: int
    cluster_description: str
    
    assessment_date: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "vendor_gstin": "33GSPTN2635F1ZU",
                "vendor_name": "Sample Vendor Ltd",
                "risk_score": 65.5,
                "risk_level": "HIGH",
                "confidence_score": 0.85,
                "risk_factors": ["HIGH_MISMATCH_RATE", "MISSING_INVOICES"],
                "risk_factor_scores": {"mismatch_rate": 25.0, "missing_invoices": 15.0},
                "predicted_mismatch_probability": 0.35,
                "predicted_compliance_score": 0.65,
                "anomaly_score": 0.45,
                "monitoring_level": "ENHANCED",
                "recommended_actions": ["Investigate mismatches", "Schedule vendor audit"],
                "vendor_cluster": 4,
                "cluster_description": "High-risk, requires close monitoring",
                "assessment_date": "2024-01-15T10:30:00"
            }
        }


class VendorRiskResponse(BaseModel):
    """Response model for vendor risk assessment endpoint."""
    
    total_vendors: int
    vendors: List[VendorRiskDetail]
    
    risk_distribution: Dict[str, int] = Field(
        ...,
        description="Distribution of vendors by risk level"
    )
    
    summary: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "total_vendors": 50,
                "vendors": [],
                "risk_distribution": {
                    "VERY_LOW": 10,
                    "LOW": 15,
                    "MEDIUM": 15,
                    "HIGH": 8,
                    "CRITICAL": 2
                },
                "summary": {
                    "average_risk_score": 45.2,
                    "high_risk_count": 10,
                    "vendors_requiring_action": 15
                }
            }
        }


class DashboardStatsResponse(BaseModel):
    """Response model for dashboard statistics endpoint."""
    
    overview: Dict[str, Any] = Field(
        ...,
        description="Overview statistics"
    )
    
    reconciliation_stats: Dict[str, Any] = Field(
        ...,
        description="Reconciliation statistics"
    )
    
    mismatch_stats: Dict[str, Any] = Field(
        ...,
        description="Mismatch statistics"
    )
    
    vendor_stats: Dict[str, Any] = Field(
        ...,
        description="Vendor statistics"
    )
    
    compliance_stats: Dict[str, Any] = Field(
        ...,
        description="Compliance statistics"
    )
    
    trends: Optional[Dict[str, Any]] = Field(
        None,
        description="Trend analysis if requested"
    )
    
    generated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        schema_extra = {
            "example": {
                "overview": {
                    "total_taxpayers": 100,
                    "total_invoices": 15000,
                    "total_mismatches": 750,
                    "mismatch_rate": 5.0
                },
                "reconciliation_stats": {
                    "total_reconciliations": 120,
                    "successful_reconciliations": 110,
                    "failed_reconciliations": 10,
                    "average_processing_time_ms": 1250.5
                },
                "mismatch_stats": {
                    "by_type": {"AMOUNT_MISMATCH": 450, "MISSING_IN_GSTR2B": 300},
                    "by_severity": {"CRITICAL": 50, "HIGH": 250, "MEDIUM": 300, "LOW": 150},
                    "total_financial_impact": 5000000.0
                },
                "vendor_stats": {
                    "total_vendors": 500,
                    "high_risk_vendors": 50,
                    "average_risk_score": 35.5
                },
                "compliance_stats": {
                    "itc_chain_valid_rate": 85.5,
                    "on_time_filing_rate": 92.0,
                    "compliance_score": 88.5
                },
                "generated_at": "2024-01-15T10:30:00"
            }
        }
