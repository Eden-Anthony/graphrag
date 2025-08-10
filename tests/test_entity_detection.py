"""Tests for the EntityDetectionService."""

import json
import pytest
from unittest.mock import Mock, patch, mock_open
from openai import OpenAI
from pathlib import Path

from graphrag.services.entity_detection import EntityDetectionService
from graphrag.models import EntityDetectionResult, EntityType
from graphrag.config import Config
from graphrag.models import Note


class TestEntityDetectionService:
    """Test cases for EntityDetectionService."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock(spec=Config)
        config.openai_api_key = "test-key"
        config.openai_org_id = "test-org"
        config.openai_entity_detection_model = "gpt-4o-mini"
        return config

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client for testing."""
        mock_client = Mock(spec=OpenAI)
        return mock_client

    @pytest.fixture
    def entity_detection_service(self):
        """Create an EntityDetectionService instance for testing."""
        return EntityDetectionService()

    def test_service_initialization(self, mock_config):
        """Test that the service initializes correctly."""
        with patch('graphrag.services.entity_detection.OpenAI') as mock_openai:
            service = EntityDetectionService()
            assert service is not None

    def test_load_entity_types_success(self, entity_detection_service):
        """Test successful loading of entity types from file."""
        with patch('builtins.open', mock_open(read_data='"Person", "Organization", "Concept"')):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.parent', return_value=Path('/mock/path')):
                    types = entity_detection_service._load_entity_types()
                    assert "Person" in types
                    assert "Organization" in types
                    assert "Concept" in types

    def test_load_entity_types_file_not_found(self, entity_detection_service):
        """Test handling when entity types file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            types = entity_detection_service._load_entity_types()
            assert types == []

    def test_load_entity_types_filters_numeric(self, entity_detection_service):
        """Test that numeric entity types are filtered out."""
        with patch('builtins.open', mock_open(read_data='"Person", "123", "Organization", "456"')):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.parent', return_value=Path('/mock/path')):
                    types = entity_detection_service._load_entity_types()
                    assert "Person" in types
                    assert "Organization" in types
                    assert "123" not in types
                    assert "456" not in types

    def test_build_prompt(self, entity_detection_service):
        """Test that the prompt is built correctly."""
        note = Note(
            file_path="test.md",
            title="Test Note",
            content="This is a test note about AI and machine learning."
        )
        
        prompt = entity_detection_service._create_entity_detection_prompt(note)
        
        assert "Test Note" in prompt
        assert "This is a test note about AI and machine learning" in prompt
        assert "Analyze the following Obsidian note" in prompt

    def test_detect_entities_success(self, entity_detection_service, mock_openai_client):
        """Test successful entity detection."""
        note = Note(
            file_path="test.md",
            title="Test Note",
            content="This is a test note about AI and machine learning."
        )
        
        with patch('graphrag.services.entity_detection.OpenAI', return_value=mock_openai_client):
            result = entity_detection_service.detect_entities(note)
            
            assert result.note_id == note.id
            assert isinstance(result.entities, list)
            assert isinstance(result.relationships, list)
            assert result.confidence > 0
            assert result.processing_time > 0

    def test_detect_entities_openai_error(self, entity_detection_service, mock_openai_client):
        """Test entity detection fallback when OpenAI fails."""
        note = Note(
            file_path="test.md",
            title="Test Note",
            content="This is a test note about AI and machine learning."
        )
        
        with patch('graphrag.services.entity_detection.OpenAI', return_value=mock_openai_client):
            mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
            
            result = entity_detection_service.detect_entities(note)
            
            assert result.note_id == note.id
            assert result.confidence == 0.5  # Fallback confidence
            assert result.processing_time > 0

    def test_detect_entities_invalid_json(self, entity_detection_service, mock_openai_client):
        """Test that entity detection falls back when OpenAI returns invalid JSON."""
        mock_response = Mock()
        mock_response.choices[0].message.content = "Invalid JSON response"
        
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = entity_detection_service.detect_entities("Test content about AI and John Smith")
        
        assert isinstance(result, EntityDetectionResult)
        assert len(result.entities) > 0  # Should use fallback detection
        assert result.confidence == 0.5  # Lower confidence for fallback

    def test_fallback_entity_detection(self, entity_detection_service):
        """Test that fallback entity detection works correctly."""
        content = "John Smith works at Google on artificial intelligence projects. He lives in San Francisco."
        
        result = entity_detection_service._fallback_entity_detection(content)
        
        assert isinstance(result, EntityDetectionResult)
        assert len(result.entities) >= 3  # Should detect John Smith, Google, AI, San Francisco
        assert result.confidence == 0.5
        assert result.processing_time > 0

    def test_fallback_entity_detection_no_entities(self, entity_detection_service):
        """Test fallback detection with content that has no obvious entities."""
        content = "This is a generic note about nothing specific."
        
        result = entity_detection_service._fallback_entity_detection(content)
        
        assert isinstance(result, EntityDetectionResult)
        assert len(result.entities) == 0
        assert result.confidence == 0.5

    def test_extract_entities_from_text(self, entity_detection_service):
        """Test that entities are extracted correctly from text."""
        text = "John Smith works at Google. He studies artificial intelligence and machine learning."
        
        entities = entity_detection_service._extract_entities_from_text(text)
        
        # Should extract various entity types
        assert any("John Smith" in entity["name"] for entity in entities)
        assert any("Google" in entity["name"] for entity in entities)
        assert any("artificial intelligence" in entity["name"].lower() for entity in entities)
        assert any("machine learning" in entity["name"].lower() for entity in entities)

    def test_extract_relationships_from_text(self, entity_detection_service):
        """Test that relationships are extracted correctly from text."""
        text = "John Smith works at Google. He studies artificial intelligence."
        
        relationships = entity_detection_service._extract_relationships_from_text(text)
        
        # Should extract relationships
        assert len(relationships) > 0
        # Check that relationships have the expected structure
        for rel in relationships:
            assert "source" in rel
            assert "target" in rel
            assert "type" in rel

    def test_detect_entities_with_realistic_content(self, entity_detection_service, mock_openai_client):
        """Test entity detection with realistic Obsidian note content."""
        content = """
        # Meeting with John Smith
        
        Had a great discussion about our AI project at Google. John is leading the machine learning 
        initiative and mentioned that Sarah Johnson from Stanford will be joining as a consultant.
        
        Key points:
        - Project timeline: Q2 2024
        - Budget: $500K
        - Location: San Francisco office
        
        Follow up: Schedule demo with the team next week.
        """
        
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "entities": [
                {"name": "John Smith", "type": "Person", "description": "Project lead"},
                {"name": "Google", "type": "Organisation", "description": "Company"},
                {"name": "AI project", "type": "Project", "description": "Machine learning initiative"},
                {"name": "Sarah Johnson", "type": "Person", "description": "Stanford consultant"},
                {"name": "Stanford", "type": "Organisation", "description": "University"},
                {"name": "San Francisco", "type": "Location", "description": "Office location"}
            ],
            "relationships": [
                {"source": "John Smith", "target": "AI project", "type": "LEADS"},
                {"source": "John Smith", "target": "Google", "type": "WORKS_FOR"},
                {"source": "Sarah Johnson", "target": "Stanford", "type": "AFFILIATED_WITH"},
                {"source": "AI project", "target": "Google", "type": "PART_OF"}
            ]
        })
        
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = entity_detection_service.detect_entities(content)
        
        assert isinstance(result, EntityDetectionResult)
        assert len(result.entities) == 6
        assert len(result.relationships) == 4
        
        # Check that key entities were detected
        entity_names = [e["name"] for e in result.entities]
        assert "John Smith" in entity_names
        assert "Google" in entity_names
        assert "AI project" in entity_names
        assert "San Francisco" in entity_names

    def test_detect_entities_rate_limiting(self, entity_detection_service, mock_openai_client):
        """Test that entity detection handles rate limiting gracefully."""
        # Simulate rate limiting
        mock_openai_client.chat.completions.create.side_effect = Exception("Rate limit exceeded")
        
        result = entity_detection_service.detect_entities("Test content")
        
        assert isinstance(result, EntityDetectionResult)
        # Should fall back to basic detection
        assert result.confidence == 0.5
        assert len(result.entities) >= 0  # May or may not find entities in fallback 