# GraphRAG Quick Start Guide

Get up and running with GraphRAG in minutes!

## Prerequisites

- Python 3.12 or higher
- [UV](https://docs.astral.sh/uv/) for fast Python package management
- Docker (optional, for Neo4j)

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
docker-compose up -d

# Wait for Neo4j to be ready (check logs)
docker-compose logs -f neo4j
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

## Step 4: Index Your First Directory

```bash
# Index the current directory
uv run graphrag index .

# Or index a specific directory
uv run graphrag index /path/to/your/codebase
```

## Step 5: Start Querying

```bash
# Search for files containing specific text
uv run graphrag search --query "def main"

# Find all Python files
uv run graphrag search --extension py

# Get codebase statistics
uv run graphrag stats

# Find largest files
uv run graphrag largest

# Get info about a specific file
uv run graphrag info /path/to/your/file.py
```

## Step 6: Advanced Queries

```bash
# Find files that import pandas
uv run graphrag query --query "MATCH (f:File)-[:IMPORTS]->(m:ImportedModule {name: 'pandas'}) RETURN f.path, f.name"

# Find files with most functions
uv run graphrag query --query "MATCH (f:File)-[:DEFINES]->(func:Function) RETURN f.name, count(func) as function_count ORDER BY function_count DESC LIMIT 10"

# Find recently modified files
uv run graphrag query --query "MATCH (f:File) WHERE f.modified > timestamp() - 86400000 RETURN f.name, f.modified ORDER BY f.modified DESC LIMIT 10"
```

## Example Workflow

Here's a complete example workflow:

```bash
# 1. Start Neo4j
docker-compose up -d

# 2. Wait for Neo4j to be ready
sleep 30

# 3. Index a Python project
uv run graphrag index ./my-python-project

# 4. Search for main functions
uv run graphrag search --query "def main"

# 5. Find all imports
uv run graphrag query --query "MATCH (f:File)-[:IMPORTS]->(m:ImportedModule) RETURN f.name, m.name LIMIT 20"

# 6. Get project statistics
uv run graphrag stats

# 7. Find largest files
uv run graphrag largest --limit 10
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
docker-compose ps

# Check Neo4j logs
docker-compose logs neo4j

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

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out [examples/basic_usage.py](examples/basic_usage.py) for programmatic usage
- Explore the CLI help: `uv run graphrag --help`
- Try different query types: `uv run graphrag search --help`

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run `uv run python test_installation.py` to verify your setup
3. Check the Neo4j logs: `docker-compose logs neo4j`
4. Open an issue on GitHub with details about your environment

Happy indexing! 🚀 