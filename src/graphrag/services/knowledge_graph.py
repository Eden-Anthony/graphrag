"""Knowledge graph service for managing Neo4j operations."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.retrievers import HybridCypherRetriever

from ..config import Config
from ..models import Entity, Note, Relationship, RelationshipType

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Service for managing the Neo4j knowledge graph."""

    def __init__(self):
        """Initialize the knowledge graph service."""
        neo4j_config = Config.get_neo4j_config()
        self.driver = GraphDatabase.driver(
            neo4j_config["uri"],
            auth=(neo4j_config["user"], neo4j_config["password"])
        )

        # Test connection
        try:
            self.driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j")
        except ServiceUnavailable:
            logger.error("Failed to connect to Neo4j")
            raise

        # Initialize embeddings
        self.embedder = OpenAIEmbeddings(model="text-embedding-ada-002")

        # Initialize hybrid cypher retriever
        self.retriever = HybridCypherRetriever(
            driver=self.driver,
            vector_index_name=Config.VECTOR_INDEX_NAME,
            fulltext_index_name=Config.FULLTEXT_INDEX_NAME,
            retrieval_query=self._get_retrieval_query(),
            embedder=self.embedder,
        )

        # Ensure indexes exist
        self._ensure_indexes()

    def _get_retrieval_query(self) -> str:
        """Get the Cypher query for hybrid retrieval."""
        return """
        MATCH (note:Note)
        OPTIONAL MATCH (note)-[:CONTAINS_ENTITY]->(entity:Entity)
        OPTIONAL MATCH (entity)-[rel:RELATED_TO|MENTIONS|WORKS_FOR|AUTHOR_OF|PART_OF|SIMILAR_TO|COLLABORATES_WITH|LOCATED_IN|DISCUSSES|ATTENDS]->(related_entity:Entity)
        OPTIONAL MATCH (related_entity)<-[:CONTAINS_ENTITY]-(related_note:Note)
        
        RETURN DISTINCT
            note.title AS note_title,
            note.content AS note_content,
            note.file_path AS note_path,
            collect(DISTINCT entity.name) AS entities,
            collect(DISTINCT {
                name: related_entity.name,
                type: related_entity.entity_type,
                relationship: type(rel)
            }) AS related_entities,
            collect(DISTINCT related_note.title) AS related_notes
        ORDER BY note.last_modified DESC
        """

    def _ensure_indexes(self):
        """Ensure required indexes exist in Neo4j."""
        with self.driver.session() as session:
            # Create vector index for note content
            session.run("""
                CALL db.index.vector.createIfNotExists(
                    $index_name,
                    'Note',
                    'content_embedding',
                    1536,
                    'cosine'
                )
            """, index_name=Config.VECTOR_INDEX_NAME)

            # Create fulltext index for note content
            session.run("""
                CALL db.index.fulltext.createIfNotExists(
                    $index_name,
                    ['Note'],
                    ['title', 'content']
                )
            """, index_name=Config.FULLTEXT_INDEX_NAME)

            # Create constraints for unique properties
            session.run(
                "CREATE CONSTRAINT note_file_path_unique IF NOT EXISTS FOR (n:Note) REQUIRE n.file_path IS UNIQUE")
            session.run(
                "CREATE CONSTRAINT entity_name_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE")

    def create_note_node(self, note: Note) -> str:
        """Create a Note node in Neo4j."""
        with self.driver.session() as session:
            result = session.run("""
                MERGE (n:Note {file_path: $file_path})
                SET n.title = $title,
                    n.content = $content,
                    n.frontmatter = $frontmatter,
                    n.tags = $tags,
                    n.links = $links,
                    n.last_modified = $last_modified,
                    n.updated_at = $updated_at
                RETURN n.file_path
            """,
                                 file_path=note.file_path,
                                 title=note.title,
                                 content=note.content,
                                 frontmatter=note.frontmatter,
                                 tags=list(note.tags),
                                 links=list(note.links),
                                 last_modified=note.last_modified,
                                 updated_at=note.updated_at
                                 )
            return result.single()["n.file_path"]

    def create_entity_node(self, entity: Entity) -> str:
        """Create an Entity node in Neo4j."""
        with self.driver.session() as session:
            result = session.run("""
                MERGE (e:Entity {name: $name})
                SET e.entity_type = $entity_type,
                    e.confidence = $confidence,
                    e.aliases = $aliases,
                    e.properties = $properties,
                    e.updated_at = $updated_at
                RETURN e.name
            """,
                                 name=entity.name,
                                 entity_type=entity.entity_type.value,
                                 confidence=entity.confidence,
                                 aliases=list(entity.aliases),
                                 properties=entity.properties,
                                 updated_at=entity.updated_at
                                 )
            return result.single()["e.name"]

    def create_relationship(self, relationship: Relationship, source_name: str, target_name: str):
        """Create a relationship between entities."""
        with self.driver.session() as session:
            session.run("""
                MATCH (source:Entity {name: $source_name})
                MATCH (target:Entity {name: $target_name})
                MERGE (source)-[r:$relationship_type]->(target)
                SET r.confidence = $confidence,
                    r.properties = $properties,
                    r.created_at = $created_at
            """,
                        source_name=source_name,
                        target_name=target_name,
                        relationship_type=relationship.relationship_type.value,
                        confidence=relationship.confidence,
                        properties=relationship.properties,
                        created_at=relationship.created_at
                        )

    def link_note_to_entities(self, note_path: str, entity_names: List[str]):
        """Link a note to its contained entities."""
        with self.driver.session() as session:
            for entity_name in entity_names:
                session.run("""
                    MATCH (note:Note {file_path: $note_path})
                    MATCH (entity:Entity {name: $entity_name})
                    MERGE (note)-[:CONTAINS_ENTITY]->(entity)
                """,
                            note_path=note_path,
                            entity_name=entity_name
                            )

    def update_note_embeddings(self, note: Note):
        """Update vector embeddings for a note."""
        try:
            # Generate embedding for note content
            embedding = self.embedder.embed_query(note.content)

            with self.driver.session() as session:
                session.run("""
                    MATCH (n:Note {file_path: $file_path})
                    SET n.content_embedding = $embedding
                """,
                            file_path=note.file_path,
                            embedding=embedding
                            )
        except Exception as e:
            logger.warning(
                f"Failed to update embeddings for note {note.file_path}: {e}")

    def search_notes(self, query: str, top_k: int = None) -> List[Dict]:
        """Search notes using hybrid retrieval."""
        if top_k is None:
            top_k = Config.CONTEXT_WINDOW_SIZE

        try:
            result = self.retriever.search(query_text=query, top_k=top_k)
            return result.items
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_note_by_path(self, file_path: str) -> Optional[Dict]:
        """Get a note by its file path."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n:Note {file_path: $file_path})
                RETURN n
            """, file_path=file_path)

            record = result.single()
            if record:
                return dict(record["n"])
            return None

    def get_entities_by_note(self, file_path: str) -> List[Dict]:
        """Get all entities contained in a note."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (note:Note {file_path: $file_path})-[:CONTAINS_ENTITY]->(entity:Entity)
                RETURN entity
            """, file_path=file_path)

            return [dict(record["entity"]) for record in result]

    def get_related_notes(self, entity_name: str, limit: int = 10) -> List[Dict]:
        """Get notes related to a specific entity."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (entity:Entity {name: $entity_name})<-[:CONTAINS_ENTITY]-(note:Note)
                OPTIONAL MATCH (note)-[:CONTAINS_ENTITY]->(other_entity:Entity)
                RETURN note, collect(other_entity.name) as other_entities
                ORDER BY note.last_modified DESC
                LIMIT $limit
            """, entity_name=entity_name, limit=limit)

            return [
                {
                    "note": dict(record["note"]),
                    "other_entities": record["other_entities"]
                }
                for record in result
            ]

    def delete_note(self, file_path: str):
        """Delete a note and its relationships."""
        with self.driver.session() as session:
            session.run("""
                MATCH (n:Note {file_path: $file_path})
                OPTIONAL MATCH (n)-[r]-()
                DELETE r, n
            """, file_path=file_path)

    def get_graph_stats(self) -> Dict:
        """Get statistics about the knowledge graph."""
        with self.driver.session() as session:
            stats = {}

            # Count nodes
            result = session.run(
                "MATCH (n) RETURN labels(n) as labels, count(n) as count")
            for record in result:
                labels = record["labels"]
                if labels:
                    label = labels[0]
                    stats[f"{label}_count"] = record["count"]

            # Count relationships
            result = session.run(
                "MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
            for record in result:
                rel_type = record["type"]
                stats[f"{rel_type}_count"] = record["count"]

            return stats

    def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
            self.driver.close()
