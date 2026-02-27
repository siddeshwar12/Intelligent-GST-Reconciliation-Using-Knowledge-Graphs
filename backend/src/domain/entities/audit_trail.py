from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4


@dataclass
class AuditStep:
    """Single step in audit trail."""
    
    step_number: int
    action: str
    description: str
    entity_type: str  # Invoice, Return, Payment, etc.
    entity_id: UUID
    timestamp: datetime
    result: str  # MATCHED, MISMATCHED, VALIDATED, etc.
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditTrail:
    """
    Audit trail entity for explainable reconciliation.
    Tracks the complete path and decision-making process.
    """
    
    id: UUID = field(default_factory=uuid4)
    
    # Related entities
    mismatch_id: Optional[UUID] = field(default=None)
    invoice_id: UUID = field(default=None)
    reconciliation_run_id: UUID = field(default=None)
    
    # Trail details
    trail_type: str = field(default="RECONCILIATION")  # RECONCILIATION, ITC_VALIDATION, etc.
    steps: List[AuditStep] = field(default_factory=list)
    
    # Graph path (for visualization)
    graph_nodes: List[Dict[str, Any]] = field(default_factory=list)
    graph_edges: List[Dict[str, Any]] = field(default_factory=list)
    
    # Summary
    summary: str = field(default="")
    conclusion: str = field(default="")
    recommendations: List[str] = field(default_factory=list)
    
    # Evidence
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def total_steps(self) -> int:
        """Get total number of steps."""
        return len(self.steps)
    
    @property
    def has_mismatch(self) -> bool:
        """Check if trail resulted in mismatch."""
        return self.mismatch_id is not None
    
    def add_step(
        self,
        action: str,
        description: str,
        entity_type: str,
        entity_id: UUID,
        result: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a step to the audit trail."""
        step = AuditStep(
            step_number=len(self.steps) + 1,
            action=action,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            timestamp=datetime.utcnow(),
            result=result,
            details=details or {}
        )
        self.steps.append(step)
    
    def add_graph_node(
        self,
        node_id: str,
        node_type: str,
        label: str,
        properties: Dict[str, Any]
    ) -> None:
        """Add a node to graph visualization."""
        self.graph_nodes.append({
            "id": node_id,
            "type": node_type,
            "label": label,
            "properties": properties
        })
    
    def add_graph_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an edge to graph visualization."""
        self.graph_edges.append({
            "source": source_id,
            "target": target_id,
            "relationship": relationship,
            "properties": properties or {}
        })
    
    def add_evidence(self, key: str, value: Any) -> None:
        """Add evidence to the trail."""
        self.evidence[key] = value
    
    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation."""
        self.recommendations.append(recommendation)
    
    def set_conclusion(self, conclusion: str) -> None:
        """Set the final conclusion."""
        self.conclusion = conclusion
    
    def __str__(self) -> str:
        return f"AuditTrail {self.trail_type} with {self.total_steps} steps"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, AuditTrail):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
