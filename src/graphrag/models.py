"""Data models for the GraphRAG system."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Types of entities that can be detected."""
    PERSON = "Person"
    ORGANIZATION = "Organization"
    CONCEPT = "Concept"
    LOCATION = "Location"
    BOOK = "Book"
    PROJECT = "Project"
    MEETING = "Meeting"
    TOPIC = "Topic"


class Entity(BaseModel):
    """Represents an entity detected in a note."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    entity_type: EntityType
    confidence: float = Field(ge=0.0, le=1.0)
    aliases: Set[str] = Field(default_factory=set)
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class Note(BaseModel):
    """Represents an Obsidian note."""
    id: UUID = Field(default_factory=uuid4)
    file_path: str
    title: str
    content: str
    frontmatter: Dict[str, Any] = Field(default_factory=dict)
    tags: Set[str] = Field(default_factory=set)
    links: Set[str] = Field(default_factory=set)
    entities: List[Entity] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified: datetime = Field(default_factory=datetime.utcnow)


class RelationshipType(str, Enum):
    """Types of relationships between entities."""
    MENTIONS = "MENTIONS"
    RELATED_TO = "RELATED_TO"
    WORKS_FOR = "WORKS_FOR"
    AUTHOR_OF = "AUTHOR_OF"
    PART_OF = "PART_OF"
    SIMILAR_TO = "SIMILAR_TO"
    COLLABORATES_WITH = "COLLABORATES_WITH"
    LOCATED_IN = "LOCATED_IN"
    DISCUSSES = "DISCUSSES"
    ATTENDS = "ATTENDS"


class Relationship(BaseModel):
    """Represents a relationship between entities."""
    id: UUID = Field(default_factory=uuid4)
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: RelationshipType
    confidence: float = Field(ge=0.0, le=1.0)
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QueryResult(BaseModel):
    """Result of a query to the knowledge graph."""
    answer: str
    context_notes: List[Note]
    citations: List[str]
    confidence: float
    query_time: datetime = Field(default_factory=datetime.utcnow)


class EntityDetectionResult(BaseModel):
    """Result of entity detection on a note."""
    note_id: UUID
    entities: List[Entity]
    relationships: List[Relationship]
    confidence: float
    processing_time: float
