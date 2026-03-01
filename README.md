# RAG Data Pipeline

Universal data pipeline for RAG (Retrieval-Augmented Generation) systems.
Crawl any website, process content, and create searchable vector databases.

> **Migration Complete**: This project has been refactored from Odoo-specific crawler to **generic RAG pipeline** that works with any documentation source.

## Features

- **Multi-Source Support**: Organize multiple websites in separate folders
- **Universal Crawler**: Works with any website, not tied to specific platform
- **Smart Chunking**: Configurable text splitting with overlap
- **Vector Storage**: ChromaDB integration with metadata filtering
- **Category Grouping**: Group related sources for targeted search
- **Modular Design**: Use components independently or as full pipeline

## Quick Start

```bash
# 1. Clone and install
pip install -r requirements.txt

# 2. Define sources in config/sources.yaml
# See config/sources.yaml for examples

# 3. Run pipeline
python -c "
from src.multi_source_pipeline import MultiSourcePipeline
from src.storage import SourceConfig

sources = [
    SourceConfig(
        name='my_docs',
        urls=['https://docs.example.com/'],
        category='documentation'
    )
]

pipeline = MultiSourcePipeline()
pipeline.run(sources)
"
```

## Installation

```bash
# Clone repository
git clone https://github.com/anatsrii/rag-data-pipeline.git
cd rag-data-pipeline

# Install dependencies
pip install -r requirements.txt
```

## Storage Structure

```
data/                           # Base data folder
├── sources/                    # Individual source folders
│   ├── odoo/                   # Source: Odoo docs
│   │   ├── raw/               # Crawled HTML/Markdown
│   │   ├── processed/         # Chunked content
│   │   └── metadata.json      # Source config
│   ├── fastapi/               # Source: FastAPI docs
│   │   ├── raw/
│   │   ├── processed/
│   │   └── metadata.json
│   └── my_company/            # Source: Internal wiki
│       ├── raw/
│       ├── processed/
│       └── metadata.json
└── vector_db/                 # Shared vector database
    └── chroma_db/
```

## Configuration

### config/sources.yaml

```yaml
sources:
  - name: "odoo"
    description: "Odoo 19 Documentation"
    category: "erp"
    urls:
      - "https://www.odoo.com/documentation/19.0/"
    chunk_size: 1000
    chunk_overlap: 200

  - name: "fastapi"
    description: "FastAPI Docs"
    category: "framework"
    urls:
      - "https://fastapi.tiangolo.com/tutorial/"
    chunk_size: 800
    chunk_overlap: 150

  - name: "company_wiki"
    description: "Internal Documentation"
    category: "internal"
    urls:
      - "https://wiki.mycompany.com/"
    chunk_size: 1200
    chunk_overlap: 300

categories:
  erp: "ERP Systems"
  framework: "Web Frameworks"
  internal: "Internal Docs"
```

## Usage Examples

### 1. Multi-Source Pipeline (Recommended)

```python
from src.multi_source_pipeline import MultiSourcePipeline
from src.storage import SourceConfig

# Define multiple sources
sources = [
    SourceConfig(
        name="odoo",
        urls=["https://odoo.com/documentation/19.0/"],
        category="erp",
        chunk_size=1000
    ),
    SourceConfig(
        name="fastapi",
        urls=["https://fastapi.tiangolo.com/tutorial/"],
        category="framework",
        chunk_size=800
    ),
]

# Run pipeline
pipeline = MultiSourcePipeline(base_path="./data")
results = pipeline.run(sources)

# Search with category filter
results = pipeline.search(
    query_embedding=embedding,
    category_filter="erp"  # Only ERP docs
)
```

### 2. Individual Components

```python
from src.storage import SourceManager, SourceConfig
from src.crawler import UniversalCrawler, CrawlConfig
from src.processor import DocumentChunker
from src.rag import VectorStore

# Setup storage
manager = SourceManager("./data")
manager.setup_sources([
    SourceConfig(name="docs", urls=["https://example.com/"])
])

# Crawl
raw_path = manager.get_raw_path("docs")
crawler = UniversalCrawler(CrawlConfig(output_dir=str(raw_path)))
crawler.crawl_urls(["https://example.com/page1"])

# Process
chunker = DocumentChunker(chunk_size=1000)
chunks = chunker.chunk_document(content, metadata={"source": "docs"})

# Store
vector_store = VectorStore(db_path=str(manager.get_vector_db_path()))
vector_store.add_documents(chunks, embeddings=embeddings)
```

