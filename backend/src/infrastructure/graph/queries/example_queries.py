"""
Example Cypher queries for common GST reconciliation operations.
These queries demonstrate the power of graph traversal for ITC validation.
"""

# ============================================================================
# 1. BASIC QUERIES - Entity Retrieval
# ============================================================================

# Get taxpayer by GSTIN
GET_TAXPAYER_BY_GSTIN = """
MATCH (t:Taxpayer {gstin: $gstin})
RETURN t
"""

# Get all invoices for a taxpayer in a period
GET_INVOICES_BY_PERIOD = """
MATCH (t:Taxpayer {id: $taxpayer_id})-[:RECEIVED_BY]-(i:Invoice)
WHERE i.source_period = $period
RETURN i
ORDER BY i.invoice_date DESC
"""

# Get invoice with all details
GET_INVOICE_DETAILS = """
MATCH (i:Invoice {id: $invoice_id})
OPTIONAL MATCH (i)-[:ISSUED_BY]->(supplier:Taxpayer)
OPTIONAL MATCH (i)-[:RECEIVED_BY]->(buyer:Taxpayer)
OPTIONAL MATCH (i)-[:CONTAINS]->(li:LineItem)
OPTIONAL MATCH (i)-[:HAS_TAX]->(tax:TaxComponent)
RETURN i, supplier, buyer, collect(li) as line_items, tax
"""

# ============================================================================
# 2. RECONCILIATION QUERIES - Invoice Matching
# ============================================================================

# Find matching invoices across sources
FIND_MATCHING_INVOICES = """
MATCH (i1:Invoice {invoice_number: $invoice_number})
WHERE i1.source_type = $source1
MATCH (i2:Invoice {invoice_number: $invoice_number})
WHERE i2.source_type = $source2
AND abs(duration.between(i1.invoice_date, i2.invoice_date).days) <= $date_tolerance
AND abs(i1.total_amount - i2.total_amount) <= $amount_tolerance
RETURN i1, i2
"""

# Find unmatched invoices (missing in GSTR-2B)
FIND_UNMATCHED_INVOICES = """
MATCH (i:Invoice)
WHERE i.source_type = 'PURCHASE_REGISTER'
AND i.source_period = $period
AND NOT EXISTS {
    MATCH (i)-[:MATCHES]-(i2:Invoice)
    WHERE i2.source_type = 'GSTR-2B'
}
RETURN i
ORDER BY i.total_amount DESC
"""

# Find duplicate invoices
FIND_DUPLICATE_INVOICES = """
MATCH (i:Invoice)
WHERE i.source_type = $source_type
WITH i.invoice_number as inv_no, i.supplier_gstin as gstin, collect(i) as invoices
WHERE size(invoices) > 1
RETURN inv_no, gstin, invoices
"""

# ============================================================================
# 3. ITC VALIDATION QUERIES - Multi-hop Traversal
# ============================================================================

# Validate complete ITC chain
VALIDATE_ITC_CHAIN = """
MATCH (buyer:Taxpayer {id: $buyer_id})
MATCH (buyer)-[:RECEIVED_BY]-(purchase_inv:Invoice)
WHERE purchase_inv.source_type = 'PURCHASE_REGISTER'
AND purchase_inv.source_period = $period

OPTIONAL MATCH (purchase_inv)-[:ISSUED_BY]->(supplier:Taxpayer)
OPTIONAL MATCH (supplier)-[:FILED_BY]-(gstr1:Return {return_type: 'GSTR-1', return_period: $period})
OPTIONAL MATCH (purchase_inv)-[:MATCHES]-(gstr2b_inv:Invoice {source_type: 'GSTR-2B'})
OPTIONAL MATCH (gstr2b_inv)-[:REPORTED_IN]->(gstr2b:Return {return_type: 'GSTR-2B'})

RETURN 
    purchase_inv.invoice_number as invoice_number,
    purchase_inv.total_amount as purchase_amount,
    supplier.gstin as supplier_gstin,
    supplier.legal_name as supplier_name,
    gstr1.status as gstr1_filed,
    gstr2b_inv.total_amount as gstr2b_amount,
    gstr2b.status as gstr2b_available,
    CASE 
        WHEN gstr2b_inv IS NULL THEN 'MISSING_IN_GSTR2B'
        WHEN abs(purchase_inv.total_amount - gstr2b_inv.total_amount) > $tolerance THEN 'AMOUNT_MISMATCH'
        WHEN gstr1.status IS NULL OR gstr1.status <> 'FILED' THEN 'SUPPLIER_NOT_FILED'
        ELSE 'VALID'
    END as itc_status
ORDER BY purchase_inv.total_amount DESC
"""

