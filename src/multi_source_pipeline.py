"""
Multi-Source RAG Pipeline
=========================

Process multiple data sources with organized storage.

Usage:
    from src.multi_source_pipeline import MultiSourcePipeline
    from src.storage import SourceConfig
    
    sources = [
        SourceConfig(name="odoo", urls=["https://odoo.com/..."]),
        SourceConfig(name="fastapi", urls=["https://fastapi.tiangolo.com/..."]),
    ]
    
    pipeline = MultiSourcePipeline()
    pipeline.run(sources)
"""

from typing import List, Dict, Any
import logging

from .storage import SourceManager, SourceConfig
from .crawler import UniversalCrawler, CrawlConfig
from .processor import DocumentChunker
from .rag import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiSourcePipeline:
    """
    Pipeline that handles multiple data sources.
    
    Storage structure:
        data/
        ├── sources/
        │   ├── {source_name}/raw/          # Crawled content
        │   ├── {source_name}/processed/    # Chunked content
        │   └── {source_name}/metadata.json
        └── vector_db/chroma_db/            # Shared vectors
    
    Each source can have different:
        - URLs to crawl
        - Chunk size/overlap
        - Category for grouping
    """
    
    def __init__(
        self,
        base_path: str = "./data",
        crawl_delay: float = 1.0
    ):
        self.base_path = base_path
        self.crawl_delay = crawl_delay
        
        # Initialize storage manager
        self.storage = SourceManager(base_path)
        
        # Initialize shared vector store
        self.vector_store = VectorStore(
            db_path=str(self.storage.get_vector_db_path()),
            collection_name="documents"
        )
        
        logger.info("Multi-source pipeline initialized")
    
    def run(self, sources: List[SourceConfig]) -> Dict[str, Any]:
        """
        Process multiple sources.
        
        Args:
            sources: List of SourceConfig
            
        Returns:
            Summary statistics per source
        """
        # Setup folder structure
        self.storage.setup_sources(sources)
        
        results = {}
        
        for source in sources:
            logger.info(f"\n{'='*50}")
            logger.info(f"Processing source: {source.name}")
            logger.info(f"{'='*50}")
            
            result = self._process_source(source)
            results[source.name] = result
            
            # Update timestamp
            self.storage.update_source_timestamp(source.name)
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _process_source(self, source: SourceConfig) -> Dict[str, Any]:
        """Process a single source"""
        
        # Step 1: Crawl
        raw_path = self.storage.get_raw_path(source.name)
        
        crawl_config = CrawlConfig(
            delay=self.crawl_delay,
            output_dir=str(raw_path)
        )
        crawler = UniversalCrawler(crawl_config)
        
        crawl_results = crawler.crawl_urls(source.urls)
        successful_crawls = [r for r in crawl_results if r.get('success')]
        
        logger.info(f"Crawled: {len(successful_crawls)}/{len(source.urls)} pages")
        
        # Step 2: Process & Index
        chunker = DocumentChunker(
            chunk_size=source.chunk_size,
            chunk_overlap=source.chunk_overlap
        )
        
        total_chunks = 0
        
        for crawl_result in successful_crawls:
            filepath = crawl_result.get('filepath')
            if not filepath:
                continue
            
            try:
                # Read content
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Chunk with source metadata
                chunks = chunker.chunk_document(
                    content,
                    metadata={
                        'source': source.name,
                        'category': source.category,
                        'url': crawl_result['url']
                    }
                )
                
                # Add to vector store
                if chunks:
                    self.vector_store.add_documents(chunks)
                    total_chunks += len(chunks)
                    
            except Exception as e:
                logger.error(f"Failed to process {filepath}: {e}")
        
        logger.info(f"Indexed: {total_chunks} chunks")
        
        return {
            'urls_total': len(source.urls),
            'urls_success': len(successful_crawls),
            'chunks_indexed': total_chunks,
            'category': source.category
        }
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print processing summary"""
        logger.info(f"\n{'='*60}")
        logger.info("PROCESSING SUMMARY")
        logger.info(f"{'='*60}")
        
        total_urls = sum(r['urls_total'] for r in results.values())
        total_success = sum(r['urls_success'] for r in results.values())
        total_chunks = sum(r['chunks_indexed'] for r in results.values())
        
        for name, result in results.items():
            logger.info(f"\n{name}:")
            logger.info(f"  URLs: {result['urls_success']}/{result['urls_total']}")
            logger.info(f"  Chunks: {result['chunks_indexed']}")
            logger.info(f"  Category: {result['category']}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"TOTAL: {total_success}/{total_urls} URLs, {total_chunks} chunks")
        logger.info(f"{'='*60}")
    
    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        source_filter: str = None,
        category_filter: str = None
    ) -> List[Dict[str, Any]]:
        """
        Search across all sources with optional filtering.
        
        Args:
            query_embedding: Query vector
            n_results: Number of results
            source_filter: Filter by source name
            category_filter: Filter by category
            
        Returns:
            Search results
        """
        # Build filter
        filter_dict = {}
        if source_filter:
            filter_dict['source'] = source_filter
        if category_filter:
            filter_dict['category'] = category_filter
        
        # Search
        results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=n_results,
            filter_dict=filter_dict if filter_dict else None
        )
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        storage_stats = self.storage.get_stats()
        vector_stats = self.vector_store.get_stats()
        
        return {
            'storage': storage_stats,
            'vector_db': vector_stats
        }
