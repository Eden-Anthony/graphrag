"""File watcher service for monitoring Obsidian vault changes."""

from datetime import datetime
import logging
import os
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from ..config import Config
from ..models import Note
from .entity_detection import EntityDetectionService
from .knowledge_graph import KnowledgeGraphService

logger = logging.getLogger(__name__)


class ObsidianFileHandler(FileSystemEventHandler):
    """Handler for Obsidian file system events."""

    def __init__(self, vault_path: Path, callback: Callable[[Note, str], None]):
        """Initialize the file handler."""
        self.vault_path = vault_path
        self.callback = callback
        self.ignored_patterns = Config.IGNORE_PATTERNS
        self.processing_files: Set[str] = set()

    def should_ignore(self, file_path: Path) -> bool:
        """Check if a file should be ignored."""
        for pattern in self.ignored_patterns:
            if pattern in str(file_path):
                return True
        return False

    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if not event.is_directory and event.src_path.endswith('.md'):
            self._process_file_change(event.src_path, "created")

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if not event.is_directory and event.src_path.endswith('.md'):
            self._process_file_change(event.src_path, "modified")

    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events."""
        if not event.is_directory and event.src_path.endswith('.md'):
            self._process_file_change(event.src_path, "deleted")

    def on_moved(self, event: FileSystemEvent):
        """Handle file move/rename events."""
        if not event.is_directory and event.src_path.endswith('.md'):
            self._process_file_change(event.src_path, "moved")

    def _process_file_change(self, file_path: str, event_type: str):
        """Process a file change event."""
        try:
            file_path_obj = Path(file_path)

            # Check if file should be ignored
            if self.should_ignore(file_path_obj):
                logger.debug(f"Ignoring {event_type} event for {file_path}")
                return

            # Prevent duplicate processing
            if file_path in self.processing_files:
                logger.debug(f"Already processing {file_path}, skipping")
                return

            self.processing_files.add(file_path)

            # Process the file change
            self.callback(file_path_obj, event_type)

        except Exception as e:
            logger.error(
                f"Error processing {event_type} event for {file_path}: {e}")
        finally:
            self.processing_files.discard(file_path)


class FileWatcherService:
    """Service for watching Obsidian vault files for changes."""

    def __init__(self,
                 vault_path: str,
                 entity_detection_service: EntityDetectionService,
                 knowledge_graph_service: KnowledgeGraphService):
        """Initialize the file watcher service."""
        self.vault_path = Path(vault_path)
        self.entity_detection_service = entity_detection_service
        self.kg_service = knowledge_graph_service
        self.observer = Observer()
        self.handler = None
        self.is_watching = False

        # Track file modification times to avoid duplicate processing
        self.last_modified: Dict[str, float] = {}

        # Debounce timer for file changes
        self.debounce_timer = None
        self.debounce_delay = 2.0  # seconds

    def start_watching(self):
        """Start watching the Obsidian vault for changes."""
        if self.is_watching:
            logger.warning("File watcher is already running")
            return

        try:
            # Create the file handler
            self.handler = ObsidianFileHandler(
                self.vault_path,
                self._handle_file_change
            )

            # Schedule the observer
            self.observer.schedule(
                self.handler,
                str(self.vault_path),
                recursive=True
            )

            # Start the observer
            self.observer.start()
            self.is_watching = True

            logger.info(f"Started watching Obsidian vault: {self.vault_path}")

        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")
            raise

    def stop_watching(self):
        """Stop watching the Obsidian vault."""
        if not self.is_watching:
            return

        try:
            self.observer.stop()
            self.observer.join()
            self.is_watching = False
            logger.info("Stopped watching Obsidian vault")

        except Exception as e:
            logger.error(f"Error stopping file watcher: {e}")

    def _handle_file_change(self, file_path: Path, event_type: str):
        """Handle a file change event."""
        try:
            # Debounce rapid file changes
            current_time = time.time()
            file_key = str(file_path)

            if file_key in self.last_modified:
                time_since_last = current_time - self.last_modified[file_key]
                if time_since_last < self.debounce_delay:
                    logger.debug(
                        f"Debouncing {event_type} event for {file_path}")
                    return

            self.last_modified[file_key] = current_time

            # Process the file change based on event type
            if event_type == "created" or event_type == "modified":
                self._process_note_update(file_path)
            elif event_type == "deleted":
                self._process_note_deletion(file_path)
            elif event_type == "moved":
                # Handle as both deletion and creation
                self._process_note_deletion(file_path)
                # Note: The new location will trigger a "created" event

        except Exception as e:
            logger.error(
                f"Error handling file change {event_type} for {file_path}: {e}")

    def _process_note_update(self, file_path: Path):
        """Process a note update (create or modify)."""
        try:
            logger.info(f"Processing note update: {file_path}")

            # Read the note file
            note = self._read_note_file(file_path)
            if not note:
                return

            # Detect entities in the note
            detection_result = self.entity_detection_service.detect_entities(
                note)

            # Update the knowledge graph
            self._update_knowledge_graph(note, detection_result)

            logger.info(f"Successfully processed note update: {file_path}")

        except Exception as e:
            logger.error(f"Error processing note update for {file_path}: {e}")

    def _process_note_deletion(self, file_path: Path):
        """Process a note deletion."""
        try:
            logger.info(f"Processing note deletion: {file_path}")

            # Remove the note from the knowledge graph
            self.kg_service.delete_note(str(file_path))

            # Clean up tracking
            file_key = str(file_path)
            if file_key in self.last_modified:
                del self.last_modified[file_key]

            logger.info(f"Successfully processed note deletion: {file_path}")

        except Exception as e:
            logger.error(
                f"Error processing note deletion for {file_path}: {e}")

    def _read_note_file(self, file_path: Path) -> Optional[Note]:
        """Read and parse an Obsidian note file."""
        try:
            # Check file size
            if file_path.stat().st_size > Config.MAX_NOTE_SIZE:
                logger.warning(f"Note file too large, skipping: {file_path}")
                return None

            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse frontmatter and content
            frontmatter, note_content = self._parse_frontmatter(content)

            # Extract title from filename or frontmatter
            title = frontmatter.get('title', file_path.stem)

            # Extract tags
            tags = set(frontmatter.get('tags', []))

            # Extract links (basic Obsidian link detection)
            links = self._extract_links(note_content)

            # Create Note object
            note = Note(
                file_path=str(file_path),
                title=title,
                content=note_content,
                frontmatter=frontmatter,
                tags=tags,
                links=links,
                last_modified=datetime.fromtimestamp(file_path.stat().st_mtime)
            )

            return note

        except Exception as e:
            logger.error(f"Error reading note file {file_path}: {e}")
            return None

    def _parse_frontmatter(self, content: str) -> tuple[Dict, str]:
        """Parse YAML frontmatter from note content."""
        import yaml

        frontmatter = {}
        note_content = content

        # Check if content starts with frontmatter
        if content.startswith('---'):
            try:
                # Find frontmatter boundaries
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1].strip()
                    note_content = parts[2].strip()

                    # Parse YAML frontmatter
                    if frontmatter_text:
                        frontmatter = yaml.safe_load(frontmatter_text) or {}

            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse frontmatter: {e}")

        return frontmatter, note_content

    def _extract_links(self, content: str) -> Set[str]:
        """Extract Obsidian links from note content."""
        import re

        links = set()

        # Extract [[internal links]]
        internal_links = re.findall(r'\[\[([^\]]+)\]\]', content)
        links.update(internal_links)

        # Extract [external links](url)
        external_links = re.findall(r'\[([^\]]+)\]\([^)]+\)', content)
        links.update(external_links)

        return links

    def _update_knowledge_graph(self, note: Note, detection_result):
        """Update the knowledge graph with the note and its entities."""
        try:
            # Create or update the note node
            self.kg_service.create_note_node(note)

            # Create entity nodes
            entity_names = []
            for entity in detection_result.entities:
                self.kg_service.create_entity_node(entity)
                entity_names.append(entity.name)

            # Link note to entities
            if entity_names:
                self.kg_service.link_note_to_entities(
                    note.file_path, entity_names)

            # Create relationships between entities
            for relationship in detection_result.relationships:
                # Find entity names by ID
                source_entity = next(
                    (e for e in detection_result.entities if e.id == relationship.source_entity_id), None)
                target_entity = next(
                    (e for e in detection_result.entities if e.id == relationship.target_entity_id), None)

                if source_entity and target_entity:
                    self.kg_service.create_relationship(
                        relationship,
                        source_entity.name,
                        target_entity.name
                    )

            # Update embeddings
            self.kg_service.update_note_embeddings(note)

            logger.info(
                f"Successfully updated knowledge graph for note: {note.file_path}")

        except Exception as e:
            logger.error(
                f"Error updating knowledge graph for note {note.file_path}: {e}")

    def get_status(self) -> Dict:
        """Get the current status of the file watcher."""
        return {
            "is_watching": self.is_watching,
            "vault_path": str(self.vault_path),
            "files_tracked": len(self.last_modified),
            "observer_status": "running" if self.observer.is_alive() else "stopped"
        }


# Import datetime at the top to avoid circular imports
