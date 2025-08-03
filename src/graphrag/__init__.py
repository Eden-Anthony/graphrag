"""
GraphRAG - A knowledge graph system using Neo4j for indexing and querying Obsidian note collections.
"""

__version__ = "0.1.0"

from .core import KnowledgeGraph
from .indexer import ObsidianIndexer
from .query import ObsidianQueryEngine

__all__ = ["KnowledgeGraph", "ObsidianIndexer", "ObsidianQueryEngine"]
