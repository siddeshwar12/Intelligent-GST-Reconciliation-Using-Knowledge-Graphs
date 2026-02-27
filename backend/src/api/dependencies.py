"""Dependency injection for FastAPI endpoints."""

import sys
from pathlib import Path
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from functools import lru_cache

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import services
try:
    from reconciliation.reconcile_service import GSTReconciliationService
    from reconciliation.classification import FinancialRiskClassifier
    from audit.audit_service import AuditTrailService
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False
    print("⚠ Service modules not available")

try:
    from ml.vendor_risk import VendorRiskPredictor
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    VendorRiskPredictor = None  # type: ignore
    print("⚠ ML module not available")

from graph.neo4j_connection import get_connection, Neo4jConnectionError


class ServiceContainer:
    """Container for service instances with lazy initialization."""
    
    _reconciliation_service: Optional[GSTReconciliationService] = None
    _risk_classifier: Optional[FinancialRiskClassifier] = None
    _audit_service: Optional[AuditTrailService] = None
    _vendor_risk_predictor: Optional[object] = None  # Use object instead of VendorRiskPredictor
    _neo4j_connection = None
    
    @classmethod
    def get_reconciliation_service(cls) -> GSTReconciliationService:
        """Get or create reconciliation service instance."""
        if not SERVICES_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Reconciliation service not available"
            )
        
        if cls._reconciliation_service is None:
            cls._reconciliation_service = GSTReconciliationService()
        
        return cls._reconciliation_service
    
    @classmethod
    def get_risk_classifier(cls) -> FinancialRiskClassifier:
        """Get or create risk classifier instance."""
        if not SERVICES_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Risk classifier not available"
            )
        
        if cls._risk_classifier is None:
            cls._risk_classifier = FinancialRiskClassifier()
        
        return cls._risk_classifier
    
    @classmethod
    def get_audit_service(cls) -> AuditTrailService:
        """Get or create audit trail service instance."""
        if not SERVICES_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Audit trail service not available"
            )
        
        if cls._audit_service is None:
            cls._audit_service = AuditTrailService()
        
        return cls._audit_service
    
    @classmethod
    def get_vendor_risk_predictor(cls):
        """Get or create vendor risk predictor instance."""
        if not ML_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vendor risk predictor not available"
            )
        
        if cls._vendor_risk_predictor is None:
            cls._vendor_risk_predictor = VendorRiskPredictor()
        
        return cls._vendor_risk_predictor
    
    @classmethod
    def get_neo4j_connection(cls):
        """Get or create Neo4j connection instance."""
        if cls._neo4j_connection is None:
            try:
                cls._neo4j_connection = get_connection()
            except Neo4jConnectionError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Neo4j connection failed: {str(e)}"
                )
        
        return cls._neo4j_connection
    
    @classmethod
    def reset_all(cls):
        """Reset all service instances (useful for testing)."""
        cls._reconciliation_service = None
        cls._risk_classifier = None
        cls._audit_service = None
        cls._vendor_risk_predictor = None
        cls._neo4j_connection = None


# Dependency functions for FastAPI
def get_reconciliation_service() -> GSTReconciliationService:
    """Dependency for reconciliation service."""
    return ServiceContainer.get_reconciliation_service()


def get_risk_classifier() -> FinancialRiskClassifier:
    """Dependency for risk classifier."""
    return ServiceContainer.get_risk_classifier()


def get_audit_service() -> AuditTrailService:
    """Dependency for audit trail service."""
    return ServiceContainer.get_audit_service()


def get_vendor_risk_predictor():
    """Dependency for vendor risk predictor."""
    return ServiceContainer.get_vendor_risk_predictor()


def get_neo4j_connection():
    """Dependency for Neo4j connection."""
    return ServiceContainer.get_neo4j_connection()


# Optional: API Key authentication dependency
def verify_api_key(api_key: Optional[str] = None) -> bool:
    """
    Verify API key for authentication.
    
    Args:
        api_key: API key from header
        
    Returns:
        True if valid
        
    Raises:
        HTTPException: If API key is invalid
    """
    # TODO: Implement actual API key verification
    # For now, allow all requests
    return True


# Optional: Rate limiting dependency
class RateLimiter:
    """Simple rate limiter for API endpoints."""
    
    def __init__(self, calls: int = 100, period: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            calls: Number of calls allowed
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
        self.requests = {}
    
    def __call__(self, client_id: str = "default") -> bool:
        """
        Check if request is allowed.
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if allowed
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        # TODO: Implement actual rate limiting logic
        # For now, allow all requests
        return True


# Create rate limiter instance
rate_limiter = RateLimiter(calls=100, period=60)


def check_rate_limit(client_id: str = "default") -> bool:
    """Dependency for rate limiting."""
    return rate_limiter(client_id)
