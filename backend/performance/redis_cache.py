"""
Redis caching layer for Neo4j query results.

This module provides intelligent caching for expensive Neo4j queries to improve
performance when handling 10k+ invoices.

Features:
- Automatic cache key generation
- TTL-based expiration
- Cache invalidation strategies
- Batch caching support
- Cache statistics
"""

import json
import hashlib
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
import redis
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)


class CacheConfig:
    """Cache configuration constants."""
    
    # TTL values (in seconds)
    TTL_SHORT = 300  # 5 minutes - for frequently changing data
    TTL_MEDIUM = 1800  # 30 minutes - for moderately stable data
    TTL_LONG = 3600  # 1 hour - for stable data
    TTL_VERY_LONG = 86400  # 24 hours - for rarely changing data
    
    # Cache key prefixes
    PREFIX_INVOICE = "invoice"
    PREFIX_TAXPAYER = "taxpayer"
    PREFIX_MISMATCH = "mismatch"
    PREFIX_VENDOR = "vendor"
    PREFIX_DASHBOARD = "dashboard"
    PREFIX_RECONCILIATION = "reconciliation"
    PREFIX_ITC_VALIDATION = "itc_validation"
    
    # Cache invalidation patterns
    INVALIDATE_ON_WRITE = True
    INVALIDATE_ON_RECONCILIATION = True


