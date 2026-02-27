"""
Audit Trail Service for GST Reconciliation System.

This service generates comprehensive audit trails showing graph traversal paths,
matched nodes, mismatched fields, and explainable results designed for
frontend graph visualization.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass, asdict
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from graph.neo4j_connection import get_connection, Neo4jConnectionError
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("⚠ Neo4j connection not available - using mock data mode")


class NodeType(str, Enum):
    """Graph node types."""
    TAXPAYER = "Taxpayer"
    INVOICE = "Invoice"
    MISMATCH = "Mismatch"
    AUDIT_TRAIL = "AuditTrail"


class RelationshipType(str, Enum):
    """Graph relationship types."""
    ISSUED_BY = "ISSUED_BY"
    RECEIVED_BY = "RECEIVED_BY"
    MATCHES = "MATCHES"
    HAS_MISMATCH = "HAS_MISMATCH"
    PART_OF_CHAIN = "PART_OF_CHAIN"


class TraversalStep(str, Enum):
    """Traversal step types."""
    START = "START"
    FIND_SUPPLIER = "FIND_SUPPLIER"
    FIND_GSTR1 = "FIND_GSTR1"
    FIND_GSTR2B = "FIND_GSTR2B"
    VALIDATE_MATCH = "VALIDATE_MATCH"
    DETECT_MISMATCH = "DETECT_MISMATCH"
    END = "END"


@dataclass
class GraphNode:
    """Represents a node in the graph visualization."""
    id: str
    type: NodeType
    label: str
    properties: Dict[str, Any]
    status: str  # "matched", "mismatched", "missing", "valid"
    coordinates: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class GraphEdge:
    """Represents an edge in the graph visualization."""
    id: str
    source: str
    target: str
    type: RelationshipType
    label: str
    properties: Dict[str, Any]
    status: str  # "valid", "broken", "suspicious"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class TraversalStepResult:
    """Result of a single traversal step."""
    step: TraversalStep
    description: str
    query_executed: str
    nodes_found: List[GraphNode]
    relationships_created: List[GraphEdge]
    success: bool
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "step": self.step.value,
            "description": self.description,
            "query_executed": self.query_executed,
            "nodes_found": [node.to_dict() for node in self.nodes_found],
            "relationships_created": [edge.to_dict() for edge in self.relationships_created],
            "success": self.success,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms
        }


@dataclass
class FieldComparison:
    """Comparison of a specific field between two entities."""
    field_name: str
    source_value: Any
    target_value: Any
    is_match: bool
    variance_percentage: Optional[float] = None
    tolerance_applied: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class MismatchDetail:
    """Detailed information about a mismatch."""
    mismatch_type: str
    severity: str
    description: str
    field_comparisons: List[FieldComparison]
    financial_impact: float
    compliance_impact: str
    recommendation: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "mismatch_type": self.mismatch_type,
            "severity": self.severity,
            "description": self.description,
            "field_comparisons": [fc.to_dict() for fc in self.field_comparisons],
            "financial_impact": self.financial_impact,
            "compliance_impact": self.compliance_impact,
            "recommendation": self.recommendation
        }


@dataclass
class AuditTrail:
    """Complete audit trail for a reconciliation process."""
    audit_id: str
    invoice_id: str
    invoice_number: str
    taxpayer_gstin: str
    created_at: datetime
    
    # Graph structure
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    
    # Traversal path
    traversal_steps: List[TraversalStepResult]
    
    # Analysis results
    itc_chain_valid: bool
    mismatches_found: List[MismatchDetail]
    
    # Summary
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "audit_id": self.audit_id,
            "invoice_id": self.invoice_id,
            "invoice_number": self.invoice_number,
            "taxpayer_gstin": self.taxpayer_gstin,
            "created_at": self.created_at.isoformat(),
            "graph": {
                "nodes": [node.to_dict() for node in self.nodes],
                "edges": [edge.to_dict() for edge in self.edges]
            },
            "traversal_path": [step.to_dict() for step in self.traversal_steps],
            "analysis": {
                "itc_chain_valid": self.itc_chain_valid,
                "mismatches_found": [m.to_dict() for m in self.mismatches_found]
            },
            "summary": self.summary
        }


class AuditTrailService:
    """
    Audit Trail Service for GST Reconciliation.
    
    Generates comprehensive audit trails with graph visualization data,
    showing complete traversal paths and explainable results.
    """
    
    def __init__(self):
        """Initialize audit trail service."""
        self.connection = None
        if NEO4J_AVAILABLE:
            try:
                self.connection = get_connection()
                print("✓ Connected to Neo4j for audit trail generation")
            except Neo4jConnectionError as e:
                print(f"⚠ Neo4j not available: {e}")
        
        # Configuration
        self.amount_tolerance = 5.0  # 5% tolerance
        self.date_tolerance_days = 30
        
        # Graph layout configuration
        self.layout_config = {
            "node_spacing": 200,
            "level_height": 150,
            "center_x": 400,
            "center_y": 300
        }
    
    def generate_audit_trail(
        self,
        invoice_id: str,
        invoice_number: str,
        taxpayer_gstin: str
    ) -> AuditTrail:
        """
        Generate comprehensive audit trail for an invoice.
        
        Args:
            invoice_id: Invoice ID to audit
            invoice_number: Invoice number for reference
            taxpayer_gstin: Taxpayer GSTIN
            
        Returns:
            Complete AuditTrail with visualization data
        """
        audit_id = str(uuid4())
        created_at = datetime.now()
        
        print(f"\n=== Generating Audit Trail ===")
        print(f"Audit ID: {audit_id}")
        print(f"Invoice: {invoice_number}")
        print(f"Taxpayer: {taxpayer_gstin}")
        
        # Initialize collections
        nodes = []
        edges = []
        traversal_steps = []
        mismatches = []
        
        # Step 1: Find the source invoice
        step_result = self._step_find_source_invoice(invoice_id, invoice_number, taxpayer_gstin)
        traversal_steps.append(step_result)
        nodes.extend(step_result.nodes_found)
        edges.extend(step_result.relationships_created)
        
        if not step_result.success:
            return self._create_failed_audit_trail(audit_id, invoice_id, invoice_number, taxpayer_gstin, created_at, "Source invoice not found")
        
        source_invoice = step_result.nodes_found[0] if step_result.nodes_found else None
        
        # Step 2: Find supplier
        step_result = self._step_find_supplier(source_invoice)
        traversal_steps.append(step_result)
        nodes.extend(step_result.nodes_found)
        edges.extend(step_result.relationships_created)
        
        supplier = step_result.nodes_found[0] if step_result.nodes_found else None
        
        # Step 3: Find GSTR-1 entry
        step_result = self._step_find_gstr1(source_invoice, supplier)
        traversal_steps.append(step_result)
        nodes.extend(step_result.nodes_found)
        edges.extend(step_result.relationships_created)
        
        gstr1_invoice = step_result.nodes_found[0] if step_result.nodes_found else None
        
        # Step 4: Find GSTR-2B entry
        step_result = self._step_find_gstr2b(source_invoice)
        traversal_steps.append(step_result)
        nodes.extend(step_result.nodes_found)
        edges.extend(step_result.relationships_created)
        
        gstr2b_invoice = step_result.nodes_found[0] if step_result.nodes_found else None
        
        # Step 5: Validate matches and detect mismatches
        step_result = self._step_validate_matches(source_invoice, gstr1_invoice, gstr2b_invoice)
        traversal_steps.append(step_result)
        nodes.extend(step_result.nodes_found)
        edges.extend(step_result.relationships_created)
        
        # Step 6: Analyze mismatches
        if gstr2b_invoice:
            mismatch_details = self._analyze_invoice_mismatches(source_invoice, gstr2b_invoice)
            mismatches.extend(mismatch_details)
        else:
            # Missing invoice mismatch
            missing_mismatch = self._create_missing_invoice_mismatch(source_invoice)
            mismatches.append(missing_mismatch)
        
        # Calculate ITC chain validity
        itc_chain_valid = (
            source_invoice is not None and
            supplier is not None and
            gstr1_invoice is not None and
            gstr2b_invoice is not None and
            len(mismatches) == 0
        )
        
        # Apply graph layout
        self._apply_graph_layout(nodes, edges)
        
        # Generate summary
        summary = self._generate_summary(nodes, edges, traversal_steps, mismatches, itc_chain_valid)
        
        return AuditTrail(
            audit_id=audit_id,
            invoice_id=invoice_id,
            invoice_number=invoice_number,
            taxpayer_gstin=taxpayer_gstin,
            created_at=created_at,
            nodes=nodes,
            edges=edges,
            traversal_steps=traversal_steps,
            itc_chain_valid=itc_chain_valid,
            mismatches_found=mismatches,
            summary=summary
        )
    
    def _step_find_source_invoice(
        self,
        invoice_id: str,
        invoice_number: str,
        taxpayer_gstin: str
    ) -> TraversalStepResult:
        """Step 1: Find the source invoice."""
        start_time = datetime.now()
        
        if self.connection:
            query = """
            MATCH (buyer:Taxpayer {gstin: $taxpayer_gstin})-[:RECEIVED_BY]-(i:Invoice)
            WHERE i.id = $invoice_id OR i.invoice_number = $invoice_number
            RETURN i, buyer
            LIMIT 1
            """
            
            try:
                records = self.connection.execute_query(
                    query,
                    {
                        "invoice_id": invoice_id,
                        "invoice_number": invoice_number,
                        "taxpayer_gstin": taxpayer_gstin
                    }
                )
                
                nodes = []
                edges = []
                
                if records:
                    record = records[0]
                    
                    # Create invoice node
                    invoice_data = dict(record["i"])
                    invoice_node = GraphNode(
                        id=invoice_data["id"],
                        type=NodeType.INVOICE,
                        label=f"Invoice: {invoice_data.get('invoice_number', 'N/A')}",
                        properties=invoice_data,
                        status="valid"
                    )
                    nodes.append(invoice_node)
                    
                    # Create buyer node
                    buyer_data = dict(record["buyer"])
                    buyer_node = GraphNode(
                        id=buyer_data["id"],
                        type=NodeType.TAXPAYER,
                        label=f"Buyer: {buyer_data.get('legal_name', 'N/A')}",
                        properties=buyer_data,
                        status="valid"
                    )
                    nodes.append(buyer_node)
                    
                    # Create relationship
                    edge = GraphEdge(
                        id=f"{invoice_node.id}-{buyer_node.id}",
                        source=invoice_node.id,
                        target=buyer_node.id,
                        type=RelationshipType.RECEIVED_BY,
                        label="RECEIVED_BY",
                        properties={},
                        status="valid"
                    )
                    edges.append(edge)
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return TraversalStepResult(
                    step=TraversalStep.START,
                    description=f"Find source invoice {invoice_number} for taxpayer {taxpayer_gstin}",
                    query_executed=query,
                    nodes_found=nodes,
                    relationships_created=edges,
                    success=len(nodes) > 0,
                    execution_time_ms=execution_time
                )
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                return TraversalStepResult(
                    step=TraversalStep.START,
                    description=f"Find source invoice {invoice_number}",
                    query_executed=query,
                    nodes_found=[],
                    relationships_created=[],
                    success=False,
                    error_message=str(e),
                    execution_time_ms=execution_time
                )
        else:
            # Mock data when Neo4j not available
            return self._create_mock_source_invoice(invoice_id, invoice_number, taxpayer_gstin)
    
    def _step_find_supplier(self, source_invoice: GraphNode) -> TraversalStepResult:
        """Step 2: Find the supplier."""
        start_time = datetime.now()
        
        if self.connection and source_invoice:
            query = """
            MATCH (i:Invoice {id: $invoice_id})-[:ISSUED_BY]->(supplier:Taxpayer)
            RETURN supplier
            """
            
            try:
                records = self.connection.execute_query(
                    query,
                    {"invoice_id": source_invoice.id}
                )
                
                nodes = []
                edges = []
                
                if records:
                    supplier_data = dict(records[0]["supplier"])
                    supplier_node = GraphNode(
                        id=supplier_data["id"],
                        type=NodeType.TAXPAYER,
                        label=f"Supplier: {supplier_data.get('legal_name', 'N/A')}",
                        properties=supplier_data,
                        status="valid"
                    )
                    nodes.append(supplier_node)
                    
                    # Create relationship
                    edge = GraphEdge(
                        id=f"{source_invoice.id}-{supplier_node.id}",
                        source=source_invoice.id,
                        target=supplier_node.id,
                        type=RelationshipType.ISSUED_BY,
                        label="ISSUED_BY",
                        properties={},
                        status="valid"
                    )
                    edges.append(edge)
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return TraversalStepResult(
                    step=TraversalStep.FIND_SUPPLIER,
                    description=f"Find supplier for invoice {source_invoice.properties.get('invoice_number', 'N/A')}",
                    query_executed=query,
                    nodes_found=nodes,
                    relationships_created=edges,
                    success=len(nodes) > 0,
                    execution_time_ms=execution_time
                )
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                return TraversalStepResult(
                    step=TraversalStep.FIND_SUPPLIER,
                    description="Find supplier",
                    query_executed=query,
                    nodes_found=[],
                    relationships_created=[],
                    success=False,
                    error_message=str(e),
                    execution_time_ms=execution_time
                )
        else:
            # Mock data
            return self._create_mock_supplier(source_invoice)
    
    def _step_find_gstr1(self, source_invoice: GraphNode, supplier: GraphNode) -> TraversalStepResult:
        """Step 3: Find GSTR-1 entry."""
        start_time = datetime.now()
        
        if self.connection and source_invoice and supplier:
            query = """
            MATCH (supplier:Taxpayer {id: $supplier_id})-[:ISSUED_BY]-(gstr1:Invoice)
            WHERE gstr1.source_type = 'GSTR-1'
            AND gstr1.invoice_number = $invoice_number
            AND gstr1.recipient_gstin = $recipient_gstin
            RETURN gstr1
            LIMIT 1
            """
            
            try:
                records = self.connection.execute_query(
                    query,
                    {
                        "supplier_id": supplier.id,
                        "invoice_number": source_invoice.properties.get("invoice_number"),
                        "recipient_gstin": source_invoice.properties.get("recipient_gstin")
                    }
                )
                
                nodes = []
                edges = []
                
                if records:
                    gstr1_data = dict(records[0]["gstr1"])
                    gstr1_node = GraphNode(
                        id=gstr1_data["id"],
                        type=NodeType.INVOICE,
                        label=f"GSTR-1: {gstr1_data.get('invoice_number', 'N/A')}",
                        properties=gstr1_data,
                        status="valid"
                    )
                    nodes.append(gstr1_node)
                    
                    # Create relationship to supplier
                    edge = GraphEdge(
                        id=f"{gstr1_node.id}-{supplier.id}",
                        source=gstr1_node.id,
                        target=supplier.id,
                        type=RelationshipType.ISSUED_BY,
                        label="ISSUED_BY",
                        properties={},
                        status="valid"
                    )
                    edges.append(edge)
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return TraversalStepResult(
                    step=TraversalStep.FIND_GSTR1,
                    description=f"Find GSTR-1 entry for invoice {source_invoice.properties.get('invoice_number', 'N/A')}",
                    query_executed=query,
                    nodes_found=nodes,
                    relationships_created=edges,
                    success=len(nodes) > 0,
                    execution_time_ms=execution_time
                )
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                return TraversalStepResult(
                    step=TraversalStep.FIND_GSTR1,
                    description="Find GSTR-1 entry",
                    query_executed=query,
                    nodes_found=[],
                    relationships_created=[],
                    success=False,
                    error_message=str(e),
                    execution_time_ms=execution_time
                )
        else:
            # Mock data
            return self._create_mock_gstr1(source_invoice, supplier)
    
    def _step_find_gstr2b(self, source_invoice: GraphNode) -> TraversalStepResult:
        """Step 4: Find GSTR-2B entry."""
        start_time = datetime.now()
        
        if self.connection and source_invoice:
            query = """
            MATCH (buyer:Taxpayer {gstin: $recipient_gstin})-[:RECEIVED_BY]-(gstr2b:Invoice)
            WHERE gstr2b.source_type = 'GSTR-2B'
            AND gstr2b.invoice_number = $invoice_number
            AND gstr2b.supplier_gstin = $supplier_gstin
            RETURN gstr2b, buyer
            LIMIT 1
            """
            
            try:
                records = self.connection.execute_query(
                    query,
                    {
                        "invoice_number": source_invoice.properties.get("invoice_number"),
                        "supplier_gstin": source_invoice.properties.get("supplier_gstin"),
                        "recipient_gstin": source_invoice.properties.get("recipient_gstin")
                    }
                )
                
                nodes = []
                edges = []
                
                if records:
                    gstr2b_data = dict(records[0]["gstr2b"])
                    gstr2b_node = GraphNode(
                        id=gstr2b_data["id"],
                        type=NodeType.INVOICE,
                        label=f"GSTR-2B: {gstr2b_data.get('invoice_number', 'N/A')}",
                        properties=gstr2b_data,
                        status="valid"
                    )
                    nodes.append(gstr2b_node)
                    
                    buyer_data = dict(records[0]["buyer"])
                    # Create relationship to buyer
                    edge = GraphEdge(
                        id=f"{gstr2b_node.id}-{buyer_data['id']}",
                        source=gstr2b_node.id,
                        target=buyer_data["id"],
                        type=RelationshipType.RECEIVED_BY,
                        label="RECEIVED_BY",
                        properties={},
                        status="valid"
                    )
                    edges.append(edge)
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return TraversalStepResult(
                    step=TraversalStep.FIND_GSTR2B,
                    description=f"Find GSTR-2B entry for invoice {source_invoice.properties.get('invoice_number', 'N/A')}",
                    query_executed=query,
                    nodes_found=nodes,
                    relationships_created=edges,
                    success=len(nodes) > 0,
                    execution_time_ms=execution_time
                )
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                return TraversalStepResult(
                    step=TraversalStep.FIND_GSTR2B,
                    description="Find GSTR-2B entry",
                    query_executed=query,
                    nodes_found=[],
                    relationships_created=[],
                    success=False,
                    error_message=str(e),
                    execution_time_ms=execution_time
                )
        else:
            # Mock data
            return self._create_mock_gstr2b(source_invoice)
    
    def _step_validate_matches(
        self,
        source_invoice: GraphNode,
        gstr1_invoice: Optional[GraphNode],
        gstr2b_invoice: Optional[GraphNode]
    ) -> TraversalStepResult:
        """Step 5: Validate matches between invoices."""
        start_time = datetime.now()
        
        nodes = []
        edges = []
        
        # Create match relationships where applicable
        if source_invoice and gstr2b_invoice:
            # Check if amounts match within tolerance
            source_amount = source_invoice.properties.get("total_amount", 0)
            gstr2b_amount = gstr2b_invoice.properties.get("total_amount", 0)
            
            if source_amount > 0:
                variance = abs(source_amount - gstr2b_amount) / source_amount * 100
                is_match = variance <= self.amount_tolerance
            else:
                is_match = source_amount == gstr2b_amount
            
            edge_status = "valid" if is_match else "suspicious"
            
            edge = GraphEdge(
                id=f"{source_invoice.id}-matches-{gstr2b_invoice.id}",
                source=source_invoice.id,
                target=gstr2b_invoice.id,
                type=RelationshipType.MATCHES,
                label="MATCHES" if is_match else "PARTIAL_MATCH",
                properties={
                    "amount_variance": variance if source_amount > 0 else 0,
                    "is_exact_match": is_match
                },
                status=edge_status
            )
            edges.append(edge)
        
        if gstr1_invoice and gstr2b_invoice:
            # Create chain relationship
            edge = GraphEdge(
                id=f"{gstr1_invoice.id}-chain-{gstr2b_invoice.id}",
                source=gstr1_invoice.id,
                target=gstr2b_invoice.id,
                type=RelationshipType.PART_OF_CHAIN,
                label="ITC_CHAIN",
                properties={},
                status="valid"
            )
            edges.append(edge)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return TraversalStepResult(
            step=TraversalStep.VALIDATE_MATCH,
            description="Validate matches and create chain relationships",
            query_executed="// Validation logic executed in application",
            nodes_found=nodes,
            relationships_created=edges,
            success=True,
            execution_time_ms=execution_time
        )
    
    def _analyze_invoice_mismatches(
        self,
        source_invoice: GraphNode,
        target_invoice: GraphNode
    ) -> List[MismatchDetail]:
        """Analyze mismatches between two invoices."""
        mismatches = []
        
        # Compare key fields
        field_comparisons = []
        
        # Amount comparison
        source_amount = source_invoice.properties.get("total_amount", 0)
        target_amount = target_invoice.properties.get("total_amount", 0)
        amount_variance = abs(source_amount - target_amount) / source_amount * 100 if source_amount > 0 else 0
        
        field_comparisons.append(FieldComparison(
            field_name="total_amount",
            source_value=source_amount,
            target_value=target_amount,
            is_match=amount_variance <= self.amount_tolerance,
            variance_percentage=amount_variance,
            tolerance_applied=self.amount_tolerance
        ))
        
        # Tax amount comparison
        source_tax = source_invoice.properties.get("total_tax", 0)
        target_tax = target_invoice.properties.get("total_tax", 0)
        tax_variance = abs(source_tax - target_tax) / source_tax * 100 if source_tax > 0 else 0
        
        field_comparisons.append(FieldComparison(
            field_name="total_tax",
            source_value=source_tax,
            target_value=target_tax,
            is_match=tax_variance <= self.amount_tolerance,
            variance_percentage=tax_variance,
            tolerance_applied=self.amount_tolerance
        ))
        
        # Date comparison
        source_date = source_invoice.properties.get("invoice_date", "")
        target_date = target_invoice.properties.get("invoice_date", "")
        
        field_comparisons.append(FieldComparison(
            field_name="invoice_date",
            source_value=source_date,
            target_value=target_date,
            is_match=source_date == target_date
        ))
        
        # GSTIN comparison
        source_gstin = source_invoice.properties.get("supplier_gstin", "")
        target_gstin = target_invoice.properties.get("supplier_gstin", "")
        
        field_comparisons.append(FieldComparison(
            field_name="supplier_gstin",
            source_value=source_gstin,
            target_value=target_gstin,
            is_match=source_gstin == target_gstin
        ))
        
        # Create mismatch details for significant variances
        if amount_variance > self.amount_tolerance:
            severity = "CRITICAL" if amount_variance > 20 else "HIGH" if amount_variance > 10 else "MEDIUM"
            
            mismatches.append(MismatchDetail(
                mismatch_type="AMOUNT_MISMATCH",
                severity=severity,
                description=f"Amount variance of {amount_variance:.2f}% exceeds tolerance of {self.amount_tolerance}%",
                field_comparisons=field_comparisons,
                financial_impact=abs(source_amount - target_amount),
                compliance_impact="Potential ITC discrepancy",
                recommendation="Verify invoice amounts with supplier"
            ))
        
        if source_gstin != target_gstin:
            mismatches.append(MismatchDetail(
                mismatch_type="GSTIN_MISMATCH",
                severity="CRITICAL",
                description="Supplier GSTIN mismatch between sources",
                field_comparisons=field_comparisons,
                financial_impact=source_amount,  # Full amount at risk
                compliance_impact="Invalid ITC claim",
                recommendation="Immediate correction required"
            ))
        
        return mismatches
    
    def _create_missing_invoice_mismatch(self, source_invoice: GraphNode) -> MismatchDetail:
        """Create mismatch detail for missing invoice."""
        return MismatchDetail(
            mismatch_type="MISSING_IN_GSTR2B",
            severity="HIGH",
            description=f"Invoice {source_invoice.properties.get('invoice_number', 'N/A')} missing in GSTR-2B",
            field_comparisons=[],
            financial_impact=source_invoice.properties.get("total_amount", 0),
            compliance_impact="Risk of ITC loss",
            recommendation="Contact supplier to ensure GSTR-1 filing"
        )
    
    def _apply_graph_layout(self, nodes: List[GraphNode], edges: List[GraphEdge]):
        """Apply layout coordinates to nodes for visualization."""
        # Simple hierarchical layout
        levels = {
            "Taxpayer": 0,
            "Invoice": 1
        }
        
        # Group nodes by type
        node_groups = {}
        for node in nodes:
            node_type = node.type.value
            if node_type not in node_groups:
                node_groups[node_type] = []
            node_groups[node_type].append(node)
        
        # Assign coordinates
        for node_type, type_nodes in node_groups.items():
            level = levels.get(node_type, 1)
            y = self.layout_config["center_y"] + (level * self.layout_config["level_height"])
            
            for i, node in enumerate(type_nodes):
                x = self.layout_config["center_x"] + (i - len(type_nodes)/2) * self.layout_config["node_spacing"]
                node.coordinates = {"x": x, "y": y}
    
    def _generate_summary(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        steps: List[TraversalStepResult],
        mismatches: List[MismatchDetail],
        itc_valid: bool
    ) -> Dict[str, Any]:
        """Generate audit trail summary."""
        return {
            "graph_statistics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": {node_type.value: len([n for n in nodes if n.type == node_type]) for node_type in NodeType},
                "edge_types": {edge_type.value: len([e for e in edges if e.type == edge_type]) for edge_type in RelationshipType}
            },
            "traversal_statistics": {
                "total_steps": len(steps),
                "successful_steps": len([s for s in steps if s.success]),
                "failed_steps": len([s for s in steps if not s.success]),
                "total_execution_time_ms": sum(s.execution_time_ms for s in steps)
            },
            "analysis_results": {
                "itc_chain_valid": itc_valid,
                "total_mismatches": len(mismatches),
                "mismatch_severity_distribution": {
                    severity: len([m for m in mismatches if m.severity == severity])
                    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
                },
                "total_financial_impact": sum(m.financial_impact for m in mismatches)
            },
            "compliance_status": {
                "chain_complete": len([n for n in nodes if n.type == NodeType.INVOICE]) >= 2,
                "supplier_identified": len([n for n in nodes if n.type == NodeType.TAXPAYER and "supplier" in n.label.lower()]) > 0,
                "gstr1_found": len([n for n in nodes if "GSTR-1" in n.label]) > 0,
                "gstr2b_found": len([n for n in nodes if "GSTR-2B" in n.label]) > 0
            }
        }
    
    def _create_failed_audit_trail(
        self,
        audit_id: str,
        invoice_id: str,
        invoice_number: str,
        taxpayer_gstin: str,
        created_at: datetime,
        error_message: str
    ) -> AuditTrail:
        """Create audit trail for failed cases."""
        return AuditTrail(
            audit_id=audit_id,
            invoice_id=invoice_id,
            invoice_number=invoice_number,
            taxpayer_gstin=taxpayer_gstin,
            created_at=created_at,
            nodes=[],
            edges=[],
            traversal_steps=[],
            itc_chain_valid=False,
            mismatches_found=[],
            summary={"error": error_message}
        )
    
    # Mock data methods for when Neo4j is not available
    def _create_mock_source_invoice(self, invoice_id: str, invoice_number: str, taxpayer_gstin: str) -> TraversalStepResult:
        """Create mock source invoice for demo purposes."""
        invoice_node = GraphNode(
            id=invoice_id,
            type=NodeType.INVOICE,
            label=f"Invoice: {invoice_number}",
            properties={
                "id": invoice_id,
                "invoice_number": invoice_number,
                "invoice_date": "2024-01-15T00:00:00",
                "supplier_gstin": "27AABCU9603R1ZM",
                "recipient_gstin": taxpayer_gstin,
                "total_amount": 100000.0,
                "total_tax": 18000.0,
                "source_type": "PURCHASE_REGISTER"
            },
            status="valid"
        )
        
        buyer_node = GraphNode(
            id=f"buyer-{taxpayer_gstin}",
            type=NodeType.TAXPAYER,
            label=f"Buyer: {taxpayer_gstin}",
            properties={
                "id": f"buyer-{taxpayer_gstin}",
                "gstin": taxpayer_gstin,
                "legal_name": "Sample Buyer Company Ltd"
            },
            status="valid"
        )
        
        edge = GraphEdge(
            id=f"{invoice_id}-{buyer_node.id}",
            source=invoice_id,
            target=buyer_node.id,
            type=RelationshipType.RECEIVED_BY,
            label="RECEIVED_BY",
            properties={},
            status="valid"
        )
        
        return TraversalStepResult(
            step=TraversalStep.START,
            description=f"Find source invoice {invoice_number} (MOCK DATA)",
            query_executed="// Mock data - no query executed",
            nodes_found=[invoice_node, buyer_node],
            relationships_created=[edge],
            success=True,
            execution_time_ms=5.0
        )
    
    def _create_mock_supplier(self, source_invoice: GraphNode) -> TraversalStepResult:
        """Create mock supplier for demo purposes."""
        if not source_invoice:
            return TraversalStepResult(
                step=TraversalStep.FIND_SUPPLIER,
                description="Find supplier (MOCK DATA)",
                query_executed="// Mock data - no query executed",
                nodes_found=[],
                relationships_created=[],
                success=False,
                error_message="No source invoice provided"
            )
        
        supplier_gstin = source_invoice.properties.get("supplier_gstin", "27AABCU9603R1ZM")
        
        supplier_node = GraphNode(
            id=f"supplier-{supplier_gstin}",
            type=NodeType.TAXPAYER,
            label=f"Supplier: Sample Supplier Ltd",
            properties={
                "id": f"supplier-{supplier_gstin}",
                "gstin": supplier_gstin,
                "legal_name": "Sample Supplier Ltd"
            },
            status="valid"
        )
        
        edge = GraphEdge(
            id=f"{source_invoice.id}-{supplier_node.id}",
            source=source_invoice.id,
            target=supplier_node.id,
            type=RelationshipType.ISSUED_BY,
            label="ISSUED_BY",
            properties={},
            status="valid"
        )
        
        return TraversalStepResult(
            step=TraversalStep.FIND_SUPPLIER,
            description="Find supplier (MOCK DATA)",
            query_executed="// Mock data - no query executed",
            nodes_found=[supplier_node],
            relationships_created=[edge],
            success=True,
            execution_time_ms=3.0
        )
    
    def _create_mock_gstr1(self, source_invoice: GraphNode, supplier: GraphNode) -> TraversalStepResult:
        """Create mock GSTR-1 entry for demo purposes."""
        if not source_invoice or not supplier:
            return TraversalStepResult(
                step=TraversalStep.FIND_GSTR1,
                description="Find GSTR-1 entry (MOCK DATA)",
                query_executed="// Mock data - no query executed",
                nodes_found=[],
                relationships_created=[],
                success=False,
                error_message="Missing source invoice or supplier"
            )
        
        gstr1_node = GraphNode(
            id=f"gstr1-{source_invoice.id}",
            type=NodeType.INVOICE,
            label=f"GSTR-1: {source_invoice.properties.get('invoice_number', 'N/A')}",
            properties={
                "id": f"gstr1-{source_invoice.id}",
                "invoice_number": source_invoice.properties.get("invoice_number"),
                "invoice_date": source_invoice.properties.get("invoice_date"),
                "supplier_gstin": source_invoice.properties.get("supplier_gstin"),
                "recipient_gstin": source_invoice.properties.get("recipient_gstin"),
                "total_amount": source_invoice.properties.get("total_amount"),
                "total_tax": source_invoice.properties.get("total_tax"),
                "source_type": "GSTR-1"
            },
            status="valid"
        )
        
        edge = GraphEdge(
            id=f"{gstr1_node.id}-{supplier.id}",
            source=gstr1_node.id,
            target=supplier.id,
            type=RelationshipType.ISSUED_BY,
            label="ISSUED_BY",
            properties={},
            status="valid"
        )
        
        return TraversalStepResult(
            step=TraversalStep.FIND_GSTR1,
            description="Find GSTR-1 entry (MOCK DATA)",
            query_executed="// Mock data - no query executed",
            nodes_found=[gstr1_node],
            relationships_created=[edge],
            success=True,
            execution_time_ms=4.0
        )
    
    def _create_mock_gstr2b(self, source_invoice: GraphNode) -> TraversalStepResult:
        """Create mock GSTR-2B entry with intentional mismatch for demo purposes."""
        if not source_invoice:
            return TraversalStepResult(
                step=TraversalStep.FIND_GSTR2B,
                description="Find GSTR-2B entry (MOCK DATA)",
                query_executed="// Mock data - no query executed",
                nodes_found=[],
                relationships_created=[],
                success=False,
                error_message="No source invoice provided"
            )
        
        # Create GSTR-2B with 5% amount mismatch for demo
        original_amount = source_invoice.properties.get("total_amount", 100000)
        mismatched_amount = original_amount * 1.05  # 5% higher
        
        gstr2b_node = GraphNode(
            id=f"gstr2b-{source_invoice.id}",
            type=NodeType.INVOICE,
            label=f"GSTR-2B: {source_invoice.properties.get('invoice_number', 'N/A')}",
            properties={
                "id": f"gstr2b-{source_invoice.id}",
                "invoice_number": source_invoice.properties.get("invoice_number"),
                "invoice_date": source_invoice.properties.get("invoice_date"),
                "supplier_gstin": source_invoice.properties.get("supplier_gstin"),
                "recipient_gstin": source_invoice.properties.get("recipient_gstin"),
                "total_amount": mismatched_amount,  # Intentional mismatch
                "total_tax": source_invoice.properties.get("total_tax", 0) * 1.05,
                "source_type": "GSTR-2B"
            },
            status="mismatched"
        )
        
        buyer_id = f"buyer-{source_invoice.properties.get('recipient_gstin')}"
        edge = GraphEdge(
            id=f"{gstr2b_node.id}-{buyer_id}",
            source=gstr2b_node.id,
            target=buyer_id,
            type=RelationshipType.RECEIVED_BY,
            label="RECEIVED_BY",
            properties={},
            status="valid"
        )
        
        return TraversalStepResult(
            step=TraversalStep.FIND_GSTR2B,
            description="Find GSTR-2B entry (MOCK DATA - with mismatch)",
            query_executed="// Mock data - no query executed",
            nodes_found=[gstr2b_node],
            relationships_created=[edge],
            success=True,
            execution_time_ms=4.0
        )


def main():
    """Example usage of the audit trail service."""
    try:
        service = AuditTrailService()
        
        # Generate audit trail for sample invoice
        audit_trail = service.generate_audit_trail(
            invoice_id="sample-invoice-001",
            invoice_number="INV-001001",
            taxpayer_gstin="33GSPTN2635F1ZU"
        )
        
        # Convert to JSON for frontend
        audit_json = audit_trail.to_dict()
        
        # Save to file
        import json
        with open('audit_trail_sample.json', 'w') as f:
            json.dump(audit_json, f, indent=2)
        
        print(f"\n=== AUDIT TRAIL GENERATED ===")
        print(f"Audit ID: {audit_trail.audit_id}")
        print(f"Invoice: {audit_trail.invoice_number}")
        print(f"ITC Chain Valid: {audit_trail.itc_chain_valid}")
        print(f"Nodes: {len(audit_trail.nodes)}")
        print(f"Edges: {len(audit_trail.edges)}")
        print(f"Traversal Steps: {len(audit_trail.traversal_steps)}")
        print(f"Mismatches: {len(audit_trail.mismatches_found)}")
        
        print(f"\n--- GRAPH STRUCTURE ---")
        for node in audit_trail.nodes:
            print(f"Node: {node.label} ({node.status})")
        
        for edge in audit_trail.edges:
            print(f"Edge: {edge.label} ({edge.status})")
        
        if audit_trail.mismatches_found:
            print(f"\n--- MISMATCHES DETECTED ---")
            for mismatch in audit_trail.mismatches_found:
                print(f"- {mismatch.mismatch_type} ({mismatch.severity})")
                print(f"  {mismatch.description}")
                print(f"  Financial Impact: ₹{mismatch.financial_impact:,.2f}")
        
        print(f"\n✓ Audit trail exported to: audit_trail_sample.json")
        print(f"✓ Ready for frontend graph visualization!")
        
    except Exception as e:
        print(f"✗ Audit trail generation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()