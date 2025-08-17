#!/usr/bin/env python3
"""
Digital Asset Inventory Manager - Main CLI Interface
Version 2.0.0
"""

import click
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Import from local modules
from .config import settings, ensure_user_directories, show_user_paths
from .auth_selenium import HumbleBundleAuthSelenium
from .working_metadata_sync import WorkingMetadataSync
from .enhanced_sync import EnhancedHumbleBundleSync
from .database import AssetInventoryDatabase
from .search_provider import SearchProvider
from .duckdb_search_provider import DuckDBSearchProvider

console = Console()

@click.group(invoke_without_command=True)
@click.version_option(version="2.0.0")
@click.option('--show-paths', is_flag=True, help='Show file locations and exit')
@click.pass_context
def cli(ctx, show_paths: bool):
    """Digital Asset Inventory Manager
    
    Synchronize digital assets from multiple sources to a local DuckDB database
    for efficient querying and management.
    
    Features enhanced metadata extraction with HAR analysis insights,
    confidence scoring, and subscription content detection.
    
    Advanced search capabilities with regex support, field-specific searching,
    and multi-field queries with AND/OR operators.
    """
    # Ensure user directories exist
    ensure_user_directories()
    
    if show_paths:
        show_user_paths()
        return
    
    # If no command and no show-paths flag, show help
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())

@cli.command()
@click.option('--email', '-e', help='Humble Bundle email')
@click.option('--password', '-p', help='Humble Bundle password (will prompt if not provided)')
@click.option('--save', is_flag=True, help='Save credentials to .env file')
@click.option('--force-new', is_flag=True, help='Force new login even if session exists')
def login(email: Optional[str], password: Optional[str], save: bool, force_new: bool):
    """Login to Humble Bundle and test authentication."""
    # Use config values if not provided as arguments
    if not email:
        email = settings.humble_email
        if not email:
            email = click.prompt('Humble Bundle email')
    
    if not password:
        password = settings.humble_password
        if not password:
            password = click.prompt('Humble Bundle password', hide_input=True)
    
    auth = HumbleBundleAuthSelenium(headless=True)  # Run headless for login
    
    # Check for existing session first
    if not force_new and auth.has_valid_session():
        console.print("📋 Found existing session", style="blue")
        if click.confirm("Use existing session?"):
            console.print("✅ Using existing session", style="green")
            return
        else:
            console.print("🔄 Proceeding with new login", style="yellow")
    
    console.print("🔄 Starting login process...", style="green")
    success = auth.login()
    
    if success:
        console.print("✅ Login successful!", style="green")
        
        if save:
            env_path = settings.user_config_dir / ".env"
            # Read existing content if file exists
            existing_content = ""
            if env_path.exists():
                existing_content = env_path.read_text()
            
            # Check if credentials already exist
            has_email = "HUMBLE_EMAIL=" in existing_content
            has_password = "HUMBLE_PASSWORD=" in existing_content
            
            # Only add if not already present
            new_lines = []
            if not has_email:
                new_lines.append(f"HUMBLE_EMAIL={email}")
            if not has_password:
                new_lines.append(f"HUMBLE_PASSWORD={password}")
            
            if new_lines:
                with open(env_path, 'a') as f:
                    if existing_content and not existing_content.endswith('\n'):
                        f.write('\n')
                    f.write('\n'.join(new_lines) + '\n')
                console.print(f"💾 Credentials saved to {env_path}", style="blue")
            else:
                console.print(f"💾 Credentials already exist in {env_path}", style="blue")
    else:
        console.print("❌ Login failed!", style="red")
        raise click.Abort()

@cli.command()
def logout():
    """Logout and clear saved session."""
    try:
        with HumbleBundleAuthSelenium() as auth:
            auth.logout()
        console.print("👋 Logged out successfully!", style="green")
    except Exception as e:
        console.print(f"❌ Logout failed: {e}", style="red")

@cli.command()
def session():
    """Show current session status."""
    try:
        with HumbleBundleAuthSelenium() as auth:
            if auth.has_valid_session():
                console.print("📋 Session is valid and active", style="green")
                console.print("   Use 'sync' command to synchronize your library", style="blue")
            else:
                console.print("📋 No valid session found", style="yellow")
                console.print("   Use 'login' command to authenticate", style="blue")
    except Exception as e:
        console.print(f"❌ Error checking session: {e}", style="red")

