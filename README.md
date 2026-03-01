# RAG Data Pipeline

Universal data pipeline for RAG (Retrieval-Augmented Generation) systems.
Crawl any website, process content, and create searchable vector databases.

## Features

- **Multi-Source Support**: Organize multiple websites in separate folders
- **Universal Crawler**: Works with any website
- **Smart Chunking**: Configurable text splitting with overlap
- **Vector Storage**: ChromaDB integration with metadata filtering
- **Category Grouping**: Group related sources together
- **MCP Ready**: Easy integration with AI assistants

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Define your sources in config/sources.yaml
# Then run:
python -m src.multi_source_pipeline
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
    category: "erp"              # Group related sources
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

categories:
  erp: "ERP Systems"
  framework: "Web Frameworks"
```

## Usage

### Multi-Source Pipeline

```python
from src.multi_source_pipeline import MultiSourcePipeline
from src.storage import SourceConfig

# Define sources
sources = [
    SourceConfig(
        name="odoo",
        urls=["https://odoo.com/documentation/19.0/"],
        category="erp"
    ),
    SourceConfig(
        name="fastapi", 
        urls=["https://fastapi.tiangolo.com/tutorial/"],
        category="framework"
    ),
]

# Run pipeline
pipeline = MultiSourcePipeline()
results = pipeline.run(sources)

# Search with filtering
results = pipeline.search(
    query_embedding=embedding,
    category_filter="erp"  # Only search ERP docs
)
```

### Components

```python
from src.storage import SourceManager, SourceConfig
from src.crawler import UniversalCrawler
from src.processor import DocumentChunker
from src.rag import VectorStore

# Manage sources
manager = SourceManager("./data")
manager.setup_sources([SourceConfig(name="docs", urls=["..."])])

# Get paths
raw_path = manager.get_raw_path("docs")
vector_db_path = manager.get_vector_db_path()
```

## Project Structure

```
.
├── src/
│   ├── crawler/              # Web crawling
│   ├── processor/            # Text processing
│   ├── rag/                  # Vector database
│   ├── storage/              # Source management
│   ├── pipeline.py           # Simple pipeline
│   └── multi_source_pipeline.py  # Multi-source pipeline
├── config/
│   ├── config.yaml           # General config
│   └── sources.yaml          # Source definitions
├── examples/
│   └── odoo/                 # Example: Odoo docs
└── README.md
```

## When to Group Sources?

**Same folder (same source)**: When content is related
- Multiple pages from same documentation site
- Different versions of same docs

**Different folders (different sources)**: When content is unrelated
- Different websites entirely
- Different product docs
- Internal vs external docs

**Categories**: For cross-source filtering
- Same category = can search together
- Different category = separate search spaces

## License

MIT
