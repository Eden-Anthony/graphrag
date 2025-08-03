# GraphRAG Quick Start Guide

Get up and running with GraphRAG for Obsidian vault indexing in minutes!

## Prerequisites

- Python 3.12 or higher
- [UV](https://docs.astral.sh/uv/) for fast Python package management
- Docker (optional, for Neo4j)
- An Obsidian vault to index

## Step 1: Install GraphRAG

```bash
# Clone the repository
git clone <repository-url>
cd graphrag

# Install dependencies using UV
uv sync

# Or install in development mode
uv pip install -e .
```

## Step 2: Start Neo4j

### Option A: Using Docker (Recommended)

```bash
# Start Neo4j using Docker Compose
docker compose up -d

# Wait for Neo4j to be ready (check logs)
docker compose logs -f neo4j
```

### Option B: Using Neo4j Desktop

1. Download and install [Neo4j Desktop](https://neo4j.com/download/)
2. Create a new project and database
3. Set password to `password`
4. Start the database

### Option C: Using Neo4j Community Edition

1. Download [Neo4j Community Edition](https://neo4j.com/download-center/#community)
2. Install and configure with username `neo4j` and password `password`
3. Start the service

## Step 3: Test Installation

```bash
# Run the test script
uv run python test_installation.py
```

## Step 4: Index Your Obsidian Vault

```bash
# Index your Obsidian vault
uv run graphrag index /path/to/your/obsidian/vault

# Or index the current directory if it's your vault
uv run graphrag index .

# Clear existing data and re-index
uv run graphrag index /path/to/your/obsidian/vault --clear
```

## Step 5: Start Querying Your Vault

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

# Get info about a specific note
uv run graphrag info "Projects/my-note.md"
```

## Step 6: Advanced Queries

```bash
# Find notes that link to a specific note
uv run graphrag query --query "MATCH (n:Note)-[:LINKS_TO]->(l:InternalLink {name: 'project-ideas'}) RETURN n.title, n.path"

# Find notes with most tags
uv run graphrag query --query "MATCH (n:Note)-[:HAS_TAG]->(t:Tag) RETURN n.title, count(t) as tag_count ORDER BY tag_count DESC LIMIT 10"

# Find recently modified notes
uv run graphrag query --query "MATCH (n:Note) WHERE n.modified > timestamp() - 86400000 RETURN n.title, n.modified ORDER BY n.modified DESC LIMIT 10"

# Find notes with external links
uv run graphrag query --query "MATCH (n:Note)-[:LINKS_TO_EXTERNAL]->(e:ExternalLink) RETURN n.title, e.url LIMIT 20"
```

## Example Workflow

Here's a complete example workflow for indexing and querying an Obsidian vault:

```bash
# 1. Start Neo4j
docker compose up -d

# 2. Wait for Neo4j to be ready
sleep 30

# 3. Index your Obsidian vault
uv run graphrag index ~/Documents/Obsidian/MyVault

# 4. Search for notes about projects
uv run graphrag search --query "project"

# 5. Find all notes with the #ideas tag
uv run graphrag search --tag "#ideas"

# 6. Get vault statistics
uv run graphrag stats

# 7. Find most linked notes
uv run graphrag most-linked --limit 10

# 8. Get detailed info about a specific note
uv run graphrag info "Projects/2024-goals.md"

# 9. Find notes that link to a specific concept
uv run graphrag query --query "MATCH (n:Note)-[:LINKS_TO]->(l:InternalLink {name: 'graphrag'}) RETURN n.title, n.path"
```

## Development Workflow

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

## Troubleshooting

### Connection Issues

If you can't connect to Neo4j:

```bash
# Check if Neo4j is running
docker compose ps

# Check Neo4j logs
docker compose logs neo4j

# Test connection manually
curl http://localhost:7474
```

### Permission Issues

If you get permission errors:

```bash
# Make sure you have write permissions
chmod +x test_installation.py
chmod +x examples/basic_usage.py
```

### Import Errors

If you get import errors:

```bash
# Reinstall dependencies
uv sync --reinstall

# Or install in development mode
uv pip install -e .
```

### UV Issues

If UV is not working:

```bash
# Update UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or install via pip
pip install uv

# Verify installation
uv --version
```

### Obsidian Vault Issues

If you have issues with your Obsidian vault:

```bash
# Make sure the vault path is correct
ls -la /path/to/your/obsidian/vault

# Check if the vault contains .md files
find /path/to/your/obsidian/vault -name "*.md" | head -10

# Verify vault structure
tree /path/to/your/obsidian/vault -L 2
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out [examples/basic_usage.py](examples/basic_usage.py) for programmatic usage
- Explore the CLI help: `uv run graphrag --help`
- Try different query types: `uv run graphrag search --help`
- Learn about Cypher queries for advanced vault analysis

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run `uv run python test_installation.py` to verify your setup
3. Check the Neo4j logs: `docker compose logs neo4j`
4. Verify your Obsidian vault structure and permissions
5. Open an issue on GitHub with details about your environment

Happy vault indexing! 🚀 