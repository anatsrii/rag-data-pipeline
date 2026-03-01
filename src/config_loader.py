"""
Configuration Loader Module
===========================

Handles loading and validation of YAML configuration files.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Load and manage crawler configuration from YAML files."""
    
    def __init__(self, config_path: str = "./config/config.yaml"):
        """
        Initialize the configuration loader.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports nested keys with dot notation).
        
        Args:
            key: Configuration key (e.g., 'crawler.delay')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_odoo_config(self) -> Dict[str, Any]:
        """Get Odoo-specific configuration."""
        return self.config.get('odoo', {})
    
    def get_crawler_config(self) -> Dict[str, Any]:
        """Get crawler settings."""
        return self.config.get('crawler', {})
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration."""
        return self.config.get('storage', {})
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get content processing configuration."""
        return self.config.get('processing', {})
    
    def get_metadata_config(self) -> Dict[str, Any]:
        """Get metadata configuration."""
        return self.config.get('metadata', {})
    
    def get_categories_config(self) -> Dict[str, Any]:
        """Get categories configuration."""
        return self.config.get('categories', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.config.get('logging', {})
    
    def get_base_url(self) -> str:
        """Get Odoo documentation base URL."""
        return self.get('odoo.base_url', 'https://www.odoo.com/documentation/19.0')
    
    def get_raw_docs_path(self) -> Path:
        """Get raw documents storage path."""
        path = self.get('storage.raw_docs_path', './raw_docs')
        return Path(path).resolve()
    
    def get_delay(self) -> float:
        """Get request delay in seconds."""
        return float(self.get('crawler.delay', 2.0))
    
    def get_user_agent(self) -> str:
        """Get user agent string."""
        return self.get('crawler.user_agent', 
                       'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    def get_selectors(self) -> Dict[str, str]:
        """Get CSS selectors for content extraction."""
        return self.get('odoo.selectors', {
            'main_content': 'main, article, .document',
            'title': 'h1',
            'headings': 'h1, h2, h3, h4, h5, h6',
            'code_blocks': 'pre, code'
        })
    
    def get_remove_selectors(self) -> list:
        """Get CSS selectors for elements to remove."""
        return self.get('odoo.remove_selectors', [])
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        # Raw docs directory
        raw_docs = self.get_raw_docs_path()
        raw_docs.mkdir(parents=True, exist_ok=True)
        
        # Config directory
        config_dir = self.config_path.parent
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Category subdirectories
        if self.get('storage.organize_by_category', True):
            for category in self.get_categories_config().keys():
                cat_dir = raw_docs / category
                cat_dir.mkdir(exist_ok=True)
        
        # Image directory
        if self.get('processing.extract_images', False):
            img_dir = Path(self.get('processing.image_dir', './raw_docs/images'))
            img_dir.mkdir(parents=True, exist_ok=True)


# Singleton instance
_config_loader: Optional[ConfigLoader] = None


def get_config(config_path: str = "./config/config.yaml") -> ConfigLoader:
    """
    Get or create singleton ConfigLoader instance.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        ConfigLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader(config_path)
    return _config_loader
