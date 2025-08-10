"""Tests for the data models."""

import pytest
from datetime import datetime
from uuid import uuid4

from graphrag.models import (
    Entity, Note, Relationship, QueryResult, EntityDetectionResult,
    EntityType, RelationshipType
)


class TestEntityType:
    """Test EntityType enum."""

    def test_entity_type_values(self):
        """Test that entity types have expected values."""
        assert EntityType.PERSON == "Person"
        assert EntityType.ORGANIZATION == "Organization"
        assert EntityType.CONCEPT == "Concept"
        assert EntityType.LOCATION == "Location"
        assert EntityType.BOOK == "Book"
        assert EntityType.PROJECT == "Project"
        assert EntityType.MEETING == "Meeting"
        assert EntityType.TOPIC == "Topic"

    def test_entity_type_creation(self):
        """Test creating entities with different types."""
        for entity_type in EntityType:
            entity = Entity(
                name=f"Test {entity_type}",
                entity_type=entity_type,
                confidence=0.8
            )
            assert entity.entity_type == entity_type


class TestRelationshipType:
    """Test RelationshipType enum."""

    def test_relationship_type_values(self):
        """Test that relationship types have expected values."""
        assert RelationshipType.MENTIONS == "MENTIONS"
        assert RelationshipType.RELATED_TO == "RELATED_TO"
        assert RelationshipType.WORKS_FOR == "WORKS_FOR"
        assert RelationshipType.AUTHOR_OF == "AUTHOR_OF"
        assert RelationshipType.PART_OF == "PART_OF"
        assert RelationshipType.SIMILAR_TO == "SIMILAR_TO"
        assert RelationshipType.COLLABORATES_WITH == "COLLABORATES_WITH"
        assert RelationshipType.LOCATED_IN == "LOCATED_IN"
        assert RelationshipType.DISCUSSES == "DISCUSSES"
        assert RelationshipType.ATTENDS == "ATTENDS"

    def test_relationship_type_creation(self):
        """Test creating relationships with different types."""
        for rel_type in RelationshipType:
            relationship = Relationship(
                source_entity_id=uuid4(),
                target_entity_id=uuid4(),
                relationship_type=rel_type,
                confidence=0.8
            )
            assert relationship.relationship_type == rel_type


class TestEntity:
    """Test Entity model."""

    def test_entity_creation_minimal(self):
        """Test creating an entity with minimal required fields."""
        entity = Entity(
            name="Test Entity",
            entity_type=EntityType.CONCEPT,
            confidence=0.8
        )
        
        assert entity.name == "Test Entity"
        assert entity.entity_type == EntityType.CONCEPT
        assert entity.confidence == 0.8
        assert entity.id is not None
        assert entity.properties == {}
        assert entity.aliases == set()

    def test_entity_creation_full(self):
        """Test creating an entity with all fields."""
        entity_id = uuid4()
        entity = Entity(
            id=entity_id,
            name="Full Entity",
            entity_type=EntityType.PERSON,
            confidence=0.9,
            properties={"age": 30, "occupation": "Developer"},
            aliases={"FE", "Full"}
        )
        
        assert entity.id == entity_id
        assert entity.name == "Full Entity"
        assert entity.entity_type == EntityType.PERSON
        assert entity.confidence == 0.9
        assert entity.properties["age"] == 30
        assert entity.properties["occupation"] == "Developer"
        assert "FE" in entity.aliases
        assert "Full" in entity.aliases

    def test_entity_properties_mutation(self):
        """Test that entity properties can be modified."""
        entity = Entity(
            name="Mutable Entity",
            entity_type=EntityType.CONCEPT,
            confidence=0.8
        )
        
        entity.properties["new_prop"] = "new_value"
        assert entity.properties["new_prop"] == "new_value"
        
        entity.properties["nested"] = {"key": "value"}
        assert entity.properties["nested"]["key"] == "value"

    def test_entity_aliases_mutation(self):
        """Test that entity aliases can be modified."""
        entity = Entity(
            name="Alias Entity",
            entity_type=EntityType.CONCEPT,
            confidence=0.8
        )
        
        entity.aliases.add("alias1")
        assert "alias1" in entity.aliases
        
        entity.aliases.add("alias2")
        assert len(entity.aliases) == 2

    def test_entity_validation(self):
        """Test Entity validation."""
        from pydantic import ValidationError
        
        # Test invalid entity type
        with pytest.raises(ValidationError):
            Entity(
                name="Test Entity",
                entity_type="InvalidType",  # Invalid enum value
                confidence=0.8
            )
        
        with pytest.raises(ValueError):
            Entity(
                name="Invalid Entity",
                entity_type=EntityType.CONCEPT,
                confidence=-0.1  # Invalid confidence
            )


