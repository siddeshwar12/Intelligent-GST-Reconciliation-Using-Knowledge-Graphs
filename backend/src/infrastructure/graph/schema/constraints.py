"""
Neo4j Knowledge Graph Schema - Constraints and Indexes
Optimized for GST Reconciliation Performance
"""

from typing import List, Dict


# ============================================================================
# UNIQUE CONSTRAINTS
# ============================================================================

def get_unique_constraints() -> List[str]:
    """
    Get unique constraint creation queries.
    These ensure data integrity and enable fast lookups.
    """
    return [
        # Primary key constraints
        "CREATE CONSTRAINT taxpayer_id IF NOT EXISTS FOR (t:Taxpayer) REQUIRE t.id IS UNIQUE",
        "CREATE CONSTRAINT gstin_value IF NOT EXISTS FOR (g:GSTIN) REQUIRE g.gstin IS UNIQUE",
        "CREATE CONSTRAINT invoice_id IF NOT EXISTS FOR (i:Invoice) REQUIRE i.id IS UNIQUE",
        "CREATE CONSTRAINT line_item_id IF NOT EXISTS FOR (l:LineItem) REQUIRE l.id IS UNIQUE",
        "CREATE CONSTRAINT return_id IF NOT EXISTS FOR (r:Return) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT payment_id IF NOT EXISTS FOR (p:Payment) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT vendor_id IF NOT EXISTS FOR (v:Vendor) REQUIRE v.id IS UNIQUE",
        "CREATE CONSTRAINT tax_component_id IF NOT EXISTS FOR (t:TaxComponent) REQUIRE t.id IS UNIQUE",
        "CREATE CONSTRAINT mismatch_id IF NOT EXISTS FOR (m:Mismatch) REQUIRE m.id IS UNIQUE",
        
        # Business key constraints
        "CREATE CONSTRAINT taxpayer_gstin IF NOT EXISTS FOR (t:Taxpayer) REQUIRE t.gstin IS UNIQUE",
        "CREATE CONSTRAINT vendor_gstin IF NOT EXISTS FOR (v:Vendor) REQUIRE v.gstin IS UNIQUE",
    ]


# ============================================================================
# EXISTENCE CONSTRAINTS (Node properties that must exist)
# ============================================================================

def get_existence_constraints() -> List[str]:
    """
    Get existence constraint queries.
    These ensure critical properties are always present.
    """
    return [
        # Taxpayer required fields
        "CREATE CONSTRAINT taxpayer_gstin_exists IF NOT EXISTS FOR (t:Taxpayer) REQUIRE t.gstin IS NOT NULL",
        "CREATE CONSTRAINT taxpayer_legal_name_exists IF NOT EXISTS FOR (t:Taxpayer) REQUIRE t.legal_name IS NOT NULL",
        
        # Invoice required fields
        "CREATE CONSTRAINT invoice_number_exists IF NOT EXISTS FOR (i:Invoice) REQUIRE i.invoice_number IS NOT NULL",
        "CREATE CONSTRAINT invoice_date_exists IF NOT EXISTS FOR (i:Invoice) REQUIRE i.invoice_date IS NOT NULL",
        "CREATE CONSTRAINT invoice_source_exists IF NOT EXISTS FOR (i:Invoice) REQUIRE i.source_type IS NOT NULL",
        
        # Return required fields
        "CREATE CONSTRAINT return_type_exists IF NOT EXISTS FOR (r:Return) REQUIRE r.return_type IS NOT NULL",
        "CREATE CONSTRAINT return_period_exists IF NOT EXISTS FOR (r:Return) REQUIRE r.return_period IS NOT NULL",
        
        # Mismatch required fields
        "CREATE CONSTRAINT mismatch_type_exists IF NOT EXISTS FOR (m:Mismatch) REQUIRE m.mismatch_type IS NOT NULL",
        "CREATE CONSTRAINT mismatch_risk_exists IF NOT EXISTS FOR (m:Mismatch) REQUIRE m.risk_level IS NOT NULL",
    ]


# ============================================================================
# SINGLE PROPERTY INDEXES (For fast lookups)
# ============================================================================