@cli.command()
@click.option('--force', '-f', is_flag=True, help='Force sync even if not needed')
@click.option('--enhanced', '-e', is_flag=True, default=True, help='Use enhanced sync with HAR insights (default)')
@click.option('--legacy', '-l', is_flag=True, help='Use legacy working metadata sync')
def sync(force: bool, enhanced: bool, legacy: bool):
    """Synchronize Humble Bundle library with database."""
    # Legacy flag overrides enhanced
    if legacy:
        enhanced = False
    
    sync_type = "Enhanced" if enhanced else "Legacy"
    console.print(f"🚀 Starting {sync_type} Humble Bundle metadata synchronization...", style="blue")
    
    try:
        with HumbleBundleAuthSelenium(headless=True) as auth:
            # Try to use existing session first
            if not force and auth.has_valid_session():
                console.print("📋 Using existing session", style="blue")
            else:
                console.print("🔄 Authenticating...", style="blue")
                if not auth.login():
                    console.print("❌ Authentication failed", style="red")
                    raise click.Abort()
                console.print("✅ Authentication successful!", style="green")
            
            with AssetInventoryDatabase() as db:
                if enhanced:
                    # Use enhanced sync with HAR insights
                    sync = EnhancedHumbleBundleSync(auth, db)
                    console.print("🚀 Starting enhanced metadata sync with HAR insights...", style="blue")
                    results = sync.sync_humble_bundle_enhanced()
                    
                    # Enhanced sync has additional metrics
                    console.print(f"   🎫 Subscription content: {results.get('subscription_items', 0)}")
                    console.print(f"   📥 Downloadable products: {results.get('downloadable_products', 0)}")
                else:
                    # Use legacy working metadata sync
                    sync = WorkingMetadataSync(auth, db)
                    console.print("📚 Starting legacy metadata sync...", style="blue")
                    results = sync.sync_humble_bundle_metadata()
                
                if results['status'] == 'success':
                    console.print(f"✅ Sync completed successfully!", style="green")
                elif results['status'] == 'partial':
                    console.print(f"⚠️  Sync completed with some errors", style="yellow")
                else:
                    console.print(f"❌ Sync failed", style="red")
                
                console.print(f"   📦 Products synced: {results['products_synced']}")
                console.print(f"   ❌ Products failed: {results['products_failed']}")
                console.print(f"   📚 Bundles synced: {results['bundles_synced']}")
                console.print(f"   ❌ Bundles failed: {results['bundles_failed']}")
                console.print(f"   ⏱️  Duration: {results['duration_ms']}ms")
                
                if results.get('error_log'):
                    console.print(f"\n⚠️  Errors encountered:", style="yellow")
                    console.print(results['error_log'], style="red")
        
    except Exception as e:
        console.print(f"❌ Sync failed: {e}", style="red")
        raise click.Abort()

@cli.command()
def status():
    """Show sync status and library statistics."""
    try:
        with AssetInventoryDatabase() as db:
            # Get last sync info
            last_sync = db.get_last_sync('humble_bundle')
            if last_sync:
                sync_panel = Panel(
                    f"[bold]Last Sync:[/bold] {last_sync['last_sync_timestamp']}\n"
                    f"[bold]Status:[/bold] {last_sync['sync_status']}\n"
                    f"[bold]Products Synced:[/bold] {last_sync['products_synced']}\n"
                    f"[bold]Products Failed:[/bold] {last_sync['products_failed']}\n"
                    f"[bold]Bundles Synced:[/bold] {last_sync['bundles_synced']}\n"
                    f"[bold]Bundles Failed:[/bold] {last_sync['bundles_failed']}",
                    title="Sync Status",
                    border_style="blue"
                )
            else:
                sync_panel = Panel(
                    "[yellow]No sync performed yet[/yellow]",
                    title="Sync Status",
                    border_style="yellow"
                )
            
            console.print(sync_panel)
            
            # Get library summary
            summary = db.get_library_summary()
            
            if summary:
                summary_table = Table(title="Library Summary", show_header=True)
                summary_table.add_column("Category", style="cyan")
                summary_table.add_column("Subcategory", style="blue")
                summary_table.add_column("Source", style="green")
                summary_table.add_column("Products", style="magenta")
                summary_table.add_column("Bundles", style="yellow")
                
                for item in summary[:10]:  # Show first 10
                    summary_table.add_row(
                        item['category'] or 'Unknown',
                        item['subcategory'] or 'General',
                        item['source_name'],
                        str(item['product_count']),
                        str(item['bundle_count'])
                    )
                
                console.print(summary_table)
            else:
                console.print("📚 No library data found", style="yellow")
                
    except Exception as e:
        console.print(f"❌ Error getting status: {e}", style="red")