class TestNote:
    """Test Note model."""

    def test_note_creation_minimal(self):
        """Test creating a note with minimal required fields."""
        note = Note(
            title="Test Note",
            content="This is test content.",
            file_path="/tmp/test.md"
        )
        
        assert note.title == "Test Note"
        assert note.content == "This is test content."
        assert note.file_path == "/tmp/test.md"
        assert note.id is not None
        assert note.tags == set()
        assert note.frontmatter == {}
        assert note.links == set()

    def test_note_creation_full(self):
        """Test creating a note with all fields."""
        note_id = uuid4()
        note = Note(
            id=note_id,
            title="Full Note",
            content="This is full content.",
            file_path="/tmp/full.md",
            tags={"test", "full", "note"},
            frontmatter={"status": "active", "priority": "high"},
            links={"[[internal]]", "https://external.com"}
        )
        
        assert note.id == note_id
        assert note.title == "Full Note"
        assert note.content == "This is full content."
        assert note.file_path == "/tmp/full.md"
        assert note.tags == {"test", "full", "note"}
        assert note.frontmatter["status"] == "active"
        assert note.frontmatter["priority"] == "high"
        assert "[[internal]]" in note.links
        assert "https://external.com" in note.links

    def test_note_tags_mutation(self):
        """Test that note tags can be modified."""
        note = Note(
            title="Tag Note",
            content="Content with tags",
            file_path="/tmp/tags.md"
        )
        
        note.tags.add("new_tag")
        assert "new_tag" in note.tags
        
        note.tags.add("another_tag")
        assert len(note.tags) == 2

    def test_note_links_mutation(self):
        """Test that note links can be modified."""
        note = Note(
            title="Link Note",
            content="Content with links",
            file_path="/tmp/links.md"
        )
        
        note.links.add("[[new_link]]")
        assert "[[new_link]]" in note.links
        
        note.links.add("https://new-external.com")
        assert len(note.links) == 2

    def test_note_frontmatter_mutation(self):
        """Test that note frontmatter can be modified."""
        note = Note(
            title="Frontmatter Note",
            content="Content with frontmatter",
            file_path="/tmp/frontmatter.md"
        )
        
        note.frontmatter["new_field"] = "new_value"
        assert note.frontmatter["new_field"] == "new_value"
        
        note.frontmatter["nested"] = {"key": "value"}
        assert note.frontmatter["nested"]["key"] == "value"


class TestRelationship:
    """Test Relationship model."""

    def test_relationship_creation_minimal(self):
        """Test creating a relationship with minimal required fields."""
        source_id = uuid4()
        target_id = uuid4()
        
        relationship = Relationship(
            source_entity_id=source_id,
            target_entity_id=target_id,
            relationship_type=RelationshipType.RELATED_TO,
            confidence=0.8
        )
        
        assert relationship.source_entity_id == source_id
        assert relationship.target_entity_id == target_id
        assert relationship.relationship_type == RelationshipType.RELATED_TO
        assert relationship.confidence == 0.8
        assert relationship.id is not None
        assert relationship.properties == {}

    def test_relationship_creation_full(self):
        """Test creating a relationship with all fields."""
        rel_id = uuid4()
        source_id = uuid4()
        target_id = uuid4()
        
        relationship = Relationship(
            id=rel_id,
            source_entity_id=source_id,
            target_entity_id=target_id,
            relationship_type=RelationshipType.WORKS_FOR,
            confidence=0.9,
            properties={"start_date": "2024-01-01", "role": "Developer"}
        )
        
        assert relationship.id == rel_id
        assert relationship.source_entity_id == source_id
        assert relationship.target_entity_id == target_id
        assert relationship.relationship_type == RelationshipType.WORKS_FOR
        assert relationship.confidence == 0.9
        assert relationship.properties["start_date"] == "2024-01-01"
        assert relationship.properties["role"] == "Developer"

    def test_relationship_properties_mutation(self):
        """Test that relationship properties can be modified."""
        relationship = Relationship(
            source_entity_id=uuid4(),
            target_entity_id=uuid4(),
            relationship_type=RelationshipType.RELATED_TO,
            confidence=0.8
        )
        
        relationship.properties["new_prop"] = "new_value"
        assert relationship.properties["new_prop"] == "new_value"
        
        relationship.properties["nested"] = {"key": "value"}
        assert relationship.properties["nested"]["key"] == "value"

    def test_relationship_validation(self):
        """Test Relationship validation."""
        from pydantic import ValidationError
        
        # Test invalid relationship type
        with pytest.raises(ValidationError):
            Relationship(
                source_entity_id=uuid4(),
                target_entity_id=uuid4(),
                relationship_type="InvalidType",  # Invalid enum value
                confidence=0.8
            )


