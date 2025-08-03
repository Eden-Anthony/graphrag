#!/usr/bin/env python3
"""
Test script to verify GraphRAG installation and dependencies.
"""

import sys
from pathlib import Path


def test_imports():
    """Test that all required packages can be imported."""
    print("🔍 Testing imports...")

    try:
        import neo4j
        print(f"✅ neo4j {neo4j.__version__}")
    except ImportError as e:
        print(f"❌ neo4j: {e}")
        return False

    try:
        import click
        print(f"✅ click {click.__version__}")
    except ImportError as e:
        print(f"❌ click: {e}")
        return False

    try:
        import magic
        print("✅ python-magic")
    except ImportError as e:
        print(f"❌ python-magic: {e}")
        return False

    try:
        import chardet
        print(f"✅ chardet {chardet.__version__}")
    except ImportError as e:
        print(f"❌ chardet: {e}")
        return False

    try:
        import rich
        print(f"✅ rich {rich.__version__}")
    except ImportError as e:
        print(f"❌ rich: {e}")
        return False

    try:
        import tqdm
        print(f"✅ tqdm {tqdm.__version__}")
    except ImportError as e:
        print(f"❌ tqdm: {e}")
        return False

    return True


def test_graphrag_import():
    """Test that GraphRAG can be imported."""
    print("\n🔍 Testing GraphRAG import...")

    # Add src to path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))

    try:
        from graphrag import KnowledgeGraph, FileIndexer, QueryEngine
        print("✅ GraphRAG modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ GraphRAG import failed: {e}")
        return False


def test_neo4j_connection():
    """Test Neo4j connection (optional)."""
    print("\n🔍 Testing Neo4j connection...")

    try:
        from graphrag import KnowledgeGraph

        kg = KnowledgeGraph()
        if kg.connect():
            print("✅ Neo4j connection successful")
            kg.disconnect()
            return True
        else:
            print("⚠️  Neo4j connection failed (this is normal if Neo4j is not running)")
            return True  # Don't fail the test for this
    except Exception as e:
        print(f"⚠️  Neo4j connection test failed: {e}")
        return True  # Don't fail the test for this


def main():
    """Run all tests."""
    print("🚀 GraphRAG Installation Test")
    print("=" * 40)

    # Test imports
    if not test_imports():
        print("\n❌ Some dependencies are missing. Please install them:")
        print("uv sync")
        sys.exit(1)

    # Test GraphRAG import
    if not test_graphrag_import():
        print("\n❌ GraphRAG import failed. Check the installation.")
        sys.exit(1)

    # Test Neo4j connection
    test_neo4j_connection()

    print("\n✅ All tests passed! GraphRAG is ready to use.")
    print("\n📖 Next steps:")
    print("1. Start Neo4j database")
    print("2. Run: graphrag index /path/to/your/codebase")
    print("3. Run: graphrag search --query 'your search term'")


if __name__ == "__main__":
    main()
