"""Request Pydantic models for API endpoints."""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ReconcileRequest(BaseModel):
    """Request model for reconciliation endpoint."""
    
    taxpayer_gstin: str = Field(
        ...,
        description="Taxpayer GSTIN to reconcile",
        min_length=15,
        max_length=15,
        example="27AABCU9603R1ZM"
    )
    
    period: str = Field(
        ...,
        description="Tax period in MMYYYY format",
        pattern=r"^\d{6}$",
        example="032024"
    )
    
    validate_itc_chains: bool = Field(
        default=True,
        description="Whether to validate complete ITC chains"
    )
    
    include_risk_assessment: bool = Field(
        default=True,
        description="Whether to include risk classification"
    )
    
    @validator('taxpayer_gstin')
    def validate_gstin_format(cls, v):
        """Validate GSTIN format."""
        if not v or len(v) != 15:
            raise ValueError('GSTIN must be exactly 15 characters')
        if not v[:2].isdigit():
            raise ValueError('GSTIN must start with 2-digit state code')
        return v.upper()
    
    @validator('period')
    def validate_period_format(cls, v):
        """Validate period format."""
        if not v or len(v) != 6:
            raise ValueError('Period must be in MMYYYY format')
        month = int(v[:2])
        if month < 1 or month > 12:
            raise ValueError('Invalid month in period')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "taxpayer_gstin": "27AABCU9603R1ZM",
                "period": "032024",
                "validate_itc_chains": True,
                "include_risk_assessment": True
            }
        }


class VendorRiskRequest(BaseModel):
    """Request model for vendor risk assessment endpoint."""
    
    vendor_gstin: Optional[str] = Field(
        None,
        description="Specific vendor GSTIN to assess",
        min_length=15,
        max_length=15,
        example="33GSPTN2635F1ZU"
    )
    
    taxpayer_gstin: Optional[str] = Field(
        None,
        description="Taxpayer GSTIN to get all vendor risks",
        min_length=15,
        max_length=15,
        example="27AABCU9603R1ZM"
    )
    
    period: Optional[str] = Field(
        None,
        description="Tax period in MMYYYY format",
        pattern=r"^\d{6}$",
        example="032024"
    )
    
    min_risk_level: Optional[str] = Field(
        None,
        description="Minimum risk level to filter (LOW, MEDIUM, HIGH, CRITICAL)",
        example="MEDIUM"
    )
    
    @validator('vendor_gstin', 'taxpayer_gstin')
    def validate_gstin(cls, v):
        """Validate GSTIN format."""
        if v and len(v) != 15:
            raise ValueError('GSTIN must be exactly 15 characters')
        return v.upper() if v else v
    
    class Config:
        schema_extra = {
            "example": {
                "vendor_gstin": "33GSPTN2635F1ZU",
                "period": "032024"
            }
        }


class DashboardStatsRequest(BaseModel):
    """Request model for dashboard statistics endpoint."""
    
    taxpayer_gstin: Optional[str] = Field(
        None,
        description="Filter by specific taxpayer GSTIN",
        min_length=15,
        max_length=15,
        example="27AABCU9603R1ZM"
    )
    
    period: Optional[str] = Field(
        None,
        description="Filter by tax period in MMYYYY format",
        pattern=r"^\d{6}$",
        example="032024"
    )
    
    start_date: Optional[datetime] = Field(
        None,
        description="Start date for date range filter"
    )
    
    end_date: Optional[datetime] = Field(
        None,
        description="End date for date range filter"
    )
    
    include_trends: bool = Field(
        default=True,
        description="Include trend analysis"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "taxpayer_gstin": "27AABCU9603R1ZM",
                "period": "032024",
                "include_trends": True
            }
        }


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    
    skip: int = Field(
        default=0,
        ge=0,
        description="Number of records to skip"
    )
    
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of records to return"
    )
    
    sort_by: Optional[str] = Field(
        None,
        description="Field to sort by"
    )
    
    sort_order: str = Field(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort order (asc or desc)"
    )


class MismatchFilterParams(BaseModel):
    """Filter parameters for mismatch queries."""
    
    taxpayer_gstin: Optional[str] = Field(
        None,
        description="Filter by taxpayer GSTIN"
    )
    
    period: Optional[str] = Field(
        None,
        description="Filter by tax period"
    )
    
    mismatch_type: Optional[str] = Field(
        None,
        description="Filter by mismatch type"
    )
    
    severity: Optional[str] = Field(
        None,
        description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)"
    )
    
    min_amount: Optional[float] = Field(
        None,
        ge=0,
        description="Minimum mismatch amount"
    )
    
    max_amount: Optional[float] = Field(
        None,
        ge=0,
        description="Maximum mismatch amount"
    )
    
    resolved: Optional[bool] = Field(
        None,
        description="Filter by resolution status"
    )
