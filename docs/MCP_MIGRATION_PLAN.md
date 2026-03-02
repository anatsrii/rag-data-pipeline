# MCP Migration Plan

แผนการ Migrate RAG Data Pipeline เป็น MCP Server

---

## 1. เป้าหมาย (Goal)

**จาก**: Python Pipeline (ต้องเรียกผ่าน code)
**เป็น**: MCP Server (AI assistants เรียกใช้ได้โดยตรง)

```
Before:  user → python script → pipeline → result
After:   user → AI assistant → MCP Server → pipeline → result
```

---

## 2. Architecture ใหม่

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Assistant                             │
│            (Claude, Kimi, Cursor, etc.)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ MCP Protocol
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Tools (AI เรียกใช้ได้)                              │   │
│  │  ├── search_docs(query, source, category)          │   │
│  │  ├── add_source(name, urls, category)              │   │
│  │  ├── crawl_source(name)                            │   │
│  │  ├── list_sources()                                │   │
│  │  ├── get_source_status(name)                       │   │
│  │  └── delete_source(name)                           │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Resources (AI อ่านได้)                              │   │
│  │  ├── source://{name}/metadata                      │   │
│  │  ├── source://{name}/stats                         │   │
│  │  └── pipeline://status                             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Python API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              RAG Data Pipeline (existing)                    │
│         ┌─────────┐    ┌──────────┐    ┌──────┐            │
│         │ Crawler │ → │ Processor │ → │  RAG │            │
│         └─────────┘    └──────────┘    └──────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Components ที่ต้องสร้าง

### 3.1 Core MCP Server (`src/mcp_server.py`)

```python
from mcp.server.fastmcp import FastMCP
from src.multi_source_pipeline import MultiSourcePipeline

mcp = FastMCP("rag-data-pipeline")

@mcp.tool()
def search_docs(query: str, n_results: int = 5) -> list:
    """Search indexed documents"""
    pass

@mcp.tool()
def add_source(name: str, urls: list[str], category: str = "") -> dict:
    """Add new data source"""
    pass

# ... more tools
```

### 3.2 Tools ที่ต้องมี

| Tool | Input | Output | ใช้ทำอะไร |
|------|-------|--------|----------|
| `search_docs` | query, source?, category?, n | results[] | ค้นหาข้อมูล |
| `add_source` | name, urls[], category, chunk_size | success/fail | เพิ่ม source ใหม่ |
| `crawl_source` | name | stats | crawl และ index |
| `list_sources` | - | sources[] | ดูรายการ sources |
| `get_source_stats` | name | stats | ดูสถิติ source |
| `delete_source` | name | success/fail | ลบ source |
| `update_source` | name, urls? | success/fail | อัพเดต URLs |

### 3.3 Resources ที่ต้องมี

| Resource | URI | เนื้อหา |
|----------|-----|---------|
| Source Metadata | `source://{name}/metadata` | ข้อมูล source |
| Source Stats | `source://{name}/stats` | จำนวน docs, chunks |
| Pipeline Status | `pipeline://status` | สถานะทั้งหมด |

---

## 4. Phase การทำงาน

### Phase 1: Basic MCP Server
- [ ] ติดตั้ง `mcp` library
- [ ] สร้าง `src/mcp_server.py`
- [ ] Implement `search_docs` tool
- [ ] Test ด้วย MCP Inspector

### Phase 2: Source Management
- [ ] Implement `add_source` tool
- [ ] Implement `list_sources` tool
- [ ] Implement `crawl_source` tool
- [ ] Implement `delete_source` tool

### Phase 3: Resources & Prompts
- [ ] Add resource: `source://{name}/metadata`
- [ ] Add resource: `source://{name}/stats`
- [ ] Add prompt: `search_help`

### Phase 4: Integration & Testing
- [ ] เขียน `mcp_config.json` สำหรับ Claude Desktop
- [ ] Test กับ Claude Desktop
- [ ] Test กับ Kimi Code
- [ ] เขียน Documentation

