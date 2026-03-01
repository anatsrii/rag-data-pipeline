# RAG Data Pipeline

Universal data pipeline for RAG (Retrieval-Augmented Generation) systems.
Crawl any website, process content, and create searchable vector databases.

## Features

- **Universal Crawler**: Works with any website, not tied to specific platform
- **Smart Chunking**: Configurable text splitting with overlap
- **Vector Storage**: ChromaDB integration for efficient search
- **Modular Design**: Use components independently or as full pipeline
- **MCP Ready**: Easy integration with AI assistants

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Create urls.txt with your target URLs
echo "https://docs.example.com/page1" > urls.txt
echo "https://docs.example.com/page2" >> urls.txt

# Run pipeline
python -m src.pipeline
```

## Usage

### Basic Pipeline

```python
from src.pipeline import RAGPipeline, PipelineConfig

config = PipelineConfig(
    output_dir="./my_data",
    db_path="./my_vectors",
    chunk_size=500
)

pipeline = RAGPipeline(config)
results = pipeline.run([
    'https://docs.example.com/page1',
    'https://docs.example.com/page2'
])

print(f"Indexed {results['chunks_indexed']} chunks")
```

### Components

Use components independently:

```python
from src.crawler import UniversalCrawler, CrawlConfig
from src.processor import DocumentChunker
from src.rag import VectorStore

# Crawl
crawler = UniversalCrawler(CrawlConfig(delay=2.0))
crawler.crawl_urls(['https://example.com/docs'])

# Process
chunker = DocumentChunker(chunk_size=1000)
chunks = chunker.chunk_document(content, metadata={'source': 'example.com'})

# Store
store = VectorStore(db_path="./vectors")
store.add_documents(chunks, embeddings=embeddings)
```

## Configuration

Edit `config/config.yaml`:

```yaml
crawler:
  delay: 1.0
  max_retries: 3
  output_dir: "./data/raw"

processor:
  chunk_size: 1000
  chunk_overlap: 200

vector_store:
  db_path: "./chroma_db"
  collection_name: "documents"

sources:
  - "https://docs.example.com/page1"
  - "https://docs.example.com/page2"
```

## Examples

See `examples/` directory for complete examples:

- `examples/odoo/` - Odoo 19 documentation crawler

## Project Structure

```
.
├── src/
│   ├── crawler/          # Web crawling
│   ├── processor/        # Text processing
│   ├── rag/              # Vector database
│   └── pipeline.py       # End-to-end pipeline
├── config/
│   └── config.yaml       # Configuration
├── examples/
│   └── odoo/             # Example: Odoo docs
├── requirements.txt
└── README.md
```

## License

MIT
