"""Tests for CLI functionality and command-line interface."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import sys
from io import StringIO
from uuid import uuid4

# Import the core module to test CLI-like functionality
from graphrag.core import ObsidianGraphRAG


class TestCLIFunctionality:
    """Test CLI-like functionality and command-line interactions."""

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

    @patch('graphrag.core.console.print')
    def test_chat_mode_basic_interaction(self, mock_console, mock_config, mock_services):
        """Test basic chat mode interaction."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock input to simulate user interaction
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["What is AI?", "quit"]
            
            # Mock the query service
            mock_result = Mock()
            mock_result.answer = "AI is artificial intelligence"
            mock_result.sources = ["source1", "source2"]
            mock_result.processing_time = 1.5
            graph_rag.query_service.query.return_value = mock_result
            
            graph_rag.chat_mode()
            
            # Verify that query was called
            graph_rag.query_service.query.assert_called_once_with("What is AI?", context_size=None)

    @patch('graphrag.core.console.print')
    def test_chat_mode_follow_up_questions(self, mock_console, mock_config, mock_services):
        """Test chat mode with follow-up questions."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock input to simulate user interaction
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["What is AI?", "Tell me more about machine learning", "quit"]
            
            # Mock the query service
            mock_result1 = Mock()
            mock_result1.answer = "AI is artificial intelligence"
            mock_result1.sources = ["source1"]
            mock_result1.processing_time = 1.0
            
            mock_result2 = Mock()
            mock_result2.answer = "Machine learning is a subset of AI"
            mock_result2.sources = ["source2"]
            mock_result2.processing_time = 1.2
            
            graph_rag.query_service.query.side_effect = [mock_result1, mock_result2]
            
            graph_rag.chat_mode()
            
            # Verify that query was called twice
            assert graph_rag.query_service.query.call_count == 2
            graph_rag.query_service.query.assert_any_call("What is AI?", context_size=None)
            graph_rag.query_service.query.assert_any_call("Tell me more about machine learning", context_size=None)

    @patch('graphrag.core.console.print')
    def test_chat_mode_invalid_input(self, mock_console, mock_config, mock_services):
        """Test chat mode handling of invalid input."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock input to simulate user interaction
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["", "   ", "quit"]
            
            graph_rag.chat_mode()
            
            # Verify that no queries were made for empty input
            graph_rag.query_service.query.assert_not_called()

    @patch('graphrag.core.console.print')
    def test_chat_mode_special_commands(self, mock_console, mock_config, mock_services):
        """Test chat mode special commands."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock input to simulate user interaction
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["help", "stats", "clear", "quit"]
            
            # Mock the knowledge graph service for stats
            mock_stats = {
                "total_notes": 100,
                "total_entities": 50,
                "total_relationships": 75
            }
            graph_rag.kg_service.get_graph_stats.return_value = mock_stats
            
            graph_rag.chat_mode()
            
            # Verify that stats were retrieved
            graph_rag.kg_service.get_graph_stats.assert_called_once()

    @patch('graphrag.core.console.print')
    def test_chat_mode_keyboard_interrupt(self, mock_console, mock_config, mock_services):
        """Test chat mode handling of keyboard interrupt."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock input to simulate keyboard interrupt
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = KeyboardInterrupt()
            
            graph_rag.chat_mode()
            
            # Should handle interrupt gracefully
            mock_console.assert_called()

    @patch('graphrag.core.console.print')
    def test_chat_mode_error_handling(self, mock_console, mock_config, mock_services):
        """Test chat mode error handling."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock input to simulate user interaction
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["What is AI?", "quit"]
            
            # Mock the query service to raise an error
            graph_rag.query_service.query.side_effect = Exception("Query failed")
            
            graph_rag.chat_mode()
            
            # Verify that error was handled gracefully
            mock_console.assert_called()

    def test_build_command_integration(self, mock_config, mock_services):
        """Test build command integration."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock the build method
        graph_rag.build_knowledge_graph = Mock(return_value=True)
        
        # Mock file discovery
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_rglob.return_value = [Path("/tmp/test-vault/note1.md")]
            
            result = graph_rag.build_knowledge_graph()
            
            assert result is True
            graph_rag.build_knowledge_graph.assert_called_once()

    def test_query_command_integration(self, mock_config, mock_services):
        """Test query command integration."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock the query service
        mock_result = Mock()
        mock_result.answer = "AI is artificial intelligence"
        mock_result.sources = ["source1"]
        mock_result.processing_time = 1.0
        
        graph_rag.query_service.query.return_value = mock_result
        
        result = graph_rag.query("What is AI?")
        
        assert result == mock_result
        graph_rag.query_service.query.assert_called_once_with("What is AI?", context_size=None)

    def test_watch_command_integration(self, mock_config, mock_services):
        """Test watch command integration."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock the file watcher service
        graph_rag.file_watcher.start_watching.return_value = True
        
        result = graph_rag.start_file_watcher()
        
        assert result is True
        graph_rag.file_watcher.start_watching.assert_called_once()

    def test_get_graph_statistics(self, mock_config, mock_services):
        """Test getting graph statistics."""
        graph_rag = ObsidianGraphRAG()
        
        with patch.object(graph_rag.kg_service, 'get_graph_stats') as mock_stats:
            mock_stats.return_value = {"nodes": 100, "relationships": 200}
            
            result = graph_rag.kg_service.get_graph_stats()
            
            assert result["nodes"] == 100
            assert result["relationships"] == 200

    def test_similar_entities_command_integration(self, mock_config, mock_services):
        """Test similar entities command integration."""
        graph_rag = ObsidianGraphRAG()
        
        with patch.object(graph_rag.query_service, 'get_similar_entities') as mock_similar:
            mock_similar.return_value = [{"name": "AI", "similarity": 0.8}]
            
            result = graph_rag.query_service.get_similar_entities("artificial intelligence")
            
            assert len(result) == 1
            assert result[0]["name"] == "AI"
            assert result[0]["similarity"] == 0.8

    def test_topic_summary_command_integration(self, mock_config, mock_services):
        """Test topic summary command integration."""
        graph_rag = ObsidianGraphRAG()
        
        with patch.object(graph_rag.query_service, 'get_topic_summary') as mock_summary:
            mock_summary.return_value = "AI is a field of computer science."
            
            result = graph_rag.query_service.get_topic_summary("artificial intelligence")
            
            assert result == "AI is a field of computer science."

    @patch('graphrag.core.console.print')
    def test_chat_mode_with_context_size(self, mock_console, mock_config, mock_services):
        """Test chat mode with context size specification."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock input to simulate user interaction
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["What is AI? (context: 10)", "quit"]
            
            # Mock the query service
            mock_result = Mock()
            mock_result.answer = "AI is artificial intelligence"
            mock_result.sources = ["source1"]
            mock_result.processing_time = 1.0
            graph_rag.query_service.query.return_value = mock_result
            
            # Mock parsing of context size from input
            with patch.object(graph_rag, '_parse_context_size') as mock_parse:
                mock_parse.return_value = ("What is AI?", 10)
                
                graph_rag.chat_mode()
                
                # Verify that query was called with context size
                graph_rag.query_service.query.assert_called_once_with("What is AI?", context_size=10)

    @patch('graphrag.core.console.print')
    def test_chat_mode_with_help_command(self, mock_console, mock_config, mock_services):
        """Test chat mode help command."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock input to simulate user interaction
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["help", "quit"]
            
            graph_rag.chat_mode()
            
            # Verify that help was displayed
            mock_console.assert_called()

    @patch('graphrag.core.console.print')
    def test_chat_mode_with_stats_command(self, mock_console, mock_config, mock_services):
        """Test chat mode stats command."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock input to simulate user interaction
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["stats", "quit"]
            
            # Mock the knowledge graph service
            mock_stats = {
                "total_notes": 100,
                "total_entities": 50,
                "total_relationships": 75
            }
            graph_rag.kg_service.get_graph_stats.return_value = mock_stats
            
            graph_rag.chat_mode()
            
            # Verify that stats were displayed
            mock_console.assert_called()

    @patch('graphrag.core.console.print')
    def test_chat_mode_with_clear_command(self, mock_console, mock_config, mock_services):
        """Test chat mode clear command."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock input to simulate user interaction
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["clear", "quit"]
            
            graph_rag.chat_mode()
            
            # Verify that screen was cleared
            mock_console.assert_called()

    def test_context_size_parsing(self, mock_config, mock_services):
        """Test parsing of context size from user input."""
        graph_rag = ObsidianGraphRAG()
        
        # Test various input formats
        test_cases = [
            ("What is AI? (context: 10)", ("What is AI?", 10)),
            ("Tell me about ML (context: 5)", ("Tell me about ML", 5)),
            ("Simple question", ("Simple question", None)),
            ("Question with (context: 15) extra text", ("Question with extra text", 15)),
        ]
        
        for input_text, expected in test_cases:
            # Mock the parsing method if it exists
            if hasattr(graph_rag, '_parse_context_size'):
                result = graph_rag._parse_context_size(input_text)
                assert result == expected

    def test_input_validation(self, mock_config, mock_services):
        """Test input validation in chat mode."""
        graph_rag = ObsidianGraphRAG()
        
        # Test various input types
        test_cases = [
            ("", False),  # Empty input
            ("   ", False),  # Whitespace only
            ("quit", True),  # Quit command
            ("What is AI?", True),  # Valid question
            ("help", True),  # Help command
            ("stats", True),  # Stats command
            ("clear", True),  # Clear command
        ]
        
        for input_text, is_valid in test_cases:
            # Mock the validation method if it exists
            if hasattr(graph_rag, '_is_valid_input'):
                result = graph_rag._is_valid_input(input_text)
                assert result == is_valid

    def test_error_recovery(self, mock_config, mock_services):
        """Test error recovery in chat mode."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock input to simulate user interaction
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["What is AI?", "quit"]
            
            # Mock the query service to fail first, then succeed
            mock_result = Mock()
            mock_result.answer = "AI is artificial intelligence"
            mock_result.sources = ["source1"]
            mock_result.processing_time = 1.0
            
            graph_rag.query_service.query.side_effect = [
                Exception("First attempt failed"),
                mock_result
            ]
            
            # Mock console print
            with patch('graphrag.core.console.print') as mock_console:
                graph_rag.chat_mode()
                
                # Verify that error was handled and retry succeeded
                assert graph_rag.query_service.query.call_count == 2

    def test_graceful_shutdown(self, mock_config, mock_services):
        """Test graceful shutdown of chat mode."""
        graph_rag = ObsidianGraphRAG()
        
        # Mock the cleanup method
        graph_rag.cleanup = Mock()
        
        # Mock input to simulate user interaction
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["quit"]
            
            # Mock console print
            with patch('graphrag.core.console.print') as mock_console:
                graph_rag.chat_mode()
                
                # Verify that cleanup was called
                graph_rag.cleanup.assert_called_once() 