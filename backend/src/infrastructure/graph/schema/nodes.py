"""
Neo4j Knowledge Graph Schema - Node Definitions
Optimized for GST Reconciliation and ITC Validation
"""

from enum import Enum
from typing import Dict, List


class NodeType(str, Enum):
    """Node types in the GST Knowledge Graph."""
    
    TAXPAYER = "Taxpayer"
    GSTIN = "GSTIN"
    INVOICE = "Invoice"
    LINE_ITEM = "LineItem"
    RETURN = "Return"
    PAYMENT = "Payment"
    VENDOR = "Vendor"
    TAX_COMPONENT = "TaxComponent"
    MISMATCH = "Mismatch"


# ============================================================================
# NODE PROPERTY SCHEMAS
# ============================================================================

TAXPAYER_PROPERTIES = {
    "id": "STRING",                    # UUID
    "gstin": "STRING",                 # Primary GSTIN (indexed)
    "legal_name": "STRING",            # Legal business name
    "trade_name": "STRING",            # Trade name (optional)
    "taxpayer_type": "STRING",         # Regular, Composition, ISD, etc.
    "registration_date": "DATE",       # GST registration date
    "state_code": "STRING",            # 2-digit state code (indexed)
    "is_active": "BOOLEAN",            # Active status
    "pan": "STRING",                   # PAN number
    "business_type": "STRING",         # Manufacturer, Trader, Service Provider
    "created_at": "DATETIME",
    "updated_at": "DATETIME"
}

GSTIN_PROPERTIES = {
    "gstin": "STRING",                 # 15-character GSTIN (unique)
    "state_code": "STRING",            # First 2 digits
    "pan": "STRING",                   # Characters 3-12
    "entity_number": "STRING",         # 13th character
    "checksum": "STRING",              # 15th character
    "is_valid": "BOOLEAN",             # Validation status
    "created_at": "DATETIME"
}

INVOICE_PROPERTIES = {
    "id": "STRING",                    # UUID
    "invoice_number": "STRING",        # Invoice number (indexed)
    "invoice_date": "DATE",            # Invoice date (indexed)
    "financial_year": "STRING",        # FY: 2023-24 (indexed)
    
    # Amounts
    "taxable_value": "FLOAT",          # Taxable amount
    "cgst_amount": "FLOAT",            # CGST amount
    "sgst_amount": "FLOAT",            # SGST amount
    "igst_amount": "FLOAT",            # IGST amount
    "cess_amount": "FLOAT",            # Cess amount
    "total_tax": "FLOAT",              # Total tax (indexed for sorting)
    "total_amount": "FLOAT",           # Total invoice amount
    
    # e-Invoice details
    "irn": "STRING",                   # Invoice Reference Number (64 chars)
    "irn_date": "DATETIME",            # IRN generation date
    "ack_number": "STRING",            # Acknowledgement number
    
    # Location and type
    "place_of_supply": "STRING",       # State code
    "pos_state_code": "STRING",        # Place of supply state
    "reverse_charge": "BOOLEAN",       # Reverse charge applicable
    "invoice_type": "STRING",          # B2B, B2C, Export, Import (indexed)
    "document_type": "STRING",         # INV, CRN, DBN
    
    # Source tracking (critical for reconciliation)
    "source_type": "STRING",           # GSTR-1, GSTR-2B, PURCHASE_REGISTER, E_INVOICE (indexed)
    "source_period": "STRING",         # MMYYYY format (indexed)
    "filing_status": "STRING",         # FILED, NOT_FILED, AMENDED
    
    # Reconciliation metadata
    "is_matched": "BOOLEAN",           # Matched status (indexed)
    "match_confidence": "FLOAT",       # Match confidence score (0-1)
    "has_mismatch": "BOOLEAN",         # Has mismatch flag (indexed)
    "itc_eligible": "BOOLEAN",         # ITC eligibility (indexed)
    
    # Timestamps
    "created_at": "DATETIME",
    "updated_at": "DATETIME",
    "reconciled_at": "DATETIME"
}

