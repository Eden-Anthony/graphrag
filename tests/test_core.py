"""Tests for the core ObsidianGraphRAG module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
from uuid import uuid4

from graphrag.core import ObsidianGraphRAG
from graphrag.models import Note, Entity, EntityType, Relationship, RelationshipType
from graphrag.services.entity_detection import EntityDetectionResult


class TestObsidianGraphRAG:
    """Test the main ObsidianGraphRAG class."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        with patch('graphrag.core.Config') as mock_config_class:
            mock_config = Mock()
            mock_config.OBSIDIAN_VAULT_PATH = '/tmp/test-vault'
            mock_config_class.validate.return_value = None
            mock_config_class.OBSIDIAN_VAULT_PATH = '/tmp/test-vault'
            yield mock_config_class

    @pytest.fixture
    def mock_services(self):
        """Mock all the services."""
        with patch.multiple('graphrag.core',
                           EntityDetectionService=Mock(),
                           KnowledgeGraphService=Mock(),
                           QueryService=Mock(),
                           FileWatcherService=Mock()):
            yield

    @pytest.fixture
    def temp_vault(self, tmp_path):
        """Create a temporary vault with some test files."""
        vault_path = tmp_path / "test-vault"
        vault_path.mkdir()
        
        # Create some test markdown files
        (vault_path / "note1.md").write_text("# Test Note 1\n\nThis is a test note about AI.")
        (vault_path / "note2.md").write_text("# Test Note 2\n\nThis is about machine learning.")
        (vault_path / "⭕Meta" / "meta.md").write_text("# Meta note\n\nThis should be ignored.")
        
        return vault_path

    def test_initialization_success(self, mock_config, mock_services):
        """Test successful initialization of ObsidianGraphRAG."""
        with patch('graphrag.core.logging.getLogger') as mock_logger:
            graph_rag = ObsidianGraphRAG()
            
            assert graph_rag.vault_path == '/tmp/test-vault'
            assert graph_rag.entity_detection_service is not None
            assert graph_rag.kg_service is not None
            assert graph_rag.query_service is not None
            assert graph_rag.file_watcher is not None

    def test_initialization_with_config_validation_error(self, mock_services):
        """Test initialization when config validation fails."""
        with patch('graphrag.core.Config') as mock_config_class:
            mock_config_class.validate.side_effect = Exception("Config error")
            
            with pytest.raises(Exception):
                ObsidianGraphRAG()

    def test_build_knowledge_graph(self, obsidian_graph_rag, mock_entity_detection_service, mock_knowledge_graph_service):
        """Test building the knowledge graph."""
        with patch('pathlib.Path.glob') as mock_glob:
            mock_glob.return_value = [Path("test1.md"), Path("test2.md")]
            
            with patch.object(obsidian_graph_rag, '_read_note_file') as mock_read:
                mock_read.return_value = Mock()
                
                result = obsidian_graph_rag.build_initial_knowledge_graph()
                
                assert result["status"] == "success"
                assert result["files_processed"] == 2

    def test_build_knowledge_graph_with_errors(self, mock_config, mock_services):
        """Test knowledge graph building with file processing errors."""
        graph_rag = ObsidianGraphRAG()
        
        with patch('pathlib.Path.glob') as mock_glob:
            mock_glob.return_value = [Path("test1.md"), Path("test2.md")]
            
            with patch.object(graph_rag, '_read_note_file') as mock_read:
                mock_read.side_effect = [Mock(), Exception("File read error")]
                
                result = graph_rag.build_initial_knowledge_graph()
                
                assert result["status"] == "success"
                assert result["files_processed"] == 1  # Only one file processed successfully

    def test_start_file_watcher_success(self, mock_config, mock_services):
        """Test starting the file watcher successfully."""
        graph_rag = ObsidianGraphRAG()
        
        with patch.object(graph_rag.file_watcher, 'start_watching') as mock_start:
            mock_start.return_value = True
            
            result = graph_rag.start_file_watcher()
            
            assert result is True
            mock_start.assert_called_once()

    def test_start_file_watcher_failure(self, mock_config, mock_services):
        """Test starting the file watcher with failure."""
        graph_rag = ObsidianGraphRAG()
        
        with patch.object(graph_rag.file_watcher, 'start_watching') as mock_start:
            mock_start.return_value = False
            
            result = graph_rag.start_file_watcher()
            
            assert result is False
            mock_start.assert_called_once()

    def test_stop_file_watcher(self, mock_config, mock_services):
        """Test stopping the file watcher."""
        graph_rag = ObsidianGraphRAG()
        
        with patch.object(graph_rag.file_watcher, 'stop_watching') as mock_stop:
            graph_rag.stop_file_watcher()
            
            mock_stop.assert_called_once()

    def test_query_success(self, mock_config, mock_services):
        """Test successful query processing."""
        graph_rag = ObsidianGraphRAG()
        
        with patch.object(graph_rag.query_service, 'query') as mock_query:
            mock_result = Mock()
            mock_query.return_value = mock_result
            
            result = graph_rag.query("What is AI?")
            
            assert result == mock_result
            mock_query.assert_called_once_with("What is AI?", None)

    def test_query_with_context_size(self, mock_config, mock_services):
        """Test query processing with custom context size."""
        graph_rag = ObsidianGraphRAG()
        
        with patch.object(graph_rag.query_service, 'query') as mock_query:
            mock_result = Mock()
            mock_query.return_value = mock_result
            
            result = graph_rag.query("What is AI?", context_size=10)
            
            assert result == mock_result
            mock_query.assert_called_once_with("What is AI?", 10)

    def test_query_failure(self, mock_config, mock_services):
        """Test query processing failure."""
        graph_rag = ObsidianGraphRAG()
        
        with patch.object(graph_rag.query_service, 'query') as mock_query:
            mock_query.side_effect = Exception("Query failed")
            
            with pytest.raises(Exception, match="Query failed"):
                graph_rag.query("What is AI?")

    def test_chat_mode_basic(self, mock_config, mock_services):
        """Test basic chat mode functionality."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock the query service
        mock_result = Mock()
        mock_result.answer = "AI is artificial intelligence"
        mock_result.sources = ["source1"]
        mock_result.processing_time = 1.0
        
        graph_rag.query_service.query.return_value = mock_result
        
        # Mock input to simulate user interaction
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["What is AI?", "quit"]
            
            # Mock console print
            with patch('graphrag.core.console.print') as mock_console:
                graph_rag.chat_mode()
                
                # Verify that query was called
                graph_rag.query_service.query.assert_called_once_with("What is AI?", context_size=None)

    def test_chat_mode_with_follow_up(self, mock_config, mock_services):
        """Test chat mode with follow-up questions."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock the query service
        mock_result = Mock()
        mock_result.answer = "AI is artificial intelligence"
        mock_result.sources = ["source1"]
        mock_result.processing_time = 1.0
        
        graph_rag.query_service.query.return_value = mock_result
        
        # Mock input to simulate user interaction
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["What is AI?", "Tell me more", "quit"]
            
            # Mock console print
            with patch('graphrag.core.console.print') as mock_console:
                graph_rag.chat_mode()
                
                # Verify that query was called twice
                assert graph_rag.query_service.query.call_count == 2

    def test_chat_mode_invalid_input(self, mock_config, mock_services):
        """Test chat mode with invalid input."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock input to simulate user interaction
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["", "   ", "quit"]
            
            # Mock console print
            with patch('graphrag.core.console.print') as mock_console:
                graph_rag.chat_mode()
                
                # Verify that no queries were made for empty input
                graph_rag.query_service.query.assert_not_called()

    def test_chat_mode_keyboard_interrupt(self, mock_config, mock_services):
        """Test chat mode handling of keyboard interrupt."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock input to simulate keyboard interrupt
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = KeyboardInterrupt()
            
            # Mock console print
            with patch('graphrag.core.console.print') as mock_console:
                graph_rag.chat_mode()
                
                # Should handle interrupt gracefully
                mock_console.assert_called()

    def test_get_similar_entities(self, mock_config, mock_services):
        """Test getting similar entities."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock the query service
        mock_entities = [
            {"name": "Entity 1", "similarity": 0.9},
            {"name": "Entity 2", "similarity": 0.8}
        ]
        
        graph_rag.query_service.get_similar_entities.return_value = mock_entities
        
        result = graph_rag.get_similar_entities("AI", limit=5)
        
        assert result == mock_entities
        graph_rag.query_service.get_similar_entities.assert_called_once_with("AI", 5)

    def test_get_topic_summary(self, mock_config, mock_services):
        """Test getting topic summary."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock the query service
        mock_summary = "AI is a broad field covering machine learning, neural networks, and more."
        graph_rag.query_service.get_topic_summary.return_value = mock_summary
        
        result = graph_rag.get_topic_summary("AI", limit=10)
        
        assert result == mock_summary
        graph_rag.query_service.get_topic_summary.assert_called_once_with("AI", 10)

    def test_get_graph_statistics(self, mock_config, mock_services):
        """Test getting graph statistics."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock the knowledge graph service
        mock_stats = {
            "total_notes": 100,
            "total_entities": 50,
            "total_relationships": 75
        }
        
        graph_rag.kg_service.get_graph_stats.return_value = mock_stats
        
        result = graph_rag.get_graph_statistics()
        
        assert result == mock_stats
        graph_rag.kg_service.get_graph_stats.assert_called_once()

    def test_parse_markdown_file_success(self, mock_config, mock_services):
        """Test successful markdown file parsing."""
        graph_rag = ObsidianGraphRAG()
        
        # Create a temporary markdown file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""---
title: Test Note
tags: [test, ai]
---

# Test Note

This is a test note about [[AI]] and [[machine learning]].

[External Link](https://example.com)
""")
            temp_file = f.name
        
        try:
            # Parse the file
            note = graph_rag._parse_markdown_file(Path(temp_file))
            
            assert note.title == "Test Note"
            assert "test" in note.tags
            assert "ai" in note.tags
            assert "[[AI]]" in note.links
            assert "[[machine learning]]" in note.links
            assert "https://example.com" in note.links
            
        finally:
            # Clean up
            import os
            os.unlink(temp_file)

    def test_parse_markdown_file_no_frontmatter(self, mock_config, mock_services):
        """Test markdown file parsing without frontmatter."""
        graph_rag = ObsidianGraphRAG()
        
        # Create a temporary markdown file without frontmatter
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Test Note