def _format_search_results_json(results: List[Dict[str, Any]]) -> str:
    """Format search results as JSON."""
    import json
    from decimal import Decimal
    
    json_results = []
    for result in results:
        # Convert Decimal to float for JSON serialization
        rating = result['rating']
        if isinstance(rating, Decimal):
            rating = float(rating)
        
        json_result = {
            'name': result['human_name'],
            'category': result['category'] or 'Unknown',
            'subcategory': result.get('subcategory', 'Unknown'),
            'source': result['source_name'],
            'developer': result['developer'] or 'Unknown',
            'publisher': result.get('publisher', 'Unknown'),
            'rating': rating,
            'release_date': str(result['release_date']) if result['release_date'] else None,
            'tags': result.get('tags', []),
            'description': result.get('description', '')
        }
        json_results.append(json_result)
    
    return json.dumps(json_results, indent=2)


def _format_search_results_csv(results: List[Dict[str, Any]]) -> str:
    """Format search results as CSV."""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Name', 'Category', 'Subcategory', 'Source', 'Developer', 'Publisher', 'Rating', 'Release Date', 'Tags', 'Description'])
    
    # Write data
    for result in results:
        writer.writerow([
            result['human_name'],
            result['category'] or 'Unknown',
            result.get('subcategory', 'Unknown'),
            result['source_name'],
            result['developer'] or 'Unknown',
            result.get('publisher', 'Unknown'),
            result['rating'] or 'N/A',
            result['release_date'] or '',
            result.get('tags', ''),
            result.get('description', '')
        ])
    
    return output.getvalue()


def _format_search_results_tsv(results: List[Dict[str, Any]]) -> str:
    """Format search results as TSV."""
    output_lines = ['Name\tCategory\tSubcategory\tSource\tDeveloper\tPublisher\tRating\tRelease Date\tTags\tDescription']
    
    for result in results:
        output_lines.append(
            f"{result['human_name']}\t{result['category'] or 'Unknown'}\t{result.get('subcategory', 'Unknown')}\t"
            f"{result['source_name']}\t{result['developer'] or 'Unknown'}\t{result.get('publisher', 'Unknown')}\t"
            f"{result['rating'] or 'N/A'}\t{result['release_date'] or ''}\t{result.get('tags', '')}\t"
            f"{result.get('description', '')}"
        )
    
    return '\n'.join(output_lines)


def _format_search_results_table(results: List[Dict[str, Any]]) -> str:
    """Format search results as simple table."""
    output_lines = [f"# Advanced Search Results - {len(results)} items"]
    output_lines.append("Name\tCategory\tSubcategory\tSource\tDeveloper\tPublisher\tRating\tRelease Date\tTags\tDescription")
    
    for result in results:
        output_lines.append(
            f"{result['human_name']}\t{result['category'] or 'Unknown'}\t{result.get('subcategory', 'Unknown')}\t"
            f"{result['source_name']}\t{result['developer'] or 'Unknown'}\t{result.get('publisher', 'Unknown')}\t"
            f"{result['rating'] or 'N/A'}\t{result['release_date'] or ''}\t{result.get('tags', '')}\t"
            f"{result.get('description', '')}"
        )
    
    return '\n'.join(output_lines)


def _dump_search_results(results: List[Dict[str, Any]], format: str) -> None:
    """Dump search results in the specified format."""
    total_results = len(results)
    console.print(f"🔍 Dumping {total_results} assets from advanced search", style="green")
    
    if format == 'json':
        print(_format_search_results_json(results))
    elif format == 'csv':
        print(_format_search_results_csv(results))
    elif format == 'tsv':
        print(_format_search_results_tsv(results))
    else:  # table format
        print(_format_search_results_table(results))


