"""
GST Reconciliation Service with Multi-hop Cypher Traversal.

This service validates ITC chains using graph traversal and detects various
types of mismatches in GST data.

Architecture: Service layer only, classification logic kept separate.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph.neo4j_connection import get_connection, Neo4jConnectionError


class ITCValidationResult:
    """Result of ITC chain validation."""
    
    def __init__(
        self,
        is_valid: bool,
        chain_length: int,
        missing_links: List[str] = None,
        validation_details: Dict[str, Any] = None
    ):
        self.is_valid = is_valid
        self.chain_length = chain_length
        self.missing_links = missing_links or []
        self.validation_details = validation_details or {}
        self.validated_at = datetime.utcnow()


class MismatchResult:
    """Result of mismatch detection."""
    
    def __init__(
        self,
        mismatch_type: str,
        severity: str,
        description: str,
        source_invoice: Dict[str, Any],
        target_invoice: Optional[Dict[str, Any]] = None,
        amount_difference: float = 0.0,
        percentage_variance: float = 0.0,
        details: Dict[str, Any] = None
    ):
        self.mismatch_type = mismatch_type
        self.severity = severity
        self.description = description
        self.source_invoice = source_invoice
        self.target_invoice = target_invoice
        self.amount_difference = amount_difference
        self.percentage_variance = percentage_variance
        self.details = details or {}
        self.detected_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "mismatch_type": self.mismatch_type,
            "severity": self.severity,
            "description": self.description,
            "source_invoice": self.source_invoice,
            "target_invoice": self.target_invoice,
            "amount_difference": self.amount_difference,
            "percentage_variance": self.percentage_variance,
            "details": self.details,
            "detected_at": self.detected_at.isoformat()
        }


class ReconciliationResult:
    """Complete reconciliation result."""
    
    def __init__(self):
        self.reconciliation_id = str(uuid4())
        self.started_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.taxpayer_gstin: Optional[str] = None
        self.period: Optional[str] = None
        self.total_invoices_processed = 0
        self.itc_validations: List[ITCValidationResult] = []
        self.mismatches: List[MismatchResult] = []
        self.summary: Dict[str, Any] = {}
    
    def complete(self):
        """Mark reconciliation as complete."""
        self.completed_at = datetime.utcnow()
        self._generate_summary()
    
    def _generate_summary(self):
        """Generate reconciliation summary."""
        self.summary = {
            "total_invoices": self.total_invoices_processed,
            "total_mismatches": len(self.mismatches),
            "mismatch_types": self._count_mismatch_types(),
            "severity_distribution": self._count_severity_distribution(),
            "itc_validation_stats": self._get_itc_stats(),
            "processing_time_seconds": (
                (self.completed_at - self.started_at).total_seconds()
                if self.completed_at else 0
            )
        }
    
    def _count_mismatch_types(self) -> Dict[str, int]:
        """Count mismatches by type."""
        counts = {}
        for mismatch in self.mismatches:
            counts[mismatch.mismatch_type] = counts.get(mismatch.mismatch_type, 0) + 1
        return counts
    
    def _count_severity_distribution(self) -> Dict[str, int]:
        """Count mismatches by severity."""
        counts = {}
        for mismatch in self.mismatches:
            counts[mismatch.severity] = counts.get(mismatch.severity, 0) + 1
        return counts
    
    def _get_itc_stats(self) -> Dict[str, Any]:
        """Get ITC validation statistics."""
        if not self.itc_validations:
            return {}
        
        valid_chains = sum(1 for v in self.itc_validations if v.is_valid)
        avg_chain_length = sum(v.chain_length for v in self.itc_validations) / len(self.itc_validations)
        
        return {
            "total_validations": len(self.itc_validations),
            "valid_chains": valid_chains,
            "invalid_chains": len(self.itc_validations) - valid_chains,
            "average_chain_length": round(avg_chain_length, 2)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "reconciliation_id": self.reconciliation_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "taxpayer_gstin": self.taxpayer_gstin,
            "period": self.period,
            "total_invoices_processed": self.total_invoices_processed,
            "mismatches": [m.to_dict() for m in self.mismatches],
            "summary": self.summary
        }


class GSTReconciliationService:
    """
    GST Reconciliation Service using multi-hop Cypher traversal.
    
    Validates ITC chains and detects mismatches across GST data sources.
    """
    
    def __init__(self):
        """Initialize reconciliation service."""
        try:
            self.connection = get_connection()
            print("✓ Connected to Neo4j for reconciliation")
        except Neo4jConnectionError as e:
            print(f"✗ Failed to connect to Neo4j: {e}")
            raise
        
        # Configuration
        self.amount_tolerance_percent = 5.0  # 5% tolerance for amount mismatches
        self.date_tolerance_days = 30  # 30 days tolerance for date mismatches
        self.min_amount_threshold = 1000.0  # Minimum amount for processing
    
    def reconcile_taxpayer(
        self,
        taxpayer_gstin: str,
        period: str,
        validate_itc_chains: bool = True
    ) -> ReconciliationResult:
        """
        Reconcile all invoices for a taxpayer in a given period.
        
        Args:
            taxpayer_gstin: Taxpayer GSTIN
            period: Period in format MMYYYY (e.g., "032024")
            validate_itc_chains: Whether to validate ITC chains
            
        Returns:
            ReconciliationResult with all findings
        """
        result = ReconciliationResult()
        result.taxpayer_gstin = taxpayer_gstin
        result.period = period
        
        try:
            print(f"\n=== Starting Reconciliation ===")
            print(f"Taxpayer: {taxpayer_gstin}")
            print(f"Period: {period}")
            
            # Step 1: Get all purchase register invoices
            purchase_invoices = self._get_purchase_register_invoices(taxpayer_gstin, period)
            result.total_invoices_processed = len(purchase_invoices)
            
            print(f"Found {len(purchase_invoices)} purchase register invoices")
            
            # Step 2: For each invoice, validate ITC chain and detect mismatches
            for invoice in purchase_invoices:
                # Validate ITC chain if requested
                if validate_itc_chains:
                    itc_validation = self._validate_itc_chain(invoice)
                    result.itc_validations.append(itc_validation)
                
                # Detect mismatches
                mismatches = self._detect_invoice_mismatches(invoice, period)
                result.mismatches.extend(mismatches)
            
            # Step 3: Find missing invoices
            missing_mismatches = self._find_missing_invoices(taxpayer_gstin, period)
            result.mismatches.extend(missing_mismatches)
            
            result.complete()
            
            print(f"\n=== Reconciliation Complete ===")
            print(f"Processed: {result.total_invoices_processed} invoices")
            print(f"Mismatches: {len(result.mismatches)}")
            print(f"ITC Validations: {len(result.itc_validations)}")
            
            return result
            
        except Exception as e:
            print(f"✗ Reconciliation failed: {e}")
            raise
    
    def _get_purchase_register_invoices(
        self,
        taxpayer_gstin: str,
        period: str
    ) -> List[Dict[str, Any]]:
        """
        Get all purchase register invoices for taxpayer and period.
        
        Args:
            taxpayer_gstin: Taxpayer GSTIN
            period: Period in MMYYYY format
            
        Returns:
            List of invoice dictionaries
        """
        query = """
        MATCH (buyer:Taxpayer {gstin: $taxpayer_gstin})-[:RECEIVED_BY]-(i:Invoice)
        WHERE i.source_type = 'PURCHASE_REGISTER'
        AND i.source_period = $period
        AND i.total_amount >= $min_amount
        OPTIONAL MATCH (i)-[:ISSUED_BY]->(supplier:Taxpayer)
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
        """
        
        try:
            records = self.connection.execute_query(
                query,
                {
                    "taxpayer_gstin": taxpayer_gstin,
                    "period": period,
                    "min_amount": self.min_amount_threshold
                }
            )
            
            invoices = []
            for record in records:
                invoice = dict(record["invoice"])
                invoice["supplier_name"] = record["supplier_name"]
                invoices.append(invoice)
            
            return invoices
            
        except Exception as e:
            print(f"✗ Failed to get purchase register invoices: {e}")
            return []
    
    def _validate_itc_chain(self, invoice: Dict[str, Any]) -> ITCValidationResult:
        """
        Validate ITC chain using multi-hop traversal.
        
        Chain: Buyer → Invoice → Vendor → GSTR-1 → GSTR-2B
        
        Args:
            invoice: Invoice dictionary
            
        Returns:
            ITCValidationResult
        """
        query = """
        // Start from the purchase register invoice
        MATCH (buyer:Taxpayer {gstin: $recipient_gstin})-[:RECEIVED_BY]-(pr_invoice:Invoice {id: $invoice_id})
        WHERE pr_invoice.source_type = 'PURCHASE_REGISTER'
        
        // Multi-hop traversal to validate ITC chain
        OPTIONAL MATCH (pr_invoice)-[:ISSUED_BY]->(supplier:Taxpayer {gstin: $supplier_gstin})
        
        // Find corresponding GSTR-1 entry (supplier's outward supply)
        OPTIONAL MATCH (supplier)-[:ISSUED_BY]-(gstr1_invoice:Invoice)
        WHERE gstr1_invoice.source_type = 'GSTR-1'
        AND gstr1_invoice.invoice_number = pr_invoice.invoice_number
        AND gstr1_invoice.recipient_gstin = pr_invoice.recipient_gstin
        AND abs(duration.between(gstr1_invoice.invoice_date, pr_invoice.invoice_date).days) <= $date_tolerance
        
        // Find corresponding GSTR-2B entry (buyer's inward supply)
        OPTIONAL MATCH (buyer)-[:RECEIVED_BY]-(gstr2b_invoice:Invoice)
        WHERE gstr2b_invoice.source_type = 'GSTR-2B'
        AND gstr2b_invoice.invoice_number = pr_invoice.invoice_number
        AND gstr2b_invoice.supplier_gstin = pr_invoice.supplier_gstin
        AND abs(duration.between(gstr2b_invoice.invoice_date, pr_invoice.invoice_date).days) <= $date_tolerance
        
        // Check for matching relationships
        OPTIONAL MATCH (pr_invoice)-[:MATCHES]-(gstr2b_invoice)
        OPTIONAL MATCH (gstr1_invoice)-[:MATCHES]-(gstr2b_invoice)
        
        RETURN 
            pr_invoice,
            supplier,
            gstr1_invoice,
            gstr2b_invoice,
            CASE 
                WHEN supplier IS NOT NULL THEN 1 ELSE 0 
            END +
            CASE 
                WHEN gstr1_invoice IS NOT NULL THEN 1 ELSE 0 
            END +
            CASE 
                WHEN gstr2b_invoice IS NOT NULL THEN 1 ELSE 0 
            END as chain_length,
            
            // Validation flags
            supplier IS NOT NULL as has_supplier,
            gstr1_invoice IS NOT NULL as has_gstr1,
            gstr2b_invoice IS NOT NULL as has_gstr2b,
            
            // Amount validations
            CASE 
                WHEN gstr1_invoice IS NOT NULL 
                THEN abs(pr_invoice.total_amount - gstr1_invoice.total_amount) <= (pr_invoice.total_amount * $amount_tolerance / 100)
                ELSE false 
            END as gstr1_amount_match,
            
            CASE 
                WHEN gstr2b_invoice IS NOT NULL 
                THEN abs(pr_invoice.total_amount - gstr2b_invoice.total_amount) <= (pr_invoice.total_amount * $amount_tolerance / 100)
                ELSE false 
            END as gstr2b_amount_match
        """
        
        try:
            records = self.connection.execute_query(
                query,
                {
                    "invoice_id": invoice["id"],
                    "recipient_gstin": invoice["recipient_gstin"],
                    "supplier_gstin": invoice["supplier_gstin"],
                    "date_tolerance": self.date_tolerance_days,
                    "amount_tolerance": self.amount_tolerance_percent
                }
            )
            
            if not records:
                return ITCValidationResult(
                    is_valid=False,
                    chain_length=0,
                    missing_links=["supplier", "gstr1", "gstr2b"]
                )
            
            record = records[0]
            chain_length = record["chain_length"]
            
            # Determine missing links
            missing_links = []
            if not record["has_supplier"]:
                missing_links.append("supplier")
            if not record["has_gstr1"]:
                missing_links.append("gstr1")
            if not record["has_gstr2b"]:
                missing_links.append("gstr2b")
            
            # Chain is valid if all links exist and amounts match
            is_valid = (
                record["has_supplier"] and
                record["has_gstr1"] and
                record["has_gstr2b"] and
                record["gstr1_amount_match"] and
                record["gstr2b_amount_match"]
            )
            
            validation_details = {
                "has_supplier": record["has_supplier"],
                "has_gstr1": record["has_gstr1"],
                "has_gstr2b": record["has_gstr2b"],
                "gstr1_amount_match": record["gstr1_amount_match"],
                "gstr2b_amount_match": record["gstr2b_amount_match"]
            }
            
            return ITCValidationResult(
                is_valid=is_valid,
                chain_length=chain_length,
                missing_links=missing_links,
                validation_details=validation_details
            )
            
        except Exception as e:
            print(f"✗ ITC validation failed for invoice {invoice['invoice_number']}: {e}")
            return ITCValidationResult(
                is_valid=False,
                chain_length=0,
                missing_links=["error"]
            )
    
    def _detect_invoice_mismatches(
        self,
        invoice: Dict[str, Any],
        period: str
    ) -> List[MismatchResult]:
        """
        Detect mismatches for a specific invoice.
        
        Args:
            invoice: Purchase register invoice
            period: Period in MMYYYY format
            
        Returns:
            List of MismatchResult objects
        """
        mismatches = []
        
        # Find potential matches in GSTR-2B
        gstr2b_matches = self._find_gstr2b_matches(invoice)
        
        if not gstr2b_matches:
            # Missing in GSTR-2B
            mismatch = MismatchResult(
                mismatch_type="MISSING_IN_GSTR2B",
                severity="HIGH",
                description=f"Invoice {invoice['invoice_number']} missing in GSTR-2B",
                source_invoice=invoice,
                amount_difference=invoice["total_amount"],
                details={
                    "potential_itc_loss": invoice["total_tax"],
                    "supplier_gstin": invoice["supplier_gstin"]
                }
            )
            mismatches.append(mismatch)
        else:
            # Check each match for specific mismatches
            for gstr2b_invoice in gstr2b_matches:
                invoice_mismatches = self._compare_invoices(invoice, gstr2b_invoice)
                mismatches.extend(invoice_mismatches)
        
        return mismatches
    
    def _find_gstr2b_matches(self, invoice: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find potential GSTR-2B matches for a purchase register invoice.
        
        Args:
            invoice: Purchase register invoice
            
        Returns:
            List of potential GSTR-2B matches
        """
        query = """
        MATCH (gstr2b:Invoice)
        WHERE gstr2b.source_type = 'GSTR-2B'
        AND (
            // Exact match criteria
            (gstr2b.invoice_number = $invoice_number 
             AND gstr2b.supplier_gstin = $supplier_gstin)
            OR
            // Fuzzy match criteria
            (gstr2b.supplier_gstin = $supplier_gstin
             AND abs(gstr2b.total_amount - $total_amount) <= ($total_amount * $amount_tolerance / 100)
             AND abs(duration.between(gstr2b.invoice_date, date($invoice_date)).days) <= $date_tolerance)
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
        } as invoice
        ORDER BY 
            CASE WHEN gstr2b.invoice_number = $invoice_number THEN 0 ELSE 1 END,
            abs(gstr2b.total_amount - $total_amount)
        LIMIT 5
        """
        
        try:
            records = self.connection.execute_query(
                query,
                {
                    "invoice_number": invoice["invoice_number"],
                    "supplier_gstin": invoice["supplier_gstin"],
                    "total_amount": invoice["total_amount"],
                    "invoice_date": invoice["invoice_date"],
                    "amount_tolerance": self.amount_tolerance_percent,
                    "date_tolerance": self.date_tolerance_days
                }
            )
            
            return [dict(record["invoice"]) for record in records]
            
        except Exception as e:
            print(f"✗ Failed to find GSTR-2B matches: {e}")
            return []
    
    def _compare_invoices(
        self,
        source_invoice: Dict[str, Any],
        target_invoice: Dict[str, Any]
    ) -> List[MismatchResult]:
        """
        Compare two invoices and detect specific mismatches.
        
        Args:
            source_invoice: Source invoice (e.g., purchase register)
            target_invoice: Target invoice (e.g., GSTR-2B)
            
        Returns:
            List of MismatchResult objects
        """
        mismatches = []
        
        # Amount mismatch
        amount_diff = abs(source_invoice["total_amount"] - target_invoice["total_amount"])
        if amount_diff > 0:
            percentage_variance = (amount_diff / source_invoice["total_amount"]) * 100
            
            if percentage_variance > self.amount_tolerance_percent:
                severity = "CRITICAL" if percentage_variance > 20 else "HIGH" if percentage_variance > 10 else "MEDIUM"
                
                mismatch = MismatchResult(
                    mismatch_type="AMOUNT_MISMATCH",
                    severity=severity,
                    description=f"Amount mismatch: PR={source_invoice['total_amount']}, GSTR-2B={target_invoice['total_amount']}",
                    source_invoice=source_invoice,
                    target_invoice=target_invoice,
                    amount_difference=amount_diff,
                    percentage_variance=percentage_variance,
                    details={
                        "source_amount": source_invoice["total_amount"],
                        "target_amount": target_invoice["total_amount"]
                    }
                )
                mismatches.append(mismatch)
        
        # Date mismatch
        source_date = datetime.fromisoformat(source_invoice["invoice_date"].replace('Z', '+00:00'))
        target_date = datetime.fromisoformat(target_invoice["invoice_date"].replace('Z', '+00:00'))
        date_diff = abs((source_date - target_date).days)
        
        if date_diff > self.date_tolerance_days:
            severity = "HIGH" if date_diff > 90 else "MEDIUM"
            
            mismatch = MismatchResult(
                mismatch_type="DATE_MISMATCH",
                severity=severity,
                description=f"Date mismatch: {date_diff} days difference",
                source_invoice=source_invoice,
                target_invoice=target_invoice,
                details={
                    "source_date": source_invoice["invoice_date"],
                    "target_date": target_invoice["invoice_date"],
                    "days_difference": date_diff
                }
            )
            mismatches.append(mismatch)
        
        # GSTIN mismatch
        if source_invoice["supplier_gstin"] != target_invoice["supplier_gstin"]:
            mismatch = MismatchResult(
                mismatch_type="GSTIN_MISMATCH",
                severity="CRITICAL",
                description="Supplier GSTIN mismatch",
                source_invoice=source_invoice,
                target_invoice=target_invoice,
                details={
                    "source_gstin": source_invoice["supplier_gstin"],
                    "target_gstin": target_invoice["supplier_gstin"]
                }
            )
            mismatches.append(mismatch)
        
        # Tax amount mismatch
        source_tax = source_invoice.get("total_tax", 0)
        target_tax = target_invoice.get("total_tax", 0)
        tax_diff = abs(source_tax - target_tax)
        
        if tax_diff > 0 and source_tax > 0:
            tax_variance = (tax_diff / source_tax) * 100
            
            if tax_variance > self.amount_tolerance_percent:
                severity = "HIGH" if tax_variance > 10 else "MEDIUM"
                
                mismatch = MismatchResult(
                    mismatch_type="TAX_AMOUNT_MISMATCH",
                    severity=severity,
                    description=f"Tax amount mismatch: {tax_variance:.2f}% variance",
                    source_invoice=source_invoice,
                    target_invoice=target_invoice,
                    amount_difference=tax_diff,
                    percentage_variance=tax_variance,
                    details={
                        "source_tax": source_tax,
                        "target_tax": target_tax
                    }
                )
                mismatches.append(mismatch)
        
        return mismatches
    
    def _find_missing_invoices(
        self,
        taxpayer_gstin: str,
        period: str
    ) -> List[MismatchResult]:
        """
        Find invoices missing in purchase register but present in GSTR-2B.
        
        Args:
            taxpayer_gstin: Taxpayer GSTIN
            period: Period in MMYYYY format
            
        Returns:
            List of MismatchResult for missing invoices
        """
        query = """
        MATCH (buyer:Taxpayer {gstin: $taxpayer_gstin})-[:RECEIVED_BY]-(gstr2b:Invoice)
        WHERE gstr2b.source_type = 'GSTR-2B'
        AND gstr2b.source_period = $period
        AND NOT EXISTS {
            MATCH (buyer)-[:RECEIVED_BY]-(pr:Invoice)
            WHERE pr.source_type = 'PURCHASE_REGISTER'
            AND pr.invoice_number = gstr2b.invoice_number
            AND pr.supplier_gstin = gstr2b.supplier_gstin
        }
        RETURN gstr2b {
            .id,
            .invoice_number,
            .invoice_date,
            .supplier_gstin,
            .total_amount,
            .total_tax,
            .source_type
        } as invoice
        ORDER BY gstr2b.total_amount DESC
        """
        
        try:
            records = self.connection.execute_query(
                query,
                {
                    "taxpayer_gstin": taxpayer_gstin,
                    "period": period
                }
            )
            
            mismatches = []
            for record in records:
                invoice = dict(record["invoice"])
                
                mismatch = MismatchResult(
                    mismatch_type="MISSING_IN_PURCHASE_REGISTER",
                    severity="MEDIUM",
                    description=f"Invoice {invoice['invoice_number']} in GSTR-2B but missing in Purchase Register",
                    source_invoice=invoice,
                    amount_difference=invoice["total_amount"],
                    details={
                        "potential_duplicate_itc": invoice["total_tax"],
                        "supplier_gstin": invoice["supplier_gstin"]
                    }
                )
                mismatches.append(mismatch)
            
            return mismatches
            
        except Exception as e:
            print(f"✗ Failed to find missing invoices: {e}")
            return []
    
    def get_reconciliation_summary(
        self,
        taxpayer_gstin: str,
        period: str
    ) -> Dict[str, Any]:
        """
        Get high-level reconciliation summary without full processing.
        
        Args:
            taxpayer_gstin: Taxpayer GSTIN
            period: Period in MMYYYY format
            
        Returns:
            Summary dictionary
        """
        query = """
        MATCH (buyer:Taxpayer {gstin: $taxpayer_gstin})
        
        // Count purchase register invoices
        OPTIONAL MATCH (buyer)-[:RECEIVED_BY]-(pr:Invoice)
        WHERE pr.source_type = 'PURCHASE_REGISTER' AND pr.source_period = $period
        WITH buyer, count(pr) as pr_count, sum(pr.total_amount) as pr_amount
        
        // Count GSTR-2B invoices
        OPTIONAL MATCH (buyer)-[:RECEIVED_BY]-(gstr2b:Invoice)
        WHERE gstr2b.source_type = 'GSTR-2B' AND gstr2b.source_period = $period
        WITH buyer, pr_count, pr_amount, count(gstr2b) as gstr2b_count, sum(gstr2b.total_amount) as gstr2b_amount
        
        // Count matched invoices
        OPTIONAL MATCH (buyer)-[:RECEIVED_BY]-(pr:Invoice)-[:MATCHES]-(gstr2b:Invoice)
        WHERE pr.source_type = 'PURCHASE_REGISTER' 
        AND gstr2b.source_type = 'GSTR-2B'
        AND pr.source_period = $period
        
        RETURN {
            taxpayer_gstin: $taxpayer_gstin,
            period: $period,
            purchase_register: {
                count: pr_count,
                total_amount: coalesce(pr_amount, 0)
            },
            gstr2b: {
                count: gstr2b_count,
                total_amount: coalesce(gstr2b_amount, 0)
            },
            matched_invoices: count(pr),
            potential_mismatches: pr_count - count(pr),
            amount_variance: coalesce(pr_amount, 0) - coalesce(gstr2b_amount, 0)
        } as summary
        """
        
        try:
            records = self.connection.execute_query(
                query,
                {
                    "taxpayer_gstin": taxpayer_gstin,
                    "period": period
                }
            )
            
            if records:
                return dict(records[0]["summary"])
            else:
                return {
                    "taxpayer_gstin": taxpayer_gstin,
                    "period": period,
                    "error": "No data found"
                }
                
        except Exception as e:
            return {
                "taxpayer_gstin": taxpayer_gstin,
                "period": period,
                "error": str(e)
            }


