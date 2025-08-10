"""Tests for the FileWatcherService."""

import os
import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from watchdog.events import FileSystemEvent, FileCreatedEvent, FileModifiedEvent, FileDeletedEvent, FileMovedEvent

from graphrag.services.file_watcher import FileWatcherService, ObsidianFileHandler
from graphrag.config import Config


class TestObsidianFileHandler:
    """Test cases for ObsidianFileHandler."""

    @pytest.fixture
    def mock_callback(self):
        """Mock callback function for testing."""
        return Mock()

    @pytest.fixture
    def handler(self, mock_callback):
        """Create ObsidianFileHandler instance for testing."""
        return ObsidianFileHandler(mock_callback, debounce_seconds=1)

    def test_handler_initialization(self, mock_callback):
        """Test that ObsidianFileHandler initializes correctly."""
        handler = ObsidianFileHandler(mock_callback, debounce_seconds=2)
        
        assert handler.callback == mock_callback
        assert handler.debounce_seconds == 2
        assert handler.pending_events == {}

    def test_on_created_event(self, handler, mock_callback):
        """Test that file creation events are handled correctly."""
        event = FileCreatedEvent("/tmp/test-vault/test-note.md")
        
        handler.on_created(event)
        
        # Should schedule the event for processing
        assert len(handler.pending_events) == 1
        assert "/tmp/test-vault/test-note.md" in handler.pending_events

    def test_on_modified_event(self, handler, mock_callback):
        """Test that file modification events are handled correctly."""
        event = FileModifiedEvent("/tmp/test-vault/test-note.md")
        
        handler.on_modified(event)
        
        # Should schedule the event for processing
        assert len(handler.pending_events) == 1
        assert "/tmp/test-vault/test-note.md" in handler.pending_events

    def test_on_deleted_event(self, handler, mock_callback):
        """Test that file deletion events are handled correctly."""
        event = FileDeletedEvent("/tmp/test-vault/test-note.md")
        
        handler.on_deleted(event)
        
        # Should call callback immediately for deletions
        mock_callback.assert_called_once_with("deleted", "/tmp/test-vault/test-note.md")

    def test_on_moved_event(self, handler, mock_callback):
        """Test that file movement events are handled correctly."""
        event = FileMovedEvent("/tmp/test-vault/old-name.md", "/tmp/test-vault/new-name.md")
        
        handler.on_moved(event)
        
        # Should call callback immediately for moves
        mock_callback.assert_called_once_with("moved", "/tmp/test-vault/old-name.md", "/tmp/test-vault/new-name.md")

    def test_ignore_non_markdown_files(self, handler, mock_callback):
        """Test that non-markdown files are ignored."""
        event = FileCreatedEvent("/tmp/test-vault/test.txt")
        
        handler.on_created(event)
        
        # Should not schedule non-markdown files
        assert len(handler.pending_events) == 0
        mock_callback.assert_not_called()

    def test_ignore_meta_folder_files(self, handler, mock_callback):
        """Test that files in the Meta folder are ignored."""
        event = FileCreatedEvent("/tmp/test-vault/⭕Meta/template.md")
        
        handler.on_created(event)
        
        # Should not schedule Meta folder files
        assert len(handler.pending_events) == 0
        mock_callback.assert_not_called()

    def test_debouncing_behavior(self, handler, mock_callback):
        """Test that rapid events are debounced correctly."""
        event1 = FileModifiedEvent("/tmp/test-vault/test-note.md")
        event2 = FileModifiedEvent("/tmp/test-vault/test-note.md")
        
        handler.on_modified(event1)
        handler.on_modified(event2)
        
        # Should only have one pending event due to debouncing
        assert len(handler.pending_events) == 1
        assert "/tmp/test-vault/test-note.md" in handler.pending_events

    def test_event_processing_after_debounce(self, handler, mock_callback):
        """Test that events are processed after debounce period."""
        event = FileCreatedEvent("/tmp/test-vault/test-note.md")
        
        handler.on_created(event)
        
        # Wait for debounce period
        time.sleep(1.1)
        
        # Should call callback after debounce
        mock_callback.assert_called_once_with("created", "/tmp/test-vault/test-note.md")

    def test_multiple_files_processed_independently(self, handler, mock_callback):
        """Test that multiple files are processed independently."""
        event1 = FileCreatedEvent("/tmp/test-vault/note1.md")
        event2 = FileModifiedEvent("/tmp/test-vault/note2.md")
        
        handler.on_created(event1)
        handler.on_modified(event2)
        
        # Should have two pending events
        assert len(handler.pending_events) == 2
        assert "/tmp/test-vault/note1.md" in handler.pending_events
        assert "/tmp/test-vault/note2.md" in handler.pending_events

    def test_event_cleanup_after_processing(self, handler, mock_callback):
        """Test that events are cleaned up after processing."""
        event = FileCreatedEvent("/tmp/test-vault/test-note.md")
        
        handler.on_created(event)
        
        # Wait for debounce period
        time.sleep(1.1)
        
        # Should have no pending events after processing
        assert len(handler.pending_events) == 0