def get_single_property_indexes() -> List[str]:
    """
    Get single property index creation queries.
    These speed up WHERE clause filtering.
    """
    return [
        # Taxpayer indexes
        "CREATE INDEX taxpayer_state_code IF NOT EXISTS FOR (t:Taxpayer) ON (t.state_code)",
        "CREATE INDEX taxpayer_pan IF NOT EXISTS FOR (t:Taxpayer) ON (t.pan)",
        "CREATE INDEX taxpayer_type IF NOT EXISTS FOR (t:Taxpayer) ON (t.taxpayer_type)",
        "CREATE INDEX taxpayer_active IF NOT EXISTS FOR (t:Taxpayer) ON (t.is_active)",
        
        # GSTIN indexes
        "CREATE INDEX gstin_state_code IF NOT EXISTS FOR (g:GSTIN) ON (g.state_code)",
        "CREATE INDEX gstin_pan IF NOT EXISTS FOR (g:GSTIN) ON (g.pan)",
        
        # Invoice indexes (Critical for reconciliation)
        "CREATE INDEX invoice_number IF NOT EXISTS FOR (i:Invoice) ON (i.invoice_number)",
        "CREATE INDEX invoice_date IF NOT EXISTS FOR (i:Invoice) ON (i.invoice_date)",
        "CREATE INDEX invoice_source_type IF NOT EXISTS FOR (i:Invoice) ON (i.source_type)",
        "CREATE INDEX invoice_source_period IF NOT EXISTS FOR (i:Invoice) ON (i.source_period)",
        "CREATE INDEX invoice_financial_year IF NOT EXISTS FOR (i:Invoice) ON (i.financial_year)",
        "CREATE INDEX invoice_type IF NOT EXISTS FOR (i:Invoice) ON (i.invoice_type)",
        "CREATE INDEX invoice_irn IF NOT EXISTS FOR (i:Invoice) ON (i.irn)",
        "CREATE INDEX invoice_total_amount IF NOT EXISTS FOR (i:Invoice) ON (i.total_amount)",
        "CREATE INDEX invoice_total_tax IF NOT EXISTS FOR (i:Invoice) ON (i.total_tax)",
        
        # Invoice reconciliation flags (Critical for performance)
        "CREATE INDEX invoice_is_matched IF NOT EXISTS FOR (i:Invoice) ON (i.is_matched)",
        "CREATE INDEX invoice_has_mismatch IF NOT EXISTS FOR (i:Invoice) ON (i.has_mismatch)",
        "CREATE INDEX invoice_itc_eligible IF NOT EXISTS FOR (i:Invoice) ON (i.itc_eligible)",
        "CREATE INDEX invoice_filing_status IF NOT EXISTS FOR (i:Invoice) ON (i.filing_status)",
        
        # LineItem indexes
        "CREATE INDEX line_item_hsn IF NOT EXISTS FOR (l:LineItem) ON (l.hsn_code)",
        "CREATE INDEX line_item_tax_rate IF NOT EXISTS FOR (l:LineItem) ON (l.total_tax_rate)",
        
        # Return indexes
        "CREATE INDEX return_type IF NOT EXISTS FOR (r:Return) ON (r.return_type)",
        "CREATE INDEX return_period IF NOT EXISTS FOR (r:Return) ON (r.return_period)",
        "CREATE INDEX return_financial_year IF NOT EXISTS FOR (r:Return) ON (r.financial_year)",
        "CREATE INDEX return_status IF NOT EXISTS FOR (r:Return) ON (r.status)",
        "CREATE INDEX return_filing_date IF NOT EXISTS FOR (r:Return) ON (r.filing_date)",
        "CREATE INDEX return_is_late IF NOT EXISTS FOR (r:Return) ON (r.is_late)",
        "CREATE INDEX return_is_amended IF NOT EXISTS FOR (r:Return) ON (r.is_amended)",
        
        # Payment indexes
        "CREATE INDEX payment_date IF NOT EXISTS FOR (p:Payment) ON (p.payment_date)",
        "CREATE INDEX payment_period IF NOT EXISTS FOR (p:Payment) ON (p.payment_period)",
        "CREATE INDEX payment_mode IF NOT EXISTS FOR (p:Payment) ON (p.payment_mode)",
        "CREATE INDEX payment_total IF NOT EXISTS FOR (p:Payment) ON (p.total_tax_paid)",
        
        # Vendor indexes (Critical for risk analysis)
        "CREATE INDEX vendor_gstin IF NOT EXISTS FOR (v:Vendor) ON (v.gstin)",
        "CREATE INDEX vendor_compliance_score IF NOT EXISTS FOR (v:Vendor) ON (v.compliance_score)",
        "CREATE INDEX vendor_risk_category IF NOT EXISTS FOR (v:Vendor) ON (v.risk_category)",
        "CREATE INDEX vendor_mismatch_rate IF NOT EXISTS FOR (v:Vendor) ON (v.mismatch_rate)",
        "CREATE INDEX vendor_is_high_risk IF NOT EXISTS FOR (v:Vendor) ON (v.is_high_risk)",
        "CREATE INDEX vendor_is_blacklisted IF NOT EXISTS FOR (v:Vendor) ON (v.is_blacklisted)",
        
        # Mismatch indexes (Critical for filtering)
        "CREATE INDEX mismatch_type IF NOT EXISTS FOR (m:Mismatch) ON (m.mismatch_type)",
        "CREATE INDEX mismatch_risk_level IF NOT EXISTS FOR (m:Mismatch) ON (m.risk_level)",
        "CREATE INDEX mismatch_status IF NOT EXISTS FOR (m:Mismatch) ON (m.status)",
        "CREATE INDEX mismatch_detected_at IF NOT EXISTS FOR (m:Mismatch) ON (m.detected_at)",
        "CREATE INDEX mismatch_variance IF NOT EXISTS FOR (m:Mismatch) ON (m.variance_percent)",
        "CREATE INDEX mismatch_itc_impact IF NOT EXISTS FOR (m:Mismatch) ON (m.itc_impact)",
        "CREATE INDEX mismatch_days_open IF NOT EXISTS FOR (m:Mismatch) ON (m.days_open)",
        "CREATE INDEX mismatch_aging_bucket IF NOT EXISTS FOR (m:Mismatch) ON (m.aging_bucket)",
    ]


