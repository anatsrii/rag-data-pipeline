# AI Module Integration Guide

## วิธีให้ AI ใช้ข้อมูล Odoo 19 จากโปรเจกต์อื่น

### 1. โครงสร้างที่แนะนำสำหรับแต่ละโปรเจกต์

```
E:\sandbox_claude\
├── data/                          # Shared RAG Data
│   └── odoo19_chroma_db/         # Vector DB
│
├── odoo/                          # โปรเจกต์ Odoo
│   ├── RAG_data_Odoo/            # Crawler (ตัวนี้)
│   ├── custom_module_ai/         # โปรเจกต์ใหม่ 1
│   └── mcp_server_odoo/          # โปรเจกต์ใหม่ 2
│
└── other_projects/               # โปรเจกต์อื่นๆ
```

### 2. ใส่ใน Plan/Spec ของแต่ละโปรเจกต์

#### ตัวอย่าง: `custom_module_ai/PLAN.md`

```markdown
# Custom Module AI - Plan

## Phase 1: Setup
- [ ] สร้างโครงสร้างโปรเจกต์
- [ ] เชื่อมต่อกับ RAG Database
  - Path: `E:/sandbox_claude/data/odoo19_chroma_db`
  - ใช้ RAGEngine จาก `RAG_data_Odoo/src/rag_engine.py`

## Phase 2: Development
- [ ] สร้าง module จาก prompt ผู้ใช้
- [ ] ใช้ RAG ค้นหา reference จาก Odoo docs
- [ ] Generate code ตาม best practices

## Dependencies
- Python 3.10+
- RAG_data_Odoo (shared)
- OpenAI API / Claude API
```

### 3. Code Template สำหรับโปรเจกต์ใหม่

```python
# custom_module_ai/src/odoo_knowledge.py
import sys
from pathlib import Path

# Add RAG_data_Odoo to path
RAG_PATH = Path("E:/sandbox_claude/odoo/RAG_data_Odoo/src")
sys.path.insert(0, str(RAG_PATH))

from rag_engine import RAGEngine

class OdooKnowledge:
    """Access Odoo 19 documentation via RAG"""
    
    def __init__(self):
        self.rag = RAGEngine(
            db_path="E:/sandbox_claude/data/odoo19_chroma_db"
        )
    
    def search(self, query: str, n_results: int = 5):
        """Search Odoo documentation"""
        return self.rag.search(query, n_results=n_results)
    
    def get_module_template(self, module_type: str):
        """Get module template from docs"""
        query = f"how to create {module_type} module in Odoo"
        return self.search(query)
    
    def get_orm_examples(self):
        """Get ORM usage examples"""
        return self.search("ORM API examples models fields")
    
    def get_security_best_practices(self):
        """Get security guidelines"""
        return self.search("security access rights rules best practices")

# Usage
if __name__ == "__main__":
    knowledge = OdooKnowledge()
    
    # ค้นหาวิธีสร้าง module
    results = knowledge.get_module_template("new")
    for r in results:
        print(f"📄 {r['metadata']['title']}")
        print(f"   {r['document'][:300]}...")
```

### 4. การทำงานร่วมกัน

```
┌─────────────────────────────────────────────────────────┐
│                    AI Module Project                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ User Prompt  │→ │ RAG Search   │→ │ Generate     │  │
│  │              │  │ (Odoo Docs)  │  │ Code         │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                 ↑                 │           │
│         │                 │                 │           │
│         └─────────────────┴─────────────────┘           │
│                           │                             │
│                    ┌──────────────┐                     │
│                    │ Shared RAG   │                     │
│                    │ E:/sandbox_  │                     │
│                    │  claude/data │                     │
│                    └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

### 5. ตัวอย่าง Prompt ให้ AI

```markdown
## Context
คุณมีความรู้จาก Odoo 19 Official Documentation ผ่าน RAG Database
ที่ `E:/sandbox_claude/data/odoo19_chroma_db`

## Task
สร้าง Odoo module ที่มี:
1. Model ชื่อ `library.book`
2. Fields: name, author, isbn, published_date
3. Views: Tree, Form, Search
4. Security: ให้ user ทั่วไปอ่านได้, librarian แก้ไขได้

## Steps
1. ใช้ RAG ค้นหา "how to create new module" → ดูโครงสร้าง
2. ใช้ RAG ค้นหา "ORM API model fields" → ดูวิธีสร้าง model
3. ใช้ RAG ค้นหา "views tree form" → ดูวิธีสร้าง views
4. ใช้ RAG ค้นหา "security access rights" → ดูวิธีตั้งค่า security
5. Generate code ตาม best practices ที่พบ

## Output
- `__manifest__.py`
- `models/library_book.py`
- `views/library_book_views.xml`
- `security/ir.model.access.csv`
```

---

## Best Practices

1. **แยกโปรเจกต์ชัดเจน**
   - Crawler/Indexer → `RAG_data_Odoo/`
   - AI Modules → โปรเจกต์ละ folder

2. **ใช้ Shared Data**
   - อย่า duplicate RAG database
   - ชี้ไปที่ `E:/sandbox_claude/data/`

3. **Document ให้ครบ**
   - ใส่ใน `data/PROJECTS_USING_THIS.md`
   - อธิบายวิธีใช้ใน README ของแต่ละโปรเจกต์

4. **Version Control**
   - อย่า commit `chroma_db/` ขึ้น Git
   - ใช้ `.gitignore`
