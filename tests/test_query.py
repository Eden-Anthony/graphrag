"""Tests for the QueryService."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from openai import OpenAI

from graphrag.services.query import QueryService
from graphrag.models import QueryResult, Note
from graphrag.config import Config


class TestQueryService:
    """Test cases for QueryService."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock(spec=Config)
        config.openai_api_key = "test-key"
        config.openai_org_id = "test-org"
        config.openai_query_model = "gpt-4o"
        config.graph_rag_context_window = 20
        return config

    @pytest.fixture
    def mock_knowledge_graph_service(self):
        """Mock KnowledgeGraphService for testing."""
        return Mock()

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client for testing."""
        mock_client = Mock(spec=OpenAI)
        return mock_client

    @pytest.fixture
    def query_service(self, mock_knowledge_graph_service):
        """Create a QueryService instance for testing."""
        return QueryService(mock_knowledge_graph_service)

    def test_service_initialization(self, mock_config, mock_knowledge_graph_service):
        """Test that the service initializes correctly."""
        with patch('graphrag.services.query.OpenAI') as mock_openai:
            service = QueryService(mock_knowledge_graph_service)
            assert service.kg_service == mock_knowledge_graph_service

    def test_query_success(self, query_service, mock_knowledge_graph_service, mock_openai_client):
        """Test successful query processing."""
        question = "What is artificial intelligence?"
        mock_notes = [Mock(), Mock()]
        mock_knowledge_graph_service.search_notes.return_value = mock_notes
        
        with patch('graphrag.services.query.OpenAI', return_value=mock_openai_client):
            result = query_service.query(question)
            
            assert result.answer is not None
            assert result.context_notes == mock_notes
            assert result.confidence > 0

    def test_query_with_no_retrieved_notes(self, query_service, mock_knowledge_graph_service):
        """Test query processing when no relevant notes are found."""
        question = "What is quantum computing?"
        mock_knowledge_graph_service.search_notes.return_value = []
        
        result = query_service.query(question)
        
        assert "error" in result.answer.lower()
        assert result.context_notes == []
        assert result.confidence == 0.0

    def test_query_openai_error(self, query_service, mock_knowledge_graph_service, mock_openai_client):
        """Test query processing when OpenAI API fails."""
        question = "What is machine learning?"
        mock_knowledge_graph_service.search_notes.return_value = [Mock()]
        
        with patch('graphrag.services.query.OpenAI', return_value=mock_openai_client):
            mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
            
            result = query_service.query(question)
            
            assert "error" in result.answer.lower()
            assert result.confidence == 0.0

    def test_build_context_from_notes(self, query_service):
        """Test that context is built correctly from notes."""
        mock_notes = [
            Mock(content="Content about AI"),
            Mock(content="Content about ML")
        ]
        
        context = query_service._prepare_context_for_llm(mock_notes)
        
        assert "Content about AI" in context
        assert "Content about ML" in context

    def test_build_context_with_metadata(self, query_service):
        """Test that context includes note metadata."""
        mock_notes = [
            Mock(title="AI Note", content="Content about AI"),
            Mock(title="ML Note", content="Content about ML")
        ]
        
        context = query_service._prepare_context_for_llm(mock_notes)
        
        assert "AI Note" in context
        assert "ML Note" in context
        assert "Content about AI" in context
        assert "Content about ML" in context

    def test_build_prompt(self, query_service):
        """Test that the prompt is built correctly."""
        question = "What is artificial intelligence?"
        context = "Context about AI and machine learning."
        
        prompt = query_service._create_answer_generation_prompt(question, context)
        
        assert question in prompt
        assert context in prompt
        assert "Based on the provided context" in prompt
        assert "citations" in prompt

    def test_extract_citations_success(self, service, mock_openai_client):
        """Test that citations are extracted successfully."""
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "citations": ["note-1", "note-2"]
        })
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        citations = service._extract_citations("AI is a field of computer science.")
        
        assert citations == ["note-1", "note-2"]

    def test_extract_citations_invalid_json(self, service, mock_openai_client):
        """Test that citation extraction handles invalid JSON gracefully."""
        mock_response = Mock()
        mock_response.choices[0].message.content = "Invalid JSON"
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        citations = service._extract_citations("AI is a field of computer science.")
        
        assert citations == []

    def test_extract_citations_openai_error(self, service, mock_openai_client):
        """Test that citation extraction handles OpenAI errors gracefully."""
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        citations = service._extract_citations("AI is a field of computer science.")
        
        assert citations == []

    def test_chat_mode_success(self, service, mock_knowledge_graph_service, mock_openai_client):
        """Test that chat mode works correctly."""
        mock_notes = [{"id": "note-1", "title": "AI Note", "content": "Content about AI"}]
        mock_knowledge_graph_service.hybrid_search.return_value = mock_notes
        
        mock_response = Mock()
        mock_response.choices[0].message.content = "AI is artificial intelligence."
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = service.chat("What is AI?")
        
        assert isinstance(result, QueryResult)
        assert "AI is artificial intelligence" in result.answer

    def test_find_similar_entities_success(self, service, mock_knowledge_graph_service, mock_openai_client):
        """Test that finding similar entities works correctly."""
        mock_entities = [
            {"id": "entity-1", "name": "Machine Learning", "type": "Concept"},
            {"id": "entity-2", "name": "Deep Learning", "type": "Concept"}
        ]
        mock_knowledge_graph_service.search_entities.return_value = mock_entities
        
        mock_response = Mock()
        mock_response.choices[0].message.content = "Machine Learning and Deep Learning are similar to AI."
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = service.find_similar_entities("Artificial Intelligence")
        
        assert isinstance(result, QueryResult)
        assert "Machine Learning" in result.answer
        assert "Deep Learning" in result.answer

    def test_generate_topic_summary_success(self, service, mock_knowledge_graph_service, mock_openai_client):
        """Test that topic summaries are generated correctly."""
        mock_notes = [
            {"id": "note-1", "title": "AI Note", "content": "Content about AI"},
            {"id": "note-2", "title": "ML Note", "content": "Content about ML"}
        ]
        mock_knowledge_graph_service.hybrid_search.return_value = mock_notes
        
        mock_response = Mock()
        mock_response.choices[0].message.content = "AI and ML are computer science fields."
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = service.generate_topic_summary("artificial intelligence")
        
        assert isinstance(result, QueryResult)
        assert "AI and ML are computer science fields" in result.answer

    def test_query_with_follow_up(self, service, mock_knowledge_graph_service, mock_openai_client):
        """Test that follow-up queries work correctly."""
        # First query
        mock_notes_1 = [{"id": "note-1", "title": "AI Note", "content": "Content about AI"}]
        mock_knowledge_graph_service.hybrid_search.return_value = mock_notes_1
        
        mock_response_1 = Mock()
        mock_response_1.choices[0].message.content = "AI is artificial intelligence."
        mock_openai_client.chat.completions.create.return_value = mock_response_1
        
        result_1 = service.query("What is AI?")
        
        # Follow-up query
        mock_notes_2 = [{"id": "note-2", "title": "ML Note", "content": "Content about ML"}]
        mock_knowledge_graph_service.hybrid_search.return_value = mock_notes_2
        
        mock_response_2 = Mock()
        mock_response_2.choices[0].message.content = "ML is a subset of AI."
        mock_openai_client.chat.completions.create.return_value = mock_response_2
        
        result_2 = service.query("How does it relate to machine learning?", 
                               conversation_history=[result_1])
        
        assert isinstance(result_2, QueryResult)
        assert "ML is a subset of AI" in result_2.answer

    def test_query_with_conversation_history(self, service, mock_knowledge_graph_service, mock_openai_client):
        """Test that conversation history is included in prompts."""
        mock_notes = [{"id": "note-1", "title": "AI Note", "content": "Content about AI"}]
        mock_knowledge_graph_service.hybrid_search.return_value = mock_notes
        
        mock_response = Mock()
        mock_response.choices[0].message.content = "Based on our previous discussion..."
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        history = [
            QueryResult(answer="AI is artificial intelligence", query="What is AI?")
        ]
        
        result = service.query("Tell me more", conversation_history=history)
        
        assert isinstance(result, QueryResult)
        assert "Based on our previous discussion" in result.answer

    def test_query_processing_time_measurement(self, service, mock_knowledge_graph_service, mock_openai_client):
        """Test that processing time is measured correctly."""
        mock_notes = [{"id": "note-1", "title": "AI Note", "content": "Content about AI"}]
        mock_knowledge_graph_service.hybrid_search.return_value = mock_notes
        
        mock_response = Mock()
        mock_response.choices[0].message.content = "AI is artificial intelligence."
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = service.query("What is AI?")
        
        assert result.processing_time > 0
        assert isinstance(result.processing_time, float)

    def test_query_with_custom_parameters(self, service, mock_knowledge_graph_service, mock_openai_client):
        """Test that queries work with custom parameters."""
        mock_notes = [{"id": "note-1", "title": "AI Note", "content": "Content about AI"}]
        mock_knowledge_graph_service.hybrid_search.return_value = mock_notes
        
        mock_response = Mock()
        mock_response.choices[0].message.content = "AI is artificial intelligence."
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = service.query("What is AI?", limit=5, filters={"tags": ["ai"]})
        
        assert isinstance(result, QueryResult)
        # Verify that the knowledge graph service was called with custom parameters
        mock_knowledge_graph_service.hybrid_search.assert_called_with(
            "What is AI?", limit=5, filters={"tags": ["ai"]}
        )

    def test_query_error_handling(self, service, mock_knowledge_graph_service):
        """Test that query errors are handled gracefully."""
        mock_knowledge_graph_service.hybrid_search.side_effect = Exception("Search error")
        
        result = service.query("What is AI?")
        
        assert isinstance(result, QueryResult)
        assert "error occurred" in result.answer.lower()
        assert result.confidence == 0.0
        assert result.processing_time > 0

    def test_build_context_with_empty_notes(self, service):
        """Test that context building handles empty notes gracefully."""
        notes = []
        
        context = service._build_context_from_notes(notes)
        
        assert context == "No relevant notes found."

    def test_build_context_with_note_without_title(self, service):
        """Test that context building handles notes without titles gracefully."""
        notes = [{"id": "note-1", "content": "Content about AI"}]
        
        context = service._build_context_from_notes(notes)
        
        assert "Content about AI" in context
        assert "note-1" in context  # Should use ID as fallback

    def test_query_with_special_characters(self, service, mock_knowledge_graph_service, mock_openai_client):
        """Test that queries with special characters are handled correctly."""
        mock_notes = [{"id": "note-1", "title": "AI Note", "content": "Content about AI"}]
        mock_knowledge_graph_service.hybrid_search.return_value = mock_notes
        
        mock_response = Mock()
        mock_response.choices[0].message.content = "AI is artificial intelligence."
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        query = "What is AI? (with examples)"
        result = service.query(query)
        
        assert isinstance(result, QueryResult)
        assert result.query == query 