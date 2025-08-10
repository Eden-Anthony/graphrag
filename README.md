# GraphRAG: Obsidian Knowledge Graph with Neo4j

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

GraphRAG is a powerful Python application that transforms your Obsidian vault into an intelligent knowledge graph using Neo4j's GraphRAG technology. It automatically detects entities, relationships, and concepts from your notes, enabling advanced semantic search, AI-powered querying, and knowledge discovery.

## 🚀 Features

- **Automatic Entity Detection**: Uses OpenAI's GPT models to identify entities, concepts, and relationships in your notes
- **Neo4j Integration**: Leverages Neo4j's GraphRAG for powerful graph-based knowledge representation
- **Real-time File Watching**: Automatically updates the knowledge graph when you modify notes
- **Hybrid Search**: Combines vector similarity and full-text search for optimal results
- **AI-Powered Queries**: Ask questions in natural language and get intelligent answers with citations
- **Comprehensive Entity Types**: Supports 100+ entity categories from philosophy to technology
- **Rich Metadata Extraction**: Parses frontmatter, tags, links, and note relationships

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Obsidian      │    │   GraphRAG       │    │     Neo4j       │
│     Vault       │───▶│   Services       │───▶│   Database      │
│                 │    │                  │    │                 │
│ • Markdown      │    │ • Entity         │    │ • Knowledge     │
│ • Frontmatter   │    │   Detection      │    │   Graph         │
│ • Links         │    │ • Knowledge      │    │ • Vector        │
│ • Tags          │    │   Graph          │    │   Indexes       │
└─────────────────┘    │ • Query          │    │ • Full-text     │
                       │ • File Watching  │    │   Search        │
                       └──────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Python 3.12 or higher
- Neo4j database (local or AuraDB cloud)
- OpenAI API key
- Obsidian vault

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/graphrag.git
   cd graphrag
   ```

2. **Install dependencies using uv (recommended):**
   ```bash
   uv sync
   ```

   Or using pip:
   ```bash
   pip install -e .
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```bash
   # Neo4j Configuration
   NEO4J_URI=neo4j://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   NEO4J_DATABASE=neo4j
   
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL_ENTITY_DETECTION=gpt-4o-mini
   OPENAI_MODEL_QUERY=gpt-4o
   
   # Obsidian Configuration
   OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault
   
   # Optional: AuraDB Configuration
   AURA_URI=neo4j+s://your-instance.neo4j.io
   AURA_USER=neo4j
   AURA_PASSWORD=your_aura_password
   AURA_DATABASE=neo4j
   ```

## 🚀 Quick Start

### Basic Usage

```python
from graphrag import ObsidianGraphRAG

# Initialize the system
graphrag = ObsidianGraphRAG()

# Build the initial knowledge graph
graphrag.build_initial_knowledge_graph()

# Query your knowledge
result = graphrag.query("What are the main concepts in my notes about philosophy?")
print(result.answer)

# Start file watching for real-time updates
graphrag.start_file_watcher()

# Interactive chat mode
graphrag.chat_mode()
```

### Advanced Usage

```python
# Get similar entities
similar = graphrag.get_similar_entities("machine learning", limit=5)

# Get topic summaries
summary = graphrag.get_topic_summary("artificial intelligence", limit=10)

# View graph statistics
graphrag._show_graph_stats()
```

## 🔧 Configuration

The system is highly configurable through environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CONTEXT_WINDOW_SIZE` | 20 | Number of notes to include in query context |
| `MAX_NOTE_SIZE` | 100000 | Maximum note size in bytes |
| `ENTITY_DETECTION_BATCH_SIZE` | 5 | Batch size for entity detection |
| `VECTOR_INDEX_NAME` | noteContentEmbedding | Neo4j vector index name |
| `FULLTEXT_INDEX_NAME` | noteFulltext | Neo4j full-text index name |

## 📊 Entity Types

GraphRAG supports a comprehensive taxonomy of 100+ entity types including:

- **Knowledge Systems** (00-09): Personal knowledge management, philosophy
- **Philosophy** (10-19): Metaphysics, epistemology, logic, ethics
- **Religion & Theology** (20-29): Major world religions, esotericism
- **Social Sciences** (30-39): Sociology, politics, economics, anthropology
- **Natural Sciences** (50-59): Mathematics, physics, biology, chemistry
- **Technology** (60-69): Computer science, engineering, medicine
- **Arts & Humanities** (70-89): Art, literature, music, language
- **History & Geography** (90-98): World history, civilizations, current affairs

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/graphrag

# Run specific test file
pytest tests/test_core.py
```

## 📁 Project Structure

```
graphrag/
├── src/graphrag/
│   ├── __init__.py          # Main package exports
│   ├── core.py              # Main ObsidianGraphRAG class
│   ├── config.py            # Configuration management
│   ├── models.py            # Data models (Note, Entity, etc.)
│   └── services/
│       ├── entity_detection.py    # Entity detection service
│       ├── knowledge_graph.py     # Neo4j knowledge graph service
│       ├── query.py               # Query processing service
│       └── file_watcher.py        # File system monitoring
├── tests/                   # Test suite
├── entity_types.txt         # Entity type definitions
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## 🔍 How It Works

1. **Note Processing**: Scans your Obsidian vault for markdown files
2. **Entity Detection**: Uses OpenAI to identify entities, concepts, and relationships
3. **Graph Construction**: Builds a Neo4j knowledge graph with nodes and relationships
4. **Vector Embeddings**: Creates semantic embeddings for similarity search
5. **Query Processing**: Combines vector search and full-text search for optimal results
6. **Real-time Updates**: Monitors file changes and updates the graph automatically

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

```bash
# Install development dependencies
uv sync --group dev

# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Neo4j GraphRAG](https://github.com/neo4j/graphrag) for the underlying graph RAG technology
- [OpenAI](https://openai.com/) for AI-powered entity detection and query processing
- [Obsidian](https://obsidian.md/) for the excellent note-taking platform

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/graphrag/issues) page
2. Create a new issue with detailed information
3. Join our community discussions

---

**Happy knowledge graphing! 🧠✨**