# Check if supplier filed GSTR-1
CHECK_SUPPLIER_FILING = """
MATCH (invoice:Invoice {id: $invoice_id})-[:ISSUED_BY]->(supplier:Taxpayer)
MATCH (supplier)-[:FILED_BY]-(return:Return {return_type: 'GSTR-1', return_period: $period})
RETURN 
    supplier.gstin as supplier_gstin,
    supplier.legal_name as supplier_name,
    return.status as filing_status,
    return.filing_date as filing_date,
    return.due_date as due_date,
    CASE 
        WHEN return.filing_date > return.due_date THEN true 
        ELSE false 
    END as is_late_filed
"""

# Trace invoice path through returns
TRACE_INVOICE_PATH = """
MATCH path = (buyer:Taxpayer)-[:RECEIVED_BY]-(inv:Invoice)-[:ISSUED_BY]->(supplier:Taxpayer)
WHERE inv.id = $invoice_id

OPTIONAL MATCH (inv)-[:REPORTED_IN]->(return:Return)
OPTIONAL MATCH (return)-[:PAID_VIA]->(payment:Payment)

RETURN 
    nodes(path) as entities,
    relationships(path) as relationships,
    return,
    payment
"""

# ============================================================================
# 4. MISMATCH QUERIES - Finding Discrepancies
# ============================================================================

# Get all mismatches for a taxpayer
GET_TAXPAYER_MISMATCHES = """
MATCH (m:Mismatch {taxpayer_id: $taxpayer_id})
OPTIONAL MATCH (m)<-[:HAS_MISMATCH]-(i1:Invoice)
OPTIONAL MATCH (m)-[:RELATES_TO]->(i2:Invoice)
RETURN m, i1, i2
ORDER BY m.risk_level DESC, m.amount_difference DESC
"""

# Get critical mismatches across all taxpayers
GET_CRITICAL_MISMATCHES = """
MATCH (m:Mismatch {risk_level: 'CRITICAL', status: 'OPEN'})
MATCH (m)-[:DETECTED_FOR]->(t:Taxpayer)
OPTIONAL MATCH (m)<-[:HAS_MISMATCH]-(i:Invoice)
RETURN 
    m.id as mismatch_id,
    m.mismatch_type as type,
    m.amount_difference as amount_diff,
    m.description as description,
    t.gstin as taxpayer_gstin,
    t.legal_name as taxpayer_name,
    i.invoice_number as invoice_number,
    m.detected_at as detected_at
ORDER BY m.amount_difference DESC
LIMIT 50
"""

# Get mismatch statistics by type
GET_MISMATCH_STATISTICS = """
MATCH (m:Mismatch)
WHERE m.detected_at >= datetime($start_date)
AND m.detected_at <= datetime($end_date)
RETURN 
    m.mismatch_type as type,
    m.risk_level as risk,
    count(m) as count,
    sum(m.amount_difference) as total_amount,
    avg(m.amount_difference) as avg_amount
ORDER BY count DESC
"""

# Find recurring mismatches with same vendor
FIND_RECURRING_VENDOR_MISMATCHES = """
MATCH (buyer:Taxpayer {id: $buyer_id})-[:RECEIVED_BY]-(inv:Invoice)-[:ISSUED_BY]->(vendor:Taxpayer)
MATCH (inv)-[:HAS_MISMATCH]->(m:Mismatch)
WITH vendor, count(m) as mismatch_count, sum(m.amount_difference) as total_diff
WHERE mismatch_count >= $threshold
RETURN 
    vendor.gstin as vendor_gstin,
    vendor.legal_name as vendor_name,
    mismatch_count,
    total_diff
ORDER BY mismatch_count DESC
"""

