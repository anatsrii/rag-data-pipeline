"""
Metadata Manager Module
=======================

Manages metadata for crawled documents and provides quality control.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

from src.config_loader import ConfigLoader


logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadata:
    """Metadata for a crawled document."""
    url: str
    title: str
    version: str
    category: str
    subcategory: Optional[str] = None
    source_url: Optional[str] = None
    last_crawled: Optional[str] = None
    word_count: int = 0
    char_count: int = 0
    headings_count: int = 0
    code_blocks_count: int = 0
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    status: str = "active"  # active, updated, deprecated
    quality_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentMetadata':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class MetadataManager:
    """Manage document metadata and quality control."""
    
    def __init__(self, config: Optional[ConfigLoader] = None):
        """
        Initialize metadata manager.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config or ConfigLoader()
        
        # Storage paths
        self.metadata_db_path = Path(self.config.get('storage.metadata_db', './config/metadata.json'))
        self.raw_docs_path = Path(self.config.get_raw_docs_path())
        
        # In-memory storage
        self.metadata: Dict[str, DocumentMetadata] = {}
        
        # Load existing metadata
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load metadata from database file."""
        if self.metadata_db_path.exists():
            try:
                with open(self.metadata_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for url, meta_dict in data.items():
                        self.metadata[url] = DocumentMetadata.from_dict(meta_dict)
                logger.info(f"Loaded metadata for {len(self.metadata)} documents")
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
                self.metadata = {}
    
    def _save_metadata(self) -> None:
        """Save metadata to database file."""
        try:
            self.metadata_db_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {url: meta.to_dict() for url, meta in self.metadata.items()}
            
            with open(self.metadata_db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def add_document(self, url: str, content: Dict[str, Any], 
                     file_path: Path) -> DocumentMetadata:
        """
        Add or update document metadata.
        
        Args:
            url: Document URL
            content: Extracted content dictionary
            file_path: Path to saved file
            
        Returns:
            DocumentMetadata object
        """
        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)
        
        # Check if document exists
        existing = self.metadata.get(url)
        
        # Extract metadata from content
        meta_dict = content.get('metadata', {})
        headings = content.get('headings', [])
        
        # Count code blocks (simple heuristic)
        markdown = content.get('markdown', '')
        code_blocks_count = markdown.count('```')
        
        # Create metadata
        metadata = DocumentMetadata(
            url=url,
            title=meta_dict.get('title', 'Untitled'),
            version=meta_dict.get('version', '19.0'),
            category=meta_dict.get('category', 'unknown'),
            subcategory=meta_dict.get('subcategory'),
            source_url=meta_dict.get('source_url', url),
            last_crawled=datetime.now().isoformat(),
            word_count=content.get('word_count', 0),
            char_count=content.get('char_count', 0),
            headings_count=len(headings),
            code_blocks_count=code_blocks_count,
            file_path=str(file_path.relative_to(self.raw_docs_path.parent)),
            file_hash=file_hash,
            status="updated" if existing else "active",
            quality_score=self._calculate_quality_score(content)
        )
        
        self.metadata[url] = metadata
        
        # Save periodically
        if len(self.metadata) % 10 == 0:
            self._save_metadata()
        
        return metadata
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate MD5 hash of file content.
        
        Args:
            file_path: Path to file
            
        Returns:
            MD5 hash string
        """
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()[:16]
        except Exception:
            return ""
    
    def _calculate_quality_score(self, content: Dict[str, Any]) -> float:
        """
        Calculate quality score for document.
        
        Args:
            content: Content dictionary
            
        Returns:
            Quality score (0-100)
        """
        score = 0.0
        
        # Content length (up to 30 points)
        word_count = content.get('word_count', 0)
        if word_count > 1000:
            score += 30
        elif word_count > 500:
            score += 20
        elif word_count > 100:
            score += 10
        
        # Has title (10 points)
        metadata = content.get('metadata', {})
        if metadata.get('title') and metadata['title'] != 'Untitled':
            score += 10
        
        # Has headings structure (up to 20 points)
        headings = content.get('headings', [])
        if len(headings) > 10:
            score += 20
        elif len(headings) > 5:
            score += 15
        elif len(headings) > 0:
            score += 10
        
        # Has code examples (up to 20 points)
        markdown = content.get('markdown', '')
        code_blocks = markdown.count('```')
        if code_blocks > 5:
            score += 20
        elif code_blocks > 2:
            score += 10
        elif code_blocks > 0:
            score += 5
        
        # Has proper formatting (up to 20 points)
        if markdown.count('**') > 0:  # Bold text
            score += 5
        if markdown.count('`') > 0:  # Inline code
            score += 5
        if markdown.count('[') > 0:  # Links
            score += 5
        if markdown.count('|') > 0:  # Tables
            score += 5
        
        return min(score, 100)
    
    def get_document(self, url: str) -> Optional[DocumentMetadata]:
        """
        Get metadata for a document.
        
        Args:
            url: Document URL
            
        Returns:
            DocumentMetadata or None
        """
        return self.metadata.get(url)
    
    def get_documents_by_category(self, category: str) -> List[DocumentMetadata]:
        """
        Get all documents in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of DocumentMetadata
        """
        return [meta for meta in self.metadata.values() if meta.category == category]
    
    def get_documents_by_quality(self, min_score: float = 0) -> List[DocumentMetadata]:
        """
        Get documents filtered by quality score.
        
        Args:
            min_score: Minimum quality score
            
        Returns:
            List of DocumentMetadata
        """
        return [meta for meta in self.metadata.values() 
                if meta.quality_score >= min_score]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get metadata statistics.
        
        Returns:
            Statistics dictionary
        """
        if not self.metadata:
            return {
                'total_documents': 0,
                'categories': {},
                'average_quality': 0,
                'total_words': 0
            }
        
        # Category counts
        categories = {}
        for meta in self.metadata.values():
            cat = meta.category
            categories[cat] = categories.get(cat, 0) + 1
        
        # Quality scores
        quality_scores = [meta.quality_score for meta in self.metadata.values()]
        
        # Word counts
        total_words = sum(meta.word_count for meta in self.metadata.values())
        
        return {
            'total_documents': len(self.metadata),
            'categories': categories,
            'average_quality': sum(quality_scores) / len(quality_scores),
            'min_quality': min(quality_scores),
            'max_quality': max(quality_scores),
            'total_words': total_words,
            'average_words': total_words / len(self.metadata)
        }
    
    def find_duplicates(self) -> List[List[str]]:
        """
        Find duplicate documents based on file hash.
        
        Returns:
            List of duplicate URL groups
        """
        hash_map: Dict[str, List[str]] = {}
        
        for url, meta in self.metadata.items():
            if meta.file_hash:
                if meta.file_hash not in hash_map:
                    hash_map[meta.file_hash] = []
                hash_map[meta.file_hash].append(url)
        
        # Return only groups with duplicates
        return [urls for urls in hash_map.values() if len(urls) > 1]
    
    def find_broken_links(self) -> List[str]:
        """
        Find documents with missing files.
        
        Returns:
            List of URLs with missing files
        """
        broken = []
        
        for url, meta in self.metadata.items():
            if meta.file_path:
                file_path = self.raw_docs_path.parent / meta.file_path
                if not file_path.exists():
                    broken.append(url)
        
        return broken
    
    def export_to_json(self, output_path: Optional[Path] = None) -> Path:
        """
        Export metadata to JSON file.
        
        Args:
            output_path: Output file path (optional)
            
        Returns:
            Path to exported file
        """
        if output_path is None:
            output_path = self.raw_docs_path / 'metadata_export.json'
        
        data = {
            'export_date': datetime.now().isoformat(),
            'statistics': self.get_statistics(),
            'documents': {url: meta.to_dict() for url, meta in self.metadata.items()}
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Metadata exported to {output_path}")
        return output_path
    
    def generate_report(self) -> str:
        """
        Generate a quality report.
        
        Returns:
            Report string
        """
        stats = self.get_statistics()
        
        lines = [
            "=" * 60,
            "Odoo 19 Documentation Crawler - Quality Report",
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "📊 Statistics",
            "-" * 40,
            f"Total Documents: {stats['total_documents']}",
            f"Total Words: {stats['total_words']:,}",
            f"Average Words per Document: {stats.get('average_words', 0):.0f}",
            "",
            "📁 Categories",
            "-" * 40,
        ]
        
        for cat, count in stats.get('categories', {}).items():
            lines.append(f"  {cat}: {count}")
        
        lines.extend([
            "",
            "⭐ Quality Scores",
            "-" * 40,
            f"Average: {stats.get('average_quality', 0):.1f}/100",
            f"Min: {stats.get('min_quality', 0):.1f}/100",
            f"Max: {stats.get('max_quality', 0):.1f}/100",
            "",
            "=" * 60,
        ])
        
        # Check for duplicates
        duplicates = self.find_duplicates()
        if duplicates:
            lines.extend([
                "⚠️  Duplicates Found",
                "-" * 40,
            ])
            for dup_group in duplicates:
                lines.append(f"  {len(dup_group)} duplicates: {dup_group[0][:50]}...")
        
        # Check for broken links
        broken = self.find_broken_links()
        if broken:
            lines.extend([
                "",
                "⚠️  Broken Links Found",
                "-" * 40,
                f"  Count: {len(broken)}",
            ])
        
        lines.append("=" * 60)
        
        return '\n'.join(lines)
    
    def save(self) -> None:
        """Save metadata to disk."""
        self._save_metadata()
