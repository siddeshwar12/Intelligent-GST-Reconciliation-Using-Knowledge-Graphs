// ============================================================================
// Neo4j Performance Optimization - Indexes and Constraints
// For handling 10k+ invoices efficiently
// ============================================================================

// ----------------------------------------------------------------------------
// 1. CONSTRAINTS (Uniqueness + Automatic Index)
// ----------------------------------------------------------------------------

// Taxpayer constraints
CREATE CONSTRAINT taxpayer_id_unique IF NOT EXISTS
FOR (t:Taxpayer) REQUIRE t.id IS UNIQUE;

CREATE CONSTRAINT taxpayer_gstin_unique IF NOT EXISTS
FOR (t:Taxpayer) REQUIRE t.gstin IS UNIQUE;

// Invoice constraints
CREATE CONSTRAINT invoice_id_unique IF NOT EXISTS
FOR (i:Invoice) REQUIRE i.id IS UNIQUE;

// Vendor constraints
CREATE CONSTRAINT vendor_id_unique IF NOT EXISTS
FOR (v:Vendor) REQUIRE v.id IS UNIQUE;

CREATE CONSTRAINT vendor_gstin_unique IF NOT EXISTS
FOR (v:Vendor) REQUIRE v.gstin IS UNIQUE;

// Mismatch constraints
CREATE CONSTRAINT mismatch_id_unique IF NOT EXISTS
FOR (m:Mismatch) REQUIRE m.id IS UNIQUE;

// ----------------------------------------------------------------------------
// 2. COMPOSITE INDEXES (Multiple Properties)
// ----------------------------------------------------------------------------

// Invoice composite indexes for common query patterns
CREATE INDEX invoice_gstin_period IF NOT EXISTS
FOR (i:Invoice) ON (i.supplier_gstin, i.period);

CREATE INDEX invoice_recipient_period IF NOT EXISTS
FOR (i:Invoice) ON (i.recipient_gstin, i.period);

CREATE INDEX invoice_number_gstin IF NOT EXISTS
FOR (i:Invoice) ON (i.invoice_number, i.supplier_gstin);

CREATE INDEX invoice_source_period IF NOT EXISTS
FOR (i:Invoice) ON (i.source_type, i.period);

// Mismatch composite indexes
CREATE INDEX mismatch_taxpayer_period IF NOT EXISTS
FOR (m:Mismatch) ON (m.taxpayer_gstin, m.period);

CREATE INDEX mismatch_severity_resolved IF NOT EXISTS
FOR (m:Mismatch) ON (m.severity, m.resolved);

CREATE INDEX mismatch_type_period IF NOT EXISTS
FOR (m:Mismatch) ON (m.mismatch_type, m.period);

// ----------------------------------------------------------------------------
// 3. SINGLE PROPERTY INDEXES
// ----------------------------------------------------------------------------

// Invoice indexes
CREATE INDEX invoice_date IF NOT EXISTS
FOR (i:Invoice) ON (i.invoice_date);

CREATE INDEX invoice_period IF NOT EXISTS
FOR (i:Invoice) ON (i.period);

CREATE INDEX invoice_source_type IF NOT EXISTS
FOR (i:Invoice) ON (i.source_type);

CREATE INDEX invoice_total_amount IF NOT EXISTS
FOR (i:Invoice) ON (i.total_amount);

CREATE INDEX invoice_status IF NOT EXISTS
FOR (i:Invoice) ON (i.status);

// Taxpayer indexes
CREATE INDEX taxpayer_state_code IF NOT EXISTS
FOR (t:Taxpayer) ON (t.state_code);

CREATE INDEX taxpayer_status IF NOT EXISTS
FOR (t:Taxpayer) ON (t.status);

// Mismatch indexes
CREATE INDEX mismatch_detected_at IF NOT EXISTS
FOR (m:Mismatch) ON (m.detected_at);

CREATE INDEX mismatch_severity IF NOT EXISTS
FOR (m:Mismatch) ON (m.severity);

CREATE INDEX mismatch_resolved IF NOT EXISTS
FOR (m:Mismatch) ON (m.resolved);

