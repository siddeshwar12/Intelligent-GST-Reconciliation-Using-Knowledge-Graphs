"""
Performance optimization module for GST Reconciliation System.

This module provides:
- Optimized Neo4j queries with pagination
- Redis caching layer
- Batch processing utilities
- Performance monitoring tools
"""

from .optimized_queries import (
    get_purchase_invoices_paginated,
    count_purchase_invoices,
    get_mismatches_paginated,
    validate_itc_chain_optimized,
    find_gstr2b_matches_optimized,
    get_dashboard_summary_optimized,
    get_vendor_risk_summary_batch,
    batch_create_matches,
    batch_create_mismatches,
    batch_update_vendor_scores,
    explain_query,
    profile_query
)

from .redis_cache import (
    RedisCache,
    ReconciliationCache,
    CacheConfig,
    get_cache,
    cached
)

from .batch_processor import (
    BatchProcessor,
    ReconciliationBatchProcessor,
    VendorRiskBatchProcessor
)


__all__ = [
    # Optimized queries
    "get_purchase_invoices_paginated",
    "count_purchase_invoices",
    "get_mismatches_paginated",
    "validate_itc_chain_optimized",
    "find_gstr2b_matches_optimized",
    "get_dashboard_summary_optimized",
    "get_vendor_risk_summary_batch",
    "batch_create_matches",
    "batch_create_mismatches",
    "batch_update_vendor_scores",
    "explain_query",
    "profile_query",
    
    # Caching
    "RedisCache",
    "ReconciliationCache",
    "CacheConfig",
    "get_cache",
    "cached",
    
    # Batch processing
    "BatchProcessor",
    "ReconciliationBatchProcessor",
    "VendorRiskBatchProcessor",
]


__version__ = "1.0.0"
__author__ = "GST Reconciliation Team"
