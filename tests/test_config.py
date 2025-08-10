"""Tests for the Config class."""

import os
import pytest
from unittest.mock import patch

from graphrag.config import Config


class TestConfig:
    """Test cases for the Config class."""

    def test_config_loading_from_env(self):
        """Test that config loads correctly from environment variables."""
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
            config = Config()
            
            assert config.neo4j_uri == 'bolt://localhost:7687'
            assert config.neo4j_user == 'neo4j'
            assert config.neo4j_password == 'password'
            assert config.openai_api_key == 'test-key'
            assert config.openai_org_id == 'test-org'
            assert config.obsidian_vault_path == '/tmp/test-vault'
            assert config.neo4j_database == 'neo4j'
            assert config.neo4j_index_name == 'test-index'
            assert config.neo4j_embedding_index_name == 'test-embedding-index'
            assert config.openai_embedding_model == 'text-embedding-ada-002'
            assert config.openai_entity_detection_model == 'gpt-4o-mini'
            assert config.openai_query_model == 'gpt-4o'
            assert config.graph_rag_context_window == 20
            assert config.file_watcher_debounce_seconds == 1
            assert config.file_watcher_max_note_size_mb == 10
            assert config.file_watcher_batch_size == 50

    def test_config_defaults(self):
        """Test that config uses sensible defaults when env vars are missing."""
        with patch.dict(os.environ, {
            'NEO4J_URI': 'bolt://localhost:7687',
            'NEO4J_USER': 'neo4j',
            'NEO4J_PASSWORD': 'password',
            'OPENAI_API_KEY': 'test-key',
            'OBSIDIAN_VAULT_PATH': '/tmp/test-vault'
        }):
            config = Config()
            
            assert config.neo4j_database == 'neo4j'
            assert config.neo4j_index_name == 'graphrag-index'
            assert config.neo4j_embedding_index_name == 'graphrag-embeddings'
            assert config.openai_embedding_model == 'text-embedding-ada-002'
            assert config.openai_entity_detection_model == 'gpt-4o-mini'
            assert config.openai_query_model == 'gpt-4o'
            assert config.graph_rag_context_window == 20
            assert config.file_watcher_debounce_seconds == 2
            assert config.file_watcher_max_note_size_mb == 5
            assert config.file_watcher_batch_size == 100

    def test_config_validation_success(self):
        """Test that config validation passes with required fields."""
        with patch.dict(os.environ, {
            'NEO4J_URI': 'bolt://localhost:7687',
            'NEO4J_USER': 'neo4j',
            'NEO4J_PASSWORD': 'password',
            'OPENAI_API_KEY': 'test-key',
            'OBSIDIAN_VAULT_PATH': '/tmp/test-vault'
        }):
            config = Config()
            config.validate()  # Should not raise any exception

    def test_config_validation_missing_neo4j_uri(self):
        """Test that config validation fails when Neo4j URI is missing."""
        with patch.dict(os.environ, {
            'NEO4J_USER': 'neo4j',
            'NEO4J_PASSWORD': 'password',
            'OPENAI_API_KEY': 'test-key',
            'OBSIDIAN_VAULT_PATH': '/tmp/test-vault'
        }):
            config = Config()
            with pytest.raises(ValueError, match="Neo4j URI is required"):
                config.validate()

    def test_config_validation_missing_neo4j_credentials(self):
        """Test that config validation fails when Neo4j credentials are missing."""
        with patch.dict(os.environ, {
            'NEO4J_URI': 'bolt://localhost:7687',
            'OPENAI_API_KEY': 'test-key',
            'OBSIDIAN_VAULT_PATH': '/tmp/test-vault'
        }):
            config = Config()
            with pytest.raises(ValueError, match="Neo4j credentials are required"):
                config.validate()

    def test_validation_missing_openai_key(self, mock_env):
        """Test validation fails when OpenAI API key is missing."""
        mock_env.pop("OPENAI_API_KEY", None)
        
        with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
            Config.validate()

    def test_config_validation_missing_vault_path(self, mock_env):
        """Test validation fails when Obsidian vault path is missing."""
        mock_env.pop("OBSIDIAN_VAULT_PATH", None)
        
        with pytest.raises(ValueError, match="OBSIDIAN_VAULT_PATH is required"):
            Config.validate()

    def test_config_aura_prefix_priority(self):
        """Test that AuraDB environment variables take priority over Neo4j ones."""
        with patch.dict(os.environ, {
            'NEO4J_URI': 'bolt://localhost:7687',
            'NEO4J_USER': 'neo4j',
            'NEO4J_PASSWORD': 'password',
            'AURA_URI': 'neo4j+s://test.neo4j.io',
            'AURA_USER': 'aura-user',
            'AURA_PASSWORD': 'aura-pass',
            'OPENAI_API_KEY': 'test-key',
            'OBSIDIAN_VAULT_PATH': '/tmp/test-vault'
        }):
            config = Config()
            
            assert config.neo4j_uri == 'neo4j+s://test.neo4j.io'
            assert config.neo4j_user == 'aura-user'
            assert config.neo4j_password == 'aura-pass'

    def test_config_integer_parsing(self):
        """Test that integer environment variables are parsed correctly."""
        with patch.dict(os.environ, {
            'NEO4J_URI': 'bolt://localhost:7687',
            'NEO4J_USER': 'neo4j',
            'NEO4J_PASSWORD': 'password',
            'OPENAI_API_KEY': 'test-key',
            'OBSIDIAN_VAULT_PATH': '/tmp/test-vault',
            'GRAPH_RAG_CONTEXT_WINDOW': '50',
            'FILE_WATCHER_DEBOUNCE_SECONDS': '5',
            'FILE_WATCHER_MAX_NOTE_SIZE_MB': '25',
            'FILE_WATCHER_BATCH_SIZE': '200'
        }):
            config = Config()
            
            assert config.graph_rag_context_window == 50
            assert config.file_watcher_debounce_seconds == 5
            assert config.file_watcher_max_note_size_mb == 25
            assert config.file_watcher_batch_size == 200

    def test_config_invalid_integer_parsing(self):
        """Test that invalid integer environment variables fall back to defaults."""
        with patch.dict(os.environ, {
            'NEO4J_URI': 'bolt://localhost:7687',
            'NEO4J_USER': 'neo4j',
            'NEO4J_PASSWORD': 'password',
            'OPENAI_API_KEY': 'test-key',
            'OBSIDIAN_VAULT_PATH': '/tmp/test-vault',
            'GRAPH_RAG_CONTEXT_WINDOW': 'invalid',
            'FILE_WATCHER_DEBOUNCE_SECONDS': 'not-a-number'
        }):
            config = Config()
            
            assert config.graph_rag_context_window == 20  # Default
            assert config.file_watcher_debounce_seconds == 2  # Default 

    def test_neo4j_config(self, mock_env):
        """Test Neo4j configuration retrieval."""
        config = Config.get_neo4j_config()
        
        assert config["uri"] == "neo4j://test:7687"
        assert config["user"] == "test-user"
        assert config["password"] == "test-pass"
        assert config["database"] == "test-db" 

    def test_aura_config(self, mock_env):
        """Test AuraDB configuration retrieval."""
        config = Config.get_neo4j_config()
        
        assert config["uri"] == "neo4j+ssc://test-aura:7687"
        assert config["user"] == "test-aura-user"
        assert config["password"] == "test-aura-pass"
        assert config["database"] == "test-aura-db" 