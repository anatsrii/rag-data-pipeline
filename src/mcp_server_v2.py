"""
RAG Data Pipeline - MCP Server (Phase 2)
========================================

MCP Server with working search using embeddings.

Usage:
    python -m src.mcp_server_v2
"""

import os
import sys
import argparse
from typing import Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP
from src.mcp_tools import SearchTool, SourceTools

# Initialize MCP server
mcp = FastMCP("rag-data-pipeline-v2")

# Initialize tools (lazy loading)
_search_tool: Optional[SearchTool] = None
_source_tools: Optional[SourceTools] = None


def get_search_tool() -> SearchTool:
    """Get or initialize search tool"""
    global _search_tool
    if _search_tool is None:
        base_path = os.environ.get("RAG_DATA_PATH", "./data")
        _search_tool = SearchTool(db_path=f"{base_path}/vector_db")
    return _search_tool


def get_source_tools() -> SourceTools:
    """Get or initialize source tools"""
    global _source_tools
    if _source_tools is None:
        base_path = os.environ.get("RAG_DATA_PATH", "./data")
        _source_tools = SourceTools(base_path=base_path)
    return _source_tools


# =============================================================================
# TOOLS
# =============================================================================

@mcp.tool()
def search_docs(
    query: str,
    source: str = "",
    category: str = "",
    n_results: int = 5
) -> list:
    """
    Search indexed documents using vector similarity.
    
    Args:
        query: Search query text
        source: Filter by source name (optional)
        category: Filter by category (optional)
        n_results: Number of results (default: 5)
    
    Returns:
        List of search results with text, metadata, and relevance score
    """
    try:
        tool = get_search_tool()
        results = tool.search(
            query=query,
            n_results=n_results,
            source=source,
            category=category
        )
        return results
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def list_sources() -> list:
    """
    List all configured data sources.
    
    Returns:
        List of sources with name, category, and stats
    """
    try:
        tools = get_source_tools()
        return tools.list_sources()
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def add_source(
    name: str,
    urls: list,
    category: str = "",
    description: str = "",
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> dict:
    """
    Add a new data source.
    
    Args:
        name: Unique source name
        urls: List of URLs to crawl
        category: Grouping category
        description: Source description
        chunk_size: Text chunk size
        chunk_overlap: Chunk overlap
    
    Returns:
        Success status and source info
    """
    try:
        tools = get_source_tools()
        return tools.add_source(
            name=name,
            urls=urls,
            category=category,
            description=description,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def crawl_source(name: str) -> dict:
    """
    Crawl and index a data source.
    
    Args:
        name: Source name to crawl
    
    Returns:
        Crawl statistics
    """
    try:
        tools = get_source_tools()
        return tools.crawl_source(name)
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_source_stats(name: str) -> dict:
    """
    Get statistics for a data source.
    
    Args:
        name: Source name
    
    Returns:
        Source statistics
    """
    try:
        tools = get_source_tools()
        return tools.get_source_stats(name)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def delete_source(name: str, keep_metadata: bool = False) -> dict:
    """
    Delete a data source.
    
    Args:
        name: Source name to delete
        keep_metadata: Keep metadata.json for history
    
    Returns:
        Success status
    """
    try:
        tools = get_source_tools()
        return tools.delete_source(name, keep_metadata)
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_search_stats() -> dict:
    """
    Get search system statistics.
    
    Returns:
        Search stats including model info and vector store status
    """
    try:
        tool = get_search_tool()
        return tool.get_stats()
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# RESOURCES
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
        tools = get_source_tools()
        stats = tools.get_source_stats(name)
        
        if "error" in stats:
            return f"Error: {stats['error']}"
        
        return f"""# Source: {name}

- **Category**: {stats.get('category', 'N/A')}
- **Description**: {stats.get('description', 'N/A')}
- **URLs**: {len(stats.get('urls', []))} URLs
- **Chunk Size**: {stats.get('chunk_size', 'N/A')}
- **Chunk Overlap**: {stats.get('chunk_overlap', 'N/A')}
- **Raw Files**: {stats.get('raw_files', 0)}
- **Processed Files**: {stats.get('processed_files', 0)}

## URLs
{chr(10).join(f"- {url}" for url in stats.get('urls', []))}
"""
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("search://stats")
def get_search_status() -> str:
    """Get search system status"""
    try:
        tool = get_search_tool()
        stats = tool.get_stats()
        
        return f"""# Search System Status

- **Database Path**: {stats.get('db_path', 'N/A')}
- **Embedding Model**: {stats.get('model', 'N/A')}
- **Dimension**: {stats.get('embedding_dimension', 'N/A')}

## Vector Store
{stats.get('vector_store_stats', {})}
"""
    except Exception as e:
        return f"Error: {e}"


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="RAG Data Pipeline MCP Server v2")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--data-path", default="./data")
    
    args = parser.parse_args()
    
    os.environ["RAG_DATA_PATH"] = args.data_path
    
    print(f"Starting RAG MCP Server v2", file=sys.stderr)
    print(f"Transport: {args.transport}", file=sys.stderr)
    print(f"Data path: {args.data_path}", file=sys.stderr)
    
    if args.transport == "http":
        mcp.run(transport="streamable-http", port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