### 3. Simple Pipeline (Single Source)

```python
from src.pipeline import RAGPipeline, PipelineConfig

config = PipelineConfig(
    output_dir="./data/raw",
    db_path="./data/vector_db",
    chunk_size=1000
)

pipeline = RAGPipeline(config)
pipeline.run(['https://docs.example.com/page1'])
```

## Project Structure

```
rag-data-pipeline/
├── src/
│   ├── crawler/                    # Web crawling module
│   │   ├── __init__.py
│   │   └── universal_crawler.py   # Generic crawler
│   ├── processor/                  # Text processing module
│   │   ├── __init__.py
│   │   └── chunker.py             # Document chunking
│   ├── rag/                        # Vector database module
│   │   ├── __init__.py
│   │   └── vector_store.py        # ChromaDB interface
│   ├── storage/                    # Source management
│   │   ├── __init__.py
│   │   └── source_manager.py      # Multi-source storage
│   ├── pipeline.py                 # Simple single-source pipeline
│   └── multi_source_pipeline.py    # Multi-source pipeline
├── config/
│   ├── config.yaml                 # General configuration
│   └── sources.yaml                # Source definitions
├── examples/
│   └── odoo/                       # Example: Odoo 19 docs
│       ├── urls.txt
│       ├── scheduled_update.py
│       └── docs/
├── requirements.txt
└── README.md
```

## Source Organization Guide

### Same Source (Same Folder)
Use when content is **related**:
- Multiple pages from same documentation site
- Different versions of same docs
- API docs + Guides from same product

```yaml
sources:
  - name: "odoo"
    urls:
      - "https://odoo.com/documentation/19.0/developer.html"
      - "https://odoo.com/documentation/19.0/applications.html"
```

### Different Sources (Different Folders)
Use when content is **unrelated**:
- Different websites entirely
- Different product docs
- Internal vs external docs

```yaml
sources:
  - name: "odoo"
    category: "erp"
  - name: "fastapi"
    category: "framework"
  - name: "internal_wiki"
    category: "internal"
```

### Categories
Use for **cross-source grouping**:
- Same category = searchable together
- Different category = separate search spaces

```python
# Search only ERP docs (odoo, sap, etc.)
results = pipeline.search(
    embedding,
    category_filter="erp"
)

# Search only framework docs
results = pipeline.search(
    embedding,
    category_filter="framework"
)
```

## Examples

See `examples/` directory:

- **`examples/odoo/`** - Complete example crawling Odoo 19 documentation

## API Reference

### SourceConfig

```python
@dataclass
class SourceConfig:
    name: str              # Unique source name (alphanumeric)
    urls: List[str]        # URLs to crawl
    description: str = ""  # Optional description
    category: str = ""     # Grouping category
    chunk_size: int = 1000
    chunk_overlap: int = 200
```

### MultiSourcePipeline

```python
pipeline = MultiSourcePipeline(
    base_path="./data",
    crawl_delay=1.0
)

# Process sources
results = pipeline.run(sources)

# Search
results = pipeline.search(
    query_embedding=[0.1, 0.2, ...],
    n_results=5,
    source_filter="odoo",      # Optional
    category_filter="erp"      # Optional
)

# Get stats
stats = pipeline.get_stats()
```

## Environment Variables

```bash
# Optional: Custom data directory
export RAG_DATA_PATH="/path/to/data"

# Optional: ChromaDB settings
export CHROMA_DB_PATH="/path/to/chroma_db"
```

## Requirements

- Python 3.10+
- See `requirements.txt` for dependencies

## Migration from Odoo-Specific Version

If you were using the old Odoo-specific version:

1. Move your Odoo config to `examples/odoo/`
2. Update imports from `src.crawler_engine` to `src.crawler`
3. Use `MultiSourcePipeline` for new projects

See `examples/odoo/` for reference implementation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- Issues: [GitHub Issues](https://github.com/anatsrii/rag-data-pipeline/issues)
- Examples: See `examples/` directory
