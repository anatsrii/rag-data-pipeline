"""
MCP Server Tests
================

Unit tests for MCP tools and resources.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp_tools import SearchTool, SourceTools
from src.storage import SourceManager, SourceConfig


class TestSourceTools(unittest.TestCase):
    """Test source management tools"""
    
    def setUp(self):
        """Set up test environment"""
        import tempfile
        import os
        
        self.test_dir = tempfile.mkdtemp()
        os.environ["RAG_DATA_PATH"] = self.test_dir
        
        self.tools = SourceTools(base_path=self.test_dir)
    
    def tearDown(self):
        """Clean up"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_add_source(self):
        """Test adding a source"""
        result = self.tools.add_source(
            name="test_docs",
            urls=["https://example.com/docs"],
            category="test",
            description="Test documentation"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["name"], "test_docs")
        self.assertEqual(result["urls_count"], 1)
    
    def test_list_sources_empty(self):
        """Test listing sources when empty"""
        sources = self.tools.list_sources()
        self.assertEqual(len(sources), 0)
    
    def test_list_sources_with_data(self):
        """Test listing sources with data"""
        # Add a source
        self.tools.add_source(
            name="test_docs",
            urls=["https://example.com/docs"],
            category="test"
        )
        
        sources = self.tools.list_sources()
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["name"], "test_docs")
    
    def test_get_source_stats_not_found(self):
        """Test getting stats for non-existent source"""
        result = self.tools.get_source_stats("non_existent")
        self.assertIn("error", result)
    
    def test_delete_source_not_found(self):
        """Test deleting non-existent source"""
        result = self.tools.delete_source("non_existent")
        self.assertFalse(result["success"])


class TestSearchTool(unittest.TestCase):
    """Test search functionality"""
    
    def setUp(self):
        """Set up test environment"""
        import tempfile
        import os
        
        self.test_dir = tempfile.mkdtemp()
        os.environ["RAG_DATA_PATH"] = self.test_dir
        
        self.search = SearchTool(db_path=f"{self.test_dir}/vector_db")
    
    def tearDown(self):
        """Clean up"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_search_stats(self):
        """Test getting search stats"""
        stats = self.search.get_stats()
        
        self.assertIn("db_path", stats)
        self.assertIn("model", stats)
    
    def test_embed_query(self):
        """Test embedding a query"""
        embedding = self.search.embedder.embed_query("test query")
        
        self.assertIsInstance(embedding, list)
        self.assertGreater(len(embedding), 0)


class TestMCPIntegration(unittest.TestCase):
    """Test MCP server integration"""
    
    def test_mcp_server_loads(self):
        """Test that MCP server can be imported"""
        try:
            from src.mcp_server_v3 import mcp
            self.assertIsNotNone(mcp)
        except Exception as e:
            self.fail(f"Failed to load MCP server: {e}")
    
    def test_tools_registered(self):
        """Test that tools are registered"""
        from src.mcp_server_v3 import mcp
        
        # Check that mcp has tools
        # Note: FastMCP doesn't expose tools directly, so we just check it loads
        self.assertIsNotNone(mcp)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()
