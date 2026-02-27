"""
Financial Risk Classification Module.

This module provides comprehensive risk assessment and classification
for GST reconciliation mismatches, separate from reconciliation logic.

Risk Levels:
- CRITICAL: >10% variance or critical compliance issues
- HIGH: 5-10% variance or significant issues  
- MEDIUM: 2-5% variance or moderate issues
- LOW: <2% variance or minor issues
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import math


class RiskLevel(str, Enum):
    """Risk level enumeration."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MismatchCategory(str, Enum):
    """Mismatch category for risk assessment."""
    AMOUNT_VARIANCE = "AMOUNT_VARIANCE"
    TAX_VARIANCE = "TAX_VARIANCE"
    MISSING_INVOICE = "MISSING_INVOICE"
    DATE_DISCREPANCY = "DATE_DISCREPANCY"
    GSTIN_MISMATCH = "GSTIN_MISMATCH"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    COMPLIANCE_VIOLATION = "COMPLIANCE_VIOLATION"


class RiskFactor(str, Enum):
    """Risk factors that influence classification."""
    HIGH_VALUE_TRANSACTION = "HIGH_VALUE_TRANSACTION"
    FREQUENT_SUPPLIER = "FREQUENT_SUPPLIER"
    NEW_SUPPLIER = "NEW_SUPPLIER"
    CROSS_STATE_TRANSACTION = "CROSS_STATE_TRANSACTION"
    REVERSE_CHARGE_APPLICABLE = "REVERSE_CHARGE_APPLICABLE"
    EXPORT_TRANSACTION = "EXPORT_TRANSACTION"
    COMPOSITION_SCHEME = "COMPOSITION_SCHEME"
    REPEAT_MISMATCH = "REPEAT_MISMATCH"
    AUDIT_HISTORY = "AUDIT_HISTORY"
    SEASONAL_VARIANCE = "SEASONAL_VARIANCE"


@dataclass
class RiskAssessment:
    """Risk assessment result."""
    risk_level: RiskLevel
    risk_score: float  # 0-100 scale
    primary_factors: List[RiskFactor]
    financial_impact: float
    compliance_impact: str
    recommendation: str
    urgency_days: int
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "primary_factors": [f.value for f in self.primary_factors],
            "financial_impact": self.financial_impact,
            "compliance_impact": self.compliance_impact,
            "recommendation": self.recommendation,
            "urgency_days": self.urgency_days,
            "details": self.details
        }


@dataclass
class MismatchContext:
    """Context information for mismatch classification."""
    mismatch_type: str
    amount_difference: float
    percentage_variance: float
    base_amount: float
    tax_amount: float
    supplier_gstin: str
    buyer_gstin: str
    invoice_date: datetime
    detection_date: datetime
    supplier_history: Optional[Dict[str, Any]] = None
    transaction_context: Optional[Dict[str, Any]] = None


