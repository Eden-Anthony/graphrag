# GraphRAG

A powerful knowledge graph system using Neo4j for indexing and querying Obsidian vaults. GraphRAG allows you to create a comprehensive knowledge graph of your Obsidian notes and perform sophisticated queries to understand relationships, connections, and knowledge structure.

## Features

- **Obsidian Vault Indexing**: Automatically scan and index Obsidian vaults into Neo4j
- **Smart Note Processing**: Processes markdown files with frontmatter, tags, and links
- **Relationship Extraction**: Automatically identifies internal links, tags, headers, and external links
- **Rich Querying**: Search by content, tags, folders, modification date, and more
- **Note Analysis**: Extract tags, internal links, external links, and headers
- **Link Analysis**: Find most linked notes and connection patterns
- **Statistics**: Comprehensive vault analytics and insights
- **Custom Queries**: Execute arbitrary Cypher queries
- **Beautiful CLI**: Rich terminal interface with tables and progress indicators
- **Visualization**: Export data for Neo4j Browser and external visualization tools

## Installation

### Prerequisites

1. **Neo4j Database**: You need a running Neo4j instance
   - [Neo4j Desktop](https://neo4j.com/download/) (recommended for development)
   - [Neo4j Community Edition](https://neo4j.com/download-center/#community)
   - [Neo4j Docker](https://neo4j.com/developer/docker/)

2. **Python 3.12+**: The system requires Python 3.12 or higher

3. **UV**: Install [UV](https://docs.astral.sh/uv/) for fast Python package management

4. **Obsidian Vault**: An Obsidian vault to index

### Install GraphRAG

```bash
# Clone the repository
git clone <repository-url>
cd graphrag

# Install dependencies using UV
uv sync

# Or install in development mode
uv pip install -e .
```

## Quick Start

### 1. Start Neo4j

Make sure your Neo4j database is running. The default connection settings are:
- URI: `bolt://localhost:7687`
- Username: `neo4j`
- Password: `password`

### 2. Index Your Obsidian Vault

```bash
# Index your Obsidian vault (default settings)
uv run graphrag index /path/to/your/obsidian/vault

# Index with custom Neo4j settings
uv run graphrag --uri bolt://localhost:7687 --username neo4j --password your_password index /path/to/your/obsidian/vault

# Clear existing data before indexing
uv run graphrag index /path/to/your/obsidian/vault --clear

# Index without recursion
uv run graphrag index /path/to/your/obsidian/vault --no-recursive
```

### 3. Search and Query Your Vault

```bash
# Search for notes containing specific text
uv run graphrag search --query "project ideas"

# Find notes with specific tags
uv run graphrag search --tag "#project"

# Find notes in a specific folder
uv run graphrag search --folder "Projects/"

# Get vault statistics
uv run graphrag stats

# Find most linked notes
uv run graphrag most-linked

# Get detailed info about a specific note
uv run graphrag info "Projects/my-note.md"

# Execute custom Cypher query
uv run graphrag query --query "MATCH (n:Note)-[:HAS_TAG]->(t:Tag) RETURN n.title, t.name LIMIT 10"
```

## Usage Examples

### Indexing Different Types of Vaults

```bash
# Index a personal knowledge vault
uv run graphrag index ~/Documents/Obsidian/PersonalVault

# Index a research vault
uv run graphrag index ~/Documents/Obsidian/ResearchVault

# Index a project vault
uv run graphrag index ~/Documents/Obsidian/ProjectVault
```

### Advanced Search Queries

```bash
# Find all notes containing "project" in content
uv run graphrag search --query "project"

# Find recently modified notes
uv run graphrag query --query "MATCH (n:Note) WHERE n.modified > timestamp() - 86400000 RETURN n.title, n.modified ORDER BY n.modified DESC LIMIT 10"

# Find notes that link to a specific note
uv run graphrag query --query "MATCH (n:Note)-[:LINKS_TO]->(l:InternalLink {name: 'project-ideas'}) RETURN n.title, n.path"
```

### Note Analysis

```bash
# Find all tags in a specific note
uv run graphrag query --query "MATCH (n:Note {path: '/path/to/note.md'})-[:HAS_TAG]->(t:Tag) RETURN t.name"

# Find notes with the most tags
uv run graphrag query --query "MATCH (n:Note)-[:HAS_TAG]->(t:Tag) RETURN n.title, count(t) as tag_count ORDER BY tag_count DESC LIMIT 10"

# Find notes with external links
uv run graphrag query --query "MATCH (n:Note)-[:LINKS_TO_EXTERNAL]->(e:ExternalLink) RETURN n.title, e.url LIMIT 20"
```

## Data Model

GraphRAG creates a rich knowledge graph with the following node types and relationships:

### Node Types

- **Note**: Represents individual Obsidian notes with properties like path, title, content, size, etc.
- **Folder**: Represents directories in the vault structure
- **Tag**: Represents tags used in notes
- **InternalLink**: Represents internal links between notes
- **ExternalLink**: Represents external links from notes
- **Header**: Represents headers within notes

### Relationships

- **CONTAINS**: Folder contains notes or subfolders
- **HAS_TAG**: Note has a specific tag
- **LINKS_TO**: Note links to an internal link
- **LINKS_TO_EXTERNAL**: Note links to an external URL
- **HAS_HEADER**: Note contains a specific header

### Example Graph Structure

```
(Folder: /Projects) -[:CONTAINS]-> (Note: project-ideas.md)
(Note: project-ideas.md) -[:HAS_TAG]-> (Tag: #ideas)
(Note: project-ideas.md) -[:LINKS_TO]-> (InternalLink: implementation)
(Note: project-ideas.md) -[:LINKS_TO_EXTERNAL]-> (ExternalLink: https://example.com)
(Note: project-ideas.md) -[:HAS_HEADER]-> (Header: Implementation Plan)
```

## CLI Commands

### `graphrag index <vault_path>`

Index an Obsidian vault into the knowledge graph.

**Options:**
- `--clear`: Clear existing data before indexing
- `--recursive/--no-recursive`: Index subdirectories recursively (default: true)

### `graphrag search`

Search the Obsidian knowledge graph.

**Options:**
- `--query, -q`: Search query for note content
- `--tag, -t`: Filter by tag
- `--folder, -f`: Filter by folder path
- `--limit, -l`: Maximum number of results (default: 10)

### `graphrag stats`

Show comprehensive vault statistics.

**Options:**
- `--limit, -l`: Maximum number of results for tag stats (default: 10)

### `graphrag most-linked`

Find the most linked notes in the vault.

**Options:**
- `--limit, -l`: Maximum number of results (default: 10)

### `graphrag info <note_path>`

Get detailed information about a specific note.

### `graphrag query --query <cypher_query>`

Execute a custom Cypher query.

### `graphrag visualize`

Export knowledge graph for visualization.

**Options:**
- `--format, -f`: Export format (cypher, json, csv, graphml)
- `--output, -o`: Output file path
- `--query, -q`: Custom query to visualize

## Configuration

### Neo4j Connection Settings

You can configure Neo4j connection settings using command-line options:

```bash
uv run graphrag --uri bolt://your-neo4j-host:7687 --username your_username --password your_password <command>
```

### Environment Variables

You can also set environment variables:

```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=your_password
```

## Note Processing

### Supported File Types

GraphRAG automatically processes Obsidian notes:

- **Markdown files**: `.md`, `.markdown`
- **Text files**: `.txt` (if present in vault)

### Skipped Directories

The following directories are automatically skipped:
- Obsidian system: `.obsidian`, `.trash`
- Version control: `.git`, `.svn`, `.hg`
- Build artifacts: `build`, `dist`, `target`, `bin`, `obj`
- Dependencies: `node_modules`, `.venv`, `venv`, `env`
- IDE files: `.idea`, `.vscode`
- Cache directories: `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.tox`

### Processing Features

- **Frontmatter**: Extracts YAML frontmatter from notes
- **Tags**: Identifies tags in content and frontmatter
- **Internal Links**: Extracts `[[wiki-links]]` and `[display text](internal-link)` format
- **External Links**: Extracts `[text](url)` format
- **Headers**: Identifies markdown headers (`#`, `##`, etc.)
- **Content Analysis**: Processes note content for search indexing

## Development

### Using UV for Development

```bash
# Install dependencies
uv sync

# Install in development mode
uv pip install -e .

# Run tests
uv run pytest

# Format code
uv run black src/
uv run isort src/

# Type checking
uv run mypy src/
```

## Advanced Usage

### Programmatic Usage

You can also use GraphRAG programmatically:

```python
from graphrag import KnowledgeGraph, ObsidianIndexer, ObsidianQueryEngine

# Initialize the knowledge graph
kg = KnowledgeGraph(uri="bolt://localhost:7687", username="neo4j", password="password")
kg.connect()

# Index an Obsidian vault
indexer = ObsidianIndexer(kg)
stats = indexer.index_vault("/path/to/your/obsidian/vault")

# Query the knowledge graph
query_engine = ObsidianQueryEngine(kg)
results = query_engine.search_notes_by_content("project ideas")
print(results)

kg.disconnect()
```

### Custom Queries

GraphRAG supports arbitrary Cypher queries for advanced analysis:

```bash
# Find notes that link to each other
uv run graphrag query --query "
MATCH (n1:Note)-[:LINKS_TO]->(l:InternalLink)<-[:LINKS_TO]-(n2:Note)
WHERE n1 <> n2
RETURN n1.title, l.name, n2.title
LIMIT 20
"

# Find notes with most tags
uv run graphrag query --query "
MATCH (n:Note)-[:HAS_TAG]->(t:Tag)
RETURN n.title, count(t) as tag_count
ORDER BY tag_count DESC
LIMIT 10
"

# Find orphaned internal links (links that don't exist)
uv run graphrag query --query "
MATCH (l:InternalLink)
WHERE NOT EXISTS((n:Note {title: l.name}))
RETURN l.name as orphaned_link
"
```

## Visualization

### Neo4j Browser (Recommended)

The easiest way to visualize your knowledge graph:

```bash
# Start Neo4j
docker compose up -d

# Open Neo4j Browser at http://localhost:7474
# Username: neo4j
# Password: password

# Run visualization queries:
MATCH (n:Note) OPTIONAL MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50
MATCH (f:Folder)-[:CONTAINS]->(n:Note) RETURN f, n
MATCH (n:Note)-[:HAS_TAG]->(t:Tag) RETURN n, t
```

### Export for External Tools

```bash
# Export Cypher queries for Neo4j Browser
uv run graphrag visualize --format cypher --output vault_visualization.cypher

# Export as JSON for D3.js, Gephi, etc.
uv run graphrag visualize --format json --output vault_data.json

# Export as CSV for spreadsheet analysis
uv run graphrag visualize --format csv --output vault_data.csv
```

## Troubleshooting

### Connection Issues

If you can't connect to Neo4j:

1. Ensure Neo4j is running
2. Check the connection URI, username, and password
3. Verify Neo4j is accessible from your network
4. Check Neo4j logs for authentication issues

### Performance Issues

For large vaults:

1. Increase Neo4j memory settings
2. Use SSD storage for Neo4j data
3. Consider indexing in smaller chunks
4. Monitor Neo4j performance metrics

### Note Processing Issues

If notes aren't being processed:

1. Check file permissions
2. Verify note encoding (GraphRAG auto-detects encoding)
3. Ensure notes aren't in skipped directories
4. Check if note format is supported

### Vault Structure Issues

If you have issues with your Obsidian vault:

1. Verify the vault path is correct
2. Check if the vault contains `.md` files
3. Ensure the vault structure is valid
4. Verify Obsidian can open the vault normally

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 