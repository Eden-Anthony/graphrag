"""Tests for the KnowledgeGraphService."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

from graphrag.services.knowledge_graph import KnowledgeGraphService
from graphrag.models import Note, Entity, Relationship, EntityType, RelationshipType
from graphrag.config import Config


class TestKnowledgeGraphService:
    """Test cases for KnowledgeGraphService."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock(spec=Config)
        config.neo4j_uri = "bolt://localhost:7687"
        config.neo4j_user = "neo4j"
        config.neo4j_password = "password"
        config.neo4j_database = "neo4j"
        config.neo4j_index_name = "test-index"
        config.neo4j_embedding_index_name = "test-embedding-index"
        config.openai_api_key = "test-key"
        config.openai_org_id = "test-org"
        config.openai_embedding_model = "text-embedding-ada-002"
        config.graph_rag_context_window = 20
        return config

    @pytest.fixture
    def mock_neo4j_driver(self):
        """Mock Neo4j driver for testing."""
        mock_driver = Mock()
        mock_session = Mock()
        
        # Mock the context manager behavior
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        
        mock_driver.session.return_value = mock_session
        return mock_driver

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client for testing."""
        mock_client = Mock()
        mock_client.embeddings.create.return_value.data[0].embedding = [0.1] * 1536
        return mock_client

    @pytest.fixture
    def service(self, mock_config, mock_neo4j_driver, mock_openai_client):
        """Create KnowledgeGraphService instance for testing."""
        with patch('graphrag.services.knowledge_graph.GraphDatabase') as mock_graph_db, \
             patch('graphrag.services.knowledge_graph.OpenAI', return_value=mock_openai_client), \
             patch('graphrag.services.knowledge_graph.OpenAIEmbeddings', return_value=Mock()), \
             patch('graphrag.services.knowledge_graph.HybridCypherRetriever', return_value=Mock()):
            
            mock_graph_db.driver.return_value = mock_neo4j_driver
            return KnowledgeGraphService(mock_config)

    def test_service_initialization(self, mock_config, mock_neo4j_driver):
        """Test that KnowledgeGraphService initializes correctly."""
        with patch('graphrag.services.knowledge_graph.GraphDatabase') as mock_graph_db, \
             patch('graphrag.services.knowledge_graph.OpenAI') as mock_openai, \
             patch('graphrag.services.knowledge_graph.OpenAIEmbeddings') as mock_embeddings, \
             patch('graphrag.services.knowledge_graph.HybridCypherRetriever') as mock_retriever:
            
            mock_graph_db.driver.return_value = mock_neo4j_driver
            
            service = KnowledgeGraphService(mock_config)
            
            assert service.config == mock_config
            assert service.driver == mock_neo4j_driver
            mock_graph_db.driver.assert_called_once_with(
                mock_config.neo4j_uri,
                auth=(mock_config.neo4j_user, mock_config.neo4j_password)
            )
            mock_openai.assert_called_once_with(
                api_key=mock_config.openai_api_key,
                organization=mock_config.openai_org_id
            )

    def test_ensure_indexes_and_constraints(self, service, mock_neo4j_driver):
        """Test that indexes and constraints are created correctly."""
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        
        service._ensure_indexes_and_constraints()
        
        # Should call session.run multiple times for indexes and constraints
        assert mock_session.run.call_count >= 3

    def test_add_note_success(self, service, mock_neo4j_driver):
        """Test that notes are added successfully to the graph."""
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        
        note = Note(
            id="test-note-1",
            title="Test Note",
            content="This is a test note about AI.",
            file_path="/tmp/test-vault/test-note.md"
        )
        
        service.add_note(note)
        
        # Should call session.run to create the note
        mock_session.run.assert_called()
        call_args = mock_session.run.call_args
        assert "CREATE (n:Note" in call_args[0][0]

    def test_add_entity_success(self, service, mock_neo4j_driver):
        """Test that entities are added successfully to the graph."""
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        
        entity = Entity(
            id="test-entity-1",
            name="Artificial Intelligence",
            type=EntityType.CONCEPT,
            description="A field of computer science"
        )
        
        service.add_entity(entity)
        
        # Should call session.run to create the entity
        mock_session.run.assert_called()
        call_args = mock_session.run.call_args
        assert "CREATE (e:Entity" in call_args[0][0]

    def test_create_relationship_success(self, service, mock_neo4j_driver):
        """Test that relationships are created successfully."""
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        
        relationship = Relationship(
            id="test-rel-1",
            source_entity_id="entity-1",
            target_entity_id="entity-2",
            type=RelationshipType.RELATED_TO
        )
        
        service.create_relationship(relationship)
        
        # Should call session.run to create the relationship
        mock_session.run.assert_called()
        call_args = mock_session.run.call_args
        assert "MATCH" in call_args[0][0]
        assert "CREATE" in call_args[0][0]

    def test_update_note_embedding_success(self, service, mock_neo4j_driver, mock_openai_client):
        """Test that note embeddings are updated successfully."""
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        
        note = Note(
            id="test-note-1",
            title="Test Note",
            content="This is a test note about AI.",
            file_path="/tmp/test-vault/test-note.md"
        )
        
        service.update_note_embedding(note)
        
        # Should call OpenAI to generate embedding
        mock_openai_client.embeddings.create.assert_called_once()
        # Should call session.run to update the embedding
        mock_session.run.assert_called()

    def test_hybrid_search_success(self, service, mock_neo4j_driver):
        """Test that hybrid search works correctly."""
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        
        # Mock the retriever to return some results
        mock_retriever = Mock()
        mock_retriever.get_relevant_documents.return_value = [
            Mock(page_content="Test content 1", metadata={"id": "note-1"}),
            Mock(page_content="Test content 2", metadata={"id": "note-2"})
        ]
        service.retriever = mock_retriever
        
        results = service.hybrid_search("test query")
        
        assert len(results) == 2
        assert results[0]["id"] == "note-1"
        assert results[1]["id"] == "note-2"

    def test_get_graph_statistics_success(self, service, mock_neo4j_driver):
        """Test that graph statistics are retrieved correctly."""
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        
        # Mock the result
        mock_result = Mock()
        mock_result.data.return_value = [
            {"nodes": 100, "relationships": 200, "notes": 50, "entities": 30}
        ]
        mock_session.run.return_value = mock_result
        
        stats = service.get_graph_statistics()
        
        assert stats["total_nodes"] == 100
        assert stats["total_relationships"] == 200
        assert stats["total_notes"] == 50
        assert stats["total_entities"] == 30

    def test_get_graph_statistics_no_data(self, service, mock_neo4j_driver):
        """Test that graph statistics handle empty results gracefully."""
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        
        # Mock empty result
        mock_result = Mock()
        mock_result.data.return_value = []
        mock_session.run.return_value = mock_result
        
        stats = service.get_graph_statistics()
        
        assert stats["total_nodes"] == 0
        assert stats["total_relationships"] == 0
        assert stats["total_notes"] == 0
        assert stats["total_entities"] == 0

    def test_connection_failure_handling(self, mock_config):
        """Test that connection failures are handled gracefully."""
        with patch('graphrag.services.knowledge_graph.GraphDatabase') as mock_graph_db:
            mock_graph_db.driver.side_effect = ServiceUnavailable("Connection failed")
            
            with pytest.raises(ServiceUnavailable):
                KnowledgeGraphService(mock_config)

    def test_session_operations_with_error(self, service, mock_neo4j_driver):
        """Test that session operations handle errors gracefully."""
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        mock_session.run.side_effect = Exception("Database error")
        
        note = Note(
            id="test-note-1",
            title="Test Note",
            content="This is a test note.",
            file_path="/tmp/test-vault/test-note.md"
        )
        
        with pytest.raises(Exception, match="Database error"):
            service.add_note(note)

    def test_batch_operations(self, service, mock_neo4j_driver):
        """Test that batch operations work correctly."""
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        
        notes = [
            Note(id=f"note-{i}", title=f"Note {i}", content=f"Content {i}", 
                 file_path=f"/tmp/note-{i}.md")
            for i in range(3)
        ]
        
        service.add_notes_batch(notes)
        
        # Should call session.run for each note
        assert mock_session.run.call_count == 3

    def test_entity_linking(self, service, mock_neo4j_driver):
        """Test that entities are linked to notes correctly."""
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        
        note_id = "test-note-1"
        entity_ids = ["entity-1", "entity-2"]
        
        service.link_entities_to_note(note_id, entity_ids)
        
        # Should call session.run to create relationships
        mock_session.run.assert_called()
        call_args = mock_session.run.call_args
        assert "MATCH" in call_args[0][0]
        assert "CREATE" in call_args[0][0]

    def test_note_retrieval_by_id(self, service, mock_neo4j_driver):
        """Test that notes can be retrieved by ID."""
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        
        # Mock the result
        mock_result = Mock()
        mock_result.data.return_value = [
            {
                "n": {
                    "id": "test-note-1",
                    "title": "Test Note",
                    "content": "Test content",
                    "file_path": "/tmp/test-note.md"
                }
            }
        ]
        mock_session.run.return_value = mock_result
        
        note = service.get_note_by_id("test-note-1")
        
        assert note is not None
        assert note["id"] == "test-note-1"
        assert note["title"] == "Test Note"

    def test_note_retrieval_not_found(self, service, mock_neo4j_driver):
        """Test that note retrieval returns None when not found."""
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        
        # Mock empty result
        mock_result = Mock()
        mock_result.data.return_value = []
        mock_session.run.return_value = mock_result
        
        note = service.get_note_by_id("non-existent-note")
        
        assert note is None

    def test_cleanup_resources(self, service, mock_neo4j_driver):
        """Test that resources are cleaned up properly."""
        service.close()
        
        # Should close the driver
        mock_neo4j_driver.close.assert_called_once()

    def test_hybrid_search_with_filters(self, service, mock_neo4j_driver):
        """Test that hybrid search works with additional filters."""
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        
        # Mock the retriever
        mock_retriever = Mock()
        mock_retriever.get_relevant_documents.return_value = [
            Mock(page_content="Filtered content", metadata={"id": "filtered-note"})
        ]
        service.retriever = mock_retriever
        
        results = service.hybrid_search("test query", limit=5, filters={"tags": ["ai"]})
        
        assert len(results) == 1
        assert results[0]["id"] == "filtered-note"

    def test_entity_search(self, service, mock_neo4j_driver):
        """Test that entity search works correctly."""
        mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
        
        # Mock the result
        mock_result = Mock()
        mock_result.data.return_value = [
            {
                "e": {
                    "id": "entity-1",
                    "name": "Artificial Intelligence",
                    "type": "Concept",
                    "description": "AI field"
                }
            }
        ]
        mock_session.run.return_value = mock_result
        
        entities = service.search_entities("AI", entity_type=EntityType.CONCEPT)
        
        assert len(entities) == 1
        assert entities[0]["name"] == "Artificial Intelligence"
        assert entities[0]["type"] == "Concept" 