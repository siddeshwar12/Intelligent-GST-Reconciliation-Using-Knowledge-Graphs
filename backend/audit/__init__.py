"""
Audit Trail Package for GST Reconciliation System.

This package provides comprehensive audit trail generation with graph
visualization data, showing complete traversal paths and explainable results.
"""

from .audit_service import (
    AuditTrailService,
    AuditTrail,
    GraphNode,
    GraphEdge,
    TraversalStepResult,
    MismatchDetail,
    FieldComparison,
    NodeType,
    RelationshipType,
    TraversalStep
)

__version__ = "1.0.0"
__all__ = [
    "AuditTrailService",
    "AuditTrail",
    "GraphNode",
    "GraphEdge",
    "TraversalStepResult",
    "MismatchDetail",
    "FieldComparison",
    "NodeType",
    "RelationshipType",
    "TraversalStep"
]