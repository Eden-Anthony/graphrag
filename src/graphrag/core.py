"""
Core KnowledgeGraph class for managing Neo4j connections and operations.
"""

import logging
from typing import Any
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """Main class for managing knowledge graph operations with Neo4j."""

    def __init__(self, uri: str = "bolt://localhost:7687",
                 username: str = "neo4j",
                 password: str = "password"):
        """
        Initialize the knowledge graph with Neo4j connection.

        Args:
            uri: Neo4j database URI
            username: Neo4j username
            password: Neo4j password
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None

    def connect(self) -> bool:
        """
        Establish connection to Neo4j database.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.username, self.password))
            # Test the connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Successfully connected to Neo4j")
            return True
        except ServiceUnavailable:
            logger.error(
                "Could not connect to Neo4j. Is the database running?")
            return False
        except AuthError:
            logger.error("Authentication failed. Check username and password.")
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Close the Neo4j connection."""
        if self.driver:
            self.driver.close()
            self.driver = None
            logger.info("Disconnected from Neo4j")

    def is_connected(self) -> bool:
        """Check if connected to Neo4j."""
        if not self.driver:
            return False
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except:
            return False

    def get_session(self):
        """Get a Neo4j session for database operations."""
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")
        return self.driver.session()

    def clear_database(self):
        """Clear all data from the database."""
        with self.get_session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Cleared all data from database")

    def create_constraints(self):
        """Create database constraints for better performance."""
        with self.get_session() as session:
            # Create unique constraints
            try:
                session.run(
                    "CREATE CONSTRAINT note_path IF NOT EXISTS FOR (n:Note) REQUIRE n.path IS UNIQUE")
                session.run(
                    "CREATE CONSTRAINT note_title IF NOT EXISTS FOR (n:Note) REQUIRE n.title IS UNIQUE")
                session.run(
                    "CREATE CONSTRAINT folder_path IF NOT EXISTS FOR (f:Folder) REQUIRE f.path IS UNIQUE")
                session.run(
                    "CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE")
                session.run(
                    "CREATE CONSTRAINT internal_link_name IF NOT EXISTS FOR (l:InternalLink) REQUIRE l.name IS UNIQUE")
                logger.info("Created database constraints")
            except Exception as e:
                logger.warning(f"Could not create constraints: {e}")

    def get_database_info(self) -> dict[str, Any]:
        """Get information about the database."""
        with self.get_session() as session:
            # Count nodes by type
            result = session.run("""
                MATCH (n)
                RETURN labels(n) as labels, count(n) as count
                ORDER BY count DESC
            """)

            node_counts = {}
            for record in result:
                labels = record["labels"]
                count = record["count"]
                label_key = ":".join(labels) if labels else "unlabeled"
                node_counts[label_key] = count

            # Count relationships by type
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)

            relationship_counts = {}
            for record in result:
                rel_type = record["type"]
                count = record["count"]
                relationship_counts[rel_type] = count

            return {
                "node_counts": node_counts,
                "relationship_counts": relationship_counts
            }

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