This is a test note without frontmatter.

[[Internal Link]]
""")
            temp_file = f.name
        
        try:
            # Parse the file
            note = graph_rag._parse_markdown_file(Path(temp_file))
            
            assert note.title == "Test Note"
            assert note.frontmatter == {}
            assert "[[Internal Link]]" in note.links
            
        finally:
            # Clean up
            import os
            os.unlink(temp_file)

    def test_parse_markdown_file_with_errors(self, mock_config, mock_services):
        """Test markdown file parsing with errors."""
        graph_rag = ObsidianGraphRAG()
        
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            graph_rag._parse_markdown_file(Path("/non/existent/file.md"))

    def test_extract_links_from_content(self, mock_config, mock_services):
        """Test link extraction from content."""
        graph_rag = ObsidianGraphRAG()
        
        content = """
        This note mentions [[AI]] and [[machine learning]].
        It also has external links like [OpenAI](https://openai.com).
        And more internal links: [[Python]], [[Neural Networks]].
        """
        
        links = graph_rag._extract_links_from_content(content)
        
        # Check internal links
        assert "[[AI]]" in links
        assert "[[machine learning]]" in links
        assert "[[Python]]" in links
        assert "[[Neural Networks]]" in links
        
        # Check external links
        assert "https://openai.com" in links

    def test_extract_links_from_content_no_links(self, mock_config, mock_services):
        """Test link extraction from content with no links."""
        graph_rag = ObsidianGraphRAG()
        
        content = "This is a simple note with no links."
        
        links = graph_rag._extract_links_from_content(content)
        
        assert links == set()

    def test_extract_links_from_content_mixed_links(self, mock_config, mock_services):
        """Test link extraction from content with mixed link types."""
        graph_rag = ObsidianGraphRAG()
        
        content = """
        # Mixed Links Note
        
        Internal: [[Note 1]], [[Note 2]]
        External: [Link 1](https://example1.com), [Link 2](https://example2.com)
        More internal: [[Note 3]]
        """
        
        links = graph_rag._extract_links_from_content(content)
        
        # Check internal links
        assert "[[Note 1]]" in links
        assert "[[Note 2]]" in links
        assert "[[Note 3]]" in links
        
        # Check external links
        assert "https://example1.com" in links
        assert "https://example2.com" in links

    def test_cleanup_on_exit(self, mock_config, mock_services):
        """Test cleanup when exiting."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock the services
        graph_rag.kg_service.close = Mock()
        graph_rag.file_watcher.stop_watching = Mock()
        
        # Call cleanup
        graph_rag.cleanup()
        
        # Verify cleanup was called
        graph_rag.kg_service.close.assert_called_once()
        graph_rag.file_watcher.stop_watching.assert_called_once()

    def test_context_manager(self, mock_config, mock_services):
        """Test ObsidianGraphRAG as a context manager."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock the cleanup method
        graph_rag.cleanup = Mock()
        
        with graph_rag:
            # Should be able to use the instance
            assert graph_rag.vault_path == '/tmp/test-vault'
        
        # Cleanup should be called when exiting context
        graph_rag.cleanup.assert_called_once() 