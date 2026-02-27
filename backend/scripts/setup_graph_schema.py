#!/usr/bin/env python
"""Script to set up Neo4j graph schema with constraints and indexes."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.graph import neo4j_client
from src.infrastructure.graph.schema import create_all_constraints
from src.shared.utils import logger


async def setup_schema():
    """Set up graph database schema."""
    try:
        logger.info("Connecting to Neo4j...")
        neo4j_client.connect()
        
        logger.info("Creating constraints and indexes...")
        await create_all_constraints(neo4j_client)
        
        logger.info("✓ Schema setup completed successfully!")
        
        # Verify setup
        query = "SHOW CONSTRAINTS"
        constraints = await neo4j_client.execute_query(query)
        logger.info(f"Total constraints created: {len(constraints)}")
        
        query = "SHOW INDEXES"
        indexes = await neo4j_client.execute_query(query)
        logger.info(f"Total indexes created: {len(indexes)}")
        
    except Exception as e:
        logger.error(f"✗ Schema setup failed: {str(e)}")
        raise
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    asyncio.run(setup_schema())