# ============================================================================
# 5. VENDOR QUERIES - Compliance and Risk
# ============================================================================

# Get vendor compliance details
GET_VENDOR_COMPLIANCE = """
MATCH (v:Vendor {id: $vendor_id})
MATCH (v)-[:IS_VENDOR]-(t:Taxpayer)
OPTIONAL MATCH (t)<-[:ISSUED_BY]-(inv:Invoice)
OPTIONAL MATCH (inv)-[:HAS_MISMATCH]->(m:Mismatch)
RETURN 
    v.gstin as gstin,
    v.name as name,
    v.compliance_score as compliance_score,
    v.total_transactions as total_transactions,
    v.total_mismatches as total_mismatches,
    v.critical_mismatches as critical_mismatches,
    v.mismatch_rate as mismatch_rate,
    count(DISTINCT inv) as invoice_count,
    count(DISTINCT m) as current_open_mismatches
"""

# Get high-risk vendors
GET_HIGH_RISK_VENDORS = """
MATCH (v:Vendor)
WHERE v.compliance_score < $threshold
MATCH (v)-[:IS_VENDOR]-(t:Taxpayer)
RETURN 
    v.id as vendor_id,
    v.gstin as gstin,
    v.name as name,
    v.compliance_score as score,
    v.total_mismatches as mismatches,
    v.critical_mismatches as critical,
    v.total_mismatch_value as mismatch_value
ORDER BY v.compliance_score ASC, v.total_mismatch_value DESC
LIMIT $limit
"""

# Get vendor transaction history
GET_VENDOR_TRANSACTION_HISTORY = """
MATCH (vendor:Taxpayer {gstin: $vendor_gstin})<-[:ISSUED_BY]-(inv:Invoice)-[:RECEIVED_BY]->(buyer:Taxpayer)
WHERE inv.invoice_date >= datetime($start_date)
AND inv.invoice_date <= datetime($end_date)
OPTIONAL MATCH (inv)-[:HAS_MISMATCH]->(m:Mismatch)
RETURN 
    inv.invoice_number as invoice_number,
    inv.invoice_date as date,
    inv.total_amount as amount,
    buyer.legal_name as buyer_name,
    m.mismatch_type as mismatch_type,
    m.risk_level as risk_level
ORDER BY inv.invoice_date DESC
"""

# Calculate vendor network metrics
GET_VENDOR_NETWORK_METRICS = """
MATCH (v:Vendor {id: $vendor_id})-[:IS_VENDOR]-(t:Taxpayer)
MATCH (t)<-[:ISSUED_BY]-(inv:Invoice)-[:RECEIVED_BY]->(buyer:Taxpayer)
WITH v, t, count(DISTINCT buyer) as buyer_count, 
     count(DISTINCT inv) as invoice_count,
     sum(inv.total_amount) as total_value
RETURN 
    v.gstin as gstin,
    v.name as name,
    buyer_count as unique_buyers,
    invoice_count as total_invoices,
    total_value as total_transaction_value,
    total_value / invoice_count as avg_invoice_value
"""

# ============================================================================
# 6. DASHBOARD QUERIES - Statistics and Aggregations
# ============================================================================

# Get reconciliation dashboard summary
GET_DASHBOARD_SUMMARY = """
MATCH (t:Taxpayer {id: $taxpayer_id})

// Total ITC claimed
OPTIONAL MATCH (t)-[:RECEIVED_BY]-(inv:Invoice)
WHERE inv.source_type = 'PURCHASE_REGISTER'
AND inv.source_period = $period
WITH t, sum(inv.total_tax) as total_itc_claimed, count(inv) as total_invoices

// Mismatches
OPTIONAL MATCH (m:Mismatch {taxpayer_id: $taxpayer_id, status: 'OPEN'})
WITH t, total_itc_claimed, total_invoices,
     count(m) as total_mismatches,
     sum(CASE WHEN m.risk_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
     sum(CASE WHEN m.risk_level = 'HIGH' THEN 1 ELSE 0 END) as high_count,
     sum(m.itc_impact) as itc_at_risk

// Vendors
OPTIONAL MATCH (v:Vendor)-[:IS_VENDOR]-(supplier:Taxpayer)<-[:ISSUED_BY]-(inv2:Invoice)-[:RECEIVED_BY]->(t)
WITH t, total_itc_claimed, total_invoices, total_mismatches, 
     critical_count, high_count, itc_at_risk,
     count(DISTINCT v) as total_vendors,
     sum(CASE WHEN v.compliance_score < 40 THEN 1 ELSE 0 END) as high_risk_vendors

RETURN 
    total_itc_claimed,
    total_invoices,
    total_mismatches,
    critical_count,
    high_count,
    itc_at_risk,
    total_vendors,
    high_risk_vendors,
    (total_itc_claimed - itc_at_risk) as safe_itc
"""