### Phase 5: Advanced Features
- [ ] Streaming responses
- [ ] Progress notifications
- [ ] Batch operations
- [ ] Advanced filtering

---

## 5. File Structure ที่เพิ่ม

```
rag-data-pipeline/
├── src/
│   ├── mcp_server.py           # ← NEW: MCP Server
│   ├── mcp_tools/              # ← NEW: Tool implementations
│   │   ├── __init__.py
│   │   ├── search.py
│   │   ├── sources.py
│   │   └── stats.py
│   └── ... (existing)
├── config/
│   ├── mcp_config.json         # ← NEW: Claude Desktop config
│   └── ... (existing)
├── docs/
│   ├── MCP_MIGRATION_PLAN.md   # ← นี่
│   └── MCP_USAGE.md            # ← NEW: User guide
└── ... (existing)
```

---

## 6. Configuration

### 6.1 Claude Desktop (`config/mcp_config.json`)

```json
{
  "mcpServers": {
    "rag-pipeline": {
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "env": {
        "RAG_DATA_PATH": "./data"
      }
    }
  }
}
```

### 6.2 Environment Variables

```bash
export RAG_DATA_PATH="./data"
export MCP_TRANSPORT="stdio"  # หรือ "http"
export MCP_PORT="8000"
```

---

## 7. Usage Examples (หลัง migrate)

### ผ่าน Claude Desktop

```
User: หาข้อมูลเกี่ยวกับ ORM ใน Odoo ให้หน่อย

Claude: [เรียก tool search_docs]
        query="ORM Odoo", category="odoo"
        
        [ได้ผลลัพธ์]
        
        นี่คือข้อมูลที่เจอ...
```

### ผ่าน Code

```python
from mcp import ClientSession, StdioServerParameters

# Connect to MCP server
server_params = StdioServerParameters(
    command="python",
    args=["-m", "src.mcp_server"]
)

async with ClientSession(server_params) as session:
    # Call tool
    result = await session.call_tool(
        "search_docs",
        {"query": "ORM Odoo", "n_results": 5}
    )
```

---

## 8. Dependencies เพิ่ม

```txt
# requirements-mcp.txt
mcp>=1.0.0
```

หรือเพิ่มใน `requirements.txt`:

```txt
# Existing
requests>=2.31.0
...

# MCP
mcp>=1.0.0
```

---

## 9. Testing Strategy

| ระดับ | วิธี | เป้าหมาย |
|-------|------|---------|
| Unit | pytest | แต่ละ tool ทำงานถูกต้อง |
| Integration | MCP Inspector | Server ตอบสนองถูกต้อง |
| E2E | Claude Desktop | AI ใช้งานได้จริง |

---

## 10. Timeline (ประมาณการ)

| Phase | เวลา | Deliverable |
|-------|------|-------------|
| 1 | 1-2 วัน | Basic server + search |
| 2 | 2-3 วัน | Source management |
| 3 | 1-2 วัน | Resources |
| 4 | 2-3 วัน | Testing + docs |
| 5 | 3-5 วัน | Advanced features |
| **รวม** | **1-2 สัปดาห์** | **MCP Server สมบูรณ์** |

---

## 11. ข้อควรระวัง

1. **Performance**: AI อาจเรียก tool บ่อย → ต้องมี caching
2. **Error Handling**: ต้องบอก AI ให้เข้าใจว่า error คืออะไร
3. **Context Length**: ผลลัพธ์ยาวเกิน → ต้อง truncate
4. **Security**: ไม่ควรให้ AI ลบข้อมูลสำคัญโดยไม่มี confirmation

---

## 12. Success Criteria

- [ ] AI สามารถ search หาข้อมูลได้
- [ ] AI สามารถเพิ่ม source ใหม่ได้
- [ ] AI สามารถดูสถิติได้
- [ ] Response time < 3 วินาที
- [ ] เอกสารครบถ้วน

---

**พร้อมเริ่ม Phase 1 ไหมครับ?**
