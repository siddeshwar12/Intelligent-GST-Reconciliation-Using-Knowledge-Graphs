"""
Neo4j Knowledge Graph Schema - Relationship Definitions
Optimized for GST Reconciliation and ITC Validation
"""

from enum import Enum
from typing import Dict, List


class RelationshipType(str, Enum):
    """Relationship types in the GST Knowledge Graph."""
    
    # ========================================================================
    # INVOICE RELATIONSHIPS
    # ========================================================================
    ISSUED_BY = "ISSUED_BY"              # Invoice -> Taxpayer (supplier)
    RECEIVED_BY = "RECEIVED_BY"          # Invoice -> Taxpayer (buyer)
    CONTAINS = "CONTAINS"                # Invoice -> LineItem
    HAS_TAX = "HAS_TAX"                  # Invoice/LineItem -> TaxComponent
    
    # ========================================================================
    # RETURN RELATIONSHIPS
    # ========================================================================
    REPORTED_IN = "REPORTED_IN"          # Invoice -> Return
    FILED_BY = "FILED_BY"                # Return -> Taxpayer
    PAID_VIA = "PAID_VIA"                # Return -> Payment
    MADE_PAYMENT = "MADE_PAYMENT"        # Taxpayer -> Payment
    
    # ========================================================================
    # GSTIN RELATIONSHIPS
    # ========================================================================
    HAS_GSTIN = "HAS_GSTIN"              # Taxpayer -> GSTIN
    REGISTERED_AS = "REGISTERED_AS"      # GSTIN -> Taxpayer
    
    # ========================================================================
    # VENDOR RELATIONSHIPS
    # ========================================================================
    IS_VENDOR = "IS_VENDOR"              # Taxpayer -> Vendor
    SUPPLIES_TO = "SUPPLIES_TO"          # Vendor -> Taxpayer
    TRANSACTS_WITH = "TRANSACTS_WITH"    # Taxpayer -> Taxpayer (bidirectional)
    
    # ========================================================================
    # RECONCILIATION RELATIONSHIPS (Critical for ITC validation)
    # ========================================================================
    MATCHES = "MATCHES"                  # Invoice -> Invoice (successful match)
    MISMATCHES = "MISMATCHES"            # Invoice -> Invoice (with discrepancy)
    HAS_MISMATCH = "HAS_MISMATCH"        # Invoice -> Mismatch
    DETECTED_FOR = "DETECTED_FOR"        # Mismatch -> Taxpayer
    RELATES_TO = "RELATES_TO"            # Mismatch -> Invoice (multiple invoices)
    
    # ========================================================================
    # ITC CHAIN RELATIONSHIPS (Multi-hop traversal)
    # ========================================================================
    ENABLES_ITC = "ENABLES_ITC"          # Invoice (GSTR-1) -> Invoice (GSTR-2B)
    CLAIMS_ITC = "CLAIMS_ITC"            # Taxpayer -> Invoice (ITC claim)
    REVERSES_ITC = "REVERSES_ITC"        # Return -> Invoice (ITC reversal)
    
    # ========================================================================
    # AMENDMENT RELATIONSHIPS
    # ========================================================================
    AMENDS = "AMENDS"                    # Invoice -> Invoice (amendment)
    AMENDED_BY = "AMENDED_BY"            # Invoice -> Invoice (reverse)
    CANCELS = "CANCELS"                  # Invoice -> Invoice (cancellation)


# ============================================================================
# RELATIONSHIP PROPERTY SCHEMAS
# ============================================================================

ISSUED_BY_PROPERTIES = {
    "issued_date": "DATE",
    "supplier_gstin": "STRING",
    "created_at": "DATETIME"
}

RECEIVED_BY_PROPERTIES = {
    "received_date": "DATE",
    "buyer_gstin": "STRING",
    "acknowledged": "BOOLEAN",
    "created_at": "DATETIME"
}

CONTAINS_PROPERTIES = {
    "line_number": "INTEGER",
    "sequence": "INTEGER",
    "created_at": "DATETIME"
}

HAS_TAX_PROPERTIES = {
    "tax_type": "STRING",              # CGST, SGST, IGST, CESS
    "created_at": "DATETIME"
}

REPORTED_IN_PROPERTIES = {
    "reported_date": "DATE",
    "return_period": "STRING",
    "return_type": "STRING",
    "filing_status": "STRING",
    "is_amended": "BOOLEAN",
    "amendment_date": "DATE",
    "created_at": "DATETIME"
}

FILED_BY_PROPERTIES = {
    "filing_date": "DATE",
    "arn": "STRING",
    "is_late": "BOOLEAN",
    "days_late": "INTEGER",
    "created_at": "DATETIME"
}

PAID_VIA_PROPERTIES = {
    "payment_date": "DATE",
    "payment_amount": "FLOAT",
    "payment_mode": "STRING",
    "challan_number": "STRING",
    "created_at": "DATETIME"
}

MADE_PAYMENT_PROPERTIES = {
    "payment_date": "DATE",
    "total_amount": "FLOAT",
    "created_at": "DATETIME"
}

