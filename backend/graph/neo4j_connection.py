"""
Production-ready Neo4j connection module.

This module provides a robust Neo4j database connection with:
- Connection pooling
- Automatic retry logic
- Comprehensive logging
- Environment variable configuration
- Clean architecture principles
"""

import os
import logging
import time
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from neo4j import GraphDatabase, Driver, Session, Transaction
from neo4j.exceptions import (
    ServiceUnavailable,
    SessionExpired,
    TransientError,
    Neo4jError
)


# Configure logging
logger = logging.getLogger(__name__)


class Neo4jConnectionError(Exception):
    """Custom exception for Neo4j connection errors."""
    pass


class Neo4jConnection:
    """
    Production-ready Neo4j database connection manager.
    
    Features:
    - Connection pooling with configurable pool size
    - Automatic retry logic with exponential backoff
    - Comprehensive error handling and logging
    - Environment-based configuration
    - Context manager support for sessions
    - Health check capabilities
    
    Environment Variables:
        NEO4J_URI: Database URI (default: bolt://localhost:7687)
        NEO4J_USER: Database username (default: neo4j)
        NEO4J_PASSWORD: Database password (required)
        NEO4J_DATABASE: Database name (default: neo4j)
        NEO4J_MAX_CONNECTION_LIFETIME: Max connection lifetime in seconds (default: 3600)
        NEO4J_MAX_CONNECTION_POOL_SIZE: Max pool size (default: 50)
        NEO4J_CONNECTION_TIMEOUT: Connection timeout in seconds (default: 30)
        NEO4J_MAX_RETRY_ATTEMPTS: Max retry attempts (default: 3)
        NEO4J_RETRY_DELAY: Initial retry delay in seconds (default: 1)
    """
    
    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        max_connection_lifetime: Optional[int] = None,
        max_connection_pool_size: Optional[int] = None,
        connection_timeout: Optional[int] = None,
        max_retry_attempts: Optional[int] = None,
        retry_delay: Optional[float] = None
    ):
        """
        Initialize Neo4j connection.
        
        Args:
            uri: Neo4j URI (overrides NEO4J_URI env var)
            user: Database username (overrides NEO4J_USER env var)
            password: Database password (overrides NEO4J_PASSWORD env var)
            database: Database name (overrides NEO4J_DATABASE env var)
            max_connection_lifetime: Max connection lifetime in seconds
            max_connection_pool_size: Max connection pool size
            connection_timeout: Connection timeout in seconds
            max_retry_attempts: Maximum number of retry attempts
            retry_delay: Initial delay between retries in seconds
        
        Raises:
            Neo4jConnectionError: If connection cannot be established
        """
        # Load configuration from environment or parameters
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")
        
        # Connection pool configuration
        self.max_connection_lifetime = max_connection_lifetime or int(
            os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", "3600")
        )
        self.max_connection_pool_size = max_connection_pool_size or int(
            os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "50")
        )
        self.connection_timeout = connection_timeout or int(
            os.getenv("NEO4J_CONNECTION_TIMEOUT", "30")
        )
        
        # Retry configuration
        self.max_retry_attempts = max_retry_attempts or int(
            os.getenv("NEO4J_MAX_RETRY_ATTEMPTS", "3")
        )
        self.retry_delay = retry_delay or float(
            os.getenv("NEO4J_RETRY_DELAY", "1.0")
        )
        
        # Initialize driver first (before validation to avoid AttributeError in __del__)
        self._driver: Optional[Driver] = None
        
        # Validate configuration
        if not self.password:
            raise Neo4jConnectionError(
                "Neo4j password is required. Set NEO4J_PASSWORD environment variable."
            )
        
        # Establish connection
        self._connect()
    
    def _connect(self) -> None:
        """
        Establish connection to Neo4j database with retry logic.
        
        Raises:
            Neo4jConnectionError: If connection fails after all retries
        """
        attempt = 0
        last_error = None
        
        while attempt < self.max_retry_attempts:
            try:
                logger.info(
                    f"Attempting to connect to Neo4j at {self.uri} "
                    f"(attempt {attempt + 1}/{self.max_retry_attempts})"
                )
                
                self._driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password),
                    max_connection_lifetime=self.max_connection_lifetime,
                    max_connection_pool_size=self.max_connection_pool_size,
                    connection_acquisition_timeout=self.connection_timeout,
                    encrypted=False  # Set to True for production with SSL
                )
                
                # Verify connectivity
                self._driver.verify_connectivity()
                
                logger.info(
                    f"Successfully connected to Neo4j at {self.uri} "
                    f"(database: {self.database})"
                )
                return
                
            except ServiceUnavailable as e:
                last_error = e
                attempt += 1
                if attempt < self.max_retry_attempts:
                    delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.warning(
                        f"Neo4j connection failed: {str(e)}. "
                        f"Retrying in {delay} seconds..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"Failed to connect to Neo4j after {self.max_retry_attempts} attempts"
                    )
            
            except Exception as e:
                logger.error(f"Unexpected error connecting to Neo4j: {str(e)}")
                raise Neo4jConnectionError(f"Failed to connect to Neo4j: {str(e)}")
        
        # If we get here, all retries failed
        raise Neo4jConnectionError(
            f"Failed to connect to Neo4j after {self.max_retry_attempts} attempts. "
            f"Last error: {str(last_error)}"
        )
    
    @contextmanager
    def session(self, **kwargs) -> Session:
        """
        Context manager for Neo4j sessions.
        
        Args:
            **kwargs: Additional session parameters
        
        Yields:
            Session: Neo4j session object
        
        Example:
            with connection.session() as session:
                result = session.run("MATCH (n) RETURN n LIMIT 1")
        """
        if not self._driver:
            raise Neo4jConnectionError("Driver not initialized")
        
        session = self._driver.session(database=self.database, **kwargs)
        try:
            logger.debug(f"Session opened for database: {self.database}")
            yield session
        finally:
            session.close()
            logger.debug("Session closed")
    
    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        retry: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query with automatic retry logic.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            retry: Enable automatic retry on transient errors
        
        Returns:
            List of result records as dictionaries
        
        Raises:
            Neo4jConnectionError: If query execution fails
        
        Example:
            results = connection.execute_query(
                "MATCH (n:Person {name: $name}) RETURN n",
                parameters={"name": "Alice"}
            )
        """
        parameters = parameters or {}
        attempt = 0
        last_error = None
        
        max_attempts = self.max_retry_attempts if retry else 1
        
        while attempt < max_attempts:
            try:
                with self.session() as session:
                    logger.debug(f"Executing query: {query[:100]}...")
                    result = session.run(query, parameters)
                    records = [dict(record) for record in result]
                    logger.debug(f"Query returned {len(records)} records")
                    return records
                    
            except (ServiceUnavailable, SessionExpired, TransientError) as e:
                last_error = e
                attempt += 1
                if attempt < max_attempts:
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"Query failed with transient error: {str(e)}. "
                        f"Retrying in {delay} seconds... (attempt {attempt}/{max_attempts})"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Query failed after {max_attempts} attempts")
            
            except Neo4jError as e:
                logger.error(f"Neo4j error executing query: {str(e)}")
                raise Neo4jConnectionError(f"Query execution failed: {str(e)}")
            
            except Exception as e:
                logger.error(f"Unexpected error executing query: {str(e)}")
                raise Neo4jConnectionError(f"Unexpected error: {str(e)}")
        
        # If we get here, all retries failed
        raise Neo4jConnectionError(
            f"Query failed after {max_attempts} attempts. Last error: {str(last_error)}"
        )
    
    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        retry: bool = True
    ) -> Dict[str, int]:
        """
        Execute a write query (CREATE, UPDATE, DELETE) with retry logic.
        
        Args:
            query: Cypher write query
            parameters: Query parameters
            retry: Enable automatic retry on transient errors
        
        Returns:
            Dictionary with execution statistics
        
        Example:
            stats = connection.execute_write(
                "CREATE (n:Person {name: $name})",
                parameters={"name": "Bob"}
            )
        """
        parameters = parameters or {}
        attempt = 0
        last_error = None
        
        max_attempts = self.max_retry_attempts if retry else 1
        
        while attempt < max_attempts:
            try:
                with self.session() as session:
                    logger.debug(f"Executing write query: {query[:100]}...")
                    result = session.run(query, parameters)
                    summary = result.consume()
                    
                    stats = {
                        "nodes_created": summary.counters.nodes_created,
                        "nodes_deleted": summary.counters.nodes_deleted,
                        "relationships_created": summary.counters.relationships_created,
                        "relationships_deleted": summary.counters.relationships_deleted,
                        "properties_set": summary.counters.properties_set,
                        "labels_added": summary.counters.labels_added,
                        "labels_removed": summary.counters.labels_removed,
                    }
                    
                    logger.debug(f"Write query completed: {stats}")
                    return stats
                    
            except (ServiceUnavailable, SessionExpired, TransientError) as e:
                last_error = e
                attempt += 1
                if attempt < max_attempts:
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"Write query failed with transient error: {str(e)}. "
                        f"Retrying in {delay} seconds... (attempt {attempt}/{max_attempts})"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Write query failed after {max_attempts} attempts")
            
            except Neo4jError as e:
                logger.error(f"Neo4j error executing write query: {str(e)}")
                raise Neo4jConnectionError(f"Write query failed: {str(e)}")
            
            except Exception as e:
                logger.error(f"Unexpected error executing write query: {str(e)}")
                raise Neo4jConnectionError(f"Unexpected error: {str(e)}")
        
        raise Neo4jConnectionError(
            f"Write query failed after {max_attempts} attempts. Last error: {str(last_error)}"
        )
    
    def health_check(self) -> bool:
        """
        Check if the database connection is healthy.
        
        Returns:
            True if connection is healthy, False otherwise
        
        Example:
            if connection.health_check():
                print("Database is healthy")
        """
        try:
            with self.session() as session:
                result = session.run("RETURN 1 AS health")
                record = result.single()
                is_healthy = record["health"] == 1
                
                if is_healthy:
                    logger.info("Neo4j health check passed")
                else:
                    logger.warning("Neo4j health check failed")
                
                return is_healthy
                
        except Exception as e:
            logger.error(f"Neo4j health check failed: {str(e)}")
            return False
    
    def close(self) -> None:
        """
        Close the database connection and release resources.
        
        Example:
            connection.close()
        """
        if hasattr(self, '_driver') and self._driver:
            logger.info("Closing Neo4j connection")
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __del__(self):
        """Destructor to ensure connection is closed."""
        try:
            self.close()
        except (AttributeError, Exception):
            # Silently ignore errors during cleanup
            pass


# Singleton instance for application-wide use
_connection_instance: Optional[Neo4jConnection] = None


def get_connection(
    uri: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    database: Optional[str] = None,
    force_new: bool = False
) -> Neo4jConnection:
    """
    Get or create a Neo4j connection instance (singleton pattern).
    
    Args:
        uri: Neo4j URI (optional, uses env var if not provided)
        user: Database username (optional, uses env var if not provided)
        password: Database password (optional, uses env var if not provided)
        database: Database name (optional, uses env var if not provided)
        force_new: Force creation of new connection instance
    
    Returns:
        Neo4jConnection instance
    
    Example:
        connection = get_connection()
        results = connection.execute_query("MATCH (n) RETURN n LIMIT 10")
    """
    global _connection_instance
    
    if force_new or _connection_instance is None:
        _connection_instance = Neo4jConnection(
            uri=uri,
            user=user,
            password=password,
            database=database
        )
    
    return _connection_instance


def close_connection() -> None:
    """
    Close the global connection instance.
    
    Example:
        close_connection()
    """
    global _connection_instance
    
    if _connection_instance:
        _connection_instance.close()
        _connection_instance = None
