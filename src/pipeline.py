"""
RAG Data Pipeline
=================

End-to-end pipeline: Crawl → Process → Index

Usage:
    from src.pipeline import RAGPipeline
    
    pipeline = RAGPipeline(config)
    pipeline.run([
        'https://example.com/docs/page1',
        'https://example.com/docs/page2'
    ])
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import logging

from .crawler import UniversalCrawler, CrawlConfig
from .processor import DocumentChunker
from .rag import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Pipeline configuration"""
    # Crawler
    crawl_delay: float = 1.0
    max_retries: int = 3
    output_dir: str = "./data/raw"
    
    # Processor
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Vector Store
    db_path: str = "./chroma_db"
    collection_name: str = "documents"
    
    # Embedding (optional - if not provided, ChromaDB uses default)
    embedding_model: Optional[str] = None


class RAGPipeline:
    """
    Complete RAG data pipeline.
    
    Example:
        config = PipelineConfig(
            output_dir="./my_data",
            db_path="./my_vectors",
            chunk_size=500
        )
        
        pipeline = RAGPipeline(config)
        
        # Run full pipeline
        results = pipeline.run([
            'https://docs.example.com/page1',
            'https://docs.example.com/page2'
        ])
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        
        # Initialize components
        crawl_config = CrawlConfig(
            delay=self.config.crawl_delay,
            max_retries=self.config.max_retries,
            output_dir=self.config.output_dir
        )
        self.crawler = UniversalCrawler(crawl_config)
        self.chunker = DocumentChunker(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )
        self.vector_store = VectorStore(
            db_path=self.config.db_path,
            collection_name=self.config.collection_name
        )
        
        logger.info("Pipeline initialized")
    
    def run(
        self,
        urls: List[str],
        extractor: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Run full pipeline on URLs.
        
        Args:
            urls: List of URLs to process
            extractor: Optional custom content extractor
            
        Returns:
            Summary statistics
        """
        logger.info(f"Starting pipeline for {len(urls)} URLs")
        
        # Step 1: Crawl
        crawl_results = self.crawler.crawl_urls(urls, extractor)
        successful_crawls = [r for r in crawl_results if r.get('success')]
        
        logger.info(f"Crawl complete: {len(successful_crawls)}/{len(urls)} successful")
        
        # Step 2: Process & Index
        total_chunks = 0
        
        for result in successful_crawls:
            filepath = result.get('filepath')
            if not filepath:
                continue
            
            try:
                # Read content
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Chunk
                chunks = self.chunker.chunk_document(
                    content,
                    metadata={'source': result['url']}
                )
                
                # Index
                if chunks:
                    self.vector_store.add_documents(chunks)
                    total_chunks += len(chunks)
                    
            except Exception as e:
                logger.error(f"Failed to process {filepath}: {e}")
        
        logger.info(f"Pipeline complete: {total_chunks} chunks indexed")
        
        return {
            'urls_total': len(urls),
            'urls_success': len(successful_crawls),
            'urls_failed': len(urls) - len(successful_crawls),
            'chunks_indexed': total_chunks
        }
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search indexed documents.
        Note: Requires embeddings to be computed.
        """
        # This is a placeholder - actual implementation would need
        # an embedder to convert query to vector
        logger.warning("search() requires embedding model. Use VectorStore directly with embeddings.")
        return []
