"""Database configuration."""

from .settings import settings


def get_neo4j_config() -> dict:
    """
    Get Neo4j configuration.
    
    Returns:
        Dictionary with Neo4j connection parameters
    """
    return {
        "uri": settings.neo4j_uri,
        "user": settings.neo4j_user,
        "password": settings.neo4j_password,
        "database": settings.neo4j_database,
    }


def get_redis_config() -> dict:
    """
    Get Redis configuration.
    
    Returns:
        Dictionary with Redis connection parameters
    """
    return {
        "host": settings.redis_host,
        "port": settings.redis_port,
        "db": settings.redis_db,
        "password": settings.redis_password if settings.redis_password else None,
    }