LINE_ITEM_PROPERTIES = {
    "id": "STRING",                    # UUID
    "item_number": "INTEGER",          # Line item sequence
    "description": "STRING",           # Item description
    "hsn_code": "STRING",              # HSN/SAC code (indexed)
    
    # Quantity and rate
    "quantity": "FLOAT",               # Quantity
    "unit_of_measurement": "STRING",   # UOM (NOS, KGS, etc.)
    "rate": "FLOAT",                   # Rate per unit
    "discount": "FLOAT",               # Discount amount
    
    # Amounts
    "taxable_value": "FLOAT",          # Taxable value
    "cgst_rate": "FLOAT",              # CGST rate %
    "sgst_rate": "FLOAT",              # SGST rate %
    "igst_rate": "FLOAT",              # IGST rate %
    "cess_rate": "FLOAT",              # Cess rate %
    "total_tax_rate": "FLOAT",         # Total GST rate (indexed)
    
    "cgst_amount": "FLOAT",
    "sgst_amount": "FLOAT",
    "igst_amount": "FLOAT",
    "cess_amount": "FLOAT",
    "total_amount": "FLOAT",
    
    "created_at": "DATETIME"
}

RETURN_PROPERTIES = {
    "id": "STRING",                    # UUID
    "return_type": "STRING",           # GSTR-1, GSTR-2B, GSTR-3B, GSTR-9 (indexed)
    "return_period": "STRING",         # MMYYYY format (indexed)
    "financial_year": "STRING",        # FY: 2023-24 (indexed)
    "quarter": "STRING",               # Q1, Q2, Q3, Q4 (for quarterly returns)
    
    # Filing details
    "filing_date": "DATE",             # Actual filing date
    "due_date": "DATE",                # Due date
    "status": "STRING",                # FILED, NOT_FILED, LATE_FILED (indexed)
    "arn": "STRING",                   # Acknowledgement Reference Number
    "is_late": "BOOLEAN",              # Late filing flag
    "days_late": "INTEGER",            # Days late (if applicable)
    
    # Summary amounts (for GSTR-3B)
    "total_outward_supply": "FLOAT",
    "total_inward_supply": "FLOAT",
    "total_itc_claimed": "FLOAT",
    "total_itc_reversed": "FLOAT",
    "total_tax_liability": "FLOAT",
    "total_tax_paid": "FLOAT",
    "net_tax_liability": "FLOAT",
    
    # Amendment tracking
    "is_amended": "BOOLEAN",
    "amendment_count": "INTEGER",
    "last_amended_date": "DATE",
    
    "created_at": "DATETIME",
    "updated_at": "DATETIME"
}

PAYMENT_PROPERTIES = {
    "id": "STRING",                    # UUID
    "payment_id": "STRING",            # Payment reference ID
    "payment_date": "DATE",            # Payment date (indexed)
    "payment_mode": "STRING",          # ONLINE, CHALLAN, CREDIT
    
    # Tax amounts paid
    "cgst_paid": "FLOAT",
    "sgst_paid": "FLOAT",
    "igst_paid": "FLOAT",
    "cess_paid": "FLOAT",
    "total_tax_paid": "FLOAT",         # Total tax paid (indexed)
    
    # Additional charges
    "interest": "FLOAT",
    "penalty": "FLOAT",
    "late_fee": "FLOAT",
    "total_amount": "FLOAT",
    
    # Reference details
    "challan_number": "STRING",
    "bank_reference": "STRING",
    "bank_name": "STRING",
    
    # Period
    "payment_period": "STRING",        # MMYYYY
    "financial_year": "STRING",
    
    "created_at": "DATETIME",
    "updated_at": "DATETIME"
}

VENDOR_PROPERTIES = {
    "id": "STRING",                    # UUID
    "gstin": "STRING",                 # Vendor GSTIN (indexed)
    "name": "STRING",                  # Vendor name
    "pan": "STRING",                   # PAN number
    
    # Compliance metrics
    "compliance_score": "FLOAT",       # 0-100 score (indexed)
    "risk_category": "STRING",         # HIGH_RISK, MEDIUM_RISK, LOW_RISK (indexed)
    
    # Transaction statistics
    "total_transactions": "INTEGER",
    "total_invoice_value": "FLOAT",
    "average_invoice_value": "FLOAT",
    "first_transaction_date": "DATE",
    "last_transaction_date": "DATE",
    
    # Mismatch statistics
    "total_mismatches": "INTEGER",
    "critical_mismatches": "INTEGER",
    "high_risk_mismatches": "INTEGER",
    "mismatch_rate": "FLOAT",          # Percentage (indexed)
    "total_mismatch_value": "FLOAT",
    "average_variance_percent": "FLOAT",
    
    # Filing behavior
    "on_time_filings": "INTEGER",
    "late_filings": "INTEGER",
    "missed_filings": "INTEGER",
    "filing_punctuality_rate": "FLOAT", # Percentage
    
    # Assessment
    "last_assessment_date": "DATETIME",
    "assessment_count": "INTEGER",
    
    # Flags
    "is_blacklisted": "BOOLEAN",
    "is_high_risk": "BOOLEAN",         # Indexed for filtering
    
    "created_at": "DATETIME",
    "updated_at": "DATETIME"
}