def _display_paginated_results(results: List[Dict[str, Any]], page: int, page_size: int, 
                              query_dict: Dict[str, str], regex: bool, operator: str) -> None:
    """Display search results with pagination."""
    total_results = len(results)
    total_pages = (total_results + page_size - 1) // page_size
    
    # Validate page number
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages
    
    # Calculate start and end indices for current page
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_results)
    page_results = results[start_idx:end_idx]
    
    console.print(f"🔍 Found {total_results} assets from advanced search", style="green")
    console.print(f"📄 Showing page {page} of {total_pages} ({start_idx + 1}-{end_idx} of {total_results})", style="blue")
    
    # Show search criteria
    criteria_text = f"Queries: {', '.join([f'{k}:{v}' for k, v in query_dict.items()])}"
    if regex:
        criteria_text += f" (Regex, {operator})"
    else:
        criteria_text += f" (Text, {operator})"
    
    search_table = Table(title=f"Advanced Search Results - Page {page}/{total_pages}", show_header=True)
    search_table.add_column("#", style="dim")
    search_table.add_column("Name", style="cyan")
    search_table.add_column("Category", style="blue")
    search_table.add_column("Source", style="green")
    search_table.add_column("Developer", style="yellow")
    search_table.add_column("Rating", style="magenta")
    
    for i, result in enumerate(page_results, start=start_idx + 1):
        search_table.add_row(
            str(i),
            result['human_name'][:50] + ('...' if len(result['human_name']) > 50 else ''),
            result['category'] or 'Unknown',
            result['source_name'],
            result['developer'] or 'Unknown',
            str(result['rating']) if result['rating'] else 'N/A'
        )
    
    console.print(search_table)
    
    # Pagination controls
    if total_pages > 1:
        console.print(f"\n📖 Pagination:", style="yellow")
        
        # Previous page
        if page > 1:
            console.print(f"   ← Previous: python main.py search '{query_dict['query']}' --page {page - 1} --page-size {page_size}", style="blue")
        
        # Page numbers
        page_range = []
        for p in range(max(1, page - 2), min(total_pages + 1, page + 3)):
            if p == page:
                page_range.append(f"[bold]{p}[/bold]")
            else:
                page_range.append(str(p))
        
        console.print(f"   Pages: {' '.join(page_range)}", style="blue")
        
        # Next page
        if page < total_pages:
            console.print(f"   → Next: python main.py search '{query_dict['query']}' --page {page + 1} --page-size {page_size}", style="blue")
        
        # Jump to specific page
        console.print(f"   Jump: python main.py search '{query_dict['query']}' --page <page> --page-size {page_size}", style="dim")
    
    # Show total results info
    console.print(f"\n📊 Total results: {total_results}", style="green")
    if total_results > page_size:
        console.print(f"   Use --page-size to change results per page (current: {page_size})", style="dim")
    console.print(f"   Use --dump to output all results for further processing", style="dim")


def _parse_query_string(queries: str) -> Dict[str, str]:
    """Parse query string into dictionary."""
    query_dict = {}
    for pair in queries.split(','):
        if ':' in pair:
            field, query = pair.split(':', 1)
            field = field.strip()
            query = query.strip()
            if field and query:
                query_dict[field] = query
    
    if not query_dict:
        raise ValueError("No valid field:query pairs found. Use format: field:query,field:query")
    
    return query_dict


def _build_search_filters(category: Optional[str], source: Optional[str], platform: Optional[str],
                         rating_min: Optional[float], rating_max: Optional[float]) -> Dict[str, Any]:
    """Build search filters dictionary."""
    filters = {}
    if category:
        filters['category'] = category
    if source:
        filters['source'] = source
    if platform:
        filters['platform'] = platform
    if rating_min:
        filters['rating_min'] = float(rating_min)
    if rating_max:
        filters['rating_max'] = float(rating_max)
    return filters