class TestQueryResult:
    """Test QueryResult model."""

    def test_query_result_creation_minimal(self):
        """Test creating a query result with minimal required fields."""
        result = QueryResult(
            answer="This is the answer.",
            sources=["source1", "source2"]
        )
        
        assert result.answer == "This is the answer."
        assert result.sources == ["source1", "source2"]
        assert result.id is not None
        assert result.processing_time == 0.0
        assert result.confidence == 0.0

    def test_query_result_creation_full(self):
        """Test creating a query result with all fields."""
        result_id = uuid4()
        result = QueryResult(
            id=result_id,
            answer="This is the full answer.",
            sources=["source1", "source2", "source3"],
            processing_time=1.5,
            confidence=0.9
        )
        
        assert result.id == result_id
        assert result.answer == "This is the full answer."
        assert result.sources == ["source1", "source2", "source3"]
        assert result.processing_time == 1.5
        assert result.confidence == 0.9

    def test_query_result_sources_mutation(self):
        """Test that query result sources can be modified."""
        result = QueryResult(
            answer="Answer with sources",
            sources=["source1"]
        )
        
        result.sources.append("source2")
        assert "source2" in result.sources
        assert len(result.sources) == 2

    def test_query_result_validation(self):
        """Test QueryResult validation."""
        # Valid QueryResult
        result = QueryResult(
            answer="This is a test answer",
            context_notes=[],
            citations=[],
            confidence=0.8
        )
        assert result.answer == "This is a test answer"
        assert result.confidence == 0.8


class TestEntityDetectionResult:
    """Test EntityDetectionResult model."""

    def test_entity_detection_result_creation_minimal(self):
        """Test creating an entity detection result with minimal required fields."""
        result = EntityDetectionResult(
            note_id=uuid4(),
            entities=[],
            relationships=[],
            confidence=0.8,
            processing_time=1.0
        )
        
        assert result.note_id is not None
        assert result.entities == []
        assert result.relationships == []
        assert result.confidence == 0.8
        assert result.processing_time == 1.0

    def test_entity_detection_result_creation_full(self):
        """Test creating an entity detection result with all fields."""
        note_id = uuid4()
        entity = Entity(
            name="Detected Entity",
            entity_type=EntityType.CONCEPT,
            confidence=0.9
        )
        relationship = Relationship(
            source_entity_id=uuid4(),
            target_entity_id=uuid4(),
            relationship_type=RelationshipType.RELATED_TO,
            confidence=0.8
        )
        
        result = EntityDetectionResult(
            note_id=note_id,
            entities=[entity],
            relationships=[relationship],
            confidence=0.85,
            processing_time=1.5
        )
        
        assert result.note_id == note_id
        assert len(result.entities) == 1
        assert result.entities[0].name == "Detected Entity"
        assert len(result.relationships) == 1
        assert result.relationships[0].relationship_type == RelationshipType.RELATED_TO
        assert result.confidence == 0.85
        assert result.processing_time == 1.5

    def test_entity_detection_result_entities_mutation(self):
        """Test that entity detection result entities can be modified."""
        result = EntityDetectionResult(
            note_id=uuid4(),
            entities=[],
            relationships=[],
            confidence=0.8,
            processing_time=1.0
        )
        
        entity = Entity(
            name="New Entity",
            entity_type=EntityType.CONCEPT,
            confidence=0.9
        )
        
        result.entities.append(entity)
        assert len(result.entities) == 1
        assert result.entities[0].name == "New Entity"

    def test_entity_detection_result_validation(self):
        """Test entity detection result validation."""
        # Test that confidence is between 0 and 1
        with pytest.raises(ValueError):
            EntityDetectionResult(
                note_id=uuid4(),
                entities=[],
                relationships=[],
                confidence=1.5,  # Invalid confidence
                processing_time=1.0
            )


