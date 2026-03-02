"""
RAG Data Pipeline - MCP Server (Phase 3)
========================================

MCP Server with Resources and Prompts.

Usage:
    python -m src.mcp_server_v3
"""

import os
import sys
import argparse
from typing import Optional
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP, Context
from src.mcp_tools import SearchTool, SourceTools

mcp = FastMCP("rag-data-pipeline-v3")

_search_tool: Optional[SearchTool] = None
_source_tools: Optional[SourceTools] = None


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


# =============================================================================
# TOOLS (จาก Phase 2)
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
    """Add a new data source."""
    try:
        return get_source_tools().add_source(name, urls, category, description, chunk_size, chunk_overlap)
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def crawl_source(name: str) -> dict:
    """Crawl and index a data source."""
    try:
        return get_source_tools().crawl_source(name)
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_source_stats(name: str) -> dict:
    """Get statistics for a data source."""
    try:
        return get_source_tools().get_source_stats(name)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def delete_source(name: str, keep_metadata: bool = False) -> dict:
    """Delete a data source."""
    try:
        return get_source_tools().delete_source(name, keep_metadata)
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_search_stats() -> dict:
    """Get search system statistics."""
    try:
        return get_search_tool().get_stats()
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# RESOURCES (Phase 3 - Dynamic)
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
- Last updated: {os.path.getmtime(get_source_tools().manager.sources_path) if sources else 'N/A'}
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


@mcp.resource("source://{name}/content")
def get_source_content(name: str) -> str:
    """Get sample content from a source"""
    try:
        import glob
        raw_path = get_source_tools().manager.get_raw_path(name)
        
        if not raw_path.exists():
            return f"Source '{name}' not found"
        
        files = list(raw_path.glob("*.html")) + list(raw_path.glob("*.md"))
        
        if not files:
            return f"No content files found for '{name}'"
        
        # Return first file as sample
        sample_file = files[0]
        content = sample_file.read_text(encoding='utf-8')[:2000]
        
        return f"""# Sample Content from {name}

**File**: {sample_file.name}

```
{content}...
```

*Total files: {len(files)}*
"""
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("search://stats")
def get_search_status() -> str:
    """Get search system status"""
    try:
        stats = get_search_tool().get_stats()
        return f"""# Search System Status

- **Database Path**: {stats.get('db_path', 'N/A')}
- **Embedding Model**: {stats.get('model', 'N/A')}
- **Dimension**: {stats.get('embedding_dimension', 'N/A')}

## Vector Store
{stats.get('vector_store_stats', {})}
"""
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("docs://help")
def get_help_docs() -> str:
    """Get help documentation"""
    return """# RAG Data Pipeline - Help

## Available Tools

### search_docs
Search indexed documents using vector similarity.
```
query: str           # Search query (required)
source: str          # Filter by source name
category: str        # Filter by category
n_results: int       # Number of results (default: 5)
```

### list_sources
List all configured data sources.

### add_source
Add a new data source.
```
name: str            # Unique source name
urls: list           # URLs to crawl
category: str        # Grouping category
description: str     # Description
chunk_size: int      # Chunk size (default: 1000)
chunk_overlap: int   # Overlap (default: 200)
```

### crawl_source
Crawl and index a source.
```
name: str            # Source name to crawl
```

### delete_source
Delete a data source.
```
name: str            # Source name
keep_metadata: bool  # Keep metadata for history
```

## Available Resources

- `pipeline://status` - Overall pipeline status
- `source://{name}/metadata` - Source metadata
- `source://{name}/content` - Sample content
- `search://stats` - Search system status
- `docs://help` - This help document
"""


# =============================================================================
# PROMPTS (Phase 3)
# =============================================================================

@mcp.prompt()
def search_help() -> str:
    """Help for searching documents"""
    return """You can search documents using the search_docs tool.

Tips:
- Use specific keywords for better results
- Filter by source or category if needed
- Check search://stats for system status

Example queries:
- "ORM models in Odoo"
- "FastAPI dependency injection"
- "Python async/await"
"""


@mcp.prompt()
def add_source_guide() -> str:
    """Guide for adding new sources"""
    return """To add a new documentation source:

1. Use add_source tool with:
   - name: Unique identifier (e.g., "fastapi", "odoo")
   - urls: List of URLs to crawl
   - category: Grouping (e.g., "framework", "erp")
   - chunk_size: 1000 (default) or adjust as needed

2. Then run crawl_source to index

3. Verify with list_sources

Example:
```
add_source(
    name="fastapi",
    urls=["https://fastapi.tiangolo.com/tutorial/"],
    category="framework"
)
```
"""


@mcp.prompt()
def source_analysis(name: str) -> str:
    """Analyze a data source"""
    return f"""Please analyze the source '{name}':

1. Check metadata with source://{name}/metadata
2. View sample content with source://{name}/content
3. Get source stats with get_source_stats tool
4. Report on:
   - Number of documents
   - Content quality
   - Coverage of topics
   - Any issues found
"""


@mcp.prompt()
def query_refinement(query: str) -> str:
    """Help refine search query"""
    return f"""The user wants to search for: "{query}"

Help refine this query:
1. Identify key concepts
2. Suggest alternative keywords
3. Recommend filters (source/category) if applicable
4. Propose follow-up searches

Current query analysis:
- Keywords: {', '.join(query.split())}
- Suggested refinements:
  - Use more specific terms
  - Add technical terminology
  - Include version numbers if relevant
"""


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="RAG Data Pipeline MCP Server v3")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--data-path", default="./data")
    
    args = parser.parse_args()
    os.environ["RAG_DATA_PATH"] = args.data_path
    
    print(f"Starting RAG MCP Server v3 (with Resources & Prompts)", file=sys.stderr)
    print(f"Transport: {args.transport}", file=sys.stderr)
    print(f"Data path: {args.data_path}", file=sys.stderr)
    
    if args.transport == "http":
        mcp.run(transport="streamable-http", port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