# ============================================================================
# COMPOSITE INDEXES (For complex queries)
# ============================================================================

def get_composite_indexes() -> List[str]:
    """
    Get composite index creation queries.
    These optimize multi-column WHERE clauses and JOINs.
    Critical for reconciliation performance.
    """
    return [
        # Invoice reconciliation composite indexes
        "CREATE INDEX invoice_reconciliation_idx IF NOT EXISTS FOR (i:Invoice) ON (i.invoice_number, i.source_type, i.source_period)",
        "CREATE INDEX invoice_matching_idx IF NOT EXISTS FOR (i:Invoice) ON (i.invoice_number, i.invoice_date, i.total_amount)",
        "CREATE INDEX invoice_itc_validation_idx IF NOT EXISTS FOR (i:Invoice) ON (i.invoice_date, i.itc_eligible, i.is_matched)",
        "CREATE INDEX invoice_period_source_idx IF NOT EXISTS FOR (i:Invoice) ON (i.source_period, i.source_type, i.filing_status)",
        
        # Return period composite indexes
        "CREATE INDEX return_period_type_idx IF NOT EXISTS FOR (r:Return) ON (r.return_type, r.return_period, r.status)",
        "CREATE INDEX return_filing_idx IF NOT EXISTS FOR (r:Return) ON (r.return_period, r.filing_date, r.is_late)",
        
        # Mismatch filtering composite indexes
        "CREATE INDEX mismatch_filter_idx IF NOT EXISTS FOR (m:Mismatch) ON (m.risk_level, m.status, m.detected_at)",
        "CREATE INDEX mismatch_analysis_idx IF NOT EXISTS FOR (m:Mismatch) ON (m.mismatch_type, m.risk_level, m.variance_percent)",
        
        # Vendor analysis composite indexes
        "CREATE INDEX vendor_analysis_idx IF NOT EXISTS FOR (v:Vendor) ON (v.compliance_score, v.mismatch_rate, v.is_high_risk)",
        "CREATE INDEX vendor_performance_idx IF NOT EXISTS FOR (v:Vendor) ON (v.risk_category, v.total_transactions, v.total_mismatches)",
    ]