class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_entity_serialization(self):
        """Test Entity model serialization."""
        entity = Entity(
            name="Serializable Entity",
            entity_type=EntityType.CONCEPT,
            confidence=0.8,
            properties={"key": "value"},
            aliases={"alias1", "alias2"}
        )
        
        # Convert to dict
        entity_dict = entity.model_dump()
        
        assert entity_dict["name"] == "Serializable Entity"
        assert entity_dict["entity_type"] == "Concept"
        assert entity_dict["confidence"] == 0.8
        assert entity_dict["properties"]["key"] == "value"
        assert "alias1" in entity_dict["aliases"]
        assert "alias2" in entity_dict["aliases"]

    def test_note_serialization(self):
        """Test Note model serialization."""
        note = Note(
            title="Serializable Note",
            content="This is serializable content.",
            file_path="/tmp/serializable.md",
            tags={"tag1", "tag2"},
            frontmatter={"status": "active"},
            links={"[[internal]]", "https://external.com"}
        )
        
        # Convert to dict
        note_dict = note.model_dump()
        
        assert note_dict["title"] == "Serializable Note"
        assert note_dict["content"] == "This is serializable content."
        assert note_dict["file_path"] == "/tmp/serializable.md"
        assert "tag1" in note_dict["tags"]
        assert "tag2" in note_dict["tags"]
        assert note_dict["frontmatter"]["status"] == "active"
        assert "[[internal]]" in note_dict["links"]
        assert "https://external.com" in note_dict["links"]

    def test_relationship_serialization(self):
        """Test Relationship model serialization."""
        source_id = uuid4()
        target_id = uuid4()
        
        relationship = Relationship(
            source_entity_id=source_id,
            target_entity_id=target_id,
            relationship_type=RelationshipType.RELATED_TO,
            confidence=0.8,
            properties={"strength": 0.9}
        )
        
        # Convert to dict
        rel_dict = relationship.model_dump()
        
        assert str(rel_dict["source_entity_id"]) == str(source_id)
        assert str(rel_dict["target_entity_id"]) == str(target_id)
        assert rel_dict["relationship_type"] == "RELATED_TO"
        assert rel_dict["confidence"] == 0.8
        assert rel_dict["properties"]["strength"] == 0.9


class TestModelValidation:
    """Test model validation rules."""

    def test_entity_name_required(self):
        """Test that entity name is required."""
        with pytest.raises(ValueError):
            Entity(
                name="",  # Empty name
                entity_type=EntityType.CONCEPT,
                confidence=0.8
            )

    def test_note_title_required(self):
        """Test that note title is required."""
        with pytest.raises(ValueError):
            Note(
                title="",  # Empty title
                content="Content",
                file_path="/tmp/test.md"
            )

    def test_note_content_required(self):
        """Test that note content is required."""
        with pytest.raises(ValueError):
            Note(
                title="Title",
                content="",  # Empty content
                file_path="/tmp/test.md"
            )

    def test_note_file_path_required(self):
        """Test that note file path is required."""
        with pytest.raises(ValueError):
            Note(
                title="Title",
                content="Content",
                file_path=""  # Empty file path
            )

    def test_relationship_source_target_different(self):
        """Test that relationship source and target must be different."""
        entity_id = uuid4()
        
        with pytest.raises(ValueError):
            Relationship(
                source_entity_id=entity_id,
                target_entity_id=entity_id,  # Same as source
                relationship_type=RelationshipType.RELATED_TO,
                confidence=0.8
            ) 