HAS_GSTIN_PROPERTIES = {
    "registration_date": "DATE",
    "is_primary": "BOOLEAN",
    "is_active": "BOOLEAN",
    "created_at": "DATETIME"
}

IS_VENDOR_PROPERTIES = {
    "vendor_since": "DATE",
    "is_active": "BOOLEAN",
    "created_at": "DATETIME"
}

SUPPLIES_TO_PROPERTIES = {
    "first_transaction_date": "DATE",
    "last_transaction_date": "DATE",
    "total_transactions": "INTEGER",
    "total_value": "FLOAT",
    "average_value": "FLOAT",
    "relationship_strength": "FLOAT",  # 0-1 score
    "is_active": "BOOLEAN",
    "created_at": "DATETIME",
    "updated_at": "DATETIME"
}

TRANSACTS_WITH_PROPERTIES = {
    "first_transaction": "DATE",
    "last_transaction": "DATE",
    "transaction_count": "INTEGER",
    "total_value": "FLOAT",
    "relationship_type": "STRING",     # BUYER, SELLER, BOTH
    "created_at": "DATETIME"
}

# ============================================================================
# RECONCILIATION RELATIONSHIP PROPERTIES (Critical for matching)
# ============================================================================

MATCHES_PROPERTIES = {
    "match_score": "FLOAT",            # 0-1 confidence score
    "match_type": "STRING",            # EXACT, FUZZY, MANUAL, AUTO
    "match_method": "STRING",          # INVOICE_NUMBER, IRN, AMOUNT
    "matched_at": "DATETIME",
    "matched_by": "STRING",            # SYSTEM, USER_ID
    
    # Matching criteria
    "invoice_number_match": "BOOLEAN",
    "amount_match": "BOOLEAN",
    "date_match": "BOOLEAN",
    "gstin_match": "BOOLEAN",
    "tax_match": "BOOLEAN",
    
    # Variance details
    "amount_variance": "FLOAT",
    "date_variance_days": "INTEGER",
    
    "created_at": "DATETIME"
}

MISMATCHES_PROPERTIES = {
    "mismatch_type": "STRING",         # AMOUNT, TAX, DATE, GSTIN, MISSING
    "risk_level": "STRING",            # CRITICAL, HIGH, MEDIUM, LOW
    "variance_percent": "FLOAT",       # Percentage variance
    "amount_difference": "FLOAT",      # Absolute difference
    "tax_difference": "FLOAT",         # Tax amount difference
    
    # Detailed variance
    "expected_amount": "FLOAT",
    "actual_amount": "FLOAT",
    "expected_tax": "FLOAT",
    "actual_tax": "FLOAT",
    
    # Detection metadata
    "detected_at": "DATETIME",
    "detected_by": "STRING",
    "detection_method": "STRING",      # AUTO, MANUAL, RULE_BASED
    
    # Root cause
    "root_cause": "STRING",
    "root_cause_category": "STRING",   # DATA_ENTRY, TIMING, AMENDMENT, FRAUD
    
    "created_at": "DATETIME"
}

HAS_MISMATCH_PROPERTIES = {
    "mismatch_id": "STRING",
    "detected_at": "DATETIME",
    "severity": "STRING",
    "created_at": "DATETIME"
}

DETECTED_FOR_PROPERTIES = {
    "taxpayer_gstin": "STRING",
    "detected_at": "DATETIME",
    "impact_amount": "FLOAT",
    "created_at": "DATETIME"
}

RELATES_TO_PROPERTIES = {
    "relationship_type": "STRING",     # PRIMARY, SECONDARY, REFERENCE
    "created_at": "DATETIME"
}

# ============================================================================
# ITC CHAIN RELATIONSHIP PROPERTIES (Multi-hop traversal optimization)
# ============================================================================

ENABLES_ITC_PROPERTIES = {
    "itc_amount": "FLOAT",             # ITC amount enabled
    "cgst_itc": "FLOAT",
    "sgst_itc": "FLOAT",
    "igst_itc": "FLOAT",
    "cess_itc": "FLOAT",
    
    # Eligibility
    "is_eligible": "BOOLEAN",
    "eligibility_reason": "STRING",
    "eligibility_checked_at": "DATETIME",
    
    # Chain validation
    "chain_validated": "BOOLEAN",
    "validation_status": "STRING",     # VALID, INVALID, PENDING
    "validation_date": "DATETIME",
    
    # Matching details
    "gstr1_invoice_id": "STRING",
    "gstr2b_invoice_id": "STRING",
    "match_confidence": "FLOAT",
    
    # Timing
    "supplier_filing_date": "DATE",
    "buyer_receipt_date": "DATE",
    "time_lag_days": "INTEGER",
    
    "created_at": "DATETIME",
    "updated_at": "DATETIME"
}

CLAIMS_ITC_PROPERTIES = {
    "claim_amount": "FLOAT",
    "claim_date": "DATE",
    "claim_period": "STRING",
    "claim_status": "STRING",          # CLAIMED, REVERSED, PENDING
    "return_type": "STRING",           # GSTR-3B
    "created_at": "DATETIME"
}

