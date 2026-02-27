"""
Optimized Neo4j queries for handling 10k+ invoices.

This module provides performance-optimized Cypher queries with:
- Pagination support (SKIP/LIMIT)
- Batch processing utilities
- Query optimization patterns
- Index-aware query design
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


# ============================================================================
# 1. PAGINATED RECONCILIATION QUERIES
# ============================================================================

def get_purchase_invoices_paginated(
    taxpayer_gstin: str,
    period: str,
    page: int = 1,
    page_size: int = 100,
    min_amount: float = 1000.0
) -> Tuple[str, Dict[str, Any]]:
    """
    Get purchase register invoices with pagination.
    
    Uses composite index: invoice_recipient_period
    
    Args:
        taxpayer_gstin: Taxpayer GSTIN
        period: Period in MMYYYY format
        page: Page number (1-indexed)
        page_size: Records per page
        min_amount: Minimum invoice amount
        
    Returns:
        Tuple of (query, parameters)
    """
    skip = (page - 1) * page_size
    
    query = """
    // Use composite index for fast filtering
    MATCH (buyer:Taxpayer {gstin: $taxpayer_gstin})-[:RECEIVED_BY]-(i:Invoice)
    WHERE i.source_type = 'PURCHASE_REGISTER'
    AND i.source_period = $period
    AND i.total_amount >= $min_amount
    
    // Get supplier info
    OPTIONAL MATCH (i)-[:ISSUED_BY]->(supplier:Taxpayer)
    
    // Return with pagination
    RETURN i {
        .id,
        .invoice_number,
        .invoice_date,
        .supplier_gstin,
        .recipient_gstin,
        .taxable_value,
        .cgst,
        .sgst,
        .igst,
        .total_tax,
        .total_amount,
        .source_type,
        .source_period,
        .hsn_code
    } as invoice,
    supplier.legal_name as supplier_name
    ORDER BY i.total_amount DESC
    SKIP $skip
    LIMIT $limit
    """
    
    params = {
        "taxpayer_gstin": taxpayer_gstin,
        "period": period,
        "min_amount": min_amount,
        "skip": skip,
        "limit": page_size
    }
    
    return query, params


def count_purchase_invoices(
    taxpayer_gstin: str,
    period: str,
    min_amount: float = 1000.0
) -> Tuple[str, Dict[str, Any]]:
    """
    Count total purchase invoices for pagination.
    
    Args:
        taxpayer_gstin: Taxpayer GSTIN
        period: Period in MMYYYY format
        min_amount: Minimum invoice amount
        
    Returns:
        Tuple of (query, parameters)
    """
    query = """
    MATCH (buyer:Taxpayer {gstin: $taxpayer_gstin})-[:RECEIVED_BY]-(i:Invoice)
    WHERE i.source_type = 'PURCHASE_REGISTER'
    AND i.source_period = $period
    AND i.total_amount >= $min_amount
    RETURN count(i) as total_count
    """
    
    params = {
        "taxpayer_gstin": taxpayer_gstin,
        "period": period,
        "min_amount": min_amount
    }
    
    return query, params


def get_mismatches_paginated(
    taxpayer_gstin: Optional[str] = None,
    period: Optional[str] = None,
    mismatch_type: Optional[str] = None,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    page: int = 1,
    page_size: int = 100,
    sort_by: str = "detected_at",
    sort_order: str = "DESC"
) -> Tuple[str, Dict[str, Any]]:
    """
    Get mismatches with filtering and pagination.
    
    Uses composite indexes: mismatch_taxpayer_period, mismatch_severity_resolved
    
    Args:
        taxpayer_gstin: Filter by taxpayer
        period: Filter by period
        mismatch_type: Filter by type
        severity: Filter by severity
        resolved: Filter by resolution status
        min_amount: Minimum amount
        max_amount: Maximum amount
        page: Page number
        page_size: Records per page
        sort_by: Sort field
        sort_order: ASC or DESC
        
    Returns:
        Tuple of (query, parameters)
    """
    skip = (page - 1) * page_size
    
    # Build WHERE clauses dynamically
    where_clauses = []
    params: Dict[str, Any] = {
        "skip": skip,
        "limit": page_size
    }
    
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
    
    if resolved is not None:
        where_clauses.append("m.resolved = $resolved")
        params["resolved"] = resolved
    
    if min_amount is not None:
        where_clauses.append("m.amount_difference >= $min_amount")
        params["min_amount"] = min_amount
    
    if max_amount is not None:
        where_clauses.append("m.amount_difference <= $max_amount")
        params["max_amount"] = max_amount
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    query = f"""
    MATCH (m:Mismatch)
    WHERE {where_clause}
    
    OPTIONAL MATCH (m)<-[:HAS_MISMATCH]-(i:Invoice)
    OPTIONAL MATCH (i)-[:ISSUED_BY]->(supplier:Taxpayer)
    
    RETURN m {{
        .id,
        .mismatch_type,
        .severity,
        .description,
        .taxpayer_gstin,
        .period,
        .amount_difference,
        .percentage_variance,
        .detected_at,
        .resolved,
        .resolution_notes
    }} as mismatch,
    i.invoice_number as invoice_number,
    supplier.gstin as supplier_gstin
    ORDER BY m.{sort_by} {sort_order}
    SKIP $skip
    LIMIT $limit
    """
    
    return query, params


# ============================================================================
# 2. BATCH PROCESSING QUERIES
# ============================================================================

def get_unprocessed_invoices_batch(
    batch_size: int = 500,
    source_type: str = "PURCHASE_REGISTER"
) -> Tuple[str, Dict[str, Any]]:
    """
    Get batch of unprocessed invoices for reconciliation.
    
    Args:
        batch_size: Number of invoices to process
        source_type: Invoice source type
        
    Returns:
        Tuple of (query, parameters)
    """
    query = """
    MATCH (i:Invoice)
    WHERE i.source_type = $source_type
    AND NOT EXISTS((i)-[:MATCHES]-())
    AND NOT EXISTS((i)-[:HAS_MISMATCH]-())
    
    WITH i
    LIMIT $batch_size
    
    OPTIONAL MATCH (i)-[:ISSUED_BY]->(supplier:Taxpayer)
    OPTIONAL MATCH (i)-[:RECEIVED_BY]->(buyer:Taxpayer)
    
    RETURN i, supplier, buyer
    """
    
    params = {
        "source_type": source_type,
        "batch_size": batch_size
    }
    
    return query, params


def batch_create_matches(
    matches: List[Tuple[str, str, float]]
) -> Tuple[str, Dict[str, Any]]:
    """
    Create multiple MATCHES relationships in a single transaction.
    
    Args:
        matches: List of (invoice1_id, invoice2_id, confidence_score) tuples
        
    Returns:
        Tuple of (query, parameters)
    """
    query = """
    UNWIND $matches as match
    MATCH (i1:Invoice {id: match.invoice1_id})
    MATCH (i2:Invoice {id: match.invoice2_id})
    MERGE (i1)-[r:MATCHES]-(i2)
    SET r.confidence_score = match.confidence_score,
        r.matched_at = datetime(),
        r.match_method = 'AUTO'
    RETURN count(r) as matches_created
    """
    
    params = {
        "matches": [
            {
                "invoice1_id": m[0],
                "invoice2_id": m[1],
                "confidence_score": m[2]
            }
            for m in matches
        ]
    }
    
    return query, params


def batch_create_mismatches(
    mismatches: List[Dict[str, Any]]
) -> Tuple[str, Dict[str, Any]]:
    """
    Create multiple mismatch nodes in a single transaction.
    
    Args:
        mismatches: List of mismatch dictionaries
        
    Returns:
        Tuple of (query, parameters)
    """
    query = """
    UNWIND $mismatches as mismatch
    CREATE (m:Mismatch)
    SET m = mismatch,
        m.detected_at = datetime(),
        m.resolved = false
    
    WITH m, mismatch
    MATCH (i:Invoice {id: mismatch.invoice_id})
    MERGE (i)-[:HAS_MISMATCH]->(m)
    
    RETURN count(m) as mismatches_created
    """
    
    params = {
        "mismatches": mismatches
    }
    
    return query, params


def batch_update_vendor_scores(
    vendor_updates: List[Dict[str, Any]]
) -> Tuple[str, Dict[str, Any]]:
    """
    Update multiple vendor risk scores in a single transaction.
    
    Args:
        vendor_updates: List of vendor update dictionaries
        
    Returns:
        Tuple of (query, parameters)
    """
    query = """
    UNWIND $updates as update
    MATCH (v:Vendor {id: update.vendor_id})
    SET v.risk_score = update.risk_score,
        v.compliance_score = update.compliance_score,
        v.last_assessment_date = datetime(),
        v.risk_level = update.risk_level
    RETURN count(v) as vendors_updated
    """
    
    params = {
        "updates": vendor_updates
    }
    
    return query, params


# ============================================================================
# 3. OPTIMIZED ITC VALIDATION QUERIES
# ============================================================================

def validate_itc_chain_optimized(
    invoice_id: str,
    recipient_gstin: str,
    supplier_gstin: str,
    date_tolerance: int = 30,
    amount_tolerance: float = 5.0
) -> Tuple[str, Dict[str, Any]]:
    """
    Optimized ITC chain validation with early termination.
    
    Uses indexes: taxpayer_gstin_unique, invoice_id_unique
    
    Args:
        invoice_id: Purchase register invoice ID
        recipient_gstin: Buyer GSTIN
        supplier_gstin: Supplier GSTIN
        date_tolerance: Date tolerance in days
        amount_tolerance: Amount tolerance percentage
        
    Returns:
        Tuple of (query, parameters)
    """
    query = """
    // Start from purchase register invoice (indexed lookup)
    MATCH (pr_invoice:Invoice {id: $invoice_id})
    WHERE pr_invoice.source_type = 'PURCHASE_REGISTER'
    
    // Early termination if basic data missing
    WITH pr_invoice
    WHERE pr_invoice.supplier_gstin IS NOT NULL
    AND pr_invoice.recipient_gstin IS NOT NULL
    
    // Find supplier (indexed lookup)
    OPTIONAL MATCH (supplier:Taxpayer {gstin: $supplier_gstin})
    
    // Find GSTR-1 entry (use composite index)
    OPTIONAL MATCH (supplier)-[:ISSUED_BY]-(gstr1_invoice:Invoice)
    WHERE gstr1_invoice.source_type = 'GSTR-1'
    AND gstr1_invoice.invoice_number = pr_invoice.invoice_number
    AND gstr1_invoice.recipient_gstin = pr_invoice.recipient_gstin
    AND abs(duration.between(gstr1_invoice.invoice_date, pr_invoice.invoice_date).days) <= $date_tolerance
    
    // Find GSTR-2B entry (use composite index)
    OPTIONAL MATCH (buyer:Taxpayer {gstin: $recipient_gstin})-[:RECEIVED_BY]-(gstr2b_invoice:Invoice)
    WHERE gstr2b_invoice.source_type = 'GSTR-2B'
    AND gstr2b_invoice.invoice_number = pr_invoice.invoice_number
    AND gstr2b_invoice.supplier_gstin = pr_invoice.supplier_gstin
    AND abs(duration.between(gstr2b_invoice.invoice_date, pr_invoice.invoice_date).days) <= $date_tolerance
    
    // Calculate validation results
    RETURN 
        pr_invoice,
        supplier IS NOT NULL as has_supplier,
        gstr1_invoice IS NOT NULL as has_gstr1,
        gstr2b_invoice IS NOT NULL as has_gstr2b,
        
        CASE 
            WHEN gstr1_invoice IS NOT NULL 
            THEN abs(pr_invoice.total_amount - gstr1_invoice.total_amount) <= (pr_invoice.total_amount * $amount_tolerance / 100)
            ELSE false 
        END as gstr1_amount_match,
        
        CASE 
            WHEN gstr2b_invoice IS NOT NULL 
            THEN abs(pr_invoice.total_amount - gstr2b_invoice.total_amount) <= (pr_invoice.total_amount * $amount_tolerance / 100)
            ELSE false 
        END as gstr2b_amount_match,
        
        CASE 
            WHEN supplier IS NOT NULL THEN 1 ELSE 0 
        END +
        CASE 
            WHEN gstr1_invoice IS NOT NULL THEN 1 ELSE 0 
        END +
        CASE 
            WHEN gstr2b_invoice IS NOT NULL THEN 1 ELSE 0 
        END as chain_length
    """
    
    params = {
        "invoice_id": invoice_id,
        "recipient_gstin": recipient_gstin,
        "supplier_gstin": supplier_gstin,
        "date_tolerance": date_tolerance,
        "amount_tolerance": amount_tolerance
    }
    
    return query, params


def find_gstr2b_matches_optimized(
    invoice_number: str,
    supplier_gstin: str,
    total_amount: float,
    invoice_date: str,
    amount_tolerance: float = 5.0,
    date_tolerance: int = 30,
    max_results: int = 5
) -> Tuple[str, Dict[str, Any]]:
    """
    Optimized GSTR-2B match finding with index hints.
    
    Uses composite index: invoice_number_gstin
    
    Args:
        invoice_number: Invoice number
        supplier_gstin: Supplier GSTIN
        total_amount: Invoice amount
        invoice_date: Invoice date
        amount_tolerance: Amount tolerance percentage
        date_tolerance: Date tolerance in days
        max_results: Maximum matches to return
        
    Returns:
        Tuple of (query, parameters)
    """
    query = """
    // Use composite index for fast lookup
    MATCH (gstr2b:Invoice)
    WHERE gstr2b.source_type = 'GSTR-2B'
    AND gstr2b.supplier_gstin = $supplier_gstin
    
    // Exact match first (uses index)
    WITH gstr2b
    WHERE gstr2b.invoice_number = $invoice_number
    OR (
        // Fuzzy match as fallback
        abs(gstr2b.total_amount - $total_amount) <= ($total_amount * $amount_tolerance / 100)
        AND abs(duration.between(gstr2b.invoice_date, date($invoice_date)).days) <= $date_tolerance
    )
    
    RETURN gstr2b {
        .id,
        .invoice_number,
        .invoice_date,
        .supplier_gstin,
        .recipient_gstin,
        .taxable_value,
        .cgst,
        .sgst,
        .igst,
        .total_tax,
        .total_amount,
        .source_type,
        .source_period
    } as invoice,
    
    // Calculate match score for ranking
    CASE WHEN gstr2b.invoice_number = $invoice_number THEN 100 ELSE 0 END +
    CASE WHEN abs(gstr2b.total_amount - $total_amount) < 1 THEN 50 ELSE 0 END as match_score
    
    ORDER BY match_score DESC, abs(gstr2b.total_amount - $total_amount) ASC
    LIMIT $max_results
    """
    
    params = {
        "invoice_number": invoice_number,
        "supplier_gstin": supplier_gstin,
        "total_amount": total_amount,
        "invoice_date": invoice_date,
        "amount_tolerance": amount_tolerance,
        "date_tolerance": date_tolerance,
        "max_results": max_results
    }
    
    return query, params


# ============================================================================
# 4. AGGREGATION QUERIES WITH OPTIMIZATION
# ============================================================================

def get_dashboard_summary_optimized(
    taxpayer_gstin: str,
    period: str
) -> Tuple[str, Dict[str, Any]]:
    """
    Optimized dashboard summary with single query.
    
    Uses composite indexes for all lookups.
    
    Args:
        taxpayer_gstin: Taxpayer GSTIN
        period: Period in MMYYYY format
        
    Returns:
        Tuple of (query, parameters)
    """
    query = """
    MATCH (t:Taxpayer {gstin: $taxpayer_gstin})
    
    // Get purchase register stats (uses composite index)
    OPTIONAL MATCH (t)-[:RECEIVED_BY]-(pr:Invoice)
    WHERE pr.source_type = 'PURCHASE_REGISTER'
    AND pr.source_period = $period
    
    WITH t, 
         count(pr) as pr_count,
         sum(pr.total_amount) as pr_amount,
         sum(pr.total_tax) as pr_tax
    
    // Get GSTR-2B stats (uses composite index)
    OPTIONAL MATCH (t)-[:RECEIVED_BY]-(gstr2b:Invoice)
    WHERE gstr2b.source_type = 'GSTR-2B'
    AND gstr2b.source_period = $period
    
    WITH t, pr_count, pr_amount, pr_tax,
         count(gstr2b) as gstr2b_count,
         sum(gstr2b.total_amount) as gstr2b_amount
    
    // Get mismatch stats (uses composite index)
    OPTIONAL MATCH (m:Mismatch)
    WHERE m.taxpayer_gstin = $taxpayer_gstin
    AND m.period = $period
    AND m.resolved = false
    
    WITH t, pr_count, pr_amount, pr_tax, gstr2b_count, gstr2b_amount,
         count(m) as mismatch_count,
         sum(CASE WHEN m.severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
         sum(CASE WHEN m.severity = 'HIGH' THEN 1 ELSE 0 END) as high_count,
         sum(m.amount_difference) as total_mismatch_amount
    
    // Get matched invoice count
    OPTIONAL MATCH (t)-[:RECEIVED_BY]-(pr2:Invoice)-[:MATCHES]-(gstr2b2:Invoice)
    WHERE pr2.source_type = 'PURCHASE_REGISTER'
    AND gstr2b2.source_type = 'GSTR-2B'
    AND pr2.source_period = $period
    
    RETURN {
        taxpayer_gstin: $taxpayer_gstin,
        period: $period,
        purchase_register: {
            count: coalesce(pr_count, 0),
            total_amount: coalesce(pr_amount, 0),
            total_tax: coalesce(pr_tax, 0)
        },
        gstr2b: {
            count: coalesce(gstr2b_count, 0),
            total_amount: coalesce(gstr2b_amount, 0)
        },
        matched_invoices: count(pr2),
        mismatches: {
            total: coalesce(mismatch_count, 0),
            critical: coalesce(critical_count, 0),
            high: coalesce(high_count, 0),
            total_amount: coalesce(total_mismatch_amount, 0)
        },
        itc_at_risk: coalesce(total_mismatch_amount, 0),
        safe_itc: coalesce(pr_tax, 0) - coalesce(total_mismatch_amount, 0)
    } as summary
    """
    
    params = {
        "taxpayer_gstin": taxpayer_gstin,
        "period": period
    }
    
    return query, params


def get_vendor_risk_summary_batch(
    vendor_ids: List[str]
) -> Tuple[str, Dict[str, Any]]:
    """
    Get risk summary for multiple vendors in one query.
    
    Args:
        vendor_ids: List of vendor IDs
        
    Returns:
        Tuple of (query, parameters)
    """
    query = """
    MATCH (v:Vendor)
    WHERE v.id IN $vendor_ids
    
    OPTIONAL MATCH (v)-[:IS_VENDOR]-(t:Taxpayer)<-[:ISSUED_BY]-(inv:Invoice)
    OPTIONAL MATCH (inv)-[:HAS_MISMATCH]->(m:Mismatch)
    
    RETURN 
        v.id as vendor_id,
        v.gstin as gstin,
        v.legal_name as name,
        v.risk_score as risk_score,
        v.compliance_score as compliance_score,
        count(DISTINCT inv) as total_invoices,
        count(DISTINCT m) as total_mismatches,
        sum(inv.total_amount) as total_transaction_value,
        sum(m.amount_difference) as total_mismatch_amount
    """
    
    params = {
        "vendor_ids": vendor_ids
    }
    
    return query, params


# ============================================================================
# 5. QUERY PERFORMANCE MONITORING
# ============================================================================

def explain_query(query: str) -> str:
    """
    Wrap query with EXPLAIN for performance analysis.
    
    Args:
        query: Cypher query
        
    Returns:
        Query with EXPLAIN prefix
    """
    return f"EXPLAIN {query}"


def profile_query(query: str) -> str:
    """
    Wrap query with PROFILE for detailed performance analysis.
    
    Args:
        query: Cypher query
        
    Returns:
        Query with PROFILE prefix
    """
    return f"PROFILE {query}"
