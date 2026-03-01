"""
Source Manager
==============

Manage multiple data sources with organized folder structure.

Structure:
    data/
    ├── sources/
    │   ├── odoo/                    # Source: odoo
    │   │   ├── raw/                 # Crawled HTML/Markdown
    │   │   ├── processed/           # Cleaned & chunked
    │   │   └── metadata.json        # Source metadata
    │   ├── fastapi/                 # Source: fastapi
    │   │   ├── raw/
    │   │   ├── processed/
    │   │   └── metadata.json
    │   └── my_company/              # Source: custom
    │       ├── raw/
    │       ├── processed/
    │       └── metadata.json
    └── vector_db/                   # Shared vector database
        └── chroma_db/

Usage:
    from src.storage import SourceManager, SourceConfig
    
    # Define sources
    sources = [
        SourceConfig(name="odoo", urls=["https://odoo.com/docs/..."]),
        SourceConfig(name="fastapi", urls=["https://fastapi.tiangolo.com/..."]),
    ]
    
    # Initialize storage
    manager = SourceManager(base_path="./data")
    manager.setup_sources(sources)
    
    # Use in pipeline
    for source in sources:
        output_dir = manager.get_raw_path(source.name)
        # ... crawl to output_dir ...
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SourceConfig:
    """Configuration for a single data source"""
    name: str                          # Unique source name (e.g., "odoo", "fastapi")
    urls: List[str]                    # URLs to crawl
    description: str = ""              # Optional description
    category: str = "default"          # Grouping category
    chunk_size: int = 1000             # Override default chunk size
    chunk_overlap: int = 200           # Override default overlap
    
    def __post_init__(self):
        # Validate name (no special chars)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.name):
            raise ValueError(f"Source name must be alphanumeric: {self.name}")


class SourceManager:
    """
    Manage organized storage for multiple data sources.
    
    Each source gets its own folder structure:
        {base_path}/sources/{source_name}/
            ├── raw/          # Original crawled content
            ├── processed/    # Chunked & cleaned
            └── metadata.json # Source info
    
    Vector database is shared:
        {base_path}/vector_db/
    """
    
    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
        self.sources_path = self.base_path / "sources"
        self.vector_db_path = self.base_path / "vector_db"
        
        # Create base directories
        self.sources_path.mkdir(parents=True, exist_ok=True)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Storage initialized at: {self.base_path.absolute()}")
    
    def setup_sources(self, sources: List[SourceConfig]):
        """
        Setup folder structure for multiple sources.
        
        Args:
            sources: List of SourceConfig
        """
        for source in sources:
            self._create_source_folders(source)
            self._save_source_metadata(source)
        
        logger.info(f"Setup complete for {len(sources)} sources")
    
    def _create_source_folders(self, source: SourceConfig):
        """Create folder structure for a source"""
        source_path = self.sources_path / source.name
        
        # Create subdirectories
        (source_path / "raw").mkdir(parents=True, exist_ok=True)
        (source_path / "processed").mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Created folders for: {source.name}")
    
    def _save_source_metadata(self, source: SourceConfig):
        """Save source metadata to JSON"""
        metadata_path = self.sources_path / source.name / "metadata.json"
        
        metadata = {
            **asdict(source),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def get_raw_path(self, source_name: str) -> Path:
        """Get path to raw data folder for a source"""
        return self.sources_path / source_name / "raw"
    
    def get_processed_path(self, source_name: str) -> Path:
        """Get path to processed data folder for a source"""
        return self.sources_path / source_name / "processed"
    
    def get_metadata_path(self, source_name: str) -> Path:
        """Get path to metadata file for a source"""
        return self.sources_path / source_name / "metadata.json"
    
    def get_vector_db_path(self) -> Path:
        """Get path to shared vector database"""
        return self.vector_db_path / "chroma_db"
    
    def list_sources(self) -> List[str]:
        """List all configured sources"""
        sources = []
        for item in self.sources_path.iterdir():
            if item.is_dir() and (item / "metadata.json").exists():
                sources.append(item.name)
        return sorted(sources)
    
    def get_source_config(self, source_name: str) -> Optional[SourceConfig]:
        """Load source configuration from metadata"""
        metadata_path = self.get_metadata_path(source_name)
        
        if not metadata_path.exists():
            return None
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Remove internal fields
        data.pop('created_at', None)
        data.pop('updated_at', None)
        
        return SourceConfig(**data)
    
    def update_source_timestamp(self, source_name: str):
        """Update the 'updated_at' timestamp for a source"""
        metadata_path = self.get_metadata_path(source_name)
        
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            metadata['updated_at'] = datetime.now().isoformat()
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def get_stats(self) -> Dict:
        """Get storage statistics"""
        stats = {
            "base_path": str(self.base_path.absolute()),
            "sources": {}
        }
        
        for source_name in self.list_sources():
            raw_path = self.get_raw_path(source_name)
            processed_path = self.get_processed_path(source_name)
            
            # Count files
            raw_files = len(list(raw_path.glob("*"))) if raw_path.exists() else 0
            processed_files = len(list(processed_path.glob("*"))) if processed_path.exists() else 0
            
            stats["sources"][source_name] = {
                "raw_files": raw_files,
                "processed_files": processed_files
            }
        
        return stats
    
    def delete_source(self, source_name: str, keep_metadata: bool = False) -> bool:
        """
        Delete a source and all its data.
        
        Args:
            source_name: Name of source to delete
            keep_metadata: If True, keep metadata.json for history
            
        Returns:
            True if successful
        """
        import shutil
        
        source_path = self.sources_path / source_name
        
        if not source_path.exists():
            logger.warning(f"Source not found: {source_name}")
            return False
        
        try:
            if keep_metadata:
                # Delete only data folders
                shutil.rmtree(source_path / "raw", ignore_errors=True)
                shutil.rmtree(source_path / "processed", ignore_errors=True)
                logger.info(f"Deleted data for: {source_name} (metadata kept)")
            else:
                # Delete entire source folder
                shutil.rmtree(source_path)
                logger.info(f"Deleted source: {source_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete {source_name}: {e}")
            return False
