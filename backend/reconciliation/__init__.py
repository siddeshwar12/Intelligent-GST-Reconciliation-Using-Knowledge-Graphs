"""
GST Reconciliation Package.

This package provides comprehensive GST reconciliation capabilities using
multi-hop Cypher traversal for ITC chain validation, mismatch detection,
and intelligent financial risk classification.
"""

from .reconcile_service import (
    GSTReconciliationService,
    ReconciliationResult,
    MismatchResult,
    ITCValidationResult
)

from .classification import (
    FinancialRiskClassifier,
    RiskAssessment,
    MismatchContext,
    RiskLevel,
    RiskFactor,
    MismatchCategory,
    classify_amount_mismatch,
    classify_missing_invoice,
    get_risk_level_from_variance
)

__version__ = "1.0.0"
__all__ = [
    # Reconciliation Service
    "GSTReconciliationService",
    "ReconciliationResult", 
    "MismatchResult",
    "ITCValidationResult",
    
    # Risk Classification
    "FinancialRiskClassifier",
    "RiskAssessment",
    "MismatchContext",
    "RiskLevel",
    "RiskFactor",
    "MismatchCategory",
    "classify_amount_mismatch",
    "classify_missing_invoice",
    "get_risk_level_from_variance"
]