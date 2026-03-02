"""
Search Tool
===========

Search functionality for MCP Server.
"""

import os
from typing import List, Dict, Any, Optional

from ..rag import VectorStore, Embedder


class SearchTool:
    """
    Search tool with embedding support.
    
    Usage:
        search = SearchTool(db_path="./data/vector_db")
        results = search.search("query text", category="odoo")
    """
    
    def __init__(self, db_path: Optional[str] = None, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.db_path = db_path or os.environ.get("RAG_DATA_PATH", "./data") + "/vector_db"
        self.model_name = model_name
        
        # Initialize components (lazy loading)
        self._embedder: Optional[Embedder] = None
        self._vector_store: Optional[VectorStore] = None
    
    @property
    def embedder(self) -> Embedder:
        """Get or create embedder"""
        if self._embedder is None:
            self._embedder = Embedder(model_name=self.model_name)
        return self._embedder
    
    @property
    def vector_store(self) -> VectorStore:
        """Get or create vector store"""
        if self._vector_store is None:
            self._vector_store = VectorStore(
                db_path=self.db_path,
                collection_name="documents"
            )
        return self._vector_store
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        source: str = "",
        category: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Search documents with filters.
        
        Args:
            query: Search query
            n_results: Number of results
            source: Filter by source name
            category: Filter by category
            
        Returns:
            List of search results
        """
        try:
            # Embed query
            query_embedding = self.embedder.embed_query(query)
            
            if not query_embedding:
                return [{"error": "Failed to embed query"}]
            
            # Build filter
            filter_dict = {}
            if source:
                filter_dict["source"] = source
            if category:
                filter_dict["category"] = category
            
            # Search
            results = self.vector_store.search(
                query_embedding=query_embedding,
                n_results=n_results,
                filter_dict=filter_dict if filter_dict else None
            )
            
            # Format results
            formatted = []
            for r in results:
                formatted.append({
                    "text": r.get("text", "")[:500] + "..." if len(r.get("text", "")) > 500 else r.get("text", ""),
                    "metadata": r.get("metadata", {}),
                    "relevance_score": r.get("distance"),
                    "source": r.get("metadata", {}).get("source", "unknown"),
                    "category": r.get("metadata", {}).get("category", "")
                })
            
            return formatted
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search stats"""
        return {
            "db_path": self.db_path,
            "model": self.model_name,
            "embedding_dimension": self.embedder.get_dimension() if self._embedder else "not loaded",
            "vector_store_stats": self.vector_store.get_stats() if self._vector_store else {}
        }