@cli.command()
@click.argument('queries', required=True)
@click.option('--operator', '-o', default='AND', type=click.Choice(['AND', 'OR']), help='Logical operator for multiple queries (default: AND)')
@click.option('--regex', '-r', is_flag=True, help='Use regex patterns for queries')
@click.option('--case-sensitive', '-c', is_flag=True, help='Case-sensitive search (for regex)')
@click.option('--category', '-k', help='Filter by category')
@click.option('--source', '-s', help='Filter by source')
@click.option('--platform', '-p', help='Filter by platform')
@click.option('--rating-min', help='Minimum rating filter')
@click.option('--rating-max', help='Maximum rating filter')
@click.option('--page-size', '-n', default=20, help='Number of results per page (default: 20)')
@click.option('--page', '-g', default=1, help='Page number to display (default: 1)')
@click.option('--dump', is_flag=True, help='Dump all results (overrides pagination)')
@click.option('--format', '-f', default='table', type=click.Choice(['table', 'json', 'csv', 'tsv']), help='Output format for dump (default: table)')
def advanced_search(queries: str, operator: str, regex: bool, case_sensitive: bool,
                   category: Optional[str], source: Optional[str], platform: Optional[str],
                   rating_min: Optional[float], rating_max: Optional[float],
                   page_size: int, page: int, dump: bool, format: str):
    """Advanced search with multiple field queries."""
    try:
        # Parse queries string into dict
        query_dict = _parse_query_string(queries)
        
        with AssetInventoryDatabase() as db:
            # Create search provider
            search_provider = DuckDBSearchProvider(db.conn)
            
            # Build filters
            filters = _build_search_filters(category, source, platform, rating_min, rating_max)
            
            # Perform advanced search
            results = search_provider.search_advanced(
                query_dict, filters, use_regex=regex, case_sensitive=case_sensitive, operator=operator
            )
            
            if results:
                if dump:
                    # Dump all results in specified format
                    _dump_search_results(results, format)
                    return
                
                # Regular paginated display
                _display_paginated_results(results, page, page_size, query_dict, regex, operator)
                
            else:
                console.print("❌ No results found for the given search criteria", style="red")
                
    except ValueError as e:
        console.print(f"❌ {e}", style="red")
    except Exception as e:
        console.print(f"❌ Error during advanced search: {e}", style="red")
        # Remove debug setting reference since it doesn't exist
        console.print_exception()

@cli.command()
def search_info():
    """Show search capabilities and statistics."""
    try:
        with AssetInventoryDatabase() as db:
            search_provider = DuckDBSearchProvider(db.conn)
            
            # Get search statistics
            stats = search_provider.get_search_stats()
            
            if 'error' not in stats:
                # Display search statistics
                stats_panel = Panel(
                    f"[bold]Search Statistics[/bold]\n"
                    f"Total Products: {stats['total_products']}\n"
                    f"Total Bundles: {stats['total_bundles']}\n"
                    f"Searchable Fields: {', '.join(stats['searchable_fields'])}\n"
                    f"Last Updated: {stats['last_updated']}",
                    title="Search Capabilities",
                    border_style="green"
                )
                console.print(stats_panel)
                
                # Show category distribution
                if stats['category_distribution']:
                    category_table = Table(title="Category Distribution", show_header=True)
                    category_table.add_column("Category", style="cyan")
                    category_table.add_column("Count", style="magenta")
                    
                    for item in stats['category_distribution'][:10]:  # Top 10
                        category_table.add_row(
                            item['category'] or 'Unknown',
                            str(item['count'])
                        )
                    
                    console.print(category_table)
                
                # Show source distribution
                if stats['source_distribution']:
                    source_table = Table(title="Source Distribution", show_header=True)
                    source_table.add_column("Source", style="blue")
                    source_table.add_column("Count", style="yellow")
                    
                    for item in stats['source_distribution']:
                        source_table.add_row(
                            item['source'],
                            str(item['count'])
                        )
                    
                    console.print(source_table)
                
                # Show search examples
                examples_panel = Panel(
                    "[bold]Search Examples:[/bold]\n"
                    f"• Text search: python main.py search 'python'\n"
                    f"• Regex search: python main.py search '^[A-Z].*' --regex\n"
                    f"• Field search: python main.py search 'game' --field category\n"
                    f"• Case sensitive: python main.py search 'Python' --regex --case-sensitive\n"
                    f"• With filters: python main.py search 'book' --category ebook --source humble_bundle",
                    title="Usage Examples",
                    border_style="blue"
                )
                console.print(examples_panel)
                
            else:
                console.print(f"❌ Error getting search stats: {stats['error']}", style="red")
                
    except Exception as e:
        console.print(f"❌ Error getting search info: {e}", style="red")


def _dump_search_results_simple(query: str, results: List[Dict[str, Any]], format: str) -> None:
    """Dump search results in the specified format for simple search."""
    total_results = len(results)
    
    if format == 'json':
        # For JSON format, output only pure JSON without console messages
        print(_format_search_results_json(results))
    elif format == 'csv':
        # For CSV format, output only pure CSV without console messages
        print(_format_search_results_csv(results))
    elif format == 'tsv':
        # For TSV format, output only pure TSV without console messages
        print(_format_search_results_tsv(results))
    else:  # table format
        # For table format, show the console message
        console.print(f"🔍 Dumping {total_results} assets matching '{query}'", style="green")
        print(f"# Search Results for '{query}' - {total_results} items")
        print("Name\tCategory\tSubcategory\tSource\tDeveloper\tPublisher\tRating\tRelease Date\tTags\tDescription")
        for result in results:
            print(f"{result['human_name']}\t{result['category'] or 'Unknown'}\t{result.get('subcategory', 'Unknown')}\t{result['source_name']}\t{result['developer'] or 'Unknown'}\t{result.get('publisher', 'Unknown')}\t{result['rating'] or 'N/A'}\t{result['release_date'] or ''}\t{result.get('tags', '')}\t{result.get('description', '')}")