class FinancialRiskClassifier:
    """
    Financial risk classifier for GST reconciliation mismatches.
    
    Provides comprehensive risk assessment based on financial impact,
    compliance requirements, and business context.
    """
    
    def __init__(self):
        """Initialize classifier with default thresholds."""
        # Amount thresholds (in INR)
        self.high_value_threshold = 500000  # 5 Lakh
        self.medium_value_threshold = 100000  # 1 Lakh
        self.low_value_threshold = 10000  # 10 Thousand
        
        # Variance thresholds (percentage)
        self.critical_variance_threshold = 10.0
        self.high_variance_threshold = 5.0
        self.medium_variance_threshold = 2.0
        
        # Time thresholds (days)
        self.critical_age_threshold = 90
        self.high_age_threshold = 60
        self.medium_age_threshold = 30
        
        # Compliance thresholds
        self.max_itc_claim_days = 180  # ITC claim time limit
        self.gst_return_due_days = 20  # GST return filing due
    
    def classify_mismatch(self, context: MismatchContext) -> RiskAssessment:
        """
        Classify mismatch risk based on context.
        
        Args:
            context: Mismatch context information
            
        Returns:
            RiskAssessment with detailed classification
        """
        # Calculate base risk score
        base_score = self._calculate_base_risk_score(context)
        
        # Apply risk factors
        risk_factors = self._identify_risk_factors(context)
        adjusted_score = self._apply_risk_factors(base_score, risk_factors)
        
        # Determine risk level
        risk_level = self._determine_risk_level(adjusted_score, context)
        
        # Calculate financial impact
        financial_impact = self._calculate_financial_impact(context)
        
        # Assess compliance impact
        compliance_impact = self._assess_compliance_impact(context)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(risk_level, context)
        
        # Determine urgency
        urgency_days = self._calculate_urgency(risk_level, context)
        
        # Compile details
        details = self._compile_assessment_details(context, risk_factors, base_score, adjusted_score)
        
        return RiskAssessment(
            risk_level=risk_level,
            risk_score=adjusted_score,
            primary_factors=risk_factors,
            financial_impact=financial_impact,
            compliance_impact=compliance_impact,
            recommendation=recommendation,
            urgency_days=urgency_days,
            details=details
        )
    
    def _calculate_base_risk_score(self, context: MismatchContext) -> float:
        """Calculate base risk score (0-100)."""
        score = 0.0
        
        # Variance-based scoring (40% weight)
        variance_score = min(context.percentage_variance * 4, 40)  # Cap at 40
        score += variance_score
        
        # Amount-based scoring (30% weight)
        if context.base_amount >= self.high_value_threshold:
            amount_score = 30
        elif context.base_amount >= self.medium_value_threshold:
            amount_score = 20
        elif context.base_amount >= self.low_value_threshold:
            amount_score = 10
        else:
            amount_score = 5
        score += amount_score
        
        # Mismatch type scoring (20% weight)
        type_scores = {
            "MISSING_IN_GSTR2B": 20,
            "GSTIN_MISMATCH": 18,
            "TAX_AMOUNT_MISMATCH": 15,
            "AMOUNT_MISMATCH": 12,
            "DATE_MISMATCH": 8,
            "DUPLICATE_ENTRY": 10
        }
        score += type_scores.get(context.mismatch_type, 10)
        
        # Age-based scoring (10% weight)
        age_days = (context.detection_date - context.invoice_date).days
        if age_days > self.critical_age_threshold:
            age_score = 10
        elif age_days > self.high_age_threshold:
            age_score = 7
        elif age_days > self.medium_age_threshold:
            age_score = 4
        else:
            age_score = 2
        score += age_score
        
        return min(score, 100)  # Cap at 100
    
    def _identify_risk_factors(self, context: MismatchContext) -> List[RiskFactor]:
        """Identify applicable risk factors."""
        factors = []
        
        # High value transaction
        if context.base_amount >= self.high_value_threshold:
            factors.append(RiskFactor.HIGH_VALUE_TRANSACTION)
        
        # Cross-state transaction
        supplier_state = context.supplier_gstin[:2] if context.supplier_gstin else ""
        buyer_state = context.buyer_gstin[:2] if context.buyer_gstin else ""
        if supplier_state != buyer_state and supplier_state and buyer_state:
            factors.append(RiskFactor.CROSS_STATE_TRANSACTION)
        
        # Transaction age
        age_days = (context.detection_date - context.invoice_date).days
        if age_days > self.critical_age_threshold:
            factors.append(RiskFactor.AUDIT_HISTORY)
        
        # Supplier history analysis
        if context.supplier_history:
            supplier_risk = self._analyze_supplier_history(context.supplier_history)
            factors.extend(supplier_risk)
        
        # Transaction context analysis
        if context.transaction_context:
            transaction_risk = self._analyze_transaction_context(context.transaction_context)
            factors.extend(transaction_risk)
        
        return factors
    
    def _analyze_supplier_history(self, history: Dict[str, Any]) -> List[RiskFactor]:
        """Analyze supplier history for risk factors."""
        factors = []
        
        # New supplier (less than 6 months)
        if history.get("months_active", 12) < 6:
            factors.append(RiskFactor.NEW_SUPPLIER)
        
        # Frequent supplier (high transaction volume)
        if history.get("monthly_transactions", 0) > 50:
            factors.append(RiskFactor.FREQUENT_SUPPLIER)
        
        # Repeat mismatch pattern
        if history.get("mismatch_rate", 0) > 0.1:  # >10% mismatch rate
            factors.append(RiskFactor.REPEAT_MISMATCH)
        
        return factors
    
    def _analyze_transaction_context(self, context: Dict[str, Any]) -> List[RiskFactor]:
        """Analyze transaction context for risk factors."""
        factors = []
        
        # Reverse charge applicable
        if context.get("reverse_charge", False):
            factors.append(RiskFactor.REVERSE_CHARGE_APPLICABLE)
        
        # Export transaction
        if context.get("is_export", False):
            factors.append(RiskFactor.EXPORT_TRANSACTION)
        
        # Composition scheme
        if context.get("composition_scheme", False):
            factors.append(RiskFactor.COMPOSITION_SCHEME)
        
        return factors
    
    def _apply_risk_factors(self, base_score: float, factors: List[RiskFactor]) -> float:
        """Apply risk factor multipliers to base score."""
        multiplier = 1.0
        
        # Risk factor multipliers
        factor_multipliers = {
            RiskFactor.HIGH_VALUE_TRANSACTION: 1.2,
            RiskFactor.FREQUENT_SUPPLIER: 0.9,  # Lower risk for known suppliers
            RiskFactor.NEW_SUPPLIER: 1.3,
            RiskFactor.CROSS_STATE_TRANSACTION: 1.1,
            RiskFactor.REVERSE_CHARGE_APPLICABLE: 1.4,
            RiskFactor.EXPORT_TRANSACTION: 1.2,
            RiskFactor.COMPOSITION_SCHEME: 0.8,  # Lower complexity
            RiskFactor.REPEAT_MISMATCH: 1.5,
            RiskFactor.AUDIT_HISTORY: 1.3,
            RiskFactor.SEASONAL_VARIANCE: 0.9
        }
        
        for factor in factors:
            multiplier *= factor_multipliers.get(factor, 1.0)
        
        # Cap multiplier effect
        multiplier = min(multiplier, 2.0)
        
        return min(base_score * multiplier, 100)
    
    def _determine_risk_level(self, score: float, context: MismatchContext) -> RiskLevel:
        """Determine risk level based on score and context."""
        # Override rules for specific conditions
        
        # Critical overrides
        if (context.percentage_variance > 20 or 
            context.base_amount > 1000000 or  # 10 Lakh
            context.mismatch_type == "GSTIN_MISMATCH"):
            return RiskLevel.CRITICAL
        
        # Score-based classification
        if score >= 80:
            return RiskLevel.CRITICAL
        elif score >= 60:
            return RiskLevel.HIGH
        elif score >= 40:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _calculate_financial_impact(self, context: MismatchContext) -> float:
        """Calculate potential financial impact."""
        # Base impact is the amount difference
        base_impact = abs(context.amount_difference)
        
        # Add potential ITC impact
        itc_impact = context.tax_amount if context.mismatch_type == "MISSING_IN_GSTR2B" else 0
        
        # Add penalty risk (18% interest + penalty)
        age_days = (context.detection_date - context.invoice_date).days
        if age_days > self.max_itc_claim_days:
            penalty_risk = base_impact * 0.18 * (age_days / 365)  # 18% annual
        else:
            penalty_risk = 0
        
        return base_impact + itc_impact + penalty_risk
    
    def _assess_compliance_impact(self, context: MismatchContext) -> str:
        """Assess compliance impact."""
        age_days = (context.detection_date - context.invoice_date).days
        
        if context.mismatch_type == "GSTIN_MISMATCH":
            return "Invalid ITC claim - immediate correction required"
        elif context.mismatch_type == "MISSING_IN_GSTR2B":
            if age_days > self.max_itc_claim_days:
                return "ITC claim time limit exceeded - permanent loss"
            else:
                return "Risk of ITC loss if not resolved timely"
        elif context.percentage_variance > self.critical_variance_threshold:
            return "Significant variance may trigger audit scrutiny"
        elif age_days > self.critical_age_threshold:
            return "Aged mismatch increases audit risk"
        else:
            return "Standard compliance monitoring required"
    
    def _generate_recommendation(self, risk_level: RiskLevel, context: MismatchContext) -> str:
        """Generate action recommendation."""
        recommendations = {
            RiskLevel.CRITICAL: "IMMEDIATE ACTION REQUIRED: Escalate to senior management and resolve within 24 hours",
            RiskLevel.HIGH: "HIGH PRIORITY: Assign dedicated resource and resolve within 3-5 business days",
            RiskLevel.MEDIUM: "MEDIUM PRIORITY: Include in weekly reconciliation cycle, resolve within 15 days",
            RiskLevel.LOW: "LOW PRIORITY: Monitor and resolve during monthly reconciliation"
        }
        
        base_recommendation = recommendations[risk_level]
        
        # Add specific actions based on mismatch type
        if context.mismatch_type == "GSTIN_MISMATCH":
            base_recommendation += ". Verify supplier GSTIN and correct immediately."
        elif context.mismatch_type == "MISSING_IN_GSTR2B":
            base_recommendation += ". Contact supplier to ensure GSTR-1 filing."
        elif context.percentage_variance > 10:
            base_recommendation += ". Conduct detailed invoice verification with supplier."
        
        return base_recommendation
    
    def _calculate_urgency(self, risk_level: RiskLevel, context: MismatchContext) -> int:
        """Calculate resolution urgency in days."""
        base_urgency = {
            RiskLevel.CRITICAL: 1,
            RiskLevel.HIGH: 5,
            RiskLevel.MEDIUM: 15,
            RiskLevel.LOW: 30
        }
        
        urgency = base_urgency[risk_level]
        
        # Adjust based on ITC claim deadline
        age_days = (context.detection_date - context.invoice_date).days
        days_to_deadline = self.max_itc_claim_days - age_days
        
        if days_to_deadline < urgency and days_to_deadline > 0:
            urgency = max(days_to_deadline - 5, 1)  # 5-day buffer
        
        return urgency
    
    def _compile_assessment_details(
        self, 
        context: MismatchContext, 
        factors: List[RiskFactor], 
        base_score: float, 
        final_score: float
    ) -> Dict[str, Any]:
        """Compile detailed assessment information."""
        return {
            "base_risk_score": base_score,
            "final_risk_score": final_score,
            "risk_factors_applied": [f.value for f in factors],
            "mismatch_details": {
                "type": context.mismatch_type,
                "amount_difference": context.amount_difference,
                "percentage_variance": context.percentage_variance,
                "base_amount": context.base_amount,
                "tax_amount": context.tax_amount
            },
            "timeline": {
                "invoice_date": context.invoice_date.isoformat(),
                "detection_date": context.detection_date.isoformat(),
                "age_days": (context.detection_date - context.invoice_date).days,
                "itc_deadline": (context.invoice_date + timedelta(days=self.max_itc_claim_days)).isoformat()
            },
            "thresholds_used": {
                "critical_variance": self.critical_variance_threshold,
                "high_variance": self.high_variance_threshold,
                "medium_variance": self.medium_variance_threshold,
                "high_value": self.high_value_threshold,
                "medium_value": self.medium_value_threshold
            }
        }
    
    def classify_batch(self, contexts: List[MismatchContext]) -> List[RiskAssessment]:
        """Classify multiple mismatches in batch."""
        return [self.classify_mismatch(context) for context in contexts]
    
    def get_risk_distribution(self, assessments: List[RiskAssessment]) -> Dict[str, Any]:
        """Get risk distribution statistics."""
        if not assessments:
            return {}
        
        # Count by risk level
        risk_counts = {level.value: 0 for level in RiskLevel}
        total_financial_impact = 0
        
        for assessment in assessments:
            risk_counts[assessment.risk_level.value] += 1
            total_financial_impact += assessment.financial_impact
        
        # Calculate percentages
        total = len(assessments)
        risk_percentages = {level: (count / total) * 100 for level, count in risk_counts.items()}
        
        # Average risk score
        avg_risk_score = sum(a.risk_score for a in assessments) / total
        
        return {
            "total_mismatches": total,
            "risk_distribution": {
                "counts": risk_counts,
                "percentages": risk_percentages
            },
            "financial_impact": {
                "total": total_financial_impact,
                "average": total_financial_impact / total,
                "by_risk_level": self._financial_impact_by_risk(assessments)
            },
            "average_risk_score": avg_risk_score,
            "urgency_summary": self._urgency_summary(assessments)
        }
    
    def _financial_impact_by_risk(self, assessments: List[RiskAssessment]) -> Dict[str, float]:
        """Calculate financial impact by risk level."""
        impact_by_risk = {level.value: 0 for level in RiskLevel}
        
        for assessment in assessments:
            impact_by_risk[assessment.risk_level.value] += assessment.financial_impact
        
        return impact_by_risk
    
    def _urgency_summary(self, assessments: List[RiskAssessment]) -> Dict[str, int]:
        """Calculate urgency summary."""
        urgent_1_day = sum(1 for a in assessments if a.urgency_days <= 1)
        urgent_1_week = sum(1 for a in assessments if 1 < a.urgency_days <= 7)
        urgent_1_month = sum(1 for a in assessments if 7 < a.urgency_days <= 30)
        
        return {
            "immediate_action_required": urgent_1_day,
            "resolve_within_week": urgent_1_week,
            "resolve_within_month": urgent_1_month,
            "routine_monitoring": len(assessments) - urgent_1_day - urgent_1_week - urgent_1_month
        }