REVERSES_ITC_PROPERTIES = {
    "reversal_amount": "FLOAT",
    "reversal_date": "DATE",
    "reversal_reason": "STRING",
    "reversal_period": "STRING",
    "created_at": "DATETIME"
}

# ============================================================================
# AMENDMENT RELATIONSHIP PROPERTIES
# ============================================================================

AMENDS_PROPERTIES = {
    "amendment_date": "DATE",
    "amendment_reason": "STRING",
    "amendment_type": "STRING",        # CORRECTION, ADDITION, DELETION
    "original_amount": "FLOAT",
    "amended_amount": "FLOAT",
    "amount_change": "FLOAT",
    "created_at": "DATETIME"
}

AMENDED_BY_PROPERTIES = {
    "amended_date": "DATE",
    "created_at": "DATETIME"
}

CANCELS_PROPERTIES = {
    "cancellation_date": "DATE",
    "cancellation_reason": "STRING",
    "cancelled_by": "STRING",
    "created_at": "DATETIME"
}


# ============================================================================
# RELATIONSHIP DIRECTIONALITY AND CARDINALITY
# ============================================================================

RELATIONSHIP_METADATA = {
    "ISSUED_BY": {
        "from": "Invoice",
        "to": "Taxpayer",
        "cardinality": "many-to-one",
        "description": "Invoice issued by supplier"
    },
    "RECEIVED_BY": {
        "from": "Invoice",
        "to": "Taxpayer",
        "cardinality": "many-to-one",
        "description": "Invoice received by buyer"
    },
    "CONTAINS": {
        "from": "Invoice",
        "to": "LineItem",
        "cardinality": "one-to-many",
        "description": "Invoice contains line items"
    },
    "HAS_TAX": {
        "from": ["Invoice", "LineItem"],
        "to": "TaxComponent",
        "cardinality": "one-to-one",
        "description": "Tax component breakdown"
    },
    "REPORTED_IN": {
        "from": "Invoice",
        "to": "Return",
        "cardinality": "many-to-one",
        "description": "Invoice reported in GST return"
    },
    "FILED_BY": {
        "from": "Return",
        "to": "Taxpayer",
        "cardinality": "many-to-one",
        "description": "Return filed by taxpayer"
    },
    "PAID_VIA": {
        "from": "Return",
        "to": "Payment",
        "cardinality": "one-to-many",
        "description": "Return paid via payment"
    },
    "MATCHES": {
        "from": "Invoice",
        "to": "Invoice",
        "cardinality": "one-to-one",
        "description": "Invoice matches another invoice",
        "bidirectional": True
    },
    "MISMATCHES": {
        "from": "Invoice",
        "to": "Invoice",
        "cardinality": "one-to-one",
        "description": "Invoice mismatches with another",
        "bidirectional": True
    },
    "ENABLES_ITC": {
        "from": "Invoice",
        "to": "Invoice",
        "cardinality": "one-to-one",
        "description": "GSTR-1 invoice enables ITC in GSTR-2B",
        "critical_for_itc": True
    },
    "SUPPLIES_TO": {
        "from": "Vendor",
        "to": "Taxpayer",
        "cardinality": "many-to-many",
        "description": "Vendor supplies to taxpayer"
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_relationship_properties(rel_type: RelationshipType) -> Dict:
    """Get property schema for a relationship type."""
    property_map = {
        RelationshipType.ISSUED_BY: ISSUED_BY_PROPERTIES,
        RelationshipType.RECEIVED_BY: RECEIVED_BY_PROPERTIES,
        RelationshipType.CONTAINS: CONTAINS_PROPERTIES,
        RelationshipType.HAS_TAX: HAS_TAX_PROPERTIES,
        RelationshipType.REPORTED_IN: REPORTED_IN_PROPERTIES,
        RelationshipType.FILED_BY: FILED_BY_PROPERTIES,
        RelationshipType.PAID_VIA: PAID_VIA_PROPERTIES,
        RelationshipType.MATCHES: MATCHES_PROPERTIES,
        RelationshipType.MISMATCHES: MISMATCHES_PROPERTIES,
        RelationshipType.HAS_MISMATCH: HAS_MISMATCH_PROPERTIES,
        RelationshipType.ENABLES_ITC: ENABLES_ITC_PROPERTIES,
        RelationshipType.CLAIMS_ITC: CLAIMS_ITC_PROPERTIES,
        RelationshipType.SUPPLIES_TO: SUPPLIES_TO_PROPERTIES,
    }
    return property_map.get(rel_type, {})


def get_itc_critical_relationships() -> List[RelationshipType]:
    """Get relationships critical for ITC validation."""
    return [
        RelationshipType.ISSUED_BY,
        RelationshipType.RECEIVED_BY,
        RelationshipType.REPORTED_IN,
        RelationshipType.ENABLES_ITC,
        RelationshipType.CLAIMS_ITC,
        RelationshipType.MATCHES,
        RelationshipType.MISMATCHES
    ]
