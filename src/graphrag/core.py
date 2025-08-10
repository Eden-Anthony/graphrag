"""Core module for the Obsidian GraphRAG system."""

from typing import Set
from datetime import datetime
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.table import Table

from .config import Config
from .models import Note, QueryResult
from .services import EntityDetectionService, KnowledgeGraphService, QueryService
from .services.file_watcher import FileWatcherService

logger = logging.getLogger(__name__)
console = Console()


class ObsidianGraphRAG:
    """Main class for the Obsidian GraphRAG system."""

    def __init__(self, vault_path: Optional[str] = None):
        """Initialize the Obsidian GraphRAG system."""
        # Validate configuration
        Config.validate()

        # Set vault path
        self.vault_path = vault_path or Config.OBSIDIAN_VAULT_PATH

        # Initialize services
        self.entity_detection_service = EntityDetectionService()
        self.kg_service = KnowledgeGraphService()
        self.query_service = QueryService(self.kg_service)
        self.file_watcher = FileWatcherService(
            self.vault_path,
            self.entity_detection_service,
            self.kg_service
        )

        logger.info("Obsidian GraphRAG system initialized successfully")

    def build_initial_knowledge_graph(self, force_rebuild: bool = False) -> Dict:
        """Build the initial knowledge graph from all notes in the vault."""
        console.print(
            "[bold blue]Building initial knowledge graph...[/bold blue]")

        try:
            # Get all markdown files in the vault
            markdown_files = self._get_all_markdown_files()

            if not markdown_files:
                console.print(
                    "[yellow]No markdown files found in the vault[/yellow]")
                return {"status": "no_files", "files_processed": 0}

            console.print(f"Found {len(markdown_files)} markdown files")

            # Process files in batches
            processed_count = 0
            total_files = len(markdown_files)

            for i, file_path in enumerate(markdown_files, 1):
                try:
                    console.print(
                        f"Processing {i}/{total_files}: {file_path.name}")

                    # Read and process the note
                    note = self._read_note_file(file_path)
                    if note:
                        # Detect entities
                        detection_result = self.entity_detection_service.detect_entities(
                            note)

                        # Add to knowledge graph
                        self._add_note_to_knowledge_graph(
                            note, detection_result)

                        processed_count += 1

                        # Show progress
                        if i % 10 == 0:
                            console.print(
                                f"Progress: {i}/{total_files} files processed")

                except Exception as e:
                    console.print(
                        f"[red]Error processing {file_path}: {e}[/red]")
                    logger.error(f"Error processing {file_path}: {e}")

            # Get final statistics
            stats = self.kg_service.get_graph_stats()

            console.print(
                f"[bold green]Knowledge graph built successfully![/bold green]")
            console.print(f"Processed {processed_count} files")
            console.print(f"Graph statistics: {stats}")

            return {
                "status": "success",
                "files_processed": processed_count,
                "total_files": total_files,
                "graph_stats": stats
            }

        except Exception as e:
            console.print(f"[red]Failed to build knowledge graph: {e}[/red]")
            logger.error(f"Failed to build knowledge graph: {e}")
            raise

    def start_file_watcher(self):
        """Start watching the Obsidian vault for changes."""
        console.print("[bold blue]Starting file watcher...[/bold blue]")

        try:
            self.file_watcher.start_watching()
            console.print(
                "[bold green]File watcher started successfully[/bold green]")
            console.print(f"Watching vault: {self.vault_path}")

        except Exception as e:
            console.print(f"[red]Failed to start file watcher: {e}[/red]")
            logger.error(f"Failed to start file watcher: {e}")
            raise

    def stop_file_watcher(self):
        """Stop watching the Obsidian vault for changes."""
        console.print("[bold blue]Stopping file watcher...[/bold blue]")

        try:
            self.file_watcher.stop_watching()
            console.print(
                "[bold green]File watcher stopped successfully[/bold green]")

        except Exception as e:
            console.print(f"[red]Error stopping file watcher: {e}[/red]")
            logger.error(f"Error stopping file watcher: {e}")

    def query(self, question: str, context_size: int = None) -> QueryResult:
        """Query the knowledge graph with a question."""
        console.print(f"[bold blue]Query:[/bold blue] {question}")

        try:
            result = self.query_service.query(question, context_size)

            # Display the result
            self._display_query_result(result)

            return result

        except Exception as e:
            console.print(f"[red]Query failed: {e}[/red]")
            logger.error(f"Query failed: {e}")
            raise

    def chat_mode(self):
        """Start an interactive chat mode."""
        console.print("[bold blue]Starting chat mode...[/bold blue]")
        console.print("Type 'quit' or 'exit' to end the chat")
        console.print("Type 'stats' to see graph statistics")
        console.print("Type 'help' for available commands")
        console.print()

        conversation_history = []

        while True:
            try:
                # Get user input
                user_input = console.input(
                    "[bold green]You:[/bold green] ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    console.print("[bold blue]Ending chat mode[/bold blue]")
                    break

                if user_input.lower() == 'stats':
                    self._show_graph_stats()
                    continue

                if user_input.lower() == 'help':
                    self._show_help()
                    continue

                if not user_input:
                    continue

                # Process the query
                result = self.query_service.chat_query(
                    user_input, conversation_history)

                # Add to conversation history
                conversation_history.append({
                    "user": user_input,
                    "assistant": result.answer,
                    "timestamp": result.query_time
                })

                # Keep only last 10 exchanges
                if len(conversation_history) > 20:
                    conversation_history = conversation_history[-10:]

            except KeyboardInterrupt:
                console.print("\n[bold blue]Chat interrupted[/bold blue]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                logger.error(f"Chat error: {e}")

    def get_similar_entities(self, entity_name: str, limit: int = 5) -> List[Dict]:
        """Find entities similar to the given entity."""
        console.print(
            f"[bold blue]Finding entities similar to:[/bold blue] {entity_name}")

        try:
            similar_entities = self.query_service.get_similar_entities(
                entity_name, limit)

            if similar_entities:
                self._display_similar_entities(similar_entities)
            else:
                console.print("[yellow]No similar entities found[/yellow]")

            return similar_entities

        except Exception as e:
            console.print(f"[red]Failed to find similar entities: {e}[/red]")
            logger.error(f"Failed to find similar entities: {e}")
            return []

    def get_topic_summary(self, topic: str, limit: int = 10) -> str:
        """Get a summary of information about a specific topic."""
        console.print(
            f"[bold blue]Generating summary for topic:[/bold blue] {topic}")

        try:
            summary = self.query_service.get_topic_summary(topic, limit)

            console.print(f"[bold green]Summary:[/bold green]")
            console.print(summary)

            return summary

        except Exception as e:
            console.print(f"[red]Failed to generate topic summary: {e}[/red]")
            logger.error(f"Failed to generate topic summary: {e}")
            return f"Failed to generate summary: {str(e)}"

    def _get_all_markdown_files(self) -> List[Path]:
        """Get all markdown files in the vault."""
        markdown_files = []
        vault_path = Path(self.vault_path)

        for file_path in vault_path.rglob("*.md"):
            # Check if file should be ignored
            if not self._should_ignore_file(file_path):
                markdown_files.append(file_path)

        return sorted(markdown_files)

    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if a file should be ignored."""
        for pattern in Config.IGNORE_PATTERNS:
            if pattern in str(file_path):
                return True
        return False

    def _read_note_file(self, file_path: Path) -> Optional[Note]:
        """Read and parse a note file."""
        try:
            # Check file size
            if file_path.stat().st_size > Config.MAX_NOTE_SIZE:
                console.print(
                    f"[yellow]File too large, skipping: {file_path}[/yellow]")
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

            # Extract links
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
            console.print(f"[red]Error reading file {file_path}: {e}[/red]")
            logger.error(f"Error reading file {file_path}: {e}")
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
                console.print(
                    f"[yellow]Failed to parse frontmatter: {e}[/yellow]")

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

    def _add_note_to_knowledge_graph(self, note: Note, detection_result):
        """Add a note and its entities to the knowledge graph."""
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

        except Exception as e:
            console.print(
                f"[red]Error adding note to knowledge graph: {e}[/red]")
            logger.error(f"Error adding note to knowledge graph: {e}")
            raise

    def _display_query_result(self, result: QueryResult):
        """Display a query result in a formatted way."""
        console.print(f"\n[bold green]Answer:[/bold green]")
        console.print(result.answer)

        if result.citations:
            console.print(f"\n[bold blue]Citations:[/bold blue]")
            for citation in result.citations:
                console.print(f"• {citation}")

        console.print(f"\n[dim]Confidence: {result.confidence:.2f}[/dim]")
        console.print(f"[dim]Query time: {result.query_time}[/dim]")

    def _display_similar_entities(self, similar_entities: List[Dict]):
        """Display similar entities in a formatted table."""
        table = Table(title="Similar Entities")
        table.add_column("Entity Name", style="cyan")
        table.add_column("Source Note", style="green")
        table.add_column("Note Path", style="dim")

        for entity in similar_entities:
            table.add_row(
                entity["entity_name"],
                entity["source_note"],
                entity["note_path"]
            )

        console.print(table)

    def _show_graph_stats(self):
        """Show knowledge graph statistics."""
        try:
            stats = self.kg_service.get_graph_stats()

            table = Table(title="Knowledge Graph Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", style="green")

            for metric, count in stats.items():
                table.add_row(metric.replace('_', ' ').title(), str(count))

            console.print(table)

        except Exception as e:
            console.print(f"[red]Failed to get graph statistics: {e}[/red]")

    def _show_help(self):
        """Show available commands."""
        help_text = """
Available Commands:
• Type your question to query the knowledge graph
• 'stats' - Show knowledge graph statistics
• 'help' - Show this help message
• 'quit', 'exit', or 'q' - End the chat
        """
        console.print(help_text)

    def close(self):
        """Clean up resources."""
        try:
            self.stop_file_watcher()
            self.kg_service.close()
            console.print(
                "[bold green]GraphRAG system closed successfully[/bold green]")
        except Exception as e:
            console.print(f"[red]Error closing system: {e}[/red]")
            logger.error(f"Error closing system: {e}")


# Import statements at the top to avoid circular imports