# Convenience functions for easy integration

def classify_amount_mismatch(
    amount_difference: float,
    base_amount: float,
    supplier_gstin: str,
    buyer_gstin: str,
    invoice_date: datetime,
    detection_date: datetime = None
) -> RiskAssessment:
    """Classify amount mismatch risk."""
    classifier = FinancialRiskClassifier()
    
    context = MismatchContext(
        mismatch_type="AMOUNT_MISMATCH",
        amount_difference=amount_difference,
        percentage_variance=(abs(amount_difference) / base_amount) * 100,
        base_amount=base_amount,
        tax_amount=base_amount * 0.18,  # Assume 18% GST
        supplier_gstin=supplier_gstin,
        buyer_gstin=buyer_gstin,
        invoice_date=invoice_date,
        detection_date=detection_date or datetime.now()
    )
    
    return classifier.classify_mismatch(context)


def classify_missing_invoice(
    invoice_amount: float,
    tax_amount: float,
    supplier_gstin: str,
    buyer_gstin: str,
    invoice_date: datetime,
    detection_date: datetime = None
) -> RiskAssessment:
    """Classify missing invoice risk."""
    classifier = FinancialRiskClassifier()
    
    context = MismatchContext(
        mismatch_type="MISSING_IN_GSTR2B",
        amount_difference=invoice_amount,
        percentage_variance=100.0,  # Complete missing
        base_amount=invoice_amount,
        tax_amount=tax_amount,
        supplier_gstin=supplier_gstin,
        buyer_gstin=buyer_gstin,
        invoice_date=invoice_date,
        detection_date=detection_date or datetime.now()
    )
    
    return classifier.classify_mismatch(context)


def get_risk_level_from_variance(variance_percent: float) -> RiskLevel:
    """Get risk level from variance percentage."""
    if variance_percent > 10:
        return RiskLevel.CRITICAL
    elif variance_percent > 5:
        return RiskLevel.HIGH
    elif variance_percent > 2:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW