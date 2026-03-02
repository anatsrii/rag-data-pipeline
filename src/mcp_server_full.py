"""
RAG Data Pipeline - MCP Server (Full Version)
=============================================

MCP Server with complete Odoo crawling support.
Includes URL discovery for full documentation crawling.

Usage:
    python -m src.mcp_server_full
"""

import os
import sys
import argparse
from typing import Optional, List
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP
from src.mcp_tools import SearchTool, SourceTools
from src.crawler import URLDiscovery

mcp = FastMCP("rag-data-pipeline-full")

_search_tool: Optional[SearchTool] = None
_source_tools: Optional[SourceTools] = None
_url_discovery: Optional[URLDiscovery] = None


def get_search_tool() -> SearchTool:
    global _search_tool
    if _search_tool is None:
        base_path = os.environ.get("RAG_DATA_PATH", "./data")
        _search_tool = SearchTool(db_path=f"{base_path}/vector_db")
    return _search_tool


def get_source_tools() -> SourceTools:
    global _source_tools
    if _source_tools is None:
        base_path = os.environ.get("RAG_DATA_PATH", "./data")
        _source_tools = SourceTools(base_path=base_path)
    return _source_tools


def get_url_discovery() -> URLDiscovery:
    global _url_discovery
    if _url_discovery is None:
        _url_discovery = URLDiscovery(delay=1.0)
    return _url_discovery


# =============================================================================
# TOOLS (Existing from v3)
# =============================================================================

@mcp.tool()
def search_docs(query: str, source: str = "", category: str = "", n_results: int = 5) -> list:
    """Search indexed documents using vector similarity."""
    try:
        tool = get_search_tool()
        return tool.search(query=query, n_results=n_results, source=source, category=category)
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def list_sources() -> list:
    """List all configured data sources."""
    try:
        return get_source_tools().list_sources()
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def add_source(name: str, urls: list, category: str = "", description: str = "", 
               chunk_size: int = 1000, chunk_overlap: int = 200) -> dict:
    """Add a new data source with specific URLs."""
    try:
        return get_source_tools().add_source(name, urls, category, description, chunk_size, chunk_overlap)
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def crawl_source(name: str, batch_size: int = 10) -> dict:
    """
    Crawl and index a data source.
    
    Args:
        name: Source name to crawl
        batch_size: Number of URLs to crawl per batch (default: 10)
    """
    try:
        tools = get_source_tools()
        return tools.crawl_source(name)
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def delete_source(name: str, keep_metadata: bool = False) -> dict:
    """Delete a data source."""
    try:
        return get_source_tools().delete_source(name, keep_metadata)
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_source_stats(name: str) -> dict:
    """Get statistics for a data source."""
    try:
        return get_source_tools().get_source_stats(name)
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# NEW TOOLS: URL Discovery & Full Crawl
# =============================================================================

@mcp.tool()
def discover_urls(
    method: str,
    start_url: str = "",
    sitemap_url: str = "",
    max_pages: int = 100,
    same_domain: bool = True,
    include_patterns: list = None,
    exclude_patterns: list = None
) -> dict:
    """
    Discover URLs for crawling.
    
    Use this BEFORE creating a source to get all URLs.
    
    Args:
        method: "sitemap", "crawl", or "navigation"
        start_url: Starting URL (for crawl/navigation methods)
        sitemap_url: Sitemap URL (for sitemap method)
        max_pages: Maximum URLs to discover (default: 100)
        same_domain: Only same domain (for crawl method)
        include_patterns: Only include URLs with these patterns
        exclude_patterns: Exclude URLs with these patterns
    
    Returns:
        Discovered URLs and count
    
    Examples:
        # Discover from sitemap
        discover_urls(method="sitemap", sitemap_url="https://example.com/sitemap.xml")
        
        # Discover by crawling
        discover_urls(method="crawl", start_url="https://example.com/docs", max_pages=200)
        
        # Discover from navigation
        discover_urls(method="navigation", start_url="https://example.com/docs")
    """
    try:
        discovery = get_url_discovery()
        
        if method == "sitemap":
            if not sitemap_url:
                return {"error": "sitemap_url required for sitemap method"}
            urls = discovery.from_sitemap(sitemap_url)
            
        elif method == "crawl":
            if not start_url:
                return {"error": "start_url required for crawl method"}
            urls = discovery.from_crawl(
                start_url=start_url,
                max_pages=max_pages,
                same_domain=same_domain
            )
            
        elif method == "navigation":
            if not start_url:
                return {"error": "start_url required for navigation method"}
            urls = discovery.from_navigation(start_url)
            
        else:
            return {"error": f"Unknown method: {method}"}
        
        # Filter URLs
        urls = discovery.filter_urls(
            urls,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            max_urls=max_pages
        )
        
        return {
            "success": True,
            "method": method,
            "urls_found": len(urls),
            "urls": urls[:50],  # Return first 50 for preview
            "message": f"Found {len(urls)} URLs. Use add_source to create source."
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def create_and_crawl_source(
    name: str,
    start_url: str,
    category: str = "",
    description: str = "",
    max_pages: int = 100,
    chunk_size: int = 1000,
    discover_method: str = "crawl"
) -> dict:
    """
    Complete workflow: Discover URLs → Create Source → Crawl → Index.
    
    This is the EASIEST way to add documentation!
    
    Args:
        name: Source name
        start_url: Starting URL (will discover more URLs automatically)
        category: Grouping category
        description: Source description
        max_pages: Maximum pages to crawl
        chunk_size: Text chunk size
        discover_method: "crawl" or "navigation"
    
    Returns:
        Complete status of all steps
    
    Example:
        create_and_crawl_source(
            name="odoo_docs",
            start_url="https://www.odoo.com/documentation/17.0/",
            category="documentation",
            max_pages=500
        )
    """
    try:
        results = {
            "source_name": name,
            "steps": []
        }
        
        # Step 1: Discover URLs
        discovery = get_url_discovery()
        
        if discover_method == "crawl":
            urls = discovery.from_crawl(
                start_url=start_url,
                max_pages=max_pages,
                same_domain=True,
                allowed_paths=["/documentation/"]  # Odoo specific
            )
        else:
            urls = discovery.from_navigation(start_url)
        
        results["steps"].append({
            "step": "discover",
            "status": "success",
            "urls_found": len(urls)
        })
        
        if not urls:
            results["success"] = False
            results["message"] = "No URLs discovered"
            return results
        
        # Step 2: Create source
        tools = get_source_tools()
        create_result = tools.add_source(
            name=name,
            urls=urls,
            category=category,
            description=description or f"Auto-discovered from {start_url}",
            chunk_size=chunk_size
        )
        
        results["steps"].append({
            "step": "create_source",
            "status": "success" if create_result.get("success") else "failed",
            "details": create_result
        })
        
        # Step 3: Crawl and index
        crawl_result = tools.crawl_source(name)
        
        results["steps"].append({
            "step": "crawl",
            "status": "success" if crawl_result.get("success") else "failed",
            "details": crawl_result
        })
        
        # Summary
        results["success"] = all(s["status"] == "success" for s in results["steps"])
        results["total_urls"] = len(urls)
        results["message"] = f"Source '{name}' created with {len(urls)} URLs and indexed."
        
        return results
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "steps": results.get("steps", [])
        }


@mcp.tool()
def batch_crawl(sources: list, sequential: bool = True) -> dict:
    """
    Crawl multiple sources in batch.
    
    Args:
        sources: List of source names to crawl
        sequential: If true, crawl one by one. If false, may crawl in parallel (future)
    
    Returns:
        Results for each source
    """
    try:
        tools = get_source_tools()
        results = {}
        
        for source_name in sources:
            results[source_name] = tools.crawl_source(source_name)
        
        return {
            "success": True,
            "sources_crawled": len(sources),
            "results": results
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# RESOURCES (from v3)
# =============================================================================

@mcp.resource("pipeline://status")
def get_pipeline_status() -> str:
    """Get overall pipeline status"""
    try:
        tools = get_source_tools()
        sources = tools.list_sources()
        
        total_raw = sum(s.get("raw_files", 0) for s in sources)
        total_processed = sum(s.get("processed_files", 0) for s in sources)
        
        return f"""# Pipeline Status

## Sources ({len(sources)} total)
{chr(10).join(f"- **{s['name']}** ({s['category']}): {s['raw_files']} raw, {s['processed_files']} processed" for s in sources)}

## Totals
- Raw files: {total_raw}
- Processed files: {total_processed}
"""
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("source://{name}/metadata")
def get_source_metadata(name: str) -> str:
    """Get source metadata"""
    try:
        stats = get_source_tools().get_source_stats(name)
        if "error" in stats:
            return f"Error: {stats['error']}"
        
        return f"""# Source: {name}

- **Category**: {stats.get('category', 'N/A')}
- **Description**: {stats.get('description', 'N/A')}
- **URLs**: {len(stats.get('urls', []))}
- **Chunk Size**: {stats.get('chunk_size', 'N/A')}
- **Raw Files**: {stats.get('raw_files', 0)}
- **Processed Files**: {stats.get('processed_files', 0)}

## URLs (first 10)
{chr(10).join(f"- {url}" for url in stats.get('urls', [])[:10])}
{'' if len(stats.get('urls', [])) <= 10 else f"... and {len(stats.get('urls', [])) - 10} more"}
"""
    except Exception as e:
        return f"Error: {e}"


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="RAG Data Pipeline MCP Server (Full)")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--data-path", default="./data")
    
    args = parser.parse_args()
    os.environ["RAG_DATA_PATH"] = args.data_path
    
    print(f"Starting RAG MCP Server (Full Version)", file=sys.stderr)
    print(f"Transport: {args.transport}", file=sys.stderr)
    print(f"Data path: {args.data_path}", file=sys.stderr)
    print(f"New tools: discover_urls, create_and_crawl_source, batch_crawl", file=sys.stderr)
    
    if args.transport == "http":
        mcp.run(transport="streamable-http", port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
