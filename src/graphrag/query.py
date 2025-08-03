"""
Query engine for the Obsidian knowledge graph.
"""

import logging
from typing import Any, Optional
from .core import KnowledgeGraph

logger = logging.getLogger(__name__)


class ObsidianQueryEngine:
    """Query engine for searching and analyzing the Obsidian knowledge graph."""

    def __init__(self, knowledge_graph: KnowledgeGraph):
        """
        Initialize the Obsidian query engine.

        Args:
            knowledge_graph: The knowledge graph instance to use
        """
        self.kg = knowledge_graph

    def search_notes_by_content(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Search notes by content using text matching.

        Args:
            query: Text to search for
            limit: Maximum number of results

        Returns:
            list of matching notes with their content
        """
        with self.kg.get_session() as session:
            result = session.run("""
                MATCH (n:Note)
                WHERE n.content CONTAINS $query OR n.title CONTAINS $query
                RETURN n.path as path, n.title as title, n.content as content
                ORDER BY n.modified DESC
                LIMIT $limit
            """, query=query, limit=limit)

            return [dict(record) for record in result]

    def find_notes_by_tag(self, tag: str) -> list[dict[str, Any]]:
        """
        Find all notes with a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            list of matching notes
        """
        with self.kg.get_session() as session:
            result = session.run("""
                MATCH (n:Note)-[:TAGGED_WITH]->(t:Tag {name: $tag})
                RETURN n.path as path, n.title as title, n.modified as modified
                ORDER BY n.modified DESC
            """, tag=tag)

            return [dict(record) for record in result]

    def find_notes_by_folder(self, folder_path: str) -> list[dict[str, Any]]:
        """
        Find all notes in a specific folder.

        Args:
            folder_path: Path to the folder

        Returns:
            list of notes in the folder
        """
        with self.kg.get_session() as session:
            result = session.run("""
                MATCH (f:Folder {path: $folder_path})-[:CONTAINS]->(n:Note)
                RETURN n.path as path, n.title as title, n.modified as modified
                ORDER BY n.title
            """, folder_path=folder_path)

            return [dict(record) for record in result]

    def find_linked_notes(self, note_path: str) -> list[dict[str, Any]]:
        """
        Find all notes that link to a specific note.

        Args:
            note_path: Path to the note

        Returns:
            list of notes that link to the specified note
        """
        with self.kg.get_session() as session:
            result = session.run("""
                MATCH (n:Note)-[:LINKS_TO]->(l:InternalLink)
                WHERE l.name = $note_name OR l.name = $note_title
                RETURN n.path as path, n.title as title, l.name as link_name
                ORDER BY n.title
            """, note_name=note_path, note_title=note_path)

            return [dict(record) for record in result]

    def find_notes_linking_to(self, target_note: str) -> list[dict[str, Any]]:
        """
        Find all notes that a specific note links to.

        Args:
            target_note: Path to the note

        Returns:
            list of notes that the specified note links to
        """
        with self.kg.get_session() as session:
            result = session.run("""
                MATCH (n:Note {path: $note_path})-[:LINKS_TO]->(l:InternalLink)
                RETURN l.name as link_name
                ORDER BY l.name
            """, note_path=target_note)

            return [dict(record) for record in result]

    def find_most_linked_notes(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Find notes that are linked to the most by other notes.

        Args:
            limit: Maximum number of results

        Returns:
            list of most linked notes
        """
        with self.kg.get_session() as session:
            result = session.run("""
                MATCH (l:InternalLink)<-[:LINKS_TO]-(n:Note)
                RETURN l.name as note_name, count(n) as link_count
                ORDER BY link_count DESC
                LIMIT $limit
            """, limit=limit)

            return [dict(record) for record in result]

    def find_most_linking_notes(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Find notes that link to the most other notes.

        Args:
            limit: Maximum number of results

        Returns:
            list of notes with most outgoing links
        """
        with self.kg.get_session() as session:
            result = session.run("""
                MATCH (n:Note)-[:LINKS_TO]->(l:InternalLink)
                RETURN n.path as path, n.title as title, count(l) as link_count
                ORDER BY link_count DESC
                LIMIT $limit
            """, limit=limit)

            return [dict(record) for record in result]

    def find_orphaned_notes(self) -> list[dict[str, Any]]:
        """
        Find notes that have no incoming links (orphaned notes).

        Returns:
            list of orphaned notes
        """
        with self.kg.get_session() as session:
            result = session.run("""
                MATCH (n:Note)
                WHERE NOT EXISTS((n)-[:LINKS_TO]->()) AND NOT EXISTS(()-[:LINKS_TO]->(:InternalLink {name: n.title}))
                RETURN n.path as path, n.title as title, n.modified as modified
                ORDER BY n.title
            """)

            return [dict(record) for record in result]

    def find_most_used_tags(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Find the most frequently used tags.

        Args:
            limit: Maximum number of results

        Returns:
            list of most used tags
        """
        with self.kg.get_session() as session:
            result = session.run("""
                MATCH (n:Note)-[:TAGGED_WITH]->(t:Tag)
                RETURN t.name as tag_name, count(n) as usage_count
                ORDER BY usage_count DESC
                LIMIT $limit
            """, limit=limit)

            return [dict(record) for record in result]

    def find_notes_by_header(self, header_title: str) -> list[dict[str, Any]]:
        """
        Find notes that contain a specific header.

        Args:
            header_title: Title of the header to search for

        Returns:
            list of notes containing the header
        """
        with self.kg.get_session() as session:
            result = session.run("""
                MATCH (n:Note)-[:HAS_HEADER]->(h:Header)
                WHERE h.title CONTAINS $header_title
                RETURN n.path as path, n.title as title, h.title as header_title, h.level as header_level
                ORDER BY n.title
            """, header_title=header_title)

            return [dict(record) for record in result]

    def find_recently_modified_notes(self, days: int = 7, limit: int = 10) -> list[dict[str, Any]]:
        """
        Find recently modified notes.

        Args:
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            list of recently modified notes
        """
        import time
        cutoff_time = time.time() - (days * 24 * 60 * 60)

        with self.kg.get_session() as session:
            result = session.run("""
                MATCH (n:Note)
                WHERE n.modified > $cutoff_time
                RETURN n.path as path, n.title as title, n.modified as modified
                ORDER BY n.modified DESC
                LIMIT $limit
            """, cutoff_time=cutoff_time, limit=limit)

            return [dict(record) for record in result]

    def find_notes_with_external_links(self) -> list[dict[str, Any]]:
        """
        Find notes that contain external links.

        Returns:
            list of notes with external links
        """
        with self.kg.get_session() as session:
            result = session.run("""
                MATCH (n:Note)-[:LINKS_TO_EXTERNAL]->(e:ExternalLink)
                RETURN n.path as path, n.title as title, count(e) as external_link_count
                ORDER BY external_link_count DESC
            """)

            return [dict(record) for record in result]

    def find_duplicate_notes(self) -> list[dict[str, Any]]:
        """
        Find notes with identical content (same hash).

        Returns:
            list of duplicate note groups
        """
        with self.kg.get_session() as session:
            result = session.run("""
                MATCH (n:Note)
                WHERE n.hash IS NOT NULL AND n.hash <> ""
                WITH n.hash as hash, collect(n) as notes
                WHERE size(notes) > 1
                RETURN hash, [n in notes | n.path] as note_paths, size(notes) as count
                ORDER BY count DESC
            """)

            return [dict(record) for record in result]

    def get_note_details(self, note_path: str) -> dict[str, Any]:
        """
        Get comprehensive details about a specific note.

        Args:
            note_path: Path to the note

        Returns:
            dictionary with note details
        """
        with self.kg.get_session() as session:
            # Get note info
            note_info = session.run("""
                MATCH (n:Note {path: $note_path})
                RETURN n.title as title, n.content as content, n.modified as modified, 
                       n.size as size, n.aliases as aliases, n.frontmatter as frontmatter
            """, note_path=note_path).single()

            if not note_info:
                return None

            # Get tags
            tags = session.run("""
                MATCH (n:Note {path: $note_path})-[:TAGGED_WITH]->(t:Tag)
                RETURN t.name as tag_name
            """, note_path=note_path)

            # Get internal links
            internal_links = session.run("""
                MATCH (n:Note {path: $note_path})-[:LINKS_TO]->(l:InternalLink)
                RETURN l.name as link_name
            """, note_path=note_path)

            # Get external links
            external_links = session.run("""
                MATCH (n:Note {path: $note_path})-[:LINKS_TO_EXTERNAL]->(e:ExternalLink)
                RETURN e.url as url, e.text as text
            """, note_path=note_path)

            # Get headers
            headers = session.run("""
                MATCH (n:Note {path: $note_path})-[:HAS_HEADER]->(h:Header)
                RETURN h.title as title, h.level as level
                ORDER BY h.level, h.title
            """, note_path=note_path)

            return {
                'note_info': dict(note_info),
                'tags': [record['tag_name'] for record in tags],
                'internal_links': [record['link_name'] for record in internal_links],
                'external_links': [dict(record) for record in external_links],
                'headers': [dict(record) for record in headers]
            }

    def search_by_custom_query(self, cypher_query: str, parameters: dict[str, Any] = None) -> list[dict[str, Any]]:
        """
        Execute a custom Cypher query.

        Args:
            cypher_query: The Cypher query to execute
            parameters: Optional parameters for the query

        Returns:
            Query results
        """
        if parameters is None:
            parameters = {}

        with self.kg.get_session() as session:
            result = session.run(cypher_query, **parameters)
            return [dict(record) for record in result]

    def get_vault_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive statistics about the Obsidian vault.

        Returns:
            dictionary with vault statistics
        """
        with self.kg.get_session() as session:
            # Note statistics
            note_stats = session.run("""
                MATCH (n:Note)
                RETURN count(n) as total_notes,
                       sum(n.size) as total_size,
                       avg(n.size) as avg_note_size,
                       max(n.size) as max_note_size,
                       min(n.size) as min_note_size
            """).single()

            # Tag statistics
            tag_stats = session.run("""
                MATCH (t:Tag)
                RETURN count(t) as total_tags
            """).single()

            # Link statistics
            link_stats = session.run("""
                MATCH (l:InternalLink)
                RETURN count(l) as total_internal_links
            """).single()

            # External link statistics
            external_link_stats = session.run("""
                MATCH (e:ExternalLink)
                RETURN count(e) as total_external_links
            """).single()

            # Header statistics
            header_stats = session.run("""
                MATCH (h:Header)
                RETURN count(h) as total_headers
            """).single()

            # Folder statistics
            folder_stats = session.run("""
                MATCH (f:Folder)
                RETURN count(f) as total_folders
            """).single()

            return {
                'note_statistics': dict(note_stats),
                'tag_statistics': dict(tag_stats),
                'link_statistics': dict(link_stats),
                'external_link_statistics': dict(external_link_stats),
                'header_statistics': dict(header_stats),
                'folder_statistics': dict(folder_stats)
            }
