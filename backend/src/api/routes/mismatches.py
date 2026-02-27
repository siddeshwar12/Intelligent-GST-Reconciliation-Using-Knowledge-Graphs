"""Mismatch API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
import uuid
from datetime import datetime

from ..models.requests import MismatchFilterParams, PaginationParams
from ..models.responses import MismatchResponse, MismatchDetail, ErrorResponse
from ..dependencies import get_neo4j_connection

router = APIRouter(
    prefix="/mismatches",
    tags=["Mismatches"],
    responses={
        404: {"model": ErrorResponse, "description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


@router.get(
    "",
    response_model=MismatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Get mismatches",
    description="Retrieve mismatches with filtering and pagination"
)
async def get_mismatches(
    taxpayer_gstin: Optional[str] = Query(None, description="Filter by taxpayer GSTIN"),
    period: Optional[str] = Query(None, description="Filter by tax period"),
    mismatch_type: Optional[str] = Query(None, description="Filter by mismatch type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum mismatch amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum mismatch amount"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    sort_by: Optional[str] = Query("detected_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    neo4j_conn = Depends(get_neo4j_connection)
) -> MismatchResponse:
    """
    Get mismatches with filtering and pagination.
    
    This endpoint retrieves mismatches from the database with support for:
    - Filtering by taxpayer, period, type, severity, amount range, resolution status
    - Pagination with skip/limit
    - Sorting by any field
    
    Args:
        taxpayer_gstin: Filter by taxpayer GSTIN
        period: Filter by tax period
        mismatch_type: Filter by mismatch type
        severity: Filter by severity level
        min_amount: Minimum mismatch amount
        max_amount: Maximum mismatch amount
        resolved: Filter by resolution status
        skip: Number of records to skip
        limit: Maximum records to return
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        neo4j_conn: Injected Neo4j connection
        
    Returns:
        Paginated mismatch results
        
    Raises:
        HTTPException: If query fails
    """
    try:
        # Build Cypher query with filters
        where_clauses = []
        params = {}
        
        if taxpayer_gstin:
            where_clauses.append("m.taxpayer_gstin = $taxpayer_gstin")
            params["taxpayer_gstin"] = taxpayer_gstin
        
        if period:
            where_clauses.append("m.period = $period")
            params["period"] = period
        
        if mismatch_type:
            where_clauses.append("m.mismatch_type = $mismatch_type")
            params["mismatch_type"] = mismatch_type
        
        if severity:
            where_clauses.append("m.severity = $severity")
            params["severity"] = severity
        
        if min_amount is not None:
            where_clauses.append("m.amount_difference >= $min_amount")
            params["min_amount"] = min_amount
        
        if max_amount is not None:
            where_clauses.append("m.amount_difference <= $max_amount")
            params["max_amount"] = max_amount
        
        if resolved is not None:
            where_clauses.append("m.resolved = $resolved")
            params["resolved"] = resolved
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Count total matching records
        count_query = f"""
        MATCH (m:Mismatch)
        WHERE {where_clause}
        RETURN count(m) as total
        """
        
        # Get paginated results
        order_direction = "DESC" if sort_order == "desc" else "ASC"
        data_query = f"""
        MATCH (m:Mismatch)
        WHERE {where_clause}
        RETURN m
        ORDER BY m.{sort_by} {order_direction}
        SKIP $skip
        LIMIT $limit
        """
        
        params["skip"] = skip
        params["limit"] = limit
        
        # Execute queries (mock data for now since Neo4j might not be available)
        # In production, use: neo4j_conn.execute_query(query, params)
        
        # Generate mock data for demonstration
        mock_mismatches = []
        for i in range(min(10, limit)):
            mismatch = MismatchDetail(
                mismatch_id=f"mismatch-{uuid.uuid4()}",
                mismatch_type=mismatch_type or "AMOUNT_MISMATCH",
                severity=severity or "MEDIUM",
                description=f"Sample mismatch {i+1}",
                invoice_number=f"INV-{1000+i}",
                supplier_gstin=taxpayer_gstin or "27AABCU9603R1ZM",
                amount_difference=1000.0 * (i+1),
                percentage_variance=5.0,
                detected_at=datetime.now(),
                resolved=resolved if resolved is not None else False
            )
            mock_mismatches.append(mismatch)
        
        total_count = 100  # Mock total count
        total_pages = (total_count + limit - 1) // limit
        current_page = (skip // limit) + 1
        
        # Build filters applied dict
        filters_applied = {}
        if taxpayer_gstin:
            filters_applied["taxpayer_gstin"] = taxpayer_gstin
        if period:
            filters_applied["period"] = period
        if mismatch_type:
            filters_applied["mismatch_type"] = mismatch_type
        if severity:
            filters_applied["severity"] = severity
        if min_amount is not None:
            filters_applied["min_amount"] = min_amount
        if max_amount is not None:
            filters_applied["max_amount"] = max_amount
        if resolved is not None:
            filters_applied["resolved"] = resolved
        
        response = MismatchResponse(
            total_count=total_count,
            page=current_page,
            page_size=limit,
            total_pages=total_pages,
            mismatches=mock_mismatches,
            filters_applied=filters_applied
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve mismatches: {str(e)}"
        )


@router.get(
    "/{mismatch_id}",
    response_model=MismatchDetail,
    summary="Get mismatch by ID",
    description="Retrieve detailed information about a specific mismatch"
)
async def get_mismatch_by_id(
    mismatch_id: str,
    neo4j_conn = Depends(get_neo4j_connection)
) -> MismatchDetail:
    """
    Get mismatch details by ID.
    
    Args:
        mismatch_id: Mismatch ID
        neo4j_conn: Injected Neo4j connection
        
    Returns:
        Mismatch details
        
    Raises:
        HTTPException: If mismatch not found
    """
    try:
        # Query Neo4j for mismatch
        # In production: neo4j_conn.execute_query(query, {"mismatch_id": mismatch_id})
        
        # Mock response for demonstration
        mismatch = MismatchDetail(
            mismatch_id=mismatch_id,
            mismatch_type="AMOUNT_MISMATCH",
            severity="HIGH",
            description="Amount mismatch between PR and GSTR-2B",
            invoice_number="INV-001001",
            supplier_gstin="27AABCU9603R1ZM",
            amount_difference=5000.0,
            percentage_variance=10.0,
            detected_at=datetime.now(),
            resolved=False
        )
        
        return mismatch
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mismatch not found: {str(e)}"
        )


@router.patch(
    "/{mismatch_id}/resolve",
    response_model=MismatchDetail,
    summary="Resolve mismatch",
    description="Mark a mismatch as resolved with optional notes"
)
async def resolve_mismatch(
    mismatch_id: str,
    resolution_notes: Optional[str] = Query(None, description="Resolution notes"),
    neo4j_conn = Depends(get_neo4j_connection)
) -> MismatchDetail:
    """
    Resolve a mismatch.
    
    Args:
        mismatch_id: Mismatch ID
        resolution_notes: Optional resolution notes
        neo4j_conn: Injected Neo4j connection
        
    Returns:
        Updated mismatch details
        
    Raises:
        HTTPException: If mismatch not found or update fails
    """
    try:
        # Update mismatch in Neo4j
        # In production: neo4j_conn.execute_query(update_query, params)
        
        # Mock response
        mismatch = MismatchDetail(
            mismatch_id=mismatch_id,
            mismatch_type="AMOUNT_MISMATCH",
            severity="HIGH",
            description="Amount mismatch between PR and GSTR-2B",
            invoice_number="INV-001001",
            supplier_gstin="27AABCU9603R1ZM",
            amount_difference=5000.0,
            percentage_variance=10.0,
            detected_at=datetime.now(),
            resolved=True,
            resolution_notes=resolution_notes or "Resolved by user"
        )
        
        return mismatch
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve mismatch: {str(e)}"
        )
