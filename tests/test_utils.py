"""Tests for utility functions and edge cases."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import shutil
import yaml
from datetime import datetime
from uuid import uuid4

from graphrag.models import Note, Entity, EntityType, Relationship, RelationshipType
from graphrag.services.entity_detection import EntityDetectionResult


class TestUtilityFunctions:
    """Test various utility functions and edge cases."""

    def test_note_with_special_characters(self):
        """Test that notes with special characters are handled correctly."""
        note = Note(
            id=uuid4(),
            title="Test Note with Special Chars: !@#$%^&*()",
            content="Content with special chars: émojis 🚀 and unicode: 你好世界",
            file_path="/tmp/test-vault/special-note.md",
            tags={"special", "unicode", "emoji"},
            frontmatter={"status": "active", "special_field": "!@#$%^&*()"},
            links={"[[special-note]]", "[[你好世界]]", "https://example.com/émojis", "https://test.com/你好世界"}
        )
        
        assert note.title == "Test Note with Special Chars: !@#$%^&*()"
        assert "émojis 🚀" in note.content
        assert "你好世界" in note.content
        assert "[[你好世界]]" in note.links
        assert "https://example.com/émojis" in note.links

    def test_entity_with_complex_properties(self):
        """Test that entities with complex properties are handled correctly."""
        entity = Entity(
            id=uuid4(),
            name="Complex Entity",
            entity_type=EntityType.CONCEPT,
            confidence=0.9,
            properties={
                "nested": {"key": "value", "list": [1, 2, 3]},
                "boolean": True,
                "number": 42.5,
                "unicode": "你好世界",
                "emoji": "🚀"
            }
        )
        
        assert entity.name == "Complex Entity"
        assert entity.properties["nested"]["key"] == "value"
        assert entity.properties["boolean"] is True
        assert entity.properties["number"] == 42.5
        assert entity.properties["unicode"] == "你好世界"
        assert entity.properties["emoji"] == "🚀"

    def test_relationship_with_complex_properties(self):
        """Test that relationships with complex properties are handled correctly."""
        relationship = Relationship(
            id=uuid4(),
            source_entity_id=uuid4(),
            target_entity_id=uuid4(),
            relationship_type=RelationshipType.RELATED_TO,
            confidence=0.8,
            properties={
                "strength": 0.9,
                "evidence": ["source1", "source2"],
                "metadata": {"created_by": "user", "verified": True},
                "scores": [0.1, 0.2, 0.3, 0.4, 0.5]
            }
        )
        
        assert relationship.properties["strength"] == 0.9
        assert relationship.properties["evidence"] == ["source1", "source2"]
        assert relationship.properties["metadata"]["verified"] is True
        assert relationship.properties["scores"] == [0.1, 0.2, 0.3, 0.4, 0.5]

    def test_entity_detection_result_edge_cases(self):
        """Test entity detection results with edge case data."""
        # Test with empty results
        empty_result = EntityDetectionResult(
            note_id=uuid4(),
            entities=[],
            relationships=[],
            confidence=0.0,
            processing_time=0.0
        )
        
        assert empty_result.entities == []
        assert empty_result.relationships == []
        assert empty_result.confidence == 0.0
        assert empty_result.processing_time == 0.0

        # Test with very high confidence
        high_confidence_result = EntityDetectionResult(
            note_id=uuid4(),
            entities=[Entity(
                name="High Confidence Entity",
                entity_type=EntityType.CONCEPT,
                confidence=1.0
            )],
            relationships=[],
            confidence=1.0,
            processing_time=0.1
        )
        
        assert high_confidence_result.confidence == 1.0
        assert high_confidence_result.entities[0].confidence == 1.0

    def test_note_with_empty_content(self):
        """Test that notes with empty content are handled correctly."""
        minimal_note = Note(
            id=uuid4(),
            title="Empty Note",
            content="",
            file_path="/tmp/test-vault/empty-note.md"
        )
        
        assert minimal_note.title == "Empty Note"
        assert minimal_note.content == ""
        assert minimal_note.tags == set()
        assert minimal_note.links == set()

        # Test with whitespace-only content
        whitespace_note = Note(
            id=uuid4(),
            title="Whitespace Note",
            content="   \n\t  \n",
            file_path="/tmp/test-vault/whitespace-note.md"
        )
        
        assert whitespace_note.content == "   \n\t  \n"

    def test_note_with_very_long_content(self):
        """Test that notes with very long content are handled correctly."""
        long_content = "This is a very long note content. " * 1000  # ~40k characters
        
        long_note = Note(
            id=uuid4(),
            title="Long Note",
            content=long_content,
            file_path="/tmp/test-vault/long-note.md"
        )
        
        assert len(long_note.content) > 10000
        assert long_note.title == "Long Note"

    def test_entity_type_validation(self):
        """Test that entity types are properly validated."""
        # Test all valid entity types
        valid_types = [
            EntityType.PERSON,
            EntityType.ORGANIZATION,
            EntityType.CONCEPT,
            EntityType.LOCATION,
            EntityType.BOOK,
            EntityType.PROJECT,
            EntityType.MEETING,
            EntityType.TOPIC
        ]
        
        for entity_type in valid_types:
            entity = Entity(
                name=f"Test {entity_type}",
                entity_type=entity_type,
                confidence=0.8
            )
            assert entity.entity_type == entity_type

    def test_relationship_type_validation(self):
        """Test that relationship types are properly validated."""
        # Test all valid relationship types
        valid_types = [
            RelationshipType.MENTIONS,
            RelationshipType.RELATED_TO,
            RelationshipType.WORKS_FOR,
            RelationshipType.AUTHOR_OF,
            RelationshipType.PART_OF,
            RelationshipType.SIMILAR_TO,
            RelationshipType.COLLABORATES_WITH,
            RelationshipType.LOCATED_IN,
            RelationshipType.DISCUSSES,
            RelationshipType.ATTENDS
        ]
        
        for rel_type in valid_types:
            relationship = Relationship(
                source_entity_id=uuid4(),
                target_entity_id=uuid4(),
                relationship_type=rel_type,
                confidence=0.8
            )
            assert relationship.relationship_type == rel_type

    def test_note_with_many_tags(self):
        """Test that notes with many tags are handled correctly."""
        many_tags = {f"tag_{i}" for i in range(100)}
        
        note = Note(
            id=uuid4(),
            title="Many Tags Note",
            content="Content with many tags",
            file_path="/tmp/test-vault/many-tags-note.md",
            tags=many_tags
        )
        
        assert len(note.tags) == 100
        assert "tag_0" in note.tags
        assert "tag_99" in note.tags

    def test_note_with_many_links(self):
        """Test that notes with many links are handled correctly."""
        many_links = {f"[[link_{i}]]" for i in range(50)}
        many_links.update({f"https://example{i}.com" for i in range(50)})
        
        note = Note(
            id=uuid4(),
            title="Many Links Note",
            content="Content with many links",
            file_path="/tmp/test-vault/many-links-note.md",
            links=many_links
        )
        
        assert len(note.links) == 100
        assert "[[link_0]]" in note.links
        assert "https://example49.com" in note.links

    def test_entity_with_many_aliases(self):
        """Test that entities with many aliases are handled correctly."""
        many_aliases = {f"alias_{i}" for i in range(100)}
        
        entity = Entity(
            id=uuid4(),
            name="Many Aliases Entity",
            entity_type=EntityType.CONCEPT,
            confidence=0.8,
            aliases=many_aliases
        )
        
        assert len(entity.aliases) == 100
        assert "alias_0" in entity.aliases
        assert "alias_99" in entity.aliases

    def test_relationship_with_many_properties(self):
        """Test that relationships with many properties are handled correctly."""
        many_properties = {f"prop_{i}": f"value_{i}" for i in range(100)}
        
        relationship = Relationship(
            id=uuid4(),
            source_entity_id=uuid4(),
            target_entity_id=uuid4(),
            relationship_type=RelationshipType.RELATED_TO,
            confidence=0.8,
            properties=many_properties
        )
        
        assert len(relationship.properties) == 100
        assert relationship.properties["prop_0"] == "value_0"
        assert relationship.properties["prop_99"] == "value_99"


class TestFileHandlingEdgeCases:
    """Test file handling edge cases."""

    def test_note_with_broken_frontmatter(self):
        """Test that notes with broken frontmatter are handled gracefully."""
        # This would typically be handled by the file parser, but we can test the model
        note = Note(
            id=uuid4(),
            title="Broken Frontmatter Note",
            content="Content with broken frontmatter",
            file_path="/tmp/test-vault/broken-frontmatter-note.md",
            frontmatter={"broken": "value", "nested": {"invalid": "structure"}}
        )
        
        assert note.frontmatter["broken"] == "value"
        assert note.frontmatter["nested"]["invalid"] == "structure"

    def test_note_with_mixed_encodings(self):
        """Test that notes with mixed encodings are handled correctly."""
        # This tests the model's ability to handle various string content
        note = Note(
            id=uuid4(),
            title="Mixed Encoding Note",
            content="ASCII: Hello World\nUnicode: 你好世界\nEmoji: 🚀",
            file_path="/tmp/test-vault/mixed-encoding-note.md"
        )
        
        assert "Hello World" in note.content
        assert "你好世界" in note.content
        assert "🚀" in note.content

    def test_note_with_unusual_filename(self):
        """Test that notes with unusual filenames are handled correctly."""
        unusual_filename = "note with spaces and (parentheses) and [brackets].md"
        
        note = Note(
            id=uuid4(),
            title="Unusual Filename Note",
            content="Content with unusual filename",
            file_path=f"/tmp/test-vault/{unusual_filename}"
        )
        
        assert unusual_filename in note.file_path
        assert note.title == "Unusual Filename Note"


class TestPerformanceEdgeCases:
    """Test performance-related edge cases."""

    def test_large_number_of_entities(self):
        """Test creating a large number of entities."""
        entities = []
        for i in range(1000):
            entity = Entity(
                id=uuid4(),
                name=f"Entity {i}",
                entity_type=EntityType.CONCEPT,
                confidence=0.8,
                properties={"index": i}
            )
            entities.append(entity)
        
        assert len(entities) == 1000
        assert entities[0].name == "Entity 0"
        assert entities[999].name == "Entity 999"

    def test_large_number_of_relationships(self):
        """Test creating a large number of relationships."""
        relationships = []
        for i in range(1000):
            relationship = Relationship(
                id=uuid4(),
                source_entity_id=uuid4(),
                target_entity_id=uuid4(),
                relationship_type=RelationshipType.RELATED_TO,
                confidence=0.8,
                properties={"index": i}
            )
            relationships.append(relationship)
        
        assert len(relationships) == 1000
        assert relationships[0].properties["index"] == 0
        assert relationships[999].properties["index"] == 999

    def test_note_with_many_links(self):
        """Test creating a note with many links."""
        many_links = {f"[[link_{i}]]" for i in range(1000)}
        many_links.update({f"https://example{i}.com" for i in range(1000)})
        
        note = Note(
            id=uuid4(),
            title="Many Links Note",
            content="Content with many links",
            file_path="/tmp/test-vault/many-links-note.md",
            links=many_links
        )
        
        assert len(note.links) == 2000
        assert "[[link_0]]" in note.links
        assert "https://example999.com" in note.links

    def test_entity_with_many_properties(self):
        """Test creating an entity with many properties."""
        many_properties = {f"property_{i}": f"value_{i}" for i in range(1000)}
        
        entity = Entity(
            id=uuid4(),
            name="Many Properties Entity",
            entity_type=EntityType.CONCEPT,
            confidence=0.8,
            properties=many_properties
        )
        
        assert len(entity.properties) == 1000
        assert entity.properties["property_0"] == "value_0"
        assert entity.properties["property_999"] == "value_999" 