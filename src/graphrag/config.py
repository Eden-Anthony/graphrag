"""Configuration management for the GraphRAG system."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the GraphRAG system."""

    # Neo4j Configuration
    NEO4J_URI: str = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")

    # AuraDB Configuration (alternative to Neo4j)
    AURA_URI: Optional[str] = os.getenv("AURA_URI")
    AURA_USER: Optional[str] = os.getenv("AURA_USER")
    AURA_PASSWORD: Optional[str] = os.getenv("AURA_PASSWORD")
    AURA_DATABASE: str = os.getenv("AURA_DATABASE", "neo4j")

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL_ENTITY_DETECTION: str = os.getenv(
        "OPENAI_MODEL_ENTITY_DETECTION", "gpt-4o-mini")
    OPENAI_MODEL_QUERY: str = os.getenv("OPENAI_MODEL_QUERY", "gpt-4o")

    # GraphRAG Configuration
    VECTOR_INDEX_NAME: str = os.getenv(
        "VECTOR_INDEX_NAME", "noteContentEmbedding")
    FULLTEXT_INDEX_NAME: str = os.getenv("FULLTEXT_INDEX_NAME", "noteFulltext")
    CONTEXT_WINDOW_SIZE: int = int(os.getenv("CONTEXT_WINDOW_SIZE", "20"))

    # File Watching Configuration
    OBSIDIAN_VAULT_PATH: str = os.getenv("OBSIDIAN_VAULT_PATH", "")
    IGNORE_PATTERNS: list = os.getenv(
        "IGNORE_PATTERNS", "⭕Meta/**,.git/**,.obsidian/**").split(",")

    # Processing Configuration
    MAX_NOTE_SIZE: int = int(os.getenv("MAX_NOTE_SIZE", "100000"))  # 100KB
    ENTITY_DETECTION_BATCH_SIZE: int = int(
        os.getenv("ENTITY_DETECTION_BATCH_SIZE", "5"))

    @classmethod
    def get_neo4j_config(cls) -> dict:
        """Get Neo4j connection configuration."""
        if cls.AURA_URI and cls.AURA_USER and cls.AURA_PASSWORD:
            return {
                "uri": cls.AURA_URI,
                "user": cls.AURA_USER,
                "password": cls.AURA_PASSWORD,
                "database": cls.AURA_DATABASE,
            }
        else:
            return {
                "uri": cls.NEO4J_URI,
                "user": cls.NEO4J_USER,
                "password": cls.NEO4J_PASSWORD,
                "database": cls.NEO4J_DATABASE,
            }

    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")

        if not cls.OBSIDIAN_VAULT_PATH:
            raise ValueError("OBSIDIAN_VAULT_PATH is required")

        vault_path = Path(cls.OBSIDIAN_VAULT_PATH)
        if not vault_path.exists():
            raise ValueError(
                f"OBSIDIAN_VAULT_PATH does not exist: {cls.OBSIDIAN_VAULT_PATH}")

        return True