def _display_search_results_paginated(query: str, results: List[Dict[str, Any]], page: int, page_size: int) -> None:
    """Display search results with pagination."""
    total_results = len(results)
    total_pages = (total_results + page_size - 1) // page_size
    
    # Validate page number
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages
    
    # Calculate start and end indices for current page
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_results)
    page_results = results[start_idx:end_idx]
    
    console.print(f"🔍 Found {total_results} assets matching '{query}'", style="green")
    console.print(f"📄 Showing page {page} of {total_pages} ({start_idx + 1}-{end_idx} of {total_results})", style="blue")
    
    search_table = Table(title=f"Search Results for '{query}' - Page {page}/{total_pages}", show_header=True)
    search_table.add_column("#", style="dim")
    search_table.add_column("Name", style="cyan")
    search_table.add_column("Category", style="blue")
    search_table.add_column("Source", style="green")
    search_table.add_column("Developer", style="yellow")
    search_table.add_column("Rating", style="magenta")
    
    for i, result in enumerate(page_results, start=start_idx + 1):
        search_table.add_row(
            str(i),
            result['human_name'][:50] + ('...' if len(result['human_name']) > 50 else ''),
            result['category'] or 'Unknown',
            result['source_name'],
            result['developer'] or 'Unknown',
            str(result['rating']) if result['rating'] else 'N/A'
        )
    
    console.print(search_table)
    
    # Pagination controls
    if total_pages > 1:
        _display_pagination_controls(query, page, total_pages, page_size)


def _display_pagination_controls(query: str, page: int, total_pages: int, page_size: int) -> None:
    """Display pagination controls."""
    console.print(f"\n📖 Pagination:", style="yellow")
    
    # Previous page
    if page > 1:
        console.print(f"   ← Previous: python main.py search '{query}' --page {page - 1} --page-size {page_size}", style="blue")
    
    # Page numbers
    page_range = []
    for p in range(max(1, page - 2), min(total_pages + 1, page + 3)):
        if p == page:
            page_range.append(f"[bold]{p}[/bold]")
        else:
            page_range.append(str(p))
    
    console.print(f"   Pages: {' '.join(page_range)}", style="blue")
    
    # Next page
    if page < total_pages:
        console.print(f"   → Next: python main.py search '{query}' --page {page + 1} --page-size {page_size}", style="blue")
    
    # Jump to specific page
    console.print(f"   Jump: python main.py search '{query}' --page <page> --page-size {page_size}", style="dim")


@cli.command()
@click.argument('query', required=True)
@click.option('--category', '-k', help='Filter by category')
@click.option('--source', '-s', help='Filter by source')
@click.option('--platform', '-p', help='Filter by platform')
@click.option('--rating-min', help='Minimum rating filter')
@click.option('--rating-max', help='Maximum rating filter')
@click.option('--regex', '-r', is_flag=True, help='Treat query as regex pattern')
@click.option('--case-sensitive', is_flag=True, help='Case sensitive search (only applies with --regex)')
@click.option('--field', help='Search in specific field only')
@click.option('--page-size', '-n', default=20, help='Number of results per page (default: 20)')
@click.option('--page', '-g', default=1, help='Page number to display (default: 1)')
@click.option('--dump', is_flag=True, help='Dump all results (overrides pagination)')
@click.option('--format', '-f', default='table', type=click.Choice(['table', 'json', 'csv', 'tsv']), help='Output format for dump (default: table)')
def search(query: str, category: Optional[str], source: Optional[str], platform: Optional[str], 
           rating_min: Optional[float], rating_max: Optional[float], regex: bool, case_sensitive: bool,
           field: Optional[str], page_size: int, page: int, dump: bool, format: str):
    """Search assets in the database."""
    try:
        with AssetInventoryDatabase() as db:
            # Create search provider
            search_provider = DuckDBSearchProvider(db.conn)
            
            # Build filters
            filters = _build_search_filters(category, source, platform, rating_min, rating_max)
            
            # Perform search based on options
            if field:
                # Search in specific field with filters applied
                results = search_provider.search_by_field(
                    field, query, use_regex=regex, case_sensitive=case_sensitive, filters=filters
                )
            else:
                # General search
                results = search_provider.search_assets(
                    query, filters, use_regex=regex, case_sensitive=case_sensitive
                )
            
            if results:
                if dump:
                    # Dump all results in specified format
                    _dump_search_results_simple(query, results, format)
                    return
                
                # Regular paginated display
                _display_search_results_paginated(query, results, page, page_size)
                
            else:
                console.print("❌ No results found for the given search criteria", style="red")
                
    except Exception as e:
        console.print(f"❌ Error during search: {e}", style="red")
        # Remove debug setting reference since it doesn't exist
        console.print_exception()