# ============================================================================
# FULL-TEXT SEARCH INDEXES
# ============================================================================

def get_fulltext_indexes() -> List[str]:
    """
    Get full-text search index creation queries.
    These enable text search on string properties.
    """
    return [
        # Taxpayer name search
        "CREATE FULLTEXT INDEX taxpayer_name_search IF NOT EXISTS FOR (t:Taxpayer) ON EACH [t.legal_name, t.trade_name]",
        
        # Invoice search
        "CREATE FULLTEXT INDEX invoice_search IF NOT EXISTS FOR (i:Invoice) ON EACH [i.invoice_number, i.irn]",
        
        # Vendor name search
        "CREATE FULLTEXT INDEX vendor_name_search IF NOT EXISTS FOR (v:Vendor) ON EACH [v.name]",
        
        # Mismatch description search
        "CREATE FULLTEXT INDEX mismatch_description_search IF NOT EXISTS FOR (m:Mismatch) ON EACH [m.description, m.root_cause]",
    ]


# ============================================================================
# RANGE INDEXES (For date and numeric range queries)
# ============================================================================

def get_range_indexes() -> List[str]:
    """
    Get range index creation queries.
    These optimize BETWEEN, <, >, <=, >= queries.
    """
    return [
        # Date range indexes
        "CREATE RANGE INDEX invoice_date_range IF NOT EXISTS FOR (i:Invoice) ON (i.invoice_date)",
        "CREATE RANGE INDEX return_filing_date_range IF NOT EXISTS FOR (r:Return) ON (r.filing_date)",
        "CREATE RANGE INDEX payment_date_range IF NOT EXISTS FOR (p:Payment) ON (p.payment_date)",
        "CREATE RANGE INDEX mismatch_detected_range IF NOT EXISTS FOR (m:Mismatch) ON (m.detected_at)",
        
        # Numeric range indexes
        "CREATE RANGE INDEX invoice_amount_range IF NOT EXISTS FOR (i:Invoice) ON (i.total_amount)",
        "CREATE RANGE INDEX vendor_score_range IF NOT EXISTS FOR (v:Vendor) ON (v.compliance_score)",
        "CREATE RANGE INDEX mismatch_variance_range IF NOT EXISTS FOR (m:Mismatch) ON (m.variance_percent)",
    ]


# ============================================================================
# RELATIONSHIP INDEXES (For traversal optimization)
# ============================================================================

def get_relationship_indexes() -> List[str]:
    """
    Get relationship property index creation queries.
    These optimize relationship property filtering during traversal.
    """
    return [
        # MATCHES relationship indexes
        "CREATE INDEX matches_score IF NOT EXISTS FOR ()-[r:MATCHES]-() ON (r.match_score)",
        "CREATE INDEX matches_type IF NOT EXISTS FOR ()-[r:MATCHES]-() ON (r.match_type)",
        
        # MISMATCHES relationship indexes
        "CREATE INDEX mismatches_type IF NOT EXISTS FOR ()-[r:MISMATCHES]-() ON (r.mismatch_type)",
        "CREATE INDEX mismatches_variance IF NOT EXISTS FOR ()-[r:MISMATCHES]-() ON (r.variance_percent)",
        
        # ENABLES_ITC relationship indexes (Critical for ITC validation)
        "CREATE INDEX enables_itc_eligible IF NOT EXISTS FOR ()-[r:ENABLES_ITC]-() ON (r.is_eligible)",
        "CREATE INDEX enables_itc_validated IF NOT EXISTS FOR ()-[r:ENABLES_ITC]-() ON (r.chain_validated)",
        "CREATE INDEX enables_itc_amount IF NOT EXISTS FOR ()-[r:ENABLES_ITC]-() ON (r.itc_amount)",
        
        # REPORTED_IN relationship indexes
        "CREATE INDEX reported_in_period IF NOT EXISTS FOR ()-[r:REPORTED_IN]-() ON (r.return_period)",
        "CREATE INDEX reported_in_status IF NOT EXISTS FOR ()-[r:REPORTED_IN]-() ON (r.filing_status)",
        
        # SUPPLIES_TO relationship indexes
        "CREATE INDEX supplies_to_value IF NOT EXISTS FOR ()-[r:SUPPLIES_TO]-() ON (r.total_value)",
        "CREATE INDEX supplies_to_active IF NOT EXISTS FOR ()-[r:SUPPLIES_TO]-() ON (r.is_active)",
    ]


