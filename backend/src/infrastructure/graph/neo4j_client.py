"""Neo4j database client."""

from typing import Optional, List, Dict, Any
from neo4j import GraphDatabase, Driver, Session
from contextlib import asynccontextmanager

from ...config import settings
from ...shared.utils import logger
from ...shared.exceptions import GraphConnectionException


class Neo4jClient:
    """Neo4j database client with connection pooling."""
    
    def __init__(self):
        self._driver: Optional[Driver] = None
        self._uri = settings.neo4j_uri
        self._user = settings.neo4j_user
        self._password = settings.neo4j_password
        self._database = settings.neo4j_database
    
    def connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            self._driver = GraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
            # Verify connectivity
            self._driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self._uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise GraphConnectionException(f"Neo4j connection failed: {str(e)}")
    
    def close(self) -> None:
        """Close database connection."""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j connection closed")
    
    @asynccontextmanager
    async def get_session(self) -> Session:
        """
        Get database session as async context manager.
        
        Usage:
            async with client.get_session() as session:
                result = session.run(query)
        """
        if not self._driver:
            self.connect()
        
        session = self._driver.session(database=self._database)
        try:
            yield session
        finally:
            session.close()
    
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records as dictionaries
        """
        async with self.get_session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
    
    async def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a write query (CREATE, UPDATE, DELETE).
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            Query execution summary
        """
        async with self.get_session() as session:
            result = session.run(query, parameters or {})
            summary = result.consume()
            return {
                "nodes_created": summary.counters.nodes_created,
                "relationships_created": summary.counters.relationships_created,
                "properties_set": summary.counters.properties_set,
                "nodes_deleted": summary.counters.nodes_deleted,
                "relationships_deleted": summary.counters.relationships_deleted
            }
    
    async def create_constraints(self) -> None:
        """Create database constraints and indexes."""
        constraints = [
            # Unique constraints
            "CREATE CONSTRAINT taxpayer_id IF NOT EXISTS FOR (t:Taxpayer) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT taxpayer_gstin IF NOT EXISTS FOR (t:Taxpayer) REQUIRE t.gstin IS UNIQUE",
            "CREATE CONSTRAINT invoice_id IF NOT EXISTS FOR (i:Invoice) REQUIRE i.id IS UNIQUE",
            "CREATE CONSTRAINT return_id IF NOT EXISTS FOR (r:Return) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT mismatch_id IF NOT EXISTS FOR (m:Mismatch) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT vendor_id IF NOT EXISTS FOR (v:Vendor) REQUIRE v.id IS UNIQUE",
            
            # Indexes for performance
            "CREATE INDEX invoice_number IF NOT EXISTS FOR (i:Invoice) ON (i.invoice_number)",
            "CREATE INDEX invoice_date IF NOT EXISTS FOR (i:Invoice) ON (i.invoice_date)",
            "CREATE INDEX invoice_source IF NOT EXISTS FOR (i:Invoice) ON (i.source_type)",
            "CREATE INDEX return_period IF NOT EXISTS FOR (r:Return) ON (r.return_period)",
            "CREATE INDEX mismatch_status IF NOT EXISTS FOR (m:Mismatch) ON (m.status)",
            "CREATE INDEX mismatch_risk IF NOT EXISTS FOR (m:Mismatch) ON (m.risk_level)",
        ]
        
        for constraint in constraints:
            try:
                await self.execute_write(constraint)
                logger.info(f"Created constraint/index: {constraint[:50]}...")
            except Exception as e:
                logger.warning(f"Constraint/index already exists or failed: {str(e)}")
    
    async def clear_database(self) -> None:
        """Clear all nodes and relationships (use with caution!)."""
        query = "MATCH (n) DETACH DELETE n"
        await self.execute_write(query)
        logger.warning("Database cleared!")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global client instance
neo4j_client = Neo4jClient()
