"""
Explainable Audit Trail Generator
Provides detailed, transparent audit trails with graph path visualization
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AuditEventType(str, Enum):
    """Types of audit events."""
    RECONCILIATION_START = "RECONCILIATION_START"
    RECONCILIATION_COMPLETE = "RECONCILIATION_COMPLETE"
    MISMATCH_DETECTED = "MISMATCH_DETECTED"
    ITC_VALIDATION = "ITC_VALIDATION"
    FRAUD_DETECTION = "FRAUD_DETECTION"
    VENDOR_ASSESSMENT = "VENDOR_ASSESSMENT"
    MANUAL_CORRECTION = "MANUAL_CORRECTION"
    SYSTEM_ACTION = "SYSTEM_ACTION"


@dataclass
class GraphNode:
    """Represents a node in the graph path."""
    node_type: str  # Invoice, Taxpayer, Return, Payment, etc.
    node_id: str
    properties: Dict
    label: str  # Human-readable label
    
    def to_dict(self) -> Dict:
        return {
            "type": self.node_type,
            "id": self.node_id,
            "properties": self.properties,
            "label": self.label
        }


@dataclass
class GraphRelationship:
    """Represents a relationship in the graph path."""
    relationship_type: str  # ISSUED_BY, RECEIVED_BY, etc.
    from_node: str
    to_node: str
    properties: Dict
    label: str  # Human-readable label
    
    def to_dict(self) -> Dict:
        return {
            "type": self.relationship_type,
            "from": self.from_node,
            "to": self.to_node,
            "properties": self.properties,
            "label": self.label
        }


@dataclass
class GraphPath:
    """Represents a complete graph traversal path."""
    path_id: str
    nodes: List[GraphNode]
    relationships: List[GraphRelationship]
    path_length: int
    path_description: str
    
    def to_dict(self) -> Dict:
        return {
            "path_id": self.path_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "relationships": [r.to_dict() for r in self.relationships],
            "path_length": self.path_length,
            "description": self.path_description
        }


@dataclass
class PropertyMismatch:
    """Represents a property-level mismatch."""
    property_name: str
    expected_value: any
    actual_value: any
    variance: Optional[float]
    variance_percent: Optional[float]
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    explanation: str
    
    def to_dict(self) -> Dict:
        return {
            "property": self.property_name,
            "expected": str(self.expected_value),
            "actual": str(self.actual_value),
            "variance": self.variance,
            "variance_percent": self.variance_percent,
            "severity": self.severity,
            "explanation": self.explanation
        }


@dataclass
class NodeMismatch:
    """Represents a node-level mismatch."""
    node_id: str
    node_type: str
    node_label: str
    property_mismatches: List[PropertyMismatch]
    overall_severity: str
    impact_description: str
    
    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "node_label": self.node_label,
            "property_mismatches": [pm.to_dict() for pm in self.property_mismatches],
            "overall_severity": self.overall_severity,
            "impact": self.impact_description
        }


@dataclass
class RiskExplanation:
    """Explains why something is risky."""
    risk_level: str
    risk_score: float
    primary_reasons: List[str]
    contributing_factors: List[str]
    financial_impact: float
    compliance_impact: str
    recommended_actions: List[str]
    evidence: Dict
    
    def to_dict(self) -> Dict:
        return {
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "primary_reasons": self.primary_reasons,
            "contributing_factors": self.contributing_factors,
            "financial_impact": self.financial_impact,
            "compliance_impact": self.compliance_impact,
            "recommended_actions": self.recommended_actions,
            "evidence": self.evidence
        }


@dataclass
class ExplainableAuditTrail:
    """
    Complete explainable audit trail with graph visualization.
    
    Instead of: "Mismatch found"
    We show:
    - Complete traversal path
    - Which node mismatched
    - What property mismatched
    - Why it is risky
    - What to do about it
    """
    audit_id: str
    event_type: AuditEventType
    timestamp: datetime
    
    # Graph path visualization
    graph_path: Optional[GraphPath]
    
    # Detailed mismatch information
    node_mismatches: List[NodeMismatch]
    
    # Risk explanation
    risk_explanation: Optional[RiskExplanation]
    
    # Context
    context: Dict
    
    # Summary
    summary: str
    detailed_description: str
    
    # Metadata
    detected_by: str  # SYSTEM, USER_ID
    confidence: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "audit_id": self.audit_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "graph_path": self.graph_path.to_dict() if self.graph_path else None,
            "node_mismatches": [nm.to_dict() for nm in self.node_mismatches],
            "risk_explanation": self.risk_explanation.to_dict() if self.risk_explanation else None,
            "context": self.context,
            "summary": self.summary,
            "detailed_description": self.detailed_description,
            "detected_by": self.detected_by,
            "confidence": self.confidence
        }


class ExplainableAuditGenerator:
    """
    Generates explainable audit trails with graph path visualization.
    
    Provides transparency and traceability for all reconciliation actions.
    """
    
    def __init__(self, neo4j_client=None):
        """Initialize audit generator."""
        self.neo4j_client = neo4j_client
    
    # ========================================================================
    # ITC VALIDATION AUDIT TRAIL
    # ========================================================================
    
    def generate_itc_validation_audit(
        self,
        invoice_number: str,
        buyer_gstin: str,
        validation_result: Dict
    ) -> ExplainableAuditTrail:
        """
        Generate explainable audit trail for ITC validation.
        
        Shows complete chain: Buyer → Invoice → Vendor → GSTR-1 → GSTR-2B → GSTR-3B → Payment
        """
        # Build graph path
        graph_path = self._build_itc_chain_path(validation_result)
        
        # Identify node mismatches
        node_mismatches = self._identify_itc_chain_mismatches(validation_result)
        
        # Generate risk explanation
        risk_explanation = self._explain_itc_risk(validation_result, node_mismatches)
        
        # Create summary
        if validation_result.get('itc_eligible'):
            summary = f"✅ ITC Eligible: Invoice {invoice_number} passed all validation checks"
        else:
            summary = f"❌ ITC Ineligible: Invoice {invoice_number} failed validation"
        
        # Detailed description
        detailed_description = self._generate_itc_description(validation_result, node_mismatches)
        
        return ExplainableAuditTrail(
            audit_id=f"ITC-{invoice_number}-{datetime.utcnow().timestamp()}",
            event_type=AuditEventType.ITC_VALIDATION,
            timestamp=datetime.utcnow(),
            graph_path=graph_path,
            node_mismatches=node_mismatches,
            risk_explanation=risk_explanation,
            context={
                "invoice_number": invoice_number,
                "buyer_gstin": buyer_gstin,
                "validation_result": validation_result
            },
            summary=summary,
            detailed_description=detailed_description,
            detected_by="SYSTEM",
            confidence=validation_result.get('chain_completeness_score', 0) / 100
        )
    
    def _build_itc_chain_path(self, validation_result: Dict) -> GraphPath:
        """Build graph path for ITC chain."""
        nodes = []
        relationships = []
        
        # Buyer node
        if 'buyer' in validation_result:
            buyer = validation_result['buyer']
            nodes.append(GraphNode(
                node_type="Taxpayer",
                node_id=buyer.get('gstin', 'UNKNOWN'),
                properties=buyer,
                label=f"Buyer: {buyer.get('name', 'Unknown')}"
            ))
        
        # Invoice node
        if 'invoice' in validation_result:
            invoice = validation_result['invoice']
            nodes.append(GraphNode(
                node_type="Invoice",
                node_id=invoice.get('invoice_number', 'UNKNOWN'),
                properties=invoice,
                label=f"Invoice: {invoice.get('invoice_number', 'Unknown')}"
            ))
            
            # RECEIVED_BY relationship
            relationships.append(GraphRelationship(
                relationship_type="RECEIVED_BY",
                from_node=invoice.get('invoice_number', 'UNKNOWN'),
                to_node=validation_result.get('buyer', {}).get('gstin', 'UNKNOWN'),
                properties={},
                label="Received by buyer"
            ))
        
        # Supplier node
        if 'supplier' in validation_result:
            supplier = validation_result['supplier']
            nodes.append(GraphNode(
                node_type="Taxpayer",
                node_id=supplier.get('gstin', 'UNKNOWN'),
                properties=supplier,
                label=f"Supplier: {supplier.get('name', 'Unknown')}"
            ))
            
            # ISSUED_BY relationship
            relationships.append(GraphRelationship(
                relationship_type="ISSUED_BY",
                from_node=validation_result.get('invoice', {}).get('invoice_number', 'UNKNOWN'),
                to_node=supplier.get('gstin', 'UNKNOWN'),
                properties={},
                label="Issued by supplier"
            ))
        
        # GSTR-1 node
        if validation_result.get('in_gstr1') and 'gstr1' in validation_result:
            gstr1 = validation_result['gstr1']
            nodes.append(GraphNode(
                node_type="Return",
                node_id=f"GSTR1-{gstr1.get('return_period', 'UNKNOWN')}",
                properties=gstr1,
                label=f"GSTR-1: {gstr1.get('return_period', 'Unknown')}"
            ))
            
            relationships.append(GraphRelationship(
                relationship_type="REPORTED_IN",
                from_node=validation_result.get('invoice', {}).get('invoice_number', 'UNKNOWN'),
                to_node=f"GSTR1-{gstr1.get('return_period', 'UNKNOWN')}",
                properties={},
                label="Reported in GSTR-1"
            ))
        
        # GSTR-2B node
        if validation_result.get('in_gstr2b') and 'gstr2b' in validation_result:
            gstr2b = validation_result['gstr2b']
            nodes.append(GraphNode(
                node_type="Return",
                node_id=f"GSTR2B-{gstr2b.get('return_period', 'UNKNOWN')}",
                properties=gstr2b,
                label=f"GSTR-2B: {gstr2b.get('return_period', 'Unknown')}"
            ))
            
            relationships.append(GraphRelationship(
                relationship_type="ENABLES_ITC",
                from_node=validation_result.get('invoice', {}).get('invoice_number', 'UNKNOWN'),
                to_node=f"GSTR2B-{gstr2b.get('return_period', 'UNKNOWN')}",
                properties={},
                label="Enables ITC in GSTR-2B"
            ))
        
        # GSTR-3B node
        if validation_result.get('in_gstr3b') and 'gstr3b' in validation_result:
            gstr3b = validation_result['gstr3b']
            nodes.append(GraphNode(
                node_type="Return",
                node_id=f"GSTR3B-{gstr3b.get('return_period', 'UNKNOWN')}",
                properties=gstr3b,
                label=f"GSTR-3B: {gstr3b.get('return_period', 'Unknown')}"
            ))
            
            relationships.append(GraphRelationship(
                relationship_type="CLAIMS_ITC",
                from_node=validation_result.get('buyer', {}).get('gstin', 'UNKNOWN'),
                to_node=f"GSTR3B-{gstr3b.get('return_period', 'UNKNOWN')}",
                properties={},
                label="Claims ITC in GSTR-3B"
            ))
        
        # Payment node
        if validation_result.get('payment_made') and 'payment' in validation_result:
            payment = validation_result['payment']
            nodes.append(GraphNode(
                node_type="Payment",
                node_id=payment.get('payment_id', 'UNKNOWN'),
                properties=payment,
                label=f"Payment: {payment.get('payment_id', 'Unknown')}"
            ))
            
            relationships.append(GraphRelationship(
                relationship_type="PAID_VIA",
                from_node=f"GSTR3B-{validation_result.get('gstr3b', {}).get('return_period', 'UNKNOWN')}",
                to_node=payment.get('payment_id', 'UNKNOWN'),
                properties={},
                label="Paid via payment"
            ))
        
        return GraphPath(
            path_id=f"ITC-PATH-{datetime.utcnow().timestamp()}",
            nodes=nodes,
            relationships=relationships,
            path_length=len(nodes),
            path_description=f"ITC validation chain with {len(nodes)} nodes and {len(relationships)} relationships"
        )
    
    def _identify_itc_chain_mismatches(self, validation_result: Dict) -> List[NodeMismatch]:
        """Identify mismatches in ITC chain."""
        mismatches = []
        
        # Check if invoice in GSTR-1
        if not validation_result.get('in_gstr1'):
            mismatches.append(NodeMismatch(
                node_id="GSTR-1",
                node_type="Return",
                node_label="Supplier's GSTR-1",
                property_mismatches=[
                    PropertyMismatch(
                        property_name="invoice_present",
                        expected_value=True,
                        actual_value=False,
                        variance=None,
                        variance_percent=None,
                        severity="CRITICAL",
                        explanation="Invoice not found in supplier's GSTR-1 return. ITC cannot be claimed."
                    )
                ],
                overall_severity="CRITICAL",
                impact_description="ITC claim will be rejected. Potential revenue loss."
            ))
        
        # Check if invoice in GSTR-2B
        if not validation_result.get('in_gstr2b'):
            mismatches.append(NodeMismatch(
                node_id="GSTR-2B",
                node_type="Return",
                node_label="Buyer's GSTR-2B",
                property_mismatches=[
                    PropertyMismatch(
                        property_name="invoice_present",
                        expected_value=True,
                        actual_value=False,
                        variance=None,
                        variance_percent=None,
                        severity="HIGH",
                        explanation="Invoice not auto-populated in GSTR-2B. Manual verification required."
                    )
                ],
                overall_severity="HIGH",
                impact_description="ITC claim may be delayed or rejected."
            ))
        
        # Check amount match
        if not validation_result.get('amount_matches'):
            invoice_amount = validation_result.get('invoice', {}).get('total_amount', 0)
            gstr2b_amount = validation_result.get('gstr2b_invoice', {}).get('total_amount', 0)
            variance = abs(invoice_amount - gstr2b_amount)
            variance_percent = (variance / invoice_amount * 100) if invoice_amount > 0 else 0
            
            mismatches.append(NodeMismatch(
                node_id=validation_result.get('invoice', {}).get('invoice_number', 'UNKNOWN'),
                node_type="Invoice",
                node_label="Invoice Amount",
                property_mismatches=[
                    PropertyMismatch(
                        property_name="total_amount",
                        expected_value=invoice_amount,
                        actual_value=gstr2b_amount,
                        variance=variance,
                        variance_percent=variance_percent,
                        severity="HIGH" if variance_percent > 5 else "MEDIUM",
                        explanation=f"Amount mismatch between invoice and GSTR-2B: ₹{variance:.2f} difference"
                    )
                ],
                overall_severity="HIGH" if variance_percent > 5 else "MEDIUM",
                impact_description=f"ITC claim may be partially rejected. Potential loss: ₹{variance * 0.18:.2f}"
            ))
        
        # Check GSTIN match
        if not validation_result.get('gstin_matches'):
            mismatches.append(NodeMismatch(
                node_id="GSTIN",
                node_type="Identifier",
                node_label="GSTIN Validation",
                property_mismatches=[
                    PropertyMismatch(
                        property_name="gstin",
                        expected_value=validation_result.get('supplier', {}).get('gstin', 'UNKNOWN'),
                        actual_value=validation_result.get('invoice', {}).get('supplier_gstin', 'UNKNOWN'),
                        variance=None,
                        variance_percent=None,
                        severity="CRITICAL",
                        explanation="GSTIN mismatch between supplier and invoice. Invalid ITC claim."
                    )
                ],
                overall_severity="CRITICAL",
                impact_description="Complete ITC claim rejection. Immediate correction required."
            ))
        
        return mismatches
    
    def _explain_itc_risk(self, validation_result: Dict, 
                         node_mismatches: List[NodeMismatch]) -> RiskExplanation:
        """Generate risk explanation for ITC validation."""
        # Determine risk level
        if not validation_result.get('itc_eligible'):
            if any(nm.overall_severity == "CRITICAL" for nm in node_mismatches):
                risk_level = "CRITICAL"
                risk_score = 90
            else:
                risk_level = "HIGH"
                risk_score = 70
        else:
            risk_level = "LOW"
            risk_score = 20
        
        # Primary reasons
        primary_reasons = []
        if not validation_result.get('in_gstr1'):
            primary_reasons.append("Invoice missing in supplier's GSTR-1")
        if not validation_result.get('amount_matches'):
            primary_reasons.append("Amount mismatch between invoice and GSTR-2B")
        if not validation_result.get('gstin_matches'):
            primary_reasons.append("GSTIN mismatch")
        
        # Contributing factors
        contributing_factors = []
        if not validation_result.get('in_gstr2b'):
            contributing_factors.append("Not auto-populated in GSTR-2B")
        if not validation_result.get('payment_made'):
            contributing_factors.append("Payment not recorded")
        
        # Financial impact
        invoice_amount = validation_result.get('invoice', {}).get('total_amount', 0)
        tax_amount = invoice_amount * 0.18  # Assume 18% GST
        financial_impact = tax_amount if not validation_result.get('itc_eligible') else 0
        
        # Recommended actions
        recommended_actions = []
        if not validation_result.get('in_gstr1'):
            recommended_actions.append("Contact supplier to file/amend GSTR-1")
        if not validation_result.get('amount_matches'):
            recommended_actions.append("Verify invoice amount with supplier")
        if not validation_result.get('gstin_matches'):
            recommended_actions.append("Correct GSTIN immediately")
        
        return RiskExplanation(
            risk_level=risk_level,
            risk_score=risk_score,
            primary_reasons=primary_reasons,
            contributing_factors=contributing_factors,
            financial_impact=financial_impact,
            compliance_impact="ITC claim rejection" if not validation_result.get('itc_eligible') else "Compliant",
            recommended_actions=recommended_actions,
            evidence={
                "chain_completeness": validation_result.get('chain_completeness_score', 0),
                "validation_checks": {
                    "in_gstr1": validation_result.get('in_gstr1', False),
                    "in_gstr2b": validation_result.get('in_gstr2b', False),
                    "amount_matches": validation_result.get('amount_matches', False),
                    "gstin_matches": validation_result.get('gstin_matches', False)
                }
            }
        )
    
    def _generate_itc_description(self, validation_result: Dict, 
                                  node_mismatches: List[NodeMismatch]) -> str:
        """Generate detailed description for ITC validation."""
        invoice_number = validation_result.get('invoice', {}).get('invoice_number', 'Unknown')
        
        description = f"ITC Validation for Invoice {invoice_number}:\n\n"
        
        # Chain status
        description += "Validation Chain Status:\n"
        description += f"  ✓ Invoice exists: Yes\n"
        description += f"  {'✓' if validation_result.get('in_gstr1') else '✗'} In supplier's GSTR-1: {validation_result.get('in_gstr1', False)}\n"
        description += f"  {'✓' if validation_result.get('in_gstr2b') else '✗'} In buyer's GSTR-2B: {validation_result.get('in_gstr2b', False)}\n"
        description += f"  {'✓' if validation_result.get('amount_matches') else '✗'} Amount matches: {validation_result.get('amount_matches', False)}\n"
        description += f"  {'✓' if validation_result.get('gstin_matches') else '✗'} GSTIN matches: {validation_result.get('gstin_matches', False)}\n"
        description += f"  {'✓' if validation_result.get('payment_made') else '✗'} Payment recorded: {validation_result.get('payment_made', False)}\n\n"
        
        # Mismatches
        if node_mismatches:
            description += f"Detected {len(node_mismatches)} issue(s):\n"
            for i, mismatch in enumerate(node_mismatches, 1):
                description += f"  {i}. {mismatch.node_label}: {mismatch.impact_description}\n"
        else:
            description += "No issues detected. ITC claim is valid.\n"
        
        # Overall result
        description += f"\nOverall ITC Eligibility: {'✓ ELIGIBLE' if validation_result.get('itc_eligible') else '✗ INELIGIBLE'}\n"
        description += f"Chain Completeness: {validation_result.get('chain_completeness_score', 0)}%"
        
        return description


# Export
__all__ = [
    'ExplainableAuditGenerator',
    'ExplainableAuditTrail',
    'GraphPath',
    'NodeMismatch',
    'PropertyMismatch',
    'RiskExplanation'
]
