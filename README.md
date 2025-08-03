# GraphRAG

A powerful knowledge graph system using Neo4j for indexing and querying file directories. GraphRAG allows you to create a comprehensive knowledge graph of your codebase and perform sophisticated queries to understand relationships, dependencies, and code structure.

## Features

- **Directory Indexing**: Automatically scan and index file directories into Neo4j
- **Smart File Processing**: Supports multiple file types and detects text content
- **Relationship Extraction**: Automatically identifies imports, functions, classes, and dependencies
- **Rich Querying**: Search by content, file type, size, modification date, and more
- **Code Analysis**: Extract functions, classes, and import relationships
- **Duplicate Detection**: Find files with identical content
- **Statistics**: Comprehensive codebase analytics
- **Custom Queries**: Execute arbitrary Cypher queries
- **Beautiful CLI**: Rich terminal interface with tables and progress indicators

## Installation

### Prerequisites

1. **Neo4j Database**: You need a running Neo4j instance
   - [Neo4j Desktop](https://neo4j.com/download/) (recommended for development)
   - [Neo4j Community Edition](https://neo4j.com/download-center/#community)
   - [Neo4j Docker](https://neo4j.com/developer/docker/)

2. **Python 3.12+**: The system requires Python 3.12 or higher

3. **UV**: Install [UV](https://docs.astral.sh/uv/) for fast Python package management

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

### 2. Index a Directory

```bash
# Index a directory (default settings)
graphrag index /path/to/your/codebase

# Index with custom Neo4j settings
graphrag --uri bolt://localhost:7687 --username neo4j --password your_password index /path/to/your/codebase

# Clear existing data before indexing
graphrag index /path/to/your/codebase --clear

# Index without recursion
graphrag index /path/to/your/codebase --no-recursive
```

### 3. Search and Query

```bash
# Search for files containing specific text
graphrag search --query "def main"

# Find files by extension
graphrag search --extension py

# Get codebase statistics
graphrag stats

# Find largest files
graphrag largest --limit 20

# Get detailed info about a specific file
graphrag info /path/to/your/file.py

# Execute custom Cypher query
graphrag query --query "MATCH (f:File)-[:IMPORTS]->(m:ImportedModule) RETURN f.name, m.name LIMIT 10"
```

## Usage Examples

### Indexing Different Types of Projects

```bash
# Index a Python project
graphrag index ./my-python-project

# Index a JavaScript/TypeScript project
graphrag index ./my-js-project

# Index a mixed codebase
graphrag index ./my-mixed-project
```

### Advanced Search Queries

```bash
# Find all Python files containing "class" definitions
graphrag search --query "class" --extension py

# Find recently modified files
graphrag query --query "MATCH (f:File) WHERE f.modified > timestamp() - 86400000 RETURN f.name, f.modified ORDER BY f.modified DESC LIMIT 10"

# Find files that import a specific module
graphrag query --query "MATCH (f:File)-[:IMPORTS]->(m:ImportedModule {name: 'pandas'}) RETURN f.path, f.name"
```

### Code Analysis

```bash
# Find all functions in a specific file
graphrag query --query "MATCH (f:File {path: '/path/to/file.py'})-[:DEFINES]->(func:Function) RETURN func.name"

# Find files with the most imports
graphrag query --query "MATCH (f:File)-[:IMPORTS]->(m:ImportedModule) RETURN f.name, count(m) as import_count ORDER BY import_count DESC LIMIT 10"

# Find duplicate files
graphrag query --query "MATCH (f:File) WHERE f.hash IS NOT NULL WITH f.hash as hash, collect(f) as files WHERE size(files) > 1 RETURN hash, [f in files | f.path] as file_paths"
```

## Data Model

GraphRAG creates a rich knowledge graph with the following node types and relationships:

### Node Types

- **File**: Represents individual files with properties like path, name, extension, content, size, etc.
- **Directory**: Represents directories in the file system
- **Function**: Represents functions defined in code files
- **Class**: Represents classes defined in code files
- **ImportedModule**: Represents modules imported by files

### Relationships

- **CONTAINS**: Directory contains files or subdirectories
- **IMPORTS**: File imports a module
- **DEFINES**: File defines a function or class

### Example Graph Structure

```
(Directory: /project) -[:CONTAINS]-> (File: main.py)
(File: main.py) -[:IMPORTS]-> (ImportedModule: pandas)
(File: main.py) -[:DEFINES]-> (Function: process_data)
(File: main.py) -[:DEFINES]-> (Class: DataProcessor)
```

## CLI Commands

### `graphrag index <directory>`

Index a directory into the knowledge graph.

**Options:**
- `--clear`: Clear existing data before indexing
- `--recursive/--no-recursive`: Index subdirectories recursively (default: true)

### `graphrag search`

Search the knowledge graph.

**Options:**
- `--query, -q`: Search query for file content
- `--extension, -e`: Filter by file extension
- `--limit, -l`: Maximum number of results (default: 10)

### `graphrag stats`

Show comprehensive codebase statistics.

**Options:**
- `--limit, -l`: Maximum number of results for extension stats (default: 10)

### `graphrag largest`

Find the largest files in the codebase.

**Options:**
- `--limit, -l`: Maximum number of results (default: 10)

### `graphrag info <file_path>`

Get detailed information about a specific file.

### `graphrag query --query <cypher_query>`

Execute a custom Cypher query.

## Configuration

### Neo4j Connection Settings

You can configure Neo4j connection settings using command-line options:

```bash
graphrag --uri bolt://your-neo4j-host:7687 --username your_username --password your_password <command>
```

### Environment Variables

You can also set environment variables:

```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=your_password
```

## File Processing

### Supported File Types

GraphRAG automatically processes text-based files including:

- **Code files**: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.h`, `.cs`, `.php`, `.rb`, `.go`, `.rs`, `.swift`, `.kt`, `.scala`, `.r`
- **Configuration files**: `.yml`, `.yaml`, `.json`, `.xml`, `.toml`, `.ini`, `.cfg`, `.conf`
- **Documentation**: `.md`, `.txt`
- **Scripts**: `.sh`, `.bash`, `.zsh`, `.fish`, `.ps1`, `.bat`
- **Web files**: `.html`, `.css`, `.scss`, `.sass`, `.less`, `.vue`, `.jsx`, `.tsx`
- **Other**: `.sql`, `.dockerfile`, `.gitignore`, `.env`

### Skipped Directories

The following directories are automatically skipped:
- Version control: `.git`, `.svn`, `.hg`
- Build artifacts: `build`, `dist`, `target`, `bin`, `obj`
- Dependencies: `node_modules`, `.venv`, `venv`, `env`
- IDE files: `.idea`, `.vscode`
- Cache directories: `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.tox`

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
from graphrag import KnowledgeGraph, FileIndexer, QueryEngine

# Initialize the knowledge graph
kg = KnowledgeGraph(uri="bolt://localhost:7687", username="neo4j", password="password")
kg.connect()

# Index a directory
indexer = FileIndexer(kg)
stats = indexer.index_directory("/path/to/your/codebase")

# Query the knowledge graph
query_engine = QueryEngine(kg)
results = query_engine.search_files_by_content("def main")
print(results)

kg.disconnect()
```

### Custom Queries

GraphRAG supports arbitrary Cypher queries for advanced analysis:

```bash
# Find circular dependencies
graphrag query --query "
MATCH path = (f:File)-[:IMPORTS*]->(f)
RETURN [node in nodes(path) | node.name] as circular_path
"

# Find files with most functions
graphrag query --query "
MATCH (f:File)-[:DEFINES]->(func:Function)
RETURN f.name, count(func) as function_count
ORDER BY function_count DESC
LIMIT 10
"

# Find unused imports
graphrag query --query "
MATCH (m:ImportedModule)
WHERE NOT EXISTS((m)<-[:IMPORTS]-())
RETURN m.name as unused_module
"
```

## Troubleshooting

### Connection Issues

If you can't connect to Neo4j:

1. Ensure Neo4j is running
2. Check the connection URI, username, and password
3. Verify Neo4j is accessible from your network
4. Check Neo4j logs for authentication issues

### Performance Issues

For large codebases:

1. Increase Neo4j memory settings
2. Use SSD storage for Neo4j data
3. Consider indexing in smaller chunks
4. Monitor Neo4j performance metrics

### File Processing Issues

If files aren't being processed:

1. Check file permissions
2. Verify file encoding (GraphRAG auto-detects encoding)
3. Ensure files aren't in skipped directories
4. Check if file type is supported

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 