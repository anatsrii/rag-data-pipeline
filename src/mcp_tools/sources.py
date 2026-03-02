"""
Source Tools
============

Source management tools for MCP Server.
"""

import os
from typing import List, Dict, Any, Optional

from ..storage import SourceManager, SourceConfig
from ..multi_source_pipeline import MultiSourcePipeline


class SourceTools:
    """
    Source management tools.
    
    Usage:
        tools = SourceTools(base_path="./data")
        tools.add_source(name="docs", urls=["..."])
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or os.environ.get("RAG_DATA_PATH", "./data")
        self._manager: Optional[SourceManager] = None
        self._pipeline: Optional[MultiSourcePipeline] = None
    
    @property
    def manager(self) -> SourceManager:
        """Get source manager"""
        if self._manager is None:
            self._manager = SourceManager(base_path=self.base_path)
        return self._manager
    
    @property
    def pipeline(self) -> MultiSourcePipeline:
        """Get pipeline"""
        if self._pipeline is None:
            self._pipeline = MultiSourcePipeline(base_path=self.base_path)
        return self._pipeline
    
    def list_sources(self) -> List[Dict[str, Any]]:
        """List all sources"""
        sources = self.manager.list_sources()
        result = []
        
        for name in sources:
            config = self.manager.get_source_config(name)
            stats = self.manager.get_stats()
            source_stats = stats.get("sources", {}).get(name, {})
            
            result.append({
                "name": name,
                "category": config.category if config else "",
                "description": config.description if config else "",
                "urls_count": len(config.urls) if config else 0,
                "raw_files": source_stats.get("raw_files", 0),
                "processed_files": source_stats.get("processed_files", 0)
            })
        
        return result
    
    def add_source(
        self,
        name: str,
        urls: List[str],
        category: str = "",
        description: str = "",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Dict[str, Any]:
        """Add new source"""
        try:
            source = SourceConfig(
                name=name,
                urls=urls,
                category=category,
                description=description,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            self.manager.setup_sources([source])
            
            return {
                "success": True,
                "name": name,
                "urls_count": len(urls),
                "category": category,
                "message": f"Source '{name}' created. Run crawl_source to index."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def crawl_source(self, name: str) -> Dict[str, Any]:
        """Crawl and index source"""
        try:
            config = self.manager.get_source_config(name)
            
            if not config:
                return {"error": f"Source '{name}' not found"}
            
            results = self.pipeline.run([config])
            
            return {
                "success": True,
                "source": name,
                "results": results.get(name, {})
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_source_stats(self, name: str) -> Dict[str, Any]:
        """Get source statistics"""
        try:
            config = self.manager.get_source_config(name)
            
            if not config:
                return {"error": f"Source '{name}' not found"}
            
            stats = self.manager.get_stats()
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
    
    def delete_source(self, name: str, keep_metadata: bool = False) -> Dict[str, Any]:
        """Delete source"""
        try:
            success = self.manager.delete_source(name, keep_metadata)
            return {
                "success": success,
                "name": name,
                "message": f"Source '{name}' deleted" if success else f"Failed to delete '{name}'"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