# Get period-over-period comparison
GET_PERIOD_COMPARISON = """
MATCH (t:Taxpayer {id: $taxpayer_id})
MATCH (t)-[:RECEIVED_BY]-(inv:Invoice)
WHERE inv.source_period IN [$period1, $period2]
WITH inv.source_period as period,
     count(inv) as invoice_count,
     sum(inv.total_amount) as total_amount,
     sum(inv.total_tax) as total_tax
RETURN period, invoice_count, total_amount, total_tax
ORDER BY period
"""

# Get top mismatches by amount
GET_TOP_MISMATCHES_BY_AMOUNT = """
MATCH (m:Mismatch {taxpayer_id: $taxpayer_id, status: 'OPEN'})
MATCH (m)<-[:HAS_MISMATCH]-(inv:Invoice)
MATCH (inv)-[:ISSUED_BY]->(supplier:Taxpayer)
RETURN 
    m.id as mismatch_id,
    m.mismatch_type as type,
    m.risk_level as risk,
    m.amount_difference as amount,
    inv.invoice_number as invoice_number,
    supplier.legal_name as supplier_name,
    m.description as description,
    m.recommendation as recommendation
ORDER BY m.amount_difference DESC
LIMIT $limit
"""

# ============================================================================
# 7. AUDIT TRAIL QUERIES - Explainability
# ============================================================================

# Generate audit trail for invoice
GENERATE_AUDIT_TRAIL = """
MATCH path = (buyer:Taxpayer)-[:RECEIVED_BY]-(inv:Invoice)-[:ISSUED_BY]->(supplier:Taxpayer)
WHERE inv.id = $invoice_id

OPTIONAL MATCH (inv)-[:MATCHES]-(matched_inv:Invoice)
OPTIONAL MATCH (inv)-[:HAS_MISMATCH]->(m:Mismatch)
OPTIONAL MATCH (inv)-[:REPORTED_IN]->(return:Return)
OPTIONAL MATCH (supplier)-[:FILED_BY]-(supplier_return:Return {return_period: $period})

RETURN 
    nodes(path) as path_nodes,
    relationships(path) as path_relationships,
    matched_inv,
    m,
    return,
    supplier_return,
    CASE 
        WHEN matched_inv IS NOT NULL THEN 'MATCHED'
        WHEN m IS NOT NULL THEN 'MISMATCHED'
        ELSE 'UNPROCESSED'
    END as reconciliation_status
"""

# Get reconciliation history for invoice
GET_RECONCILIATION_HISTORY = """
MATCH (inv:Invoice {invoice_number: $invoice_number})
OPTIONAL MATCH (inv)-[:HAS_MISMATCH]->(m:Mismatch)
OPTIONAL MATCH (inv)-[:MATCHES]-(matched:Invoice)
RETURN 
    inv.source_type as source,
    inv.invoice_date as date,
    inv.total_amount as amount,
    m.mismatch_type as mismatch_type,
    m.status as mismatch_status,
    m.resolved_at as resolved_at,
    matched.source_type as matched_source
ORDER BY inv.created_at
"""

# ============================================================================
# 8. ADVANCED QUERIES - Graph Analytics
# ============================================================================