TAX_COMPONENT_PROPERTIES = {
    "id": "STRING",                    # UUID
    "cgst_rate": "FLOAT",              # CGST rate %
    "sgst_rate": "FLOAT",              # SGST rate %
    "igst_rate": "FLOAT",              # IGST rate %
    "cess_rate": "FLOAT",              # Cess rate %
    "total_rate": "FLOAT",             # Total GST rate
    
    "cgst_amount": "FLOAT",
    "sgst_amount": "FLOAT",
    "igst_amount": "FLOAT",
    "cess_amount": "FLOAT",
    "total_tax_amount": "FLOAT",
    
    "is_intrastate": "BOOLEAN",        # CGST+SGST
    "is_interstate": "BOOLEAN",        # IGST
    
    "created_at": "DATETIME"
}

MISMATCH_PROPERTIES = {
    "id": "STRING",                    # UUID
    "mismatch_type": "STRING",         # Type of mismatch (indexed)
    "risk_level": "STRING",            # CRITICAL, HIGH, MEDIUM, LOW (indexed)
    "status": "STRING",                # OPEN, RESOLVED, ACCEPTED, DISPUTED (indexed)
    "priority": "INTEGER",             # Priority score 1-10
    
    # Financial impact
    "amount_difference": "FLOAT",      # Absolute difference
    "variance_percent": "FLOAT",       # Percentage variance (indexed)
    "tax_impact": "FLOAT",             # Tax amount impact
    "itc_impact": "FLOAT",             # ITC impact (indexed)
    
    # Description
    "description": "STRING",           # Mismatch description
    "root_cause": "STRING",            # Root cause analysis
    "recommendation": "STRING",        # Recommended action
    
    # Details (JSON-like structure in properties)
    "expected_amount": "FLOAT",
    "actual_amount": "FLOAT",
    "expected_tax": "FLOAT",
    "actual_tax": "FLOAT",
    
    # Reconciliation metadata
    "reconciliation_run_id": "STRING", # Reconciliation batch ID
    "detected_at": "DATETIME",         # Detection timestamp (indexed)
    "detected_by": "STRING",           # System/User
    
    # Resolution tracking
    "resolved_at": "DATETIME",
    "resolved_by": "STRING",
    "resolution_notes": "STRING",
    "resolution_method": "STRING",     # AUTO, MANUAL, ACCEPTED
    
    # Aging
    "days_open": "INTEGER",            # Days since detection (indexed)
    "aging_bucket": "STRING",          # 0-7, 8-15, 16-30, 30+ days
    
    "created_at": "DATETIME",
    "updated_at": "DATETIME"
}


# ============================================================================
# NODE LABELS AND COMPOSITE INDEXES
# ============================================================================

def get_node_labels() -> Dict[str, List[str]]:
    """
    Get node labels including composite labels for better query performance.
    Some nodes can have multiple labels for efficient filtering.
    """
    return {
        "Taxpayer": ["Taxpayer", "Entity"],
        "GSTIN": ["GSTIN", "Identifier"],
        "Invoice": ["Invoice", "Document"],
        "LineItem": ["LineItem", "Detail"],
        "Return": ["Return", "Document"],
        "Payment": ["Payment", "Transaction"],
        "Vendor": ["Vendor", "Entity"],
        "TaxComponent": ["TaxComponent", "Detail"],
        "Mismatch": ["Mismatch", "Issue"]
    }


def get_composite_indexes() -> List[Dict[str, any]]:
    """
    Define composite indexes for complex queries.
    These significantly improve multi-hop traversal performance.
    """
    return [
        # Invoice reconciliation queries
        {
            "node": "Invoice",
            "properties": ["invoice_number", "source_type", "source_period"],
            "name": "invoice_reconciliation_idx"
        },
        # ITC validation queries
        {
            "node": "Invoice",
            "properties": ["invoice_date", "itc_eligible", "is_matched"],
            "name": "itc_validation_idx"
        },
        # Vendor analysis queries
        {
            "node": "Vendor",
            "properties": ["compliance_score", "mismatch_rate"],
            "name": "vendor_analysis_idx"
        },
        # Mismatch filtering queries
        {
            "node": "Mismatch",
            "properties": ["risk_level", "status", "detected_at"],
            "name": "mismatch_filter_idx"
        },
        # Return period queries
        {
            "node": "Return",
            "properties": ["return_type", "return_period", "status"],
            "name": "return_period_idx"
        }
    ]
