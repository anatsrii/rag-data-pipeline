# MCP Server Usage Guide

คู่มือการใช้งาน RAG Data Pipeline MCP Server

---

## การติดตั้ง

### 1. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
pip install mcp
```

### 2. ตั้งค่า Claude Desktop

เพิ่มใน `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rag-pipeline": {
      "command": "python",
      "args": ["-m", "src.mcp_server_v3"],
      "env": {
        "RAG_DATA_PATH": "./data"
      }
    }
  }
}
```

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`

---

## การใช้งาน

### เริ่มต้น

```bash
# Run with stdio (for Claude Desktop)
python -m src.mcp_server_v3

# Run with HTTP
python -m src.mcp_server_v3 --transport http --port 8000

# Custom data path
python -m src.mcp_server_v3 --data-path /path/to/data
```

---

## Tools

### 1. search_docs

ค้นหาเอกสารด้วย vector similarity

**Parameters:**
- `query` (required): คำค้นหา
- `source` (optional): กรองตาม source name
- `category` (optional): กรองตาม category
- `n_results` (optional): จำนวนผลลัพธ์ (default: 5)

**Example:**
```json
{
  "query": "ORM models",
  "category": "odoo",
  "n_results": 10
}
```

**Response:**
```json
[
  {
    "text": "ORM models in Odoo...",
    "metadata": {"source": "odoo", "url": "..."},
    "relevance_score": 0.85,
    "source": "odoo",
    "category": "erp"
  }
]
```

---

### 2. list_sources

แสดงรายการ sources ทั้งหมด

**Parameters:** ไม่มี

**Response:**
```json
[
  {
    "name": "odoo",
    "category": "erp",
    "description": "Odoo 19 Documentation",
    "urls_count": 907,
    "raw_files": 907,
    "processed_files": 3894
  }
]
```

---

### 3. add_source

เพิ่ม source ใหม่

**Parameters:**
- `name` (required): ชื่อ source (unique)
- `urls` (required): list ของ URLs
- `category` (optional): หมวดหมู่
- `description` (optional): คำอธิบาย
- `chunk_size` (optional): ขนาด chunk (default: 1000)
- `chunk_overlap` (optional): overlap (default: 200)

**Example:**
```json
{
  "name": "fastapi",
  "urls": ["https://fastapi.tiangolo.com/tutorial/"],
  "category": "framework",
  "description": "FastAPI documentation"
}
```

---

### 4. crawl_source

Crawl และ index source

**Parameters:**
- `name` (required): ชื่อ source

**Response:**
```json
{
  "success": true,
  "source": "fastapi",
  "results": {
    "urls_total": 50,
    "urls_success": 48,
    "chunks_indexed": 1200
  }
}
```

---

### 5. get_source_stats

ดูสถิติของ source

**Parameters:**
- `name` (required): ชื่อ source

---

### 6. delete_source

ลบ source

**Parameters:**
- `name` (required): ชื่อ source
- `keep_metadata` (optional): เก็บ metadata ไว้ (default: false)

---

### 7. get_search_stats

ดูสถิติระบบ search

---

## Resources

### pipeline://status

ดูสถานะ pipeline โดยรวม

### source://{name}/metadata

ดู metadata ของ source

### source://{name}/content

ดูตัวอย่าง content จาก source

### search://stats

ดูสถิติระบบ search

### docs://help

ดูคู่มือการใช้งาน

---

## Prompts

### search_help

แนะนำการใช้งาน search

### add_source_guide

แนะนำการเพิ่ม source

### source_analysis

วิเคราะห์ source (ต้องระบุ name)

### query_refinement

ช่วยปรับปรุง query

---

## ตัวอย่างการใช้งานกับ Claude

### ค้นหาข้อมูล

```
User: หาข้อมูลเกี่ยวกับ ORM ใน Odoo ให้หน่อย

Claude: [เรียก search_docs]
        query="ORM Odoo models fields"
        category="odoo"
        
        [ผลลัพธ์]
        
        นี่คือข้อมูลที่เจอ...
```

### เพิ่ม source ใหม่

```
User: เพิ่ม FastAPI documentation เข้าไปในระบบ

Claude: [เรียก add_source]
        name="fastapi"
        urls=["https://fastapi.tiangolo.com/tutorial/"]
        category="framework"
        
        [เสร็จสิ้น]
        
        เพิ่ม FastAPI แล้ว ต้องการให้ crawl เลยไหม?
```

### ดูสถิติ

```
User: มี sources อะไรบ้างในระบบ?

Claude: [เรียก list_sources]
        
        [ผลลัพธ์]
        
        มี sources ดังนี้:
        1. odoo (erp) - 907 files
        2. fastapi (framework) - 120 files
```

---

## Troubleshooting

### Error: Module not found

```bash
# ตรวจสอบว่าอยู่ใน project root
pwd  # ควรเป็น /path/to/rag-data-pipeline

# ติดตั้ง dependencies
pip install -r requirements.txt
```

### Error: Database not found

```bash
# สร้าง data directory
mkdir -p data/sources data/vector_db

# หรือระบุ path
export RAG_DATA_PATH="/path/to/data"
```

### Error: Embedding model not loaded

```bash
# ติดตั้ง sentence-transformers
pip install sentence-transformers
```

---

## Testing

### ทดสอบด้วย MCP Inspector

```bash
# Install inspector
npm install -y @modelcontextprotocol/inspector

# Run server with inspector
npx @modelcontextprotocol/inspector python -m src.mcp_server_v3
```

### ทดสอบด้วย Python

```python
from src.mcp_tools import SearchTool, SourceTools

# Test search
search = SearchTool()
results = search.search("ORM models", category="odoo")
print(results)

# Test sources
sources = SourceTools()
print(sources.list_sources())
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RAG_DATA_PATH` | `./data` | Data directory path |
| `MCP_TRANSPORT` | `stdio` | Transport type |
| `MCP_PORT` | `8000` | HTTP port |

---

## ข้อควรระวัง

1. **First search is slow**: โหลด embedding model ครั้งแรกใช้เวลา
2. **Disk space**: Vector DB อาจใหญ่ขึ้นตามจำนวน documents
3. **Rate limiting**: Crawl ช้าๆ เพื่อไม่ให้โดน block

---

## ติดต่อ & Support

- Issues: [GitHub Issues](https://github.com/anatsrii/rag-data-pipeline/issues)
- Docs: `docs://help` (ผ่าน MCP)
