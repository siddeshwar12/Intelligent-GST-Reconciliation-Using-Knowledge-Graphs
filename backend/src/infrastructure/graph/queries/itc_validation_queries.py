"""
Multi-Hop ITC Validation Queries
Validates complete ITC chain: Buyer → Invoice → Vendor → GSTR-1 → GSTR-2B → GSTR-3B → Payment
"""

from typing import Dict, List, Optional


class ITCValidationQueries:
    """Cypher queries for multi-hop ITC chain validation."""
    
    @staticmethod
    def validate_complete_itc_chain(invoice_number: str, buyer_gstin: str) -> str:
        """
        Validate complete ITC chain for an invoice.
        
        Validates:
        1. Invoice exists in supplier's GSTR-1
        2. Invoice appears in buyer's GSTR-2B
        3. Amounts match between GSTR-1 and GSTR-2B
        4. GSTIN matches
        5. Returns filed properly
        6. Payment recorded
        
        Returns: Complete chain with validation status at each hop
        """
        return """
        MATCH path = (buyer:Taxpayer {gstin: $buyer_gstin})
          <-[:RECEIVED_BY]-(invoice:Invoice {invoice_number: $invoice_number})
          -[:ISSUED_BY]->(supplier:Taxpayer)
          
        OPTIONAL MATCH (invoice)-[:REPORTED_IN]->(gstr1:Return {return_type: 'GSTR-1'})
          -[:FILED_BY]->(supplier)
        
        OPTIONAL MATCH (invoice)-[:ENABLES_ITC]->(gstr2b_invoice:Invoice)
          -[:REPORTED_IN]->(gstr2b:Return {return_type: 'GSTR-2B'})
          -[:FILED_BY]->(buyer)
        
        OPTIONAL MATCH (buyer)-[:CLAIMS_ITC]->(invoice)
          -[:REPORTED_IN]->(gstr3b:Return {return_type: 'GSTR-3B'})
        
        OPTIONAL MATCH (gstr3b)-[:PAID_VIA]->(payment:Payment)
        
        RETURN 
          path,
          invoice,
          supplier,
          buyer,
          gstr1,
          gstr2b,
          gstr3b,
          payment,
          
          // Validation checks
          CASE WHEN gstr1 IS NOT NULL THEN true ELSE false END as in_gstr1,
          CASE WHEN gstr2b IS NOT NULL THEN true ELSE false END as in_gstr2b,
          CASE WHEN gstr3b IS NOT NULL THEN true ELSE false END as in_gstr3b,
          CASE WHEN payment IS NOT NULL THEN true ELSE false END as payment_made,
          
          // Amount validation
          CASE 
            WHEN gstr2b_invoice IS NOT NULL 
            THEN abs(invoice.total_amount - gstr2b_invoice.total_amount) < 1.0
            ELSE false 
          END as amount_matches,
          
          // GSTIN validation
          CASE 
            WHEN supplier.gstin = invoice.supplier_gstin 
            AND buyer.gstin = invoice.buyer_gstin
            THEN true 
            ELSE false 
          END as gstin_matches,
          
          // Overall ITC eligibility
          CASE 
            WHEN gstr1 IS NOT NULL 
            AND gstr2b IS NOT NULL 
            AND abs(invoice.total_amount - gstr2b_invoice.total_amount) < 1.0
            AND supplier.gstin = invoice.supplier_gstin
            THEN true 
            ELSE false 
          END as itc_eligible,
          
          // Chain completeness score (0-100)
          (
            (CASE WHEN gstr1 IS NOT NULL THEN 25 ELSE 0 END) +
            (CASE WHEN gstr2b IS NOT NULL THEN 25 ELSE 0 END) +
            (CASE WHEN gstr3b IS NOT NULL THEN 25 ELSE 0 END) +
            (CASE WHEN payment IS NOT NULL THEN 25 ELSE 0 END)
          ) as chain_completeness_score
        """
    
    @staticmethod
    def find_broken_itc_chains(buyer_gstin: str, period: str) -> str:
        """
        Find all invoices with broken ITC chains for a buyer in a period.
        
        Returns invoices where:
        - Invoice in GSTR-2B but not in supplier's GSTR-1
        - Amount mismatch between GSTR-1 and GSTR-2B
        - Missing payment
        """
        return """
        MATCH (buyer:Taxpayer {gstin: $buyer_gstin})
          <-[:RECEIVED_BY]-(invoice:Invoice)
          -[:REPORTED_IN]->(gstr2b:Return {
            return_type: 'GSTR-2B',
            return_period: $period
          })
        
        OPTIONAL MATCH (invoice)-[:ISSUED_BY]->(supplier:Taxpayer)
        OPTIONAL MATCH (invoice)-[:REPORTED_IN]->(gstr1:Return {return_type: 'GSTR-1'})
        OPTIONAL MATCH (invoice)-[:ENABLES_ITC]->(gstr2b_invoice:Invoice)
        
        WHERE 
          gstr1 IS NULL  // Not in supplier's GSTR-1
          OR abs(invoice.total_amount - gstr2b_invoice.total_amount) > 1.0  // Amount mismatch
        
        RETURN 
          invoice.invoice_number as invoice_number,
          invoice.total_amount as amount,
          supplier.gstin as supplier_gstin,
          supplier.name as supplier_name,
          
          CASE WHEN gstr1 IS NULL THEN 'MISSING_IN_GSTR1' 
               ELSE 'AMOUNT_MISMATCH' 
          END as issue_type,
          
          CASE WHEN gstr1 IS NULL THEN invoice.total_amount 
               ELSE abs(invoice.total_amount - gstr2b_invoice.total_amount) 
          END as impact_amount,
          
          'HIGH' as risk_level
        
        ORDER BY impact_amount DESC
        """
    
    @staticmethod
    def trace_itc_chain_multi_hop(invoice_number: str, max_hops: int = 5) -> str:
        """
        Trace ITC chain through multiple hops to detect circular trading.
        
        Example: Company A → Company B → Company C → Company A (circular)
        """
        return """
        MATCH path = (start_invoice:Invoice {invoice_number: $invoice_number})
          -[:ISSUED_BY]->(supplier:Taxpayer)
          -[:RECEIVED_BY*1..$max_hops]-(invoice:Invoice)
          -[:ISSUED_BY]->(end_supplier:Taxpayer)
        
        WHERE start_invoice.invoice_number <> invoice.invoice_number
        
        RETURN 
          path,
          nodes(path) as chain_nodes,
          relationships(path) as chain_relationships,
          length(path) as chain_length,
          
          // Detect circular trading
          CASE 
            WHEN start_invoice.supplier_gstin = end_supplier.gstin 
            THEN true 
            ELSE false 
          END as is_circular,
          
          // Calculate total chain value
          reduce(total = 0, inv IN [n IN nodes(path) WHERE n:Invoice | n] | 
            total + inv.total_amount
          ) as total_chain_value,
          
          // Extract all GSTINs in chain
          [n IN nodes(path) WHERE n:Taxpayer | n.gstin] as gstin_chain
        
        ORDER BY chain_length DESC
        """
    
    @staticmethod
    def validate_itc_eligibility_bulk(buyer_gstin: str, period: str) -> str:
        """
        Bulk validate ITC eligibility for all invoices in a period.
        
        Returns summary with eligible and ineligible invoices.
        """
        return """
        MATCH (buyer:Taxpayer {gstin: $buyer_gstin})
          <-[:RECEIVED_BY]-(invoice:Invoice)
          -[:REPORTED_IN]->(gstr2b:Return {
            return_type: 'GSTR-2B',
            return_period: $period
          })
        
        OPTIONAL MATCH (invoice)-[:ISSUED_BY]->(supplier:Taxpayer)
        OPTIONAL MATCH (invoice)-[:REPORTED_IN]->(gstr1:Return {return_type: 'GSTR-1'})
        OPTIONAL MATCH (invoice)-[:ENABLES_ITC]->(gstr2b_invoice:Invoice)
        
        WITH 
          invoice,
          supplier,
          gstr1,
          gstr2b_invoice,
          
          // Calculate eligibility
          CASE 
            WHEN gstr1 IS NOT NULL 
            AND gstr2b_invoice IS NOT NULL
            AND abs(invoice.total_amount - gstr2b_invoice.total_amount) < 1.0
            AND supplier.is_active = true
            THEN true 
            ELSE false 
          END as is_eligible,
          
          // Calculate ITC amount
          CASE 
            WHEN gstr1 IS NOT NULL AND gstr2b_invoice IS NOT NULL
            THEN invoice.cgst_amount + invoice.sgst_amount + invoice.igst_amount
            ELSE 0
          END as itc_amount
        
        RETURN 
          count(invoice) as total_invoices,
          sum(CASE WHEN is_eligible THEN 1 ELSE 0 END) as eligible_count,
          sum(CASE WHEN NOT is_eligible THEN 1 ELSE 0 END) as ineligible_count,
          sum(invoice.total_amount) as total_invoice_value,
          sum(itc_amount) as total_eligible_itc,
          sum(CASE WHEN NOT is_eligible THEN itc_amount ELSE 0 END) as blocked_itc,
          
          // Percentage metrics
          round(100.0 * sum(CASE WHEN is_eligible THEN 1 ELSE 0 END) / count(invoice), 2) as eligibility_rate,
          round(100.0 * sum(itc_amount) / sum(invoice.total_amount), 2) as itc_rate
        """
    
    @staticmethod
    def detect_fake_invoice_fraud(period: str, min_amount: float = 100000) -> str:
        """
        Detect potential fake invoices:
        - Invoice in GSTR-2B but supplier never filed GSTR-1
        - High-value invoices from inactive/blacklisted vendors
        - Invoices with no payment trail
        """
        return """
        MATCH (invoice:Invoice)-[:REPORTED_IN]->(gstr2b:Return {
          return_type: 'GSTR-2B',
          return_period: $period
        })
        WHERE invoice.total_amount >= $min_amount
        
        OPTIONAL MATCH (invoice)-[:ISSUED_BY]->(supplier:Taxpayer)
        OPTIONAL MATCH (supplier)-[:IS_VENDOR]->(vendor:Vendor)
        OPTIONAL MATCH (invoice)-[:REPORTED_IN]->(gstr1:Return {return_type: 'GSTR-1'})
        OPTIONAL MATCH (invoice)-[:REPORTED_IN]->(gstr3b:Return {return_type: 'GSTR-3B'})
          -[:PAID_VIA]->(payment:Payment)
        
        WHERE 
          gstr1 IS NULL  // Not in supplier's GSTR-1
          OR supplier.is_active = false  // Inactive supplier
          OR vendor.is_blacklisted = true  // Blacklisted vendor
          OR payment IS NULL  // No payment made
        
        RETURN 
          invoice.invoice_number as invoice_number,
          invoice.invoice_date as invoice_date,
          invoice.total_amount as amount,
          supplier.gstin as supplier_gstin,
          supplier.name as supplier_name,
          supplier.is_active as supplier_active,
          vendor.is_blacklisted as is_blacklisted,
          vendor.compliance_score as compliance_score,
          
          // Fraud indicators
          CASE WHEN gstr1 IS NULL THEN 1 ELSE 0 END as missing_gstr1,
          CASE WHEN supplier.is_active = false THEN 1 ELSE 0 END as inactive_supplier,
          CASE WHEN vendor.is_blacklisted = true THEN 1 ELSE 0 END as blacklisted,
          CASE WHEN payment IS NULL THEN 1 ELSE 0 END as no_payment,
          
          // Fraud score (0-4)
          (
            (CASE WHEN gstr1 IS NULL THEN 1 ELSE 0 END) +
            (CASE WHEN supplier.is_active = false THEN 1 ELSE 0 END) +
            (CASE WHEN vendor.is_blacklisted = true THEN 1 ELSE 0 END) +
            (CASE WHEN payment IS NULL THEN 1 ELSE 0 END)
          ) as fraud_score,
          
          'CRITICAL' as risk_level
        
        HAVING fraud_score >= 2
        ORDER BY fraud_score DESC, amount DESC
        """
    
    @staticmethod
    def find_missing_trader_fraud(period: str) -> str:
        """
        Detect missing trader fraud:
        - Invoices where supplier exists in chain but never filed returns
        - High ITC claims from vendors with no outward supply
        """
        return """
        MATCH (buyer:Taxpayer)<-[:RECEIVED_BY]-(invoice:Invoice)
          -[:ISSUED_BY]->(supplier:Taxpayer)
        
        WHERE invoice.source_period = $period
        
        OPTIONAL MATCH (supplier)-[:FILED_BY]-(gstr1:Return {
          return_type: 'GSTR-1',
          return_period: $period
        })
        
        OPTIONAL MATCH (supplier)-[:FILED_BY]-(gstr3b:Return {
          return_type: 'GSTR-3B',
          return_period: $period
        })
        
        WHERE gstr1 IS NULL AND gstr3b IS NULL  // Supplier never filed
        
        WITH 
          supplier,
          count(invoice) as invoice_count,
          sum(invoice.total_amount) as total_value,
          sum(invoice.cgst_amount + invoice.sgst_amount + invoice.igst_amount) as total_itc
        
        WHERE invoice_count >= 3 OR total_value >= 500000  // Significant activity
        
        RETURN 
          supplier.gstin as supplier_gstin,
          supplier.name as supplier_name,
          invoice_count,
          total_value,
          total_itc,
          'MISSING_TRADER_FRAUD' as fraud_type,
          'CRITICAL' as risk_level
        
        ORDER BY total_itc DESC
        """
    
    @staticmethod
    def calculate_itc_overclaim(buyer_gstin: str, period: str) -> str:
        """
        Calculate potential ITC overclaim by comparing:
        - ITC claimed in GSTR-3B
        - ITC eligible based on GSTR-2B validation
        """
        return """
        // Get ITC claimed in GSTR-3B
        MATCH (buyer:Taxpayer {gstin: $buyer_gstin})
          -[:FILED_BY]-(gstr3b:Return {
            return_type: 'GSTR-3B',
            return_period: $period
          })
        
        WITH buyer, gstr3b.total_itc_claimed as claimed_itc
        
        // Calculate eligible ITC from validated invoices
        MATCH (buyer)<-[:RECEIVED_BY]-(invoice:Invoice)
          -[:REPORTED_IN]->(gstr2b:Return {
            return_type: 'GSTR-2B',
            return_period: $period
          })
        
        OPTIONAL MATCH (invoice)-[:ISSUED_BY]->(supplier:Taxpayer)
        OPTIONAL MATCH (invoice)-[:REPORTED_IN]->(gstr1:Return {return_type: 'GSTR-1'})
        OPTIONAL MATCH (invoice)-[:ENABLES_ITC]->(gstr2b_invoice:Invoice)
        
        WITH 
          buyer,
          claimed_itc,
          sum(
            CASE 
              WHEN gstr1 IS NOT NULL 
              AND gstr2b_invoice IS NOT NULL
              AND abs(invoice.total_amount - gstr2b_invoice.total_amount) < 1.0
              THEN invoice.cgst_amount + invoice.sgst_amount + invoice.igst_amount
              ELSE 0
            END
          ) as eligible_itc
        
        RETURN 
          buyer.gstin as gstin,
          buyer.name as taxpayer_name,
          claimed_itc,
          eligible_itc,
          claimed_itc - eligible_itc as overclaim_amount,
          round(100.0 * (claimed_itc - eligible_itc) / claimed_itc, 2) as overclaim_percent,
          
          CASE 
            WHEN claimed_itc - eligible_itc > eligible_itc * 0.1 THEN 'CRITICAL'
            WHEN claimed_itc - eligible_itc > eligible_itc * 0.05 THEN 'HIGH'
            WHEN claimed_itc - eligible_itc > 0 THEN 'MEDIUM'
            ELSE 'LOW'
          END as risk_level
        """


# Export query class
__all__ = ['ITCValidationQueries']
