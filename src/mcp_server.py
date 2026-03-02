"""
RAG Data Pipeline - MCP Server
==============================

MCP Server for RAG Data Pipeline.
Allows AI assistants to search and manage documentation sources.

Usage:
    # Run with stdio transport (for Claude Desktop)
    python -m src.mcp_server
    
    # Run with HTTP transport
    python -m src.mcp_server --transport http --port 8000
"""

import os
import sys
import argparse
from typing import Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP
from src.multi_source_pipeline import MultiSourcePipeline
from src.storage import SourceManager, SourceConfig

# Initialize MCP server
mcp = FastMCP("rag-data-pipeline")

# Initialize pipeline (lazy loading)
_pipeline: Optional[MultiSourcePipeline] = None
_source_manager: Optional[SourceManager] = None


def get_pipeline() -> MultiSourcePipeline:
    """Get or initialize pipeline"""
    global _pipeline
    if _pipeline is None:
        base_path = os.environ.get("RAG_DATA_PATH", "./data")
        _pipeline = MultiSourcePipeline(base_path=base_path)
    return _pipeline


def get_source_manager() -> SourceManager:
    """Get or initialize source manager"""
    global _source_manager
    if _source_manager is None:
        base_path = os.environ.get("RAG_DATA_PATH", "./data")
        _source_manager = SourceManager(base_path=base_path)
    return _source_manager


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
    Search indexed documents.
    
    Args:
        query: Search query text
        source: Filter by source name (optional)
        category: Filter by category (optional)
        n_results: Number of results to return (default: 5)
    
    Returns:
        List of search results with text, metadata, and relevance score
    """
    try:
        # Note: This requires embeddings. For now, return mock results.
        # In full implementation, would use embedding model.
        pipeline = get_pipeline()
        
        # Mock implementation - in real version would:
        # 1. Convert query to embedding
        # 2. Search vector store
        # 3. Return results
        
        return [{
            "status": "info",
            "message": "Search requires embedding model. Use vector_store directly with embeddings.",
            "query": query,
            "filters": {"source": source, "category": category}
        }]
        
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
        manager = get_source_manager()
        sources = manager.list_sources()
        
        result = []
        for name in sources:
            config = manager.get_source_config(name)
            stats = manager.get_stats()
            source_stats = stats.get("sources", {}).get(name, {})
            
            result.append({
                "name": name,
                "category": config.category if config else "",
                "description": config.description if config else "",
                "raw_files": source_stats.get("raw_files", 0),
                "processed_files": source_stats.get("processed_files", 0)
            })
        
        return result
        
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
        name: Unique source name (alphanumeric, underscore, hyphen)
        urls: List of URLs to crawl
        category: Grouping category (optional)
        description: Source description (optional)
        chunk_size: Text chunk size (default: 1000)
        chunk_overlap: Chunk overlap (default: 200)
    
    Returns:
        Success status and source info
    """
    try:
        manager = get_source_manager()
        
        # Create source config
        source = SourceConfig(
            name=name,
            urls=urls,
            category=category,
            description=description,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Setup folders
        manager.setup_sources([source])
        
        return {
            "success": True,
            "name": name,
            "urls_count": len(urls),
            "category": category,
            "message": f"Source '{name}' created. Run crawl_source to index."
        }
        
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
        manager = get_source_manager()
        config = manager.get_source_config(name)
        
        if not config:
            return {"error": f"Source '{name}' not found"}
        
        pipeline = get_pipeline()
        results = pipeline.run([config])
        
        return {
            "success": True,
            "source": name,
            "results": results.get(name, {})
        }
        
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
        manager = get_source_manager()
        config = manager.get_source_config(name)
        
        if not config:
            return {"error": f"Source '{name}' not found"}
        
        stats = manager.get_stats()
        source_stats = stats.get("sources", {}).get(name, {})
        
        return {
            "name": name,
            "category": config.category,
            "description": config.description,
            "urls": config.urls,
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "raw_files": source_stats.get("raw_files", 0),
            "processed_files": source_stats.get("processed_files", 0)
        }
        
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def delete_source(name: str, keep_metadata: bool = False) -> dict:
    """
    Delete a data source.
    
    Args:
        name: Source name to delete
        keep_metadata: If true, keep metadata.json for history
    
    Returns:
        Success status
    """
    try:
        manager = get_source_manager()
        success = manager.delete_source(name, keep_metadata)
        
        return {
            "success": success,
            "name": name,
            "message": f"Source '{name}' deleted" if success else f"Failed to delete '{name}'"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# RESOURCES
# =============================================================================

@mcp.resource("pipeline://status")
def get_pipeline_status() -> str:
    """Get overall pipeline status"""
    try:
        manager = get_source_manager()
        pipeline = get_pipeline()
        
        stats = manager.get_stats()
        sources = manager.list_sources()
        
        return f"""
# Pipeline Status

## Sources
Total sources: {len(sources)}
{chr(10).join(f"- {name}" for name in sources)}

## Storage
Base path: {stats.get('base_path', 'N/A')}

## Source Details
{chr(10).join(f"- {name}: {stats.get('sources', {}).get(name, {}).get('raw_files', 0)} raw files" for name in sources)}
"""
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("source://{name}/metadata")
def get_source_metadata(name: str) -> str:
    """Get source metadata"""
    try:
        manager = get_source_manager()
        config = manager.get_source_config(name)
        
        if not config:
            return f"Source '{name}' not found"
        
        return f"""
# Source: {name}

- **Description**: {config.description or 'N/A'}
- **Category**: {config.category or 'N/A'}
- **URLs**: {len(config.urls)} URLs
- **Chunk Size**: {config.chunk_size}
- **Chunk Overlap**: {config.chunk_overlap}

## URLs
{chr(10).join(f"- {url}" for url in config.urls)}
"""
    except Exception as e:
        return f"Error: {e}"


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="RAG Data Pipeline MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport type (default: stdio)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP port (default: 8000)"
    )
    parser.add_argument(
        "--data-path",
        default="./data",
        help="Data directory path (default: ./data)"
    )
    
    args = parser.parse_args()
    
    # Set data path
    os.environ["RAG_DATA_PATH"] = args.data_path
    
    print(f"Starting RAG Data Pipeline MCP Server", file=sys.stderr)
    print(f"Transport: {args.transport}", file=sys.stderr)
    print(f"Data path: {args.data_path}", file=sys.stderr)
    
    if args.transport == "http":
        mcp.run(transport="streamable-http", port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
