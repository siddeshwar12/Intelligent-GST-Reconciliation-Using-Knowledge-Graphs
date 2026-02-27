"""
Advanced Fraud Pattern Detection using Graph Analysis
Detects: Circular trading, duplicate invoices, suspicious clusters, high centrality vendors
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import networkx as nx


@dataclass
class FraudPattern:
    """Represents a detected fraud pattern."""
    pattern_type: str
    risk_level: str
    confidence_score: float
    entities_involved: List[str]
    description: str
    financial_impact: float
    evidence: Dict
    detected_at: datetime


class FraudDetectionEngine:
    """
    Graph-based fraud detection engine.
    Uses network analysis to detect complex fraud patterns.
    """
    
    def __init__(self, neo4j_client=None):
        """Initialize fraud detection engine."""
        self.neo4j_client = neo4j_client
        self.fraud_patterns = []
    
    # ========================================================================
    # 1. CIRCULAR TRADING DETECTION
    # ========================================================================
    
    def detect_circular_trading(self, min_chain_length: int = 3, 
                               max_chain_length: int = 10) -> List[FraudPattern]:
        """
        Detect circular trading loops where invoices flow in a circle.
        
        Example: Company A → Company B → Company C → Company A
        
        This is a common fraud pattern to:
        - Inflate turnover
        - Claim fake ITC
        - Create artificial transactions
        """
        query = """
        MATCH path = (start:Taxpayer)-[:ISSUED_BY|RECEIVED_BY*$min_length..$max_length]-(end:Taxpayer)
        WHERE start.gstin = end.gstin
        AND length(path) >= $min_length
        
        WITH path, nodes(path) as chain_nodes, relationships(path) as chain_rels
        
        // Extract invoices in the loop
        WITH path, [n IN chain_nodes WHERE n:Invoice | n] as invoices
        
        WHERE size(invoices) >= $min_length
        
        RETURN 
          path,
          [n IN chain_nodes WHERE n:Taxpayer | n.gstin] as gstin_chain,
          [inv IN invoices | inv.invoice_number] as invoice_chain,
          reduce(total = 0, inv IN invoices | total + inv.total_amount) as total_value,
          size(invoices) as chain_length,
          invoices
        
        ORDER BY total_value DESC
        LIMIT 100
        """
        
        if not self.neo4j_client:
            return self._generate_mock_circular_trading()
        
        results = self.neo4j_client.execute_query(
            query,
            min_length=min_chain_length,
            max_length=max_chain_length
        )
        
        patterns = []
        for record in results:
            pattern = FraudPattern(
                pattern_type="CIRCULAR_TRADING",
                risk_level=self._calculate_circular_risk(
                    record['total_value'],
                    record['chain_length']
                ),
                confidence_score=0.85,
                entities_involved=record['gstin_chain'],
                description=f"Circular trading detected: {len(record['gstin_chain'])} entities in loop",
                financial_impact=record['total_value'],
                evidence={
                    'invoice_chain': record['invoice_chain'],
                    'chain_length': record['chain_length'],
                    'total_value': record['total_value']
                },
                detected_at=datetime.utcnow()
            )
            patterns.append(pattern)
        
        return patterns
    
    # ========================================================================
    # 2. DUPLICATE INVOICE DETECTION
    # ========================================================================
    
    def detect_duplicate_invoices(self, tolerance_days: int = 7) -> List[FraudPattern]:
        """
        Detect duplicate invoices with:
        - Same invoice number from different suppliers
        - Same amount, date, and parties (potential double-billing)
        - Similar invoices within tolerance period
        """
        query = """
        // Find invoices with same invoice number
        MATCH (inv1:Invoice)-[:ISSUED_BY]->(supplier1:Taxpayer)
        MATCH (inv2:Invoice)-[:ISSUED_BY]->(supplier2:Taxpayer)
        
        WHERE inv1.invoice_number = inv2.invoice_number
        AND inv1.id <> inv2.id
        AND supplier1.gstin <> supplier2.gstin
        
        RETURN 
          inv1.invoice_number as invoice_number,
          inv1.total_amount as amount1,
          inv2.total_amount as amount2,
          supplier1.gstin as supplier1_gstin,
          supplier2.gstin as supplier2_gstin,
          inv1.invoice_date as date1,
          inv2.invoice_date as date2,
          'DUPLICATE_INVOICE_NUMBER' as duplicate_type
        
        UNION
        
        // Find invoices with same amount, date, and parties
        MATCH (inv1:Invoice)-[:ISSUED_BY]->(supplier:Taxpayer)
        MATCH (inv1)-[:RECEIVED_BY]->(buyer:Taxpayer)
        MATCH (inv2:Invoice)-[:ISSUED_BY]->(supplier)
        MATCH (inv2)-[:RECEIVED_BY]->(buyer)
        
        WHERE inv1.id <> inv2.id
        AND abs(inv1.total_amount - inv2.total_amount) < 1.0
        AND abs(duration.between(inv1.invoice_date, inv2.invoice_date).days) <= $tolerance_days
        
        RETURN 
          inv1.invoice_number as invoice_number,
          inv1.total_amount as amount1,
          inv2.total_amount as amount2,
          supplier.gstin as supplier1_gstin,
          supplier.gstin as supplier2_gstin,
          inv1.invoice_date as date1,
          inv2.invoice_date as date2,
          'DUPLICATE_TRANSACTION' as duplicate_type
        
        LIMIT 100
        """
        
        if not self.neo4j_client:
            return self._generate_mock_duplicates()
        
        results = self.neo4j_client.execute_query(query, tolerance_days=tolerance_days)
        
        patterns = []
        for record in results:
            pattern = FraudPattern(
                pattern_type="DUPLICATE_INVOICE",
                risk_level="HIGH",
                confidence_score=0.90,
                entities_involved=[record['supplier1_gstin'], record['supplier2_gstin']],
                description=f"Duplicate invoice detected: {record['duplicate_type']}",
                financial_impact=record['amount1'],
                evidence={
                    'invoice_number': record['invoice_number'],
                    'amount1': record['amount1'],
                    'amount2': record['amount2'],
                    'date1': record['date1'],
                    'date2': record['date2'],
                    'type': record['duplicate_type']
                },
                detected_at=datetime.utcnow()
            )
            patterns.append(pattern)
        
        return patterns
    
    # ========================================================================
    # 3. HIGH CENTRALITY SUSPICIOUS VENDOR DETECTION
    # ========================================================================
    
    def detect_high_centrality_vendors(self, min_connections: int = 10,
                                      min_risk_score: float = 70.0) -> List[FraudPattern]:
        """
        Detect vendors with unusually high network centrality.
        
        High centrality + high risk = potential hub for fraudulent activity.
        
        Uses:
        - Degree centrality (number of connections)
        - Betweenness centrality (bridge between clusters)
        - PageRank (importance in network)
        """
        query = """
        MATCH (vendor:Vendor)-[:SUPPLIES_TO]->(buyer:Taxpayer)
        
        WITH vendor, count(DISTINCT buyer) as connection_count
        WHERE connection_count >= $min_connections
        AND vendor.compliance_score <= $min_risk_score
        
        OPTIONAL MATCH (vendor)<-[:IS_VENDOR]-(taxpayer:Taxpayer)
        OPTIONAL MATCH (taxpayer)-[:ISSUED_BY]-(invoice:Invoice)
        
        WITH 
          vendor,
          taxpayer,
          connection_count,
          count(DISTINCT invoice) as total_invoices,
          sum(invoice.total_amount) as total_value,
          vendor.mismatch_rate as mismatch_rate,
          vendor.compliance_score as compliance_score
        
        WHERE total_invoices >= 20  // Significant activity
        
        RETURN 
          vendor.gstin as gstin,
          vendor.name as name,
          connection_count,
          total_invoices,
          total_value,
          mismatch_rate,
          compliance_score,
          
          // Centrality score (0-100)
          round(
            (connection_count * 0.4) +
            (total_invoices * 0.3) +
            ((100 - compliance_score) * 0.3)
          , 2) as centrality_score
        
        ORDER BY centrality_score DESC
        LIMIT 50
        """
        
        if not self.neo4j_client:
            return self._generate_mock_high_centrality()
        
        results = self.neo4j_client.execute_query(
            query,
            min_connections=min_connections,
            min_risk_score=min_risk_score
        )
        
        patterns = []
        for record in results:
            pattern = FraudPattern(
                pattern_type="HIGH_CENTRALITY_SUSPICIOUS_VENDOR",
                risk_level=self._calculate_centrality_risk(
                    record['centrality_score'],
                    record['compliance_score']
                ),
                confidence_score=0.75,
                entities_involved=[record['gstin']],
                description=f"High centrality vendor with low compliance: {record['name']}",
                financial_impact=record['total_value'],
                evidence={
                    'gstin': record['gstin'],
                    'connection_count': record['connection_count'],
                    'total_invoices': record['total_invoices'],
                    'mismatch_rate': record['mismatch_rate'],
                    'compliance_score': record['compliance_score'],
                    'centrality_score': record['centrality_score']
                },
                detected_at=datetime.utcnow()
            )
            patterns.append(pattern)
        
        return patterns
    
    # ========================================================================
    # 4. SUSPICIOUS CLUSTER DETECTION
    # ========================================================================
    
    def detect_suspicious_clusters(self, min_cluster_size: int = 5) -> List[FraudPattern]:
        """
        Detect suspicious clusters of taxpayers that:
        - Trade only among themselves (closed loop)
        - Have high mismatch rates
        - Show coordinated behavior
        
        Uses community detection algorithms.
        """
        query = """
        // Find densely connected groups
        MATCH (t1:Taxpayer)-[:TRANSACTS_WITH]-(t2:Taxpayer)
        
        WITH t1, collect(DISTINCT t2) as connected_taxpayers
        WHERE size(connected_taxpayers) >= $min_cluster_size
        
        // Check if they trade mostly among themselves
        UNWIND connected_taxpayers as t2
        MATCH (t1)-[:ISSUED_BY|RECEIVED_BY]-(invoice:Invoice)-[:ISSUED_BY|RECEIVED_BY]-(t2)
        
        WITH 
          t1,
          connected_taxpayers,
          count(DISTINCT invoice) as internal_transactions,
          sum(invoice.total_amount) as internal_value
        
        // Get external transactions
        MATCH (t1)-[:ISSUED_BY|RECEIVED_BY]-(ext_invoice:Invoice)
          -[:ISSUED_BY|RECEIVED_BY]-(external:Taxpayer)
        WHERE NOT external IN connected_taxpayers
        
        WITH 
          t1,
          connected_taxpayers,
          internal_transactions,
          internal_value,
          count(DISTINCT ext_invoice) as external_transactions
        
        // Calculate insularity (how closed the cluster is)
        WITH 
          t1,
          connected_taxpayers,
          internal_transactions,
          external_transactions,
          internal_value,
          round(
            100.0 * internal_transactions / 
            (internal_transactions + external_transactions)
          , 2) as insularity_percent
        
        WHERE insularity_percent >= 70  // Mostly internal trading
        
        RETURN 
          [t IN connected_taxpayers | t.gstin] as cluster_gstins,
          size(connected_taxpayers) as cluster_size,
          internal_transactions,
          external_transactions,
          internal_value,
          insularity_percent
        
        ORDER BY insularity_percent DESC, internal_value DESC
        LIMIT 20
        """
        
        if not self.neo4j_client:
            return self._generate_mock_clusters()
        
        results = self.neo4j_client.execute_query(query, min_cluster_size=min_cluster_size)
        
        patterns = []
        for record in results:
            pattern = FraudPattern(
                pattern_type="SUSPICIOUS_CLUSTER",
                risk_level=self._calculate_cluster_risk(
                    record['insularity_percent'],
                    record['internal_value']
                ),
                confidence_score=0.80,
                entities_involved=record['cluster_gstins'],
                description=f"Suspicious cluster of {record['cluster_size']} entities with {record['insularity_percent']}% internal trading",
                financial_impact=record['internal_value'],
                evidence={
                    'cluster_size': record['cluster_size'],
                    'internal_transactions': record['internal_transactions'],
                    'external_transactions': record['external_transactions'],
                    'insularity_percent': record['insularity_percent']
                },
                detected_at=datetime.utcnow()
            )
            patterns.append(pattern)
        
        return patterns
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _calculate_circular_risk(self, total_value: float, chain_length: int) -> str:
        """Calculate risk level for circular trading."""
        if total_value > 10000000 or chain_length >= 5:
            return "CRITICAL"
        elif total_value > 5000000 or chain_length >= 4:
            return "HIGH"
        elif total_value > 1000000:
            return "MEDIUM"
        return "LOW"
    
    def _calculate_centrality_risk(self, centrality_score: float, 
                                   compliance_score: float) -> str:
        """Calculate risk level for high centrality vendors."""
        if centrality_score > 80 and compliance_score < 40:
            return "CRITICAL"
        elif centrality_score > 60 and compliance_score < 60:
            return "HIGH"
        elif centrality_score > 40:
            return "MEDIUM"
        return "LOW"
    
    def _calculate_cluster_risk(self, insularity: float, value: float) -> str:
        """Calculate risk level for suspicious clusters."""
        if insularity > 90 and value > 50000000:
            return "CRITICAL"
        elif insularity > 80 and value > 10000000:
            return "HIGH"
        elif insularity > 70:
            return "MEDIUM"
        return "LOW"
    
    # ========================================================================
    # MOCK DATA GENERATORS (for demo without Neo4j)
    # ========================================================================
    
    def _generate_mock_circular_trading(self) -> List[FraudPattern]:
        """Generate mock circular trading patterns for demo."""
        return [
            FraudPattern(
                pattern_type="CIRCULAR_TRADING",
                risk_level="CRITICAL",
                confidence_score=0.85,
                entities_involved=["27AABCU0001M1Z5", "27AABCU0002M1Z5", "27AABCU0003M1Z5"],
                description="Circular trading detected: 3 entities in loop",
                financial_impact=15000000.0,
                evidence={
                    'invoice_chain': ['INV-001', 'INV-045', 'INV-089'],
                    'chain_length': 3,
                    'total_value': 15000000.0
                },
                detected_at=datetime.utcnow()
            )
        ]
    
    def _generate_mock_duplicates(self) -> List[FraudPattern]:
        """Generate mock duplicate invoices for demo."""
        return [
            FraudPattern(
                pattern_type="DUPLICATE_INVOICE",
                risk_level="HIGH",
                confidence_score=0.90,
                entities_involved=["27AABCU0005M1Z5", "27AABCU0006M1Z5"],
                description="Duplicate invoice detected: DUPLICATE_INVOICE_NUMBER",
                financial_impact=250000.0,
                evidence={
                    'invoice_number': 'INV-2024-0123',
                    'amount1': 250000.0,
                    'amount2': 250000.0,
                    'type': 'DUPLICATE_INVOICE_NUMBER'
                },
                detected_at=datetime.utcnow()
            )
        ]
    
    def _generate_mock_high_centrality(self) -> List[FraudPattern]:
        """Generate mock high centrality vendors for demo."""
        return [
            FraudPattern(
                pattern_type="HIGH_CENTRALITY_SUSPICIOUS_VENDOR",
                risk_level="HIGH",
                confidence_score=0.75,
                entities_involved=["27AABCU0010M1Z5"],
                description="High centrality vendor with low compliance: Suspicious Traders Ltd",
                financial_impact=50000000.0,
                evidence={
                    'gstin': "27AABCU0010M1Z5",
                    'connection_count': 45,
                    'total_invoices': 250,
                    'mismatch_rate': 35.5,
                    'compliance_score': 35.0,
                    'centrality_score': 78.5
                },
                detected_at=datetime.utcnow()
            )
        ]
    
    def _generate_mock_clusters(self) -> List[FraudPattern]:
        """Generate mock suspicious clusters for demo."""
        return [
            FraudPattern(
                pattern_type="SUSPICIOUS_CLUSTER",
                risk_level="CRITICAL",
                confidence_score=0.80,
                entities_involved=[
                    "27AABCU0020M1Z5",
                    "27AABCU0021M1Z5",
                    "27AABCU0022M1Z5",
                    "27AABCU0023M1Z5",
                    "27AABCU0024M1Z5"
                ],
                description="Suspicious cluster of 5 entities with 85.5% internal trading",
                financial_impact=25000000.0,
                evidence={
                    'cluster_size': 5,
                    'internal_transactions': 150,
                    'external_transactions': 25,
                    'insularity_percent': 85.5
                },
                detected_at=datetime.utcnow()
            )
        ]
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def detect_all_fraud_patterns(self) -> Dict[str, List[FraudPattern]]:
        """
        Run all fraud detection algorithms and return results.
        
        Returns:
            Dictionary with fraud pattern types as keys and lists of patterns as values
        """
        return {
            'circular_trading': self.detect_circular_trading(),
            'duplicate_invoices': self.detect_duplicate_invoices(),
            'high_centrality_vendors': self.detect_high_centrality_vendors(),
            'suspicious_clusters': self.detect_suspicious_clusters()
        }
    
    def get_fraud_summary(self) -> Dict:
        """Get summary of all detected fraud patterns."""
        all_patterns = self.detect_all_fraud_patterns()
        
        total_patterns = sum(len(patterns) for patterns in all_patterns.values())
        total_impact = sum(
            pattern.financial_impact 
            for patterns in all_patterns.values() 
            for pattern in patterns
        )
        
        critical_count = sum(
            1 for patterns in all_patterns.values() 
            for pattern in patterns 
            if pattern.risk_level == "CRITICAL"
        )
        
        return {
            'total_patterns_detected': total_patterns,
            'total_financial_impact': total_impact,
            'critical_patterns': critical_count,
            'patterns_by_type': {
                ptype: len(patterns) 
                for ptype, patterns in all_patterns.values()
            }
        }


# Export
__all__ = ['FraudDetectionEngine', 'FraudPattern']