# Find invoice chains (buyer-supplier relationships)
FIND_INVOICE_CHAINS = """
MATCH path = (t1:Taxpayer)-[:RECEIVED_BY]-(inv1:Invoice)-[:ISSUED_BY]->(t2:Taxpayer)
              -[:RECEIVED_BY]-(inv2:Invoice)-[:ISSUED_BY]->(t3:Taxpayer)
WHERE t1.id = $taxpayer_id
AND length(path) <= $max_depth
RETURN path
LIMIT 100
"""

# Calculate taxpayer centrality (most connected)
CALCULATE_TAXPAYER_CENTRALITY = """
MATCH (t:Taxpayer)
OPTIONAL MATCH (t)-[:ISSUED_BY|RECEIVED_BY]-(inv:Invoice)
WITH t, count(DISTINCT inv) as transaction_count
RETURN 
    t.gstin as gstin,
    t.legal_name as name,
    transaction_count
ORDER BY transaction_count DESC
LIMIT 20
"""

# Find circular transactions (potential fraud)
FIND_CIRCULAR_TRANSACTIONS = """
MATCH path = (t:Taxpayer)-[:RECEIVED_BY|ISSUED_BY*4..8]-(t)
WHERE ALL(r IN relationships(path) WHERE type(r) IN ['RECEIVED_BY', 'ISSUED_BY'])
RETURN path
LIMIT 10
"""

# Get supplier-buyer network
GET_SUPPLIER_BUYER_NETWORK = """
MATCH (supplier:Taxpayer)<-[:ISSUED_BY]-(inv:Invoice)-[:RECEIVED_BY]->(buyer:Taxpayer)
WHERE supplier.id = $taxpayer_id OR buyer.id = $taxpayer_id
RETURN 
    supplier.gstin as supplier_gstin,
    supplier.legal_name as supplier_name,
    buyer.gstin as buyer_gstin,
    buyer.legal_name as buyer_name,
    count(inv) as transaction_count,
    sum(inv.total_amount) as total_value
ORDER BY total_value DESC
"""

# ============================================================================
# 9. PERFORMANCE QUERIES - Optimized for Large Datasets
# ============================================================================

# Batch process invoices for reconciliation
BATCH_PROCESS_INVOICES = """
MATCH (inv:Invoice)
WHERE inv.source_type = 'PURCHASE_REGISTER'
AND inv.source_period = $period
AND NOT EXISTS((inv)-[:MATCHES]-())
WITH inv
LIMIT $batch_size
RETURN inv
"""

# Get unprocessed invoices count
COUNT_UNPROCESSED_INVOICES = """
MATCH (inv:Invoice)
WHERE inv.source_type = 'PURCHASE_REGISTER'
AND NOT EXISTS((inv)-[:MATCHES]-())
AND NOT EXISTS((inv)-[:HAS_MISMATCH]-())
RETURN count(inv) as unprocessed_count
"""

# ============================================================================
# 10. UTILITY QUERIES - Maintenance and Cleanup
# ============================================================================

# Delete old reconciliation runs
DELETE_OLD_RECONCILIATION_RUNS = """
MATCH (m:Mismatch)
WHERE m.detected_at < datetime($cutoff_date)
AND m.status IN ['RESOLVED', 'CLOSED']
DETACH DELETE m
"""

# Update vendor compliance scores in batch
UPDATE_VENDOR_SCORES_BATCH = """
MATCH (v:Vendor)
WHERE v.last_assessment_date < datetime($cutoff_date)
OR v.last_assessment_date IS NULL
WITH v
LIMIT $batch_size
SET v.needs_assessment = true
RETURN count(v) as updated_count
"""

# Get database statistics
GET_DATABASE_STATISTICS = """
MATCH (t:Taxpayer) WITH count(t) as taxpayer_count
MATCH (i:Invoice) WITH taxpayer_count, count(i) as invoice_count
MATCH (m:Mismatch) WITH taxpayer_count, invoice_count, count(m) as mismatch_count
MATCH (v:Vendor) WITH taxpayer_count, invoice_count, mismatch_count, count(v) as vendor_count
MATCH ()-[r]->() WITH taxpayer_count, invoice_count, mismatch_count, vendor_count, count(r) as relationship_count
RETURN 
    taxpayer_count,
    invoice_count,
    mismatch_count,
    vendor_count,
    relationship_count
"""