@cli.command()
def sources():
    """Show status of all asset sources."""
    try:
        with AssetInventoryDatabase() as db:
            sources = db.get_asset_source_status()
            
            if sources:
                sources_table = Table(title="Asset Sources Status", show_header=True)
                sources_table.add_column("Source", style="cyan")
                sources_table.add_column("Type", style="blue")
                sources_table.add_column("Status", style="green")
                sources_table.add_column("Last Sync", style="yellow")
                sources_table.add_column("Products", style="magenta")
                sources_table.add_column("Bundles", style="white")
                
                for source in sources:
                    status_style = "green" if source['sync_status'] == 'active' else "yellow"
                    sources_table.add_row(
                        source['source_name'],
                        source['source_type'],
                        source['sync_status'],
                        str(source['last_sync_timestamp']) if source['last_sync_timestamp'] else 'Never',
                        str(source['total_products']),
                        str(source['total_bundles'])
                    )
                
                console.print(sources_table)
            else:
                console.print("📚 No asset sources found", style="yellow")
                
    except Exception as e:
        console.print(f"❌ Error getting sources: {e}", style="red")

@cli.command()
@click.option('--show-paths', is_flag=True, help='Show file locations')
def init(show_paths: bool):
    """Initialize the database and show setup information."""
    try:
        # Show where files will be stored
        if show_paths:
            show_user_paths()
            console.print()
        
        # Initialize database
        with AssetInventoryDatabase() as db:
            console.print("🗄️  Database initialized successfully!", style="green")
            console.print("   Schema: Multi-source asset inventory", style="blue")
            console.print("   Sources: Humble Bundle, Steam, GOG, Personal Files, etc.", style="blue")
            
        # Show setup guidance
        console.print()
        setup_panel = Panel(
            f"""[bold]Next Steps:[/bold]

1. [bold]Set up credentials (optional):[/bold]
   humble-inventory login --save

2. [bold]View file locations:[/bold]
   humble-inventory --show-paths

3. [bold]Sync your library:[/bold]
   humble-inventory sync

4. [bold]Search your collection:[/bold]
   humble-inventory search "python"

[bold]Files created:[/bold]
• Database: {settings.database_path}
• Config: {settings.user_config_dir}""",
            title="Setup Complete",
            border_style="green"
        )
        console.print(setup_panel)
            
    except Exception as e:
        console.print(f"❌ Database initialization failed: {e}", style="red")
        raise click.Abort()

@cli.command()
def config():
    """Show configuration and file locations."""
    show_user_paths()
    
    # Show current credential status
    console.print()
    cred_status = "✅ Set" if settings.humble_email else "❌ Not set"
    console.print(f"[bold]Credentials Status:[/bold] {cred_status}")
    
    if settings.humble_email:
        console.print(f"  Email: {settings.humble_email}")
        console.print("  Password: [hidden]")
    else:
        console.print("  Use 'humble-inventory login --save' to set credentials")
    
    # Show database status
    console.print()
    db_exists = Path(settings.database_path).exists()
    db_status = "✅ Created" if db_exists else "❌ Not created"
    console.print(f"[bold]Database Status:[/bold] {db_status}")
    
    if db_exists:
        try:
            with AssetInventoryDatabase() as db:
                product_count = db.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
                console.print(f"  Products: {product_count}")
        except:
            console.print("  Products: Unable to query")
    else:
        console.print("  Use 'humble-inventory init' to create database")

if __name__ == "__main__":
    cli()