# ============================================================================
# PERFORMANCE OPTIMIZATION QUERIES
# ============================================================================

def get_performance_optimization_queries() -> List[str]:
    """
    Get additional performance optimization queries.
    These improve query planning and execution.
    """
    return [
        # Update statistics for better query planning
        "CALL db.stats.retrieve('GRAPH COUNTS')",
        
        # Warm up page cache (run after data load)
        "CALL db.warmup.run()",
    ]


# ============================================================================
# CONSTRAINT AND INDEX MANAGEMENT
# ============================================================================

async def create_all_constraints(client):
    """
    Create all constraints and indexes.
    
    Args:
        client: Neo4j client instance
    """
    from ...shared.utils import logger
    
    all_queries = (
        get_unique_constraints() +
        get_existence_constraints() +
        get_single_property_indexes() +
        get_composite_indexes() +
        get_fulltext_indexes() +
        get_range_indexes() +
        get_relationship_indexes()
    )
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for query in all_queries:
        try:
            await client.execute_write(query)
            success_count += 1
            logger.debug(f"Created: {query[:60]}...")
        except Exception as e:
            if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                skip_count += 1
            else:
                error_count += 1
                logger.warning(f"Failed to create constraint/index: {str(e)}")
    
    logger.info(f"Constraints/Indexes - Created: {success_count}, Skipped: {skip_count}, Errors: {error_count}")
    
    # Run performance optimizations
    try:
        for query in get_performance_optimization_queries():
            await client.execute_query(query)
        logger.info("Performance optimizations applied")
    except Exception as e:
        logger.warning(f"Performance optimization failed: {str(e)}")


async def drop_all_constraints(client):
    """
    Drop all constraints and indexes (use with caution!).
    
    Args:
        client: Neo4j client instance
    """
    from ...shared.utils import logger
    
    # Get all constraints
    constraints_query = "SHOW CONSTRAINTS"
    constraints = await client.execute_query(constraints_query)
    
    for constraint in constraints:
        try:
            constraint_name = constraint.get('name')
            drop_query = f"DROP CONSTRAINT {constraint_name} IF EXISTS"
            await client.execute_write(drop_query)
            logger.info(f"Dropped constraint: {constraint_name}")
        except Exception as e:
            logger.error(f"Failed to drop constraint: {str(e)}")
    
    # Get all indexes
    indexes_query = "SHOW INDEXES"
    indexes = await client.execute_query(indexes_query)
    
    for index in indexes:
        try:
            index_name = index.get('name')
            drop_query = f"DROP INDEX {index_name} IF EXISTS"
            await client.execute_write(drop_query)
            logger.info(f"Dropped index: {index_name}")
        except Exception as e:
            logger.error(f"Failed to drop index: {str(e)}")


def get_constraint_summary() -> Dict[str, int]:
    """Get summary of constraints and indexes."""
    return {
        "unique_constraints": len(get_unique_constraints()),
        "existence_constraints": len(get_existence_constraints()),
        "single_property_indexes": len(get_single_property_indexes()),
        "composite_indexes": len(get_composite_indexes()),
        "fulltext_indexes": len(get_fulltext_indexes()),
        "range_indexes": len(get_range_indexes()),
        "relationship_indexes": len(get_relationship_indexes()),
        "total": (
            len(get_unique_constraints()) +
            len(get_existence_constraints()) +
            len(get_single_property_indexes()) +
            len(get_composite_indexes()) +
            len(get_fulltext_indexes()) +
            len(get_range_indexes()) +
            len(get_relationship_indexes())
        )
    }
