"""
Obsidian note indexing and processing for the knowledge graph.
"""

import os
import logging
import hashlib
import chardet
import re
from pathlib import Path
from typing import Any, Optional
from tqdm import tqdm
import frontmatter
from .core import KnowledgeGraph

logger = logging.getLogger(__name__)


class ObsidianIndexer:
    """Handles indexing of Obsidian vaults into the knowledge graph."""

    # Obsidian file extensions
    OBSIDIAN_EXTENSIONS = {'.md', '.markdown'}

    # Directories to skip in Obsidian vaults
    SKIP_DIRS = {
        '.obsidian', '.trash', '.git', '.svn', '.hg', '__pycache__',
        'node_modules', '.venv', 'venv', 'env', '.env', 'build',
        'dist', 'target', 'bin', 'obj', '.idea', '.vscode',
        'coverage', '.pytest_cache', '.mypy_cache', '.tox', '.eggs'
    }

    def __init__(self, knowledge_graph: KnowledgeGraph):
        """
        Initialize the Obsidian indexer.

        Args:
            knowledge_graph: The knowledge graph instance to use
        """
        self.kg = knowledge_graph

    def should_skip_directory(self, dir_name: str) -> bool:
        """Check if directory should be skipped."""
        return any(skip_pattern in dir_name for skip_pattern in self.SKIP_DIRS)

    def should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed as an Obsidian note."""
        # Skip hidden files
        if file_path.name.startswith('.'):
            return False

        # Check if it's a markdown file
        return file_path.suffix.lower() in self.OBSIDIAN_EXTENSIONS

    def get_note_content(self, file_path: Path) -> Optional[dict[str, Any]]:
        """Extract content and metadata from an Obsidian note."""
        try:
            # Detect encoding
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                if not raw_data:
                    return None

                # Try to detect encoding
                detected = chardet.detect(raw_data)
                encoding = detected['encoding'] if detected['encoding'] else 'utf-8'

                # Decode content
                content = raw_data.decode(encoding, errors='ignore')

                # Parse frontmatter
                post = frontmatter.loads(content)
                frontmatter_data = dict(post.metadata) if post.metadata else {}
                body_content = post.content

                return {
                    'content': body_content,
                    'frontmatter': frontmatter_data,
                    'encoding': encoding
                }
        except Exception as e:
            logger.warning(f"Could not read note {file_path}: {e}")
            return None

    def calculate_note_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of note content."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except:
            return ""

    def get_note_stats(self, file_path: Path) -> dict[str, Any]:
        """Get note statistics."""
        try:
            stat = file_path.stat()
            return {
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'accessed': stat.st_atime,
                'is_readonly': not os.access(file_path, os.W_OK)
            }
        except:
            return {}

    def extract_internal_links(self, content: str) -> list[str]:
        """Extract internal Obsidian links from note content."""
        # Match [[link]] and [[link|display]] patterns
        link_pattern = r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'
        matches = re.findall(link_pattern, content)

        links = []
        for match in matches:
            link_text = match[0].strip()
            if link_text:
                links.append(link_text)

        return links

    def extract_tags(self, content: str, frontmatter: dict[str, Any]) -> list[str]:
        """Extract tags from both frontmatter and content."""
        tags = set()

        # Extract tags from frontmatter
        if 'tags' in frontmatter:
            frontmatter_tags = frontmatter['tags']
            if isinstance(frontmatter_tags, list):
                tags.update(frontmatter_tags)
            elif isinstance(frontmatter_tags, str):
                tags.add(frontmatter_tags)

        # Extract tags from content (#tag pattern)
        tag_pattern = r'#([a-zA-Z0-9_-]+)'
        content_tags = re.findall(tag_pattern, content)
        tags.update(content_tags)

        return list(tags)

    def extract_headers(self, content: str) -> list[dict[str, Any]]:
        """Extract headers from markdown content."""
        headers = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Match markdown headers (# ## ### etc.)
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                headers.append({
                    'level': level,
                    'title': title,
                    'line_number': line_num
                })

        return headers

    def extract_external_links(self, content: str) -> list[dict[str, str]]:
        """Extract external links from note content."""
        # Match [text](url) pattern
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(link_pattern, content)

        links = []
        for match in matches:
            text, url = match
            links.append({
                'text': text.strip(),
                'url': url.strip()
            })

        return links

    def create_folder_nodes(self, folder_path: Path) -> str:
        """Create folder nodes in the graph."""
        with self.kg.get_session() as session:
            # Create folder hierarchy
            parts = folder_path.parts
            current_path = Path(parts[0])

            for i, part in enumerate(parts[1:], 1):
                current_path = current_path / part

                # Create folder node
                session.run("""
                    MERGE (f:Folder {path: $path, name: $name})
                    set f.full_path = $full_path
                """, path=str(current_path), name=part, full_path=str(current_path))

                # Create CONTAINS relationship with parent
                if i > 1:
                    parent_path = str(current_path.parent)
                    session.run("""
                        MATCH (parent:Folder {path: $parent_path})
                        MATCH (child:Folder {path: $child_path})
                        MERGE (parent)-[:CONTAINS]->(child)
                    """, parent_path=parent_path, child_path=str(current_path))

            return str(folder_path)

    def create_note_node(self, note_path: Path, content_data: dict[str, Any], stats: dict[str, Any]) -> str:
        """Create a note node in the graph."""
        with self.kg.get_session() as session:
            note_hash = self.calculate_note_hash(note_path)
            frontmatter_data = content_data.get('frontmatter', {})
            body_content = content_data.get('content', '')

            # Extract metadata
            title = frontmatter_data.get('title', note_path.stem)
            aliases = frontmatter_data.get('aliases', [])
            if isinstance(aliases, str):
                aliases = [aliases]

            # Create note node
            session.run("""
                MERGE (n:Note {path: $path})
                set n.name = $name,
                    n.title = $title,
                    n.content = $content,
                    n.hash = $hash,
                    n.size = $size,
                    n.created = $created,
                    n.modified = $modified,
                    n.accessed = $accessed,
                    n.is_readonly = $is_readonly,
                    n.aliases = $aliases,
                    n.frontmatter = $frontmatter
            """,
                        path=str(note_path),
                        name=note_path.name,
                        title=title,
                        content=body_content,
                        hash=note_hash,
                        size=stats.get('size', 0),
                        created=stats.get('created', 0),
                        modified=stats.get('modified', 0),
                        accessed=stats.get('accessed', 0),
                        is_readonly=stats.get('is_readonly', False),
                        aliases=aliases,
                        frontmatter=str(frontmatter_data)
                        )

            return str(note_path)

    def create_note_relationships(self, note_path: Path, content_data: dict[str, Any]):
        """Create relationships for a note."""
        with self.kg.get_session() as session:
            # Connect note to its folder
            folder_path = str(note_path.parent)
            session.run("""
                MATCH (f:Folder {path: $folder_path})
                MATCH (n:Note {path: $note_path})
                MERGE (f)-[:CONTAINS]->(n)
            """, folder_path=folder_path, note_path=str(note_path))

            # Create relationships based on note content
            self._create_content_relationships(
                note_path, content_data, session)

    def _create_content_relationships(self, note_path: Path, content_data: dict[str, Any], session):
        """Create relationships based on note content analysis."""
        body_content = content_data.get('content', '')
        frontmatter_data = content_data.get('frontmatter', {})

        # Extract internal links
        internal_links = self.extract_internal_links(body_content)
        for link in internal_links:
            # Create InternalLink node
            session.run("""
                MERGE (l:InternalLink {name: $link_name})
            """, link_name=link)

            # Create LINKS_TO relationship
            session.run("""
                MATCH (n:Note {path: $note_path})
                MATCH (l:InternalLink {name: $link_name})
                MERGE (n)-[:LINKS_TO]->(l)
            """, note_path=str(note_path), link_name=link)

        # Extract and create tags
        tags = self.extract_tags(body_content, frontmatter_data)
        for tag in tags:
            # Create Tag node
            session.run("""
                MERGE (t:Tag {name: $tag_name})
            """, tag_name=tag)

            # Create TAGGED_WITH relationship
            session.run("""
                MATCH (n:Note {path: $note_path})
                MATCH (t:Tag {name: $tag_name})
                MERGE (n)-[:TAGGED_WITH]->(t)
            """, note_path=str(note_path), tag_name=tag)

        # Extract and create headers
        headers = self.extract_headers(body_content)
        for header in headers:
            # Create Header node
            session.run("""
                MERGE (h:Header {title: $title, level: $level})
            """, title=header['title'], level=header['level'])

            # Create HAS_HEADER relationship
            session.run("""
                MATCH (n:Note {path: $note_path})
                MATCH (h:Header {title: $title, level: $level})
                MERGE (n)-[:HAS_HEADER]->(h)
            """, note_path=str(note_path), title=header['title'], level=header['level'])

        # Extract and create external links
        external_links = self.extract_external_links(body_content)
        for link in external_links:
            # Create ExternalLink node
            session.run("""
                MERGE (e:ExternalLink {url: $url, text: $text})
            """, url=link['url'], text=link['text'])

            # Create LINKS_TO_EXTERNAL relationship
            session.run("""
                MATCH (n:Note {path: $note_path})
                MATCH (e:ExternalLink {url: $url, text: $text})
                MERGE (n)-[:LINKS_TO_EXTERNAL]->(e)
            """, note_path=str(note_path), url=link['url'], text=link['text'])

    def index_vault(self, vault_path: str, recursive: bool = True) -> dict[str, Any]:
        """
        Index an Obsidian vault into the knowledge graph.

        Args:
            vault_path: Path to the Obsidian vault to index
            recursive: Whether to index subdirectories recursively

        Returns:
            dictionary with indexing statistics
        """
        path = Path(vault_path)
        if not path.exists() or not path.is_dir():
            raise ValueError(f"Vault does not exist: {vault_path}")

        stats = {
            'folders_processed': 0,
            'notes_processed': 0,
            'notes_skipped': 0,
            'errors': 0,
            'total_links': 0,
            'total_tags': 0,
            'total_headers': 0
        }

        logger.info(f"Starting to index Obsidian vault: {vault_path}")

        # Create root folder node
        self.create_folder_nodes(path)
        stats['folders_processed'] += 1

        # Walk through vault
        for root, dirs, files in os.walk(vault_path):
            root_path = Path(root)

            # Filter directories to skip
            dirs[:] = [d for d in dirs if not self.should_skip_directory(d)]

            # Create folder nodes
            for dir_name in dirs:
                dir_path = root_path / dir_name
                self.create_folder_nodes(dir_path)
                stats['folders_processed'] += 1

            # Process notes
            for file_name in tqdm(files, desc=f"Processing {root}", leave=False):
                file_path = root_path / file_name

                if not self.should_process_file(file_path):
                    stats['notes_skipped'] += 1
                    continue

                try:
                    content_data = self.get_note_content(file_path)
                    if content_data is None:
                        stats['notes_skipped'] += 1
                        continue

                    note_stats = self.get_note_stats(file_path)
                    self.create_note_node(file_path, content_data, note_stats)
                    self.create_note_relationships(file_path, content_data)
                    stats['notes_processed'] += 1

                    # Count relationships
                    body_content = content_data.get('content', '')
                    frontmatter_data = content_data.get('frontmatter', {})

                    stats['total_links'] += len(
                        self.extract_internal_links(body_content))
                    stats['total_tags'] += len(
                        self.extract_tags(body_content, frontmatter_data))
                    stats['total_headers'] += len(
                        self.extract_headers(body_content))

                except Exception as e:
                    logger.error(f"Error processing note {file_path}: {e}")
                    stats['errors'] += 1

        logger.info(f"Indexing completed. Stats: {stats}")
        return stats
