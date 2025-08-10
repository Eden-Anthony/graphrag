"""Neo4j GraphRAG implementation for Obsidian vaults."""

__version__ = "0.1.0"

from .core import ObsidianGraphRAG
from .models import Entity, Note, Relationship
from .services import EntityDetectionService, KnowledgeGraphService, QueryService

__all__ = [
    "ObsidianGraphRAG",
    "Entity",
    "Note",
    "Relationship",
    "EntityDetectionService",
    "KnowledgeGraphService",
    "QueryService",
]

