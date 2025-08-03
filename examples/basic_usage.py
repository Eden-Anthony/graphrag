#!/usr/bin/env python3
"""
Basic usage example for GraphRAG.

This script demonstrates how to use GraphRAG programmatically to index a directory
and perform various queries on the knowledge graph.
"""

from graphrag import KnowledgeGraph, FileIndexer, QueryEngine
import os
import sys
from pathlib import Path

# Add the src directory to the path so we can import graphrag
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main():
    """Demonstrate basic GraphRAG usage."""

    # Configuration
    neo4j_uri = "bolt://localhost:7687"
    neo4j_username = "neo4j"
    neo4j_password = "password"

    # Directory to index (use current directory as example)
    directory_to_index = "."

    print("🚀 GraphRAG Basic Usage Example")
    print("=" * 50)

    # Initialize the knowledge graph
    print("📡 Connecting to Neo4j...")
    kg = KnowledgeGraph(
        uri=neo4j_uri, username=neo4j_username, password=neo4j_password)

    if not kg.connect():
        print("❌ Failed to connect to Neo4j. Please ensure Neo4j is running.")
        return

    print("✅ Connected to Neo4j successfully!")

    try:
        # Create constraints for better performance
        print("🔧 Creating database constraints...")
        kg.create_constraints()

        # Initialize indexer and query engine
        indexer = FileIndexer(kg)
        query_engine = QueryEngine(kg)

        # Index the directory
        print(f"📁 Indexing directory: {directory_to_index}")
        stats = indexer.index_directory(directory_to_index)

        print("\n📊 Indexing Results:")
        print(f"  - Directories processed: {stats['directories_processed']}")
        print(f"  - Files processed: {stats['files_processed']}")
        print(f"  - Files skipped: {stats['files_skipped']}")
        print(f"  - Errors: {stats['errors']}")

        # Get codebase statistics
        print("\n📈 Codebase Statistics:")
        codebase_stats = query_engine.get_codebase_statistics()

        file_stats = codebase_stats['file_statistics']
        print(f"  - Total files: {file_stats['total_files']}")
        print(
            f"  - Total size: {file_stats['total_size'] / (1024*1024):.2f} MB")
        print(
            f"  - Average file size: {file_stats['avg_file_size'] / 1024:.2f} KB")

        code_stats = codebase_stats['code_statistics']
        print(f"  - Functions: {code_stats['function_count']}")
        print(f"  - Classes: {code_stats['class_count']}")
        print(
            f"  - Imported modules: {codebase_stats['import_statistics']['total_modules']}")

        # Search for files containing specific content
        print("\n🔍 Searching for files containing 'def main':")
        search_results = query_engine.search_files_by_content(
            "def main", limit=5)

        if search_results:
            for result in search_results:
                print(f"  - {result['path']} ({result['name']})")
        else:
            print("  No files found containing 'def main'")

        # Find Python files
        print("\n🐍 Finding Python files:")
        python_files = query_engine.find_files_by_extension("py")

        if python_files:
            for file_info in python_files[:5]:  # Show first 5
                size_mb = file_info['size'] / \
                    (1024 * 1024) if file_info['size'] else 0
                print(f"  - {file_info['path']} ({size_mb:.2f} MB)")
        else:
            print("  No Python files found")

        # Find largest files
        print("\n📏 Largest files:")
        largest_files = query_engine.find_largest_files(limit=5)

        if largest_files:
            for file_info in largest_files:
                size_mb = file_info['size'] / \
                    (1024 * 1024) if file_info['size'] else 0
                print(f"  - {file_info['path']} ({size_mb:.2f} MB)")
        else:
            print("  No files found")

        # Find duplicate files
        print("\n🔄 Duplicate files:")
        duplicates = query_engine.find_duplicate_files()

        if duplicates:
            for dup in duplicates[:3]:  # Show first 3 groups
                print(
                    f"  - Hash: {dup['hash'][:16]}... ({dup['count']} files)")
                for file_path in dup['file_paths'][:3]:  # Show first 3 files
                    print(f"    * {file_path}")
        else:
            print("  No duplicate files found")

        # Custom query example
        print("\n🔧 Custom query - Files with most imports:")
        custom_results = query_engine.search_by_custom_query("""
            MATCH (f:File)-[:IMPORTS]->(m:ImportedModule)
            RETURN f.name as file_name, count(m) as import_count
            ORDER BY import_count DESC
            LIMIT 5
        """)

        if custom_results:
            for result in custom_results:
                print(
                    f"  - {result['file_name']}: {result['import_count']} imports")
        else:
            print("  No results found")

        print("\n✅ Example completed successfully!")

    except Exception as e:
        print(f"❌ Error during execution: {e}")

    finally:
        # Clean up
        kg.disconnect()
        print("🔌 Disconnected from Neo4j")


if __name__ == "__main__":
    main()