class TestFileWatcherService:
    """Test cases for FileWatcherService."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock(spec=Config)
        config.obsidian_vault_path = "/tmp/test-vault"
        config.file_watcher_debounce_seconds = 1
        config.file_watcher_max_note_size_mb = 10
        config.file_watcher_batch_size = 50
        return config

    @pytest.fixture
    def mock_obsidian_graph_rag(self):
        """Mock ObsidianGraphRAG instance for testing."""
        return Mock()

    @pytest.fixture
    def file_watcher_service(self, mock_entity_detection_service, mock_knowledge_graph_service):
        """Create a FileWatcherService instance for testing."""
        return FileWatcherService(
            vault_path="/test/vault",
            entity_detection_service=mock_entity_detection_service,
            knowledge_graph_service=mock_knowledge_graph_service
        )

    @pytest.fixture
    def file_handler(self, mock_callback):
        """Create an ObsidianFileHandler instance for testing."""
        return ObsidianFileHandler(
            vault_path=Path("/test/vault"),
            callback=mock_callback
        )

    def test_service_initialization(self, mock_config, mock_obsidian_graph_rag):
        """Test that the service initializes correctly."""
        service = FileWatcherService(
            vault_path="/test/vault",
            entity_detection_service=Mock(),
            knowledge_graph_service=Mock()
        )
        
        assert service.vault_path == Path("/test/vault")
        assert service.is_watching is False

    def test_start_watching_success(self, file_watcher_service, mock_config):
        """Test that file watching starts successfully."""
        with patch('watchdog.observers.Observer') as mock_observer_class:
            mock_observer = Mock()
            mock_observer_class.return_value = mock_observer
            
            result = file_watcher_service.start_watching()
            
            assert result is True
            assert file_watcher_service.is_watching is True
            mock_observer.start.assert_called_once()

    def test_start_watching_already_running(self, service):
        """Test that starting when already watching doesn't cause issues."""
        service.observer = Mock()
        service.handler = Mock()
        
        service.start_watching()
        
        # Should not create new observer/handler
        assert service.observer is not None

    def test_stop_watching_success(self, service):
        """Test that file watching stops successfully."""
        mock_observer = Mock()
        service.observer = mock_observer
        service.handler = Mock()
        
        service.stop_watching()
        
        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once()
        assert service.observer is None
        assert service.handler is None

    def test_stop_watching_not_running(self, service):
        """Test that stopping when not watching doesn't cause issues."""
        service.observer = None
        service.handler = None
        
        service.stop_watching()
        
        # Should not raise any errors

    def test_handle_file_event_created(self, service, mock_obsidian_graph_rag):
        """Test that file creation events are handled correctly."""
        service.handle_file_event("created", "/tmp/test-vault/test-note.md")
        
        # Should call the graph RAG service to process the new note
        mock_obsidian_graph_rag.process_note.assert_called_once_with("/tmp/test-vault/test-note.md")

    def test_handle_file_event_modified(self, service, mock_obsidian_graph_rag):
        """Test that file modification events are handled correctly."""
        service.handle_file_event("modified", "/tmp/test-vault/test-note.md")
        
        # Should call the graph RAG service to process the modified note
        mock_obsidian_graph_rag.process_note.assert_called_once_with("/tmp/test-vault/test-note.md")

    def test_handle_file_event_deleted(self, service, mock_obsidian_graph_rag):
        """Test that file deletion events are handled correctly."""
        service.handle_file_event("deleted", "/tmp/test-vault/test-note.md")
        
        # Should call the graph RAG service to remove the deleted note
        mock_obsidian_graph_rag.remove_note.assert_called_once_with("/tmp/test-vault/test-note.md")

    def test_handle_file_event_moved(self, service, mock_obsidian_graph_rag):
        """Test that file movement events are handled correctly."""
        service.handle_file_event("moved", "/tmp/test-vault/old-name.md", "/tmp/test-vault/new-name.md")
        
        # Should call the graph RAG service to handle the move
        mock_obsidian_graph_rag.move_note.assert_called_once_with(
            "/tmp/test-vault/old-name.md", "/tmp/test-vault/new-name.md"
        )

    def test_handle_file_event_unknown_type(self, service, mock_obsidian_graph_rag):
        """Test that unknown event types are handled gracefully."""
        service.handle_file_event("unknown", "/tmp/test-vault/test-note.md")
        
        # Should not call any graph RAG methods
        mock_obsidian_graph_rag.process_note.assert_not_called()
        mock_obsidian_graph_rag.remove_note.assert_not_called()
        mock_obsidian_graph_rag.move_note.assert_not_called()

    def test_handle_file_event_with_errors(self, service, mock_obsidian_graph_rag):
        """Test that file event handling errors are handled gracefully."""
        mock_obsidian_graph_rag.process_note.side_effect = Exception("Processing error")
        
        # Should not raise the exception
        service.handle_file_event("created", "/tmp/test-vault/test-note.md")
        
        # Should still have called the method
        mock_obsidian_graph_rag.process_note.assert_called_once()

    def test_is_markdown_file(self, service):
        """Test that markdown file detection works correctly."""
        assert service._is_markdown_file("/tmp/test-vault/test.md") is True
        assert service._is_markdown_file("/tmp/test-vault/test.MD") is True
        assert service._is_markdown_file("/tmp/test-vault/test.txt") is False
        assert service._is_markdown_file("/tmp/test-vault/test") is False

    def test_is_meta_folder_file(self, service):
        """Test that Meta folder file detection works correctly."""
        assert service._is_meta_folder_file("/tmp/test-vault/⭕Meta/template.md") is True
        assert service._is_meta_folder_file("/tmp/test-vault/⭕Meta/subfolder/note.md") is True
        assert service._is_meta_folder_file("/tmp/test-vault/notes/template.md") is False
        assert service._is_meta_folder_file("/tmp/test-vault/test.md") is False

    def test_context_manager_usage(self, service):
        """Test that FileWatcherService can be used as a context manager."""
        with patch('graphrag.services.file_watcher.Observer') as mock_observer_class, \
             patch('graphrag.services.file_watcher.ObsidianFileHandler') as mock_handler_class:
            
            mock_observer = Mock()
            mock_observer_class.return_value = mock_observer
            mock_handler = Mock()
            mock_handler_class.return_value = mock_handler
            
            with service:
                assert service.observer == mock_observer
                assert service.handler == mock_handler
            
            # Should stop watching when exiting context
            mock_observer.stop.assert_called_once()
            mock_observer.join.assert_called_once()

    def test_file_size_validation(self, service):
        """Test that file size validation works correctly."""
        # Mock a large file
        with patch('os.path.getsize', return_value=15 * 1024 * 1024):  # 15MB
            assert service._is_file_size_valid("/tmp/test-vault/large-note.md") is False
        
        # Mock a normal file
        with patch('os.path.getsize', return_value=1024):  # 1KB
            assert service._is_file_size_valid("/tmp/test-vault/normal-note.md") is True

    def test_recursive_directory_watching(self, service, mock_config):
        """Test that recursive directory watching is enabled."""
        with patch('graphrag.services.file_watcher.Observer') as mock_observer_class, \
             patch('graphrag.services.file_watcher.ObsidianFileHandler') as mock_handler_class:
            
            mock_observer = Mock()
            mock_observer_class.return_value = mock_observer
            mock_handler = Mock()
            mock_handler_class.return_value = mock_handler
            
            service.start_watching()
            
            # Should schedule with recursive=True
            mock_observer.schedule.assert_called_once_with(
                mock_handler, mock_config.obsidian_vault_path, recursive=True
            )

    def test_multiple_event_types_same_file(self, service, mock_obsidian_graph_rag):
        """Test that multiple event types for the same file are handled correctly."""
        # Create event
        service.handle_file_event("created", "/tmp/test-vault/test-note.md")
        mock_obsidian_graph_rag.process_note.assert_called_once_with("/tmp/test-vault/test-note.md")
        
        # Modify event
        mock_obsidian_graph_rag.process_note.reset_mock()
        service.handle_file_event("modified", "/tmp/test-vault/test-note.md")
        mock_obsidian_graph_rag.process_note.assert_called_once_with("/tmp/test-vault/test-note.md")
        
        # Delete event
        mock_obsidian_graph_rag.remove_note.reset_mock()
        service.handle_file_event("deleted", "/tmp/test-note.md")
        mock_obsidian_graph_rag.remove_note.assert_called_once_with("/tmp/test-note.md") 