class RedisCache:
    """
    Redis cache manager for Neo4j query results.
    
    Environment Variables:
        REDIS_HOST: Redis host (default: localhost)
        REDIS_PORT: Redis port (default: 6379)
        REDIS_DB: Redis database number (default: 0)
        REDIS_PASSWORD: Redis password (optional)
        REDIS_ENABLED: Enable/disable caching (default: true)
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            enabled: Enable/disable caching
        """
        self.enabled = enabled
        self._client: Optional[redis.Redis] = None
        
        if self.enabled:
            try:
                self._client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self._client.ping()
                logger.info(f"Redis cache connected: {host}:{port}")
            except RedisError as e:
                logger.warning(f"Redis connection failed: {e}. Caching disabled.")
                self.enabled = False
                self._client = None
    
    def _generate_cache_key(
        self,
        prefix: str,
        params: Dict[str, Any]
    ) -> str:
        """
        Generate cache key from prefix and parameters.
        
        Args:
            prefix: Cache key prefix
            params: Query parameters
            
        Returns:
            Cache key string
        """
        # Sort params for consistent key generation
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()
        return f"{prefix}:{param_hash}"
    
    def get(
        self,
        prefix: str,
        params: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Get cached value.
        
        Args:
            prefix: Cache key prefix
            params: Query parameters
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self._client:
            return None
        
        try:
            key = self._generate_cache_key(prefix, params)
            value = self._client.get(key)
            
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            else:
                logger.debug(f"Cache MISS: {key}")
                return None
                
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(
        self,
        prefix: str,
        params: Dict[str, Any],
        value: Any,
        ttl: int = CacheConfig.TTL_MEDIUM
    ) -> bool:
        """
        Set cached value with TTL.
        
        Args:
            prefix: Cache key prefix
            params: Query parameters
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self._client:
            return False
        
        try:
            key = self._generate_cache_key(prefix, params)
            serialized = json.dumps(value)
            self._client.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
            
        except (RedisError, TypeError) as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(
        self,
        prefix: str,
        params: Dict[str, Any]
    ) -> bool:
        """
        Delete cached value.
        
        Args:
            prefix: Cache key prefix
            params: Query parameters
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self._client:
            return False
        
        try:
            key = self._generate_cache_key(prefix, params)
            self._client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
            
        except RedisError as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def invalidate_pattern(
        self,
        pattern: str
    ) -> int:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "invoice:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self._client:
            return 0
        
        try:
            keys = self._client.keys(pattern)
            if keys:
                deleted = self._client.delete(*keys)
                logger.info(f"Cache INVALIDATE: {pattern} ({deleted} keys)")
                return deleted
            return 0
            
        except RedisError as e:
            logger.error(f"Cache invalidate error: {e}")
            return 0
    
    def invalidate_taxpayer(
        self,
        taxpayer_gstin: str
    ) -> int:
        """
        Invalidate all cache entries for a taxpayer.
        
        Args:
            taxpayer_gstin: Taxpayer GSTIN
            
        Returns:
            Number of keys deleted
        """
        patterns = [
            f"{CacheConfig.PREFIX_INVOICE}:*{taxpayer_gstin}*",
            f"{CacheConfig.PREFIX_MISMATCH}:*{taxpayer_gstin}*",
            f"{CacheConfig.PREFIX_DASHBOARD}:*{taxpayer_gstin}*",
            f"{CacheConfig.PREFIX_RECONCILIATION}:*{taxpayer_gstin}*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.invalidate_pattern(pattern)
        
        return total_deleted
    
    def invalidate_period(
        self,
        period: str
    ) -> int:
        """
        Invalidate all cache entries for a period.
        
        Args:
            period: Period in MMYYYY format
            
        Returns:
            Number of keys deleted
        """
        patterns = [
            f"{CacheConfig.PREFIX_INVOICE}:*{period}*",
            f"{CacheConfig.PREFIX_MISMATCH}:*{period}*",
            f"{CacheConfig.PREFIX_DASHBOARD}:*{period}*",
            f"{CacheConfig.PREFIX_RECONCILIATION}:*{period}*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.invalidate_pattern(pattern)
        
        return total_deleted
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        if not self.enabled or not self._client:
            return {"enabled": False}
        
        try:
            info = self._client.info("stats")
            return {
                "enabled": True,
                "total_keys": self._client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                ),
                "memory_used": info.get("used_memory_human", "N/A")
            }
            
        except RedisError as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"enabled": True, "error": str(e)}
    
    def _calculate_hit_rate(
        self,
        hits: int,
        misses: int
    ) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    def clear_all(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self._client:
            return False
        
        try:
            self._client.flushdb()
            logger.info("Cache cleared")
            return True
            
        except RedisError as e:
            logger.error(f"Failed to clear cache: {e}")
            return False


def cached(
    prefix: str,
    ttl: int = CacheConfig.TTL_MEDIUM,
    key_params: Optional[List[str]] = None
):
    """
    Decorator for caching function results.
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_params: List of parameter names to use for cache key
        
    Example:
        @cached(prefix="invoice", ttl=300, key_params=["taxpayer_gstin", "period"])
        def get_invoices(taxpayer_gstin: str, period: str):
            # Expensive query
            return results
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache instance (assumes it's passed as first arg or in kwargs)
            cache = None
            if args and isinstance(args[0], RedisCache):
                cache = args[0]
            elif 'cache' in kwargs:
                cache = kwargs['cache']
            
            if not cache or not cache.enabled:
                return func(*args, **kwargs)
            
            # Build cache key from specified parameters
            cache_params = {}
            if key_params:
                # Get function signature
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                
                # Extract values for key_params
                for i, param_name in enumerate(param_names):
                    if param_name in key_params:
                        if i < len(args):
                            cache_params[param_name] = args[i]
                        elif param_name in kwargs:
                            cache_params[param_name] = kwargs[param_name]
            
            # Try to get from cache
            cached_value = cache.get(prefix, cache_params)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(prefix, cache_params, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# ============================================================================
# CACHE STRATEGIES FOR SPECIFIC QUERIES
# ============================================================================

class ReconciliationCache:
    """Cache strategies for reconciliation queries."""
    
    def __init__(self, cache: RedisCache):
        self.cache = cache
    
    def get_purchase_invoices(
        self,
        taxpayer_gstin: str,
        period: str,
        page: int = 1
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached purchase invoices."""
        params = {
            "taxpayer_gstin": taxpayer_gstin,
            "period": period,
            "page": page
        }
        return self.cache.get(CacheConfig.PREFIX_INVOICE, params)
    
    def set_purchase_invoices(
        self,
        taxpayer_gstin: str,
        period: str,
        page: int,
        invoices: List[Dict[str, Any]]
    ) -> bool:
        """Cache purchase invoices."""
        params = {
            "taxpayer_gstin": taxpayer_gstin,
            "period": period,
            "page": page
        }
        return self.cache.set(
            CacheConfig.PREFIX_INVOICE,
            params,
            invoices,
            CacheConfig.TTL_MEDIUM
        )
    
    def get_dashboard_summary(
        self,
        taxpayer_gstin: str,
        period: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached dashboard summary."""
        params = {
            "taxpayer_gstin": taxpayer_gstin,
            "period": period
        }
        return self.cache.get(CacheConfig.PREFIX_DASHBOARD, params)
    
    def set_dashboard_summary(
        self,
        taxpayer_gstin: str,
        period: str,
        summary: Dict[str, Any]
    ) -> bool:
        """Cache dashboard summary."""
        params = {
            "taxpayer_gstin": taxpayer_gstin,
            "period": period
        }
        return self.cache.set(
            CacheConfig.PREFIX_DASHBOARD,
            params,
            summary,
            CacheConfig.TTL_SHORT  # Dashboard data changes frequently
        )
    
    def get_itc_validation(
        self,
        invoice_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached ITC validation result."""
        params = {"invoice_id": invoice_id}
        return self.cache.get(CacheConfig.PREFIX_ITC_VALIDATION, params)
    
    def set_itc_validation(
        self,
        invoice_id: str,
        validation_result: Dict[str, Any]
    ) -> bool:
        """Cache ITC validation result."""
        params = {"invoice_id": invoice_id}
        return self.cache.set(
            CacheConfig.PREFIX_ITC_VALIDATION,
            params,
            validation_result,
            CacheConfig.TTL_LONG  # ITC validation is stable
        )
    
    def invalidate_reconciliation(
        self,
        taxpayer_gstin: str,
        period: str
    ) -> int:
        """Invalidate all reconciliation-related cache for taxpayer and period."""
        total_deleted = 0
        
        # Invalidate invoices
        total_deleted += self.cache.invalidate_pattern(
            f"{CacheConfig.PREFIX_INVOICE}:*{taxpayer_gstin}*{period}*"
        )
        
        # Invalidate mismatches
        total_deleted += self.cache.invalidate_pattern(
            f"{CacheConfig.PREFIX_MISMATCH}:*{taxpayer_gstin}*{period}*"
        )
        
        # Invalidate dashboard
        total_deleted += self.cache.invalidate_pattern(
            f"{CacheConfig.PREFIX_DASHBOARD}:*{taxpayer_gstin}*{period}*"
        )
        
        # Invalidate reconciliation results
        total_deleted += self.cache.invalidate_pattern(
            f"{CacheConfig.PREFIX_RECONCILIATION}:*{taxpayer_gstin}*{period}*"
        )
        
        logger.info(
            f"Invalidated reconciliation cache for {taxpayer_gstin}/{period}: "
            f"{total_deleted} keys"
        )
        
        return total_deleted


# Singleton instance
_cache_instance: Optional[RedisCache] = None


def get_cache(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None,
    enabled: bool = True,
    force_new: bool = False
) -> RedisCache:
    """
    Get or create Redis cache instance (singleton).
    
    Args:
        host: Redis host
        port: Redis port
        db: Redis database number
        password: Redis password
        enabled: Enable/disable caching
        force_new: Force creation of new instance
        
    Returns:
        RedisCache instance
    """
    global _cache_instance
    
    if force_new or _cache_instance is None:
        _cache_instance = RedisCache(
            host=host,
            port=port,
            db=db,
            password=password,
            enabled=enabled
        )
    
    return _cache_instance