CREATE INDEX mismatch_amount IF NOT EXISTS
FOR (m:Mismatch) ON (m.amount_difference);

// Vendor indexes
CREATE INDEX vendor_risk_level IF NOT EXISTS
FOR (v:Vendor) ON (v.risk_level);

CREATE INDEX vendor_state_code IF NOT EXISTS
FOR (v:Vendor) ON (v.state_code);

// ----------------------------------------------------------------------------
// 4. FULL-TEXT SEARCH INDEXES
// ----------------------------------------------------------------------------

// Full-text search on taxpayer names
CREATE FULLTEXT INDEX taxpayer_name_search IF NOT EXISTS
FOR (t:Taxpayer) ON EACH [t.legal_name, t.trade_name];

// Full-text search on invoice numbers
CREATE FULLTEXT INDEX invoice_number_search IF NOT EXISTS
FOR (i:Invoice) ON EACH [i.invoice_number];

// Full-text search on vendor names
CREATE FULLTEXT INDEX vendor_name_search IF NOT EXISTS
FOR (v:Vendor) ON EACH [v.legal_name, v.trade_name];

// ----------------------------------------------------------------------------
// 5. RANGE INDEXES (For Date/Amount Queries)
// ----------------------------------------------------------------------------

// Range index for invoice dates
CREATE RANGE INDEX invoice_date_range IF NOT EXISTS
FOR (i:Invoice) ON (i.invoice_date);

// Range index for amounts
CREATE RANGE INDEX invoice_amount_range IF NOT EXISTS
FOR (i:Invoice) ON (i.total_amount);

CREATE RANGE INDEX mismatch_amount_range IF NOT EXISTS
FOR (m:Mismatch) ON (m.amount_difference);

// Range index for timestamps
CREATE RANGE INDEX mismatch_timestamp_range IF NOT EXISTS
FOR (m:Mismatch) ON (m.detected_at);

// ----------------------------------------------------------------------------
// 6. RELATIONSHIP INDEXES
// ----------------------------------------------------------------------------

// Index on relationship types for faster traversal
CREATE INDEX rel_issued_by_date IF NOT EXISTS
FOR ()-[r:ISSUED_BY]-() ON (r.created_at);

CREATE INDEX rel_received_by_date IF NOT EXISTS
FOR ()-[r:RECEIVED_BY]-() ON (r.created_at);

CREATE INDEX rel_matches_confidence IF NOT EXISTS
FOR ()-[r:MATCHES]-() ON (r.confidence_score);

// ----------------------------------------------------------------------------
// 7. VERIFY INDEXES
// ----------------------------------------------------------------------------

// Show all indexes
SHOW INDEXES;

// Show all constraints
SHOW CONSTRAINTS;

// ----------------------------------------------------------------------------
// 8. INDEX STATISTICS
// ----------------------------------------------------------------------------

// Get index statistics (run after data load)
CALL db.stats.retrieve('GRAPH COUNTS');

// ----------------------------------------------------------------------------
// 9. MAINTENANCE QUERIES
// ----------------------------------------------------------------------------

// Drop unused indexes (example - adjust as needed)
// DROP INDEX index_name IF EXISTS;

// Rebuild statistics (run periodically)
// CALL db.stats.clear();

// ----------------------------------------------------------------------------
// 10. PERFORMANCE MONITORING
// ----------------------------------------------------------------------------

// Check query performance
// PROFILE <your_query>
// EXPLAIN <your_query>

// Example:
// PROFILE MATCH (t:Taxpayer {gstin: '27AABCU9603R1ZM'})-[:RECEIVED_BY]-(i:Invoice)
// WHERE i.period = '032024'
// RETURN count(i);

// ----------------------------------------------------------------------------
// NOTES:
// - Run this script once during initial setup
// - Indexes are created asynchronously
// - Check index status with SHOW INDEXES
// - Composite indexes are used when all properties in the index are in the query
// - Full-text indexes require CALL db.index.fulltext.queryNodes()
// ----------------------------------------------------------------------------
