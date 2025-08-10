"""Pytest configuration and common fixtures."""

import os
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from graphrag.config import Config
from graphrag.models import Entity, Note, Relationship, EntityType, RelationshipType


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    with patch.dict(os.environ, {
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USER': 'neo4j',
        'NEO4J_PASSWORD': 'password',
        'OPENAI_API_KEY': 'test-key',
        'OPENAI_ORG_ID': 'test-org',
        'OBSIDIAN_VAULT_PATH': '/tmp/test-vault',
        'NEO4J_DATABASE': 'neo4j',
        'NEO4J_INDEX_NAME': 'test-index',
        'NEO4J_EMBEDDING_INDEX_NAME': 'test-embedding-index',
        'OPENAI_EMBEDDING_MODEL': 'text-embedding-ada-002',
        'OPENAI_ENTITY_DETECTION_MODEL': 'gpt-4o-mini',
        'OPENAI_QUERY_MODEL': 'gpt-4o',
        'GRAPH_RAG_CONTEXT_WINDOW': '20',
        'FILE_WATCHER_DEBOUNCE_SECONDS': '1',
        'FILE_WATCHER_MAX_NOTE_SIZE_MB': '10',
        'FILE_WATCHER_BATCH_SIZE': '50'
    }):
        return Config()


@pytest.fixture
def sample_note():
    """Sample note for testing."""
    return Note(
        id="test-note-1",
        title="Test Note",
        content="This is a test note about AI and machine learning.",
        file_path="/tmp/test-vault/test-note.md",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
        tags=["ai", "ml"],
        frontmatter={"status": "active"},
        internal_links=["[[other-note]]"],
        external_links=["https://example.com"]
    )


@pytest.fixture
def sample_entity():
    """Sample entity for testing."""
    return Entity(
        id="test-entity-1",
        name="Artificial Intelligence",
        type=EntityType.CONCEPT,
        description="A field of computer science",
        source_notes=["test-note-1"],
        properties={"field": "computer-science"}
    )


@pytest.fixture
def sample_relationship():
    """Sample relationship for testing."""
    return Relationship(
        id="test-rel-1",
        source_entity_id="test-entity-1",
        target_entity_id="test-entity-2",
        type=RelationshipType.RELATED_TO,
        properties={"strength": 0.8}
    )


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_client.embeddings.create.return_value.data[0].embedding = [0.1] * 1536
    mock_client.chat.completions.create.return_value.choices[0].message.content = '{"entities": []}'
    return mock_client


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver for testing."""
    mock_driver = Mock()
    mock_session = Mock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_driver.session.return_value.__exit__.return_value = None
    return mock_driver


@pytest.fixture
def temp_vault_path(tmp_path):
    """Temporary vault path for testing."""
    vault_path = tmp_path / "test-vault"
    vault_path.mkdir()
    (vault_path / "⭕Meta").mkdir()
    return vault_path 