def main():
    """Example usage of the reconciliation service."""
    try:
        service = GSTReconciliationService()
        
        # Example: Reconcile a specific taxpayer
        taxpayer_gstin = "27AABCU9603R1ZM"  # Example GSTIN
        period = "032024"
        
        print(f"Starting reconciliation for {taxpayer_gstin}, period {period}")
        
        # Get summary first
        summary = service.get_reconciliation_summary(taxpayer_gstin, period)
        print(f"\nSummary: {json.dumps(summary, indent=2)}")
        
        # Run full reconciliation
        result = service.reconcile_taxpayer(
            taxpayer_gstin=taxpayer_gstin,
            period=period,
            validate_itc_chains=True
        )
        
        # Output results
        print(f"\n=== RECONCILIATION RESULTS ===")
        print(f"Reconciliation ID: {result.reconciliation_id}")
        print(f"Total Invoices: {result.total_invoices_processed}")
        print(f"Total Mismatches: {len(result.mismatches)}")
        print(f"ITC Validations: {len(result.itc_validations)}")
        
        # Show mismatch breakdown
        if result.mismatches:
            print(f"\n=== MISMATCH BREAKDOWN ===")
            for mismatch_type, count in result.summary["mismatch_types"].items():
                print(f"{mismatch_type}: {count}")
        
        # Export to JSON
        output_file = f"reconciliation_{taxpayer_gstin}_{period}.json"
        with open(output_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        print(f"\nResults exported to: {output_file}")
        
    except Exception as e:
        print(f"✗ Reconciliation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()