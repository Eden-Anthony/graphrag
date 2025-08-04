"""
Command-line interface for GraphRAG.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

from .core import KnowledgeGraph
from .indexer import ObsidianIndexer
from .query import ObsidianQueryEngine

console = Console()


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--uri', default='bolt://localhost:7687', help='Neo4j database URI')
@click.option('--username', default='neo4j', help='Neo4j username')
@click.option('--password', default='password', help='Neo4j password')
@click.pass_context
def main(ctx, verbose: bool, uri: str, username: str, password: str):
    """GraphRAG - A knowledge graph system for indexing and querying Obsidian vaults."""
    setup_logging(verbose)

    # Store configuration in context
    ctx.ensure_object(dict)
    ctx.obj['uri'] = uri
    ctx.obj['username'] = username
    ctx.obj['password'] = password


@main.command()
@click.argument('vault', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--clear', is_flag=True, help='Clear existing data before indexing')
@click.option('--recursive', is_flag=True, default=True, help='Index subdirectories recursively')
@click.pass_context
def index(ctx, vault: str, clear: bool, recursive: bool):
    """Index an Obsidian vault into the knowledge graph."""
    console.print(f"[bold blue]Indexing Obsidian vault: {vault}[/bold blue]")

    # Initialize knowledge graph
    kg = KnowledgeGraph(
        uri=ctx.obj['uri'],
        username=ctx.obj['username'],
        password=ctx.obj['password']
    )

    try:
        # Connect to Neo4j
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Connecting to Neo4j...", total=None)

            if not kg.connect():
                console.print(
                    "[red]Failed to connect to Neo4j. Please check your connection settings.[/red]")
                sys.exit(1)

            progress.update(task, description="Connected to Neo4j")

        # Clear database if requested
        if clear:
            if Confirm.ask("Are you sure you want to clear all existing data?"):
                console.print("[yellow]Clearing existing data...[/yellow]")
                kg.clear_database()
                kg.create_constraints()

        # Initialize indexer and query engine
        indexer = ObsidianIndexer(kg)

        # Index the vault
        console.print(f"[green]Starting to index: {vault}[/green]")
        stats = indexer.index_vault(vault, recursive=recursive)

        # Display results
        table = Table(title="Indexing Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="magenta")

        table.add_row("Folders Processed", str(stats['folders_processed']))
        table.add_row("Notes Processed", str(stats['notes_processed']))
        table.add_row("Notes Skipped", str(stats['notes_skipped']))
        table.add_row("Errors", str(stats['errors']))
        table.add_row("Total Internal Links", str(stats['total_links']))
        table.add_row("Total Tags", str(stats['total_tags']))
        table.add_row("Total Headers", str(stats['total_headers']))

        console.print(table)

        # Show database info
        info = kg.get_database_info()

        info_table = Table(title="Database Information")
        info_table.add_column("Node Type", style="cyan")
        info_table.add_column("Count", style="magenta")

        for node_type, count in info['node_counts'].items():
            info_table.add_row(node_type, str(count))

        console.print(info_table)

    except Exception as e:
        console.print(f"[red]Error during indexing: {e}[/red]")
        sys.exit(1)
    finally:
        kg.disconnect()


@main.command()
@click.option('--query', '-q', help='Search query for note content')
@click.option('--tag', '-t', help='Filter by tag')
@click.option('--folder', '-f', help='Filter by folder path')
@click.option('--limit', '-l', default=10, help='Maximum number of results')
@click.pass_context
def search(ctx, query: Optional[str], tag: Optional[str], folder: Optional[str], limit: int):
    """Search the Obsidian knowledge graph."""
    if not query and not tag and not folder:
        console.print(
            "[red]Please provide a search query (--query), tag (--tag), or folder (--folder)[/red]")
        sys.exit(1)

    # Initialize knowledge graph and query engine
    kg = KnowledgeGraph(
        uri=ctx.obj['uri'],
        username=ctx.obj['username'],
        password=ctx.obj['password']
    )

    try:
        if not kg.connect():
            console.print("[red]Failed to connect to Neo4j.[/red]")
            sys.exit(1)

        query_engine = ObsidianQueryEngine(kg)

        if query:
            console.print(f"[bold blue]Searching for: {query}[/bold blue]")
            results = query_engine.search_notes_by_content(query, limit)

            if results:
                table = Table(title=f"Search Results for '{query}'")
                table.add_column("Note", style="cyan")
                table.add_column("Title", style="green")
                table.add_column("Content Preview", style="yellow")

                for result in results:
                    content_preview = result['content'][:100] + "..." if len(
                        result['content']) > 100 else result['content']
                    table.add_row(result['path'],
                                  result['title'], content_preview)

                console.print(table)
            else:
                console.print(
                    "[yellow]No notes found matching the query.[/yellow]")

        if tag:
            console.print(
                f"[bold blue]Finding notes with tag: {tag}[/bold blue]")
            results = query_engine.find_notes_by_tag(tag)

            if results:
                table = Table(title=f"Notes with tag '{tag}'")
                table.add_column("Note", style="cyan")
                table.add_column("Title", style="green")
                table.add_column("Modified", style="yellow")

                for result in results[:limit]:
                    table.add_row(
                        result['path'], result['title'], str(result['modified']))

                console.print(table)
            else:
                console.print(
                    f"[yellow]No notes found with tag '{tag}'.[/yellow]")

        if folder:
            console.print(
                f"[bold blue]Finding notes in folder: {folder}[/bold blue]")
            results = query_engine.find_notes_by_folder(folder)

            if results:
                table = Table(title=f"Notes in folder '{folder}'")
                table.add_column("Note", style="cyan")
                table.add_column("Title", style="green")
                table.add_column("Modified", style="yellow")

                for result in results[:limit]:
                    table.add_row(
                        result['path'], result['title'], str(result['modified']))

                console.print(table)
            else:
                console.print(
                    f"[yellow]No notes found in folder '{folder}'.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error during search: {e}[/red]")
        sys.exit(1)
    finally:
        kg.disconnect()


@main.command()
@click.option('--limit', '-l', default=10, help='Maximum number of results')
@click.pass_context
def stats(ctx, limit: int):
    """Show vault statistics."""
    kg = KnowledgeGraph(
        uri=ctx.obj['uri'],
        username=ctx.obj['username'],
        password=ctx.obj['password']
    )

    try:
        if not kg.connect():
            console.print("[red]Failed to connect to Neo4j.[/red]")
            sys.exit(1)

        query_engine = ObsidianQueryEngine(kg)
        stats = query_engine.get_vault_statistics()

        # Note statistics
        note_stats = stats['note_statistics']
        note_table = Table(title="Note Statistics")
        note_table.add_column("Metric", style="cyan")
        note_table.add_column("Value", style="magenta")

        note_table.add_row("Total Notes", str(note_stats['total_notes']))
        note_table.add_row(
            "Total Size", f"{note_stats['total_size'] / (1024*1024):.2f} MB")
        note_table.add_row("Average Note Size",
                           f"{note_stats['avg_note_size'] / 1024:.2f} KB")
        note_table.add_row(
            "Largest Note", f"{note_stats['max_note_size'] / (1024*1024):.2f} MB")
        note_table.add_row(
            "Smallest Note", f"{note_stats['min_note_size']} bytes")

        console.print(note_table)

        # Tag statistics
        tag_stats = stats['tag_statistics']
        tag_table = Table(title="Tag Statistics")
        tag_table.add_column("Metric", style="cyan")
        tag_table.add_column("Value", style="magenta")

        tag_table.add_row("Total Tags", str(tag_stats['total_tags']))

        console.print(tag_table)

        # Link statistics
        link_stats = stats['link_statistics']
        external_link_stats = stats['external_link_statistics']
        link_table = Table(title="Link Statistics")
        link_table.add_column("Metric", style="cyan")
        link_table.add_column("Value", style="magenta")

        link_table.add_row("Internal Links", str(
            link_stats['total_internal_links']))
        link_table.add_row("External Links", str(
            external_link_stats['total_external_links']))

        console.print(link_table)

        # Most used tags
        most_used_tags = query_engine.find_most_used_tags(limit)
        if most_used_tags:
            tag_usage_table = Table(title="Most Used Tags")
            tag_usage_table.add_column("Tag", style="cyan")
            tag_usage_table.add_column("Usage Count", style="magenta")

            for tag_info in most_used_tags:
                tag_usage_table.add_row(
                    tag_info['tag_name'], str(tag_info['usage_count']))

            console.print(tag_usage_table)

    except Exception as e:
        console.print(f"[red]Error getting statistics: {e}[/red]")
        sys.exit(1)
    finally:
        kg.disconnect()


@main.command()
@click.option('--limit', '-l', default=10, help='Maximum number of results')
@click.pass_context
def most_linked(ctx, limit: int):
    """Find the most linked notes in the vault."""
    kg = KnowledgeGraph(
        uri=ctx.obj['uri'],
        username=ctx.obj['username'],
        password=ctx.obj['password']
    )

    try:
        if not kg.connect():
            console.print("[red]Failed to connect to Neo4j.[/red]")
            sys.exit(1)

        query_engine = ObsidianQueryEngine(kg)
        results = query_engine.find_most_linked_notes(limit)

        if results:
            table = Table(title="Most Linked Notes")
            table.add_column("Note Name", style="cyan")
            table.add_column("Link Count", style="magenta")

            for result in results:
                table.add_row(result['note_name'], str(result['link_count']))

            console.print(table)
        else:
            console.print("[yellow]No notes found.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error finding most linked notes: {e}[/red]")
        sys.exit(1)
    finally:
        kg.disconnect()


@main.command()
@click.argument('note_path')
@click.pass_context
def info(ctx, note_path: str):
    """Get detailed information about a specific note."""
    kg = KnowledgeGraph(
        uri=ctx.obj['uri'],
        username=ctx.obj['username'],
        password=ctx.obj['password']
    )

    try:
        if not kg.connect():
            console.print("[red]Failed to connect to Neo4j.[/red]")
            sys.exit(1)

        query_engine = ObsidianQueryEngine(kg)
        details = query_engine.get_note_details(note_path)

        if not details:
            console.print(f"[red]Note not found: {note_path}[/red]")
            sys.exit(1)

        # Note info
        note_info = details['note_info']
        info_table = Table(title=f"Note Information: {note_path}")
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="magenta")

        info_table.add_row("Title", note_info['title'])
        info_table.add_row("Size", f"{note_info['size'] / 1024:.2f} KB")
        info_table.add_row("Modified", str(note_info['modified']))

        console.print(info_table)

        # Tags
        if details['tags']:
            tag_table = Table(title="Tags")
            tag_table.add_column("Tag", style="cyan")

            for tag in details['tags']:
                tag_table.add_row(tag)

            console.print(tag_table)

        # Internal links
        if details['internal_links']:
            link_table = Table(title="Internal Links")
            link_table.add_column("Link", style="cyan")

            for link in details['internal_links']:
                link_table.add_row(link)

            console.print(link_table)

        # External links
        if details['external_links']:
            external_table = Table(title="External Links")
            external_table.add_column("Text", style="cyan")
            external_table.add_column("URL", style="green")

            for link in details['external_links']:
                external_table.add_row(link['text'], link['url'])

            console.print(external_table)

        # Headers
        if details['headers']:
            header_table = Table(title="Headers")
            header_table.add_column("Level", style="cyan")
            header_table.add_column("Title", style="green")

            for header in details['headers']:
                header_table.add_row(str(header['level']), header['title'])

            console.print(header_table)

    except Exception as e:
        console.print(f"[red]Error getting note info: {e}[/red]")
        sys.exit(1)
    finally:
        kg.disconnect()


@main.command()
@click.option('--query', '-q', required=True, help='Custom Cypher query to execute')
@click.pass_context
def query(ctx, query: str):
    """Execute a custom Cypher query."""
    kg = KnowledgeGraph(
        uri=ctx.obj['uri'],
        username=ctx.obj['username'],
        password=ctx.obj['password']
    )

    try:
        if not kg.connect():
            console.print("[red]Failed to connect to Neo4j.[/red]")
            sys.exit(1)

        query_engine = ObsidianQueryEngine(kg)
        results = query_engine.search_by_custom_query(query)

        if results:
            # Create a dynamic table based on the first result
            if results:
                columns = list(results[0].keys())
                table = Table(title="Query Results")

                for col in columns:
                    table.add_column(col, style="cyan")

                for result in results:
                    row = [str(result.get(col, '')) for col in columns]
                    table.add_row(*row)

                console.print(table)
            else:
                console.print("[yellow]No results found.[/yellow]")
        else:
            console.print("[yellow]No results found.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error executing query: {e}[/red]")
        sys.exit(1)
    finally:
        kg.disconnect()


@main.command()
@click.option('--format', '-f', type=click.Choice(['cypher', 'json', 'csv', 'graphml']), default='cypher', help='Export format')
@click.option('--output', '-o', help='Output file path (optional)')
@click.option('--query', '-q', help='Custom query to visualize (optional)')
@click.pass_context
def visualize(ctx, format: str, output: Optional[str], query: Optional[str]):
    """Export knowledge graph for visualization."""
    kg = KnowledgeGraph(
        uri=ctx.obj['uri'],
        username=ctx.obj['username'],
        password=ctx.obj['password']
    )

    try:
        if not kg.connect():
            console.print("[red]Failed to connect to Neo4j.[/red]")
            sys.exit(1)

        # Default query to get a good overview of the graph
        if not query:
            query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT 100
            """

        console.print(
            f"[bold blue]Exporting knowledge graph in {format.upper()} format...[/bold blue]")

        if format == 'cypher':
            # Export as Cypher queries for Neo4j Browser
            if not output:
                output = 'graphrag_export.cypher'

            with open(output, 'w') as f:
                f.write("// GraphRAG Knowledge Graph Export\n")
                f.write("// Generated for visualization in Neo4j Browser\n\n")
                f.write("// Clear existing data (optional)\n")
                f.write("// MATCH (n) DETACH DELETE n;\n\n")
                f.write("// Query to visualize the graph:\n")
                f.write(f"// {query.strip()}\n\n")
                f.write("// Alternative visualization queries:\n")
                f.write(
                    "// MATCH (n:Note) OPTIONAL MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50\n")
                f.write(
                    "// MATCH (f:Folder)-[:CONTAINS]->(n:Note) RETURN f, n\n")
                f.write("// MATCH (n:Note)-[:HAS_TAG]->(t:Tag) RETURN n, t\n")
                f.write(
                    "// MATCH (n1:Note)-[:LINKS_TO]->(l:InternalLink)<-[:LINKS_TO]-(n2:Note) WHERE n1 <> n2 RETURN n1, l, n2 LIMIT 20\n")

            console.print(
                f"[green]Cypher queries exported to: {output}[/green]")
            console.print(
                f"[yellow]Open Neo4j Browser at http://localhost:7474 and run the queries from {output}[/yellow]")

        elif format == 'json':
            # Export as JSON for external tools
            if not output:
                output = 'graphrag_export.json'

            query_engine = ObsidianQueryEngine(kg)
            results = query_engine.search_by_custom_query(query)

            import json
            with open(output, 'w') as f:
                json.dump(results, f, indent=2, default=str)

            console.print(f"[green]JSON data exported to: {output}[/green]")
            console.print(
                f"[yellow]You can use this file with tools like D3.js, Gephi, or other graph visualization libraries[/yellow]")

        elif format == 'csv':
            # Export as CSV for spreadsheet tools
            if not output:
                output = 'graphrag_export.csv'

            query_engine = ObsidianQueryEngine(kg)
            results = query_engine.search_by_custom_query(query)

            if results:
                import csv
                with open(output, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)

                console.print(f"[green]CSV data exported to: {output}[/green]")
                console.print(
                    f"[yellow]You can import this into Excel, Google Sheets, or other data analysis tools[/yellow]")

        elif format == 'graphml':
            # Export as GraphML for Gephi and other graph tools
            if not output:
                output = 'graphrag_export.graphml'

            console.print(
                "[yellow]GraphML export not yet implemented. Use 'cypher' format for Neo4j Browser instead.[/yellow]")
            console.print(
                "[yellow]Or use 'json' format and convert with external tools.[/yellow]")

        # Show Neo4j Browser instructions
        console.print("\n[bold cyan]Visualization Options:[/bold cyan]")
        console.print(
            "1. [bold]Neo4j Browser[/bold]: Open http://localhost:7474")
        console.print("   - Username: neo4j")
        console.print("   - Password: password")
        console.print("   - Run the exported Cypher queries")
        console.print(
            "2. [bold]External Tools[/bold]: Use the exported data with:")
        console.print("   - Gephi (https://gephi.org/)")
        console.print("   - D3.js (https://d3js.org/)")
        console.print("   - NetworkX + Matplotlib (Python)")
        console.print("   - Cytoscape (https://cytoscape.org/)")

    except Exception as e:
        console.print(f"[red]Error during export: {e}[/red]")
        sys.exit(1)
    finally:
        kg.disconnect()


if __name__ == '__main__':
    main()
