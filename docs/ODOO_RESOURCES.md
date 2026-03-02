# Odoo Resources

รวมแหล่งข้อมูลสำคัญสำหรับการพัฒนา Odoo

---

## 1. Core Repository (ตัวหลัก)

### Odoo Source Code
- **URL**: https://github.com/odoo/odoo
- **คำอธิบาย**: ตัวโปรเจกต์หลักที่ต้อง Fork หรือ Clone มาติดตั้ง
- **ประกอบด้วย**: 
  - Python (Backend)
  - JavaScript (Frontend)
  - XML (Views)
  - CSS/SCSS (Styling)

**วิธีใช้กับ RAG Pipeline**:
```yaml
# config/sources.yaml
sources:
  - name: "odoo_source"
    description: "Odoo Core Source Code"
    category: "core"
    urls:
      - "https://github.com/odoo/odoo/tree/17.0/odoo"
      - "https://github.com/odoo/odoo/tree/17.0/addons"
    chunk_size: 1500  # Code files are dense
```

---

### Odoo Community Association (OCA)
- **URL**: https://github.com/OCA
- **คำอธิบาย**: แหล่งรวมโมดูลเสริม (Add-ons) ที่ใหญ่ที่สุดในโลก
- **จุดเด่น**: Code ระดับมาตรฐานสากล เป็นตัวอย่างที่ดีในการเขียน

**Popular OCA Repositories**:
| Repo | คำอธิบาย |
|------|---------|
| `oca/server-tools` | เครื่องมือสำหรับ server |
| `oca/web` | Web client extensions |
| `oca/sale-workflow` | การขาย |
| `oca/purchase-workflow` | การจัดซื้อ |
| `oca/stock-logistics` | คลังสินค้า |

**วิธีใช้กับ RAG Pipeline**:
```yaml
sources:
  - name: "oca_server_tools"
    description: "OCA Server Tools"
    category: "oca"
    urls:
      - "https://github.com/OCA/server-tools/tree/17.0"
```

---

## 2. OWL Framework (หัวใจของ Frontend)

### OWL Framework Official
- **URL**: https://github.com/odoo/owl
- **คำอธิบาย**: Library หลักที่ Odoo พัฒนาขึ้นเอง (คล้าย React)
- **ใช้ใน**: Odoo 14+ แทน Backbone.js

**Key Concepts**:
- Components (คล้าย React components)
- Props (รับข้อมูลจาก parent)
- State (ข้อมูลภายใน component)
- Hooks (useState, useEffect, ฯลฯ)
- Reactive system

**วิธีใช้กับ RAG Pipeline**:
```yaml
sources:
  - name: "owl_framework"
    description: "OWL Framework Documentation"
    category: "frontend"
    urls:
      - "https://github.com/odoo/owl/tree/master/doc"
      - "https://github.com/odoo/owl/tree/master/examples"
```

---

### OWL Tutorial / Playground
- **Playground**: https://odoo.github.io/owl/playground/
- **Tutorial**: https://github.com/odoo/owl/tree/master/doc

**เริ่มต้นเร็วๆ**:
```javascript
// Simple OWL Component
const { Component, xml } = owl;

class MyComponent extends Component {
    static template = xml`
        <div class="my-component">
            <h1>Hello OWL!</h1>
            <p>Count: <t t-esc="state.count"/></p>
            <button t-on-click="increment">+</button>
        </div>
    `;
    
    state = { count: 0 };
    
    increment() {
        this.state.count++;
    }
}
```

---

## 3. แหล่งเรียนรู้และเครื่องมือ

### Odoo Documentation (Official)
- **URL**: https://www.odoo.com/documentation/17.0/
- **ประกอบด้วย**:
  - Developer Tutorial
  - API Reference
  - ORM Documentation
  - Views and Actions
  - Security (Access Rights)
  - Testing

**วิธีใช้กับ RAG Pipeline**:
```yaml
sources:
  - name: "odoo_docs"
    description: "Odoo 17.0 Documentation"
    category: "documentation"
    urls:
      - "https://www.odoo.com/documentation/17.0/developer.html"
      - "https://www.odoo.com/documentation/17.0/applications.html"
```

---

### VS Code Extension for Odoo
- **Extension**: `Odoo Snippets` หรือ `Odoo IDE`
- **Features**:
  - Syntax highlighting สำหรับ XML (Odoo views)
  - Auto-complete สำหรับ Python (Odoo models)
  - Snippets สำหรับสร้าง module ใหม่
  - Linting

**ติดตั้ง**:
1. เปิด VS Code
2. Extensions → Search "Odoo"
3. ติดตั้ง `Odoo Snippets` หรือ `Odoo IDE`

---

## 4. ตัวอย่างการเขียน (Full-stack)

### Odoo OWL Samples
- **URL**: https://github.com/odoo/owl/tree/master/examples
- **คำอธิบาย**: โปรเจกต์ตัวอย่างเล็กๆ ที่เขียนด้วย OWL เพียวๆ

**Examples ที่มี**:
- `counter` - ตัวนับพื้นฐาน
- `todo_list` - Todo app แบบเต็ม
- `form_validation` - การ validate form
- `routing` - Client-side routing

**เรียนรู้จาก Examples**:
- State management
- Props passing
- Event handling
- Component lifecycle

---

## 5. แหล่งข้อมูลเพิ่มเติม

### YouTube Channels
| Channel | เนื้อหา |
|---------|---------|
| Odoo | Official tutorials |
| Odoo Mates | Technical tutorials |
| Cybrosys Technologies | Odoo development |

### Forums & Communities
- **Odoo Forum**: https://www.odoo.com/forum/help-1
- **Reddit r/Odoo**: https://www.reddit.com/r/Odoo/
- **Stack Overflow**: Tag `odoo`

### Books
- "Odoo Development Cookbook" - Packt Publishing
- "Odoo 14 Development Essentials" - Daniel Reis

---

## 6. ใช้กับ RAG Pipeline

### ตัวอย่าง Config ครบถ้วน

```yaml
# config/sources.yaml - Odoo Complete Setup

sources:
  # Core Documentation
  - name: "odoo_docs"
    description: "Odoo 17.0 Official Documentation"
    category: "documentation"
    urls:
      - "https://www.odoo.com/documentation/17.0/developer.html"
      - "https://www.odoo.com/documentation/17.0/applications.html"
    chunk_size: 1000

  # OWL Framework
  - name: "owl_framework"
    description: "OWL Framework Docs & Examples"
    category: "frontend"
    urls:
      - "https://github.com/odoo/owl/tree/master/doc"
      - "https://odoo.github.io/owl/playground/"
    chunk_size: 800

  # OCA Modules (เลือกบางส่วน)
  - name: "oca_server_tools"
    description: "OCA Server Tools"
    category: "oca"
    urls:
      - "https://github.com/OCA/server-tools/tree/17.0"
    chunk_size: 1500

  - name: "oca_web"
    description: "OCA Web Extensions"
    category: "oca"
    urls:
      - "https://github.com/OCA/web/tree/17.0"
    chunk_size: 1500

categories:
  documentation: "Official Documentation"
  frontend: "Frontend Development"
  oca: "OCA Community Modules"
  core: "Core Source Code"
```

### คำสั่งรัน

```bash
# Add sources
python -c "
from src.mcp_tools import SourceTools
tools = SourceTools()
tools.add_source('odoo_docs', ['https://www.odoo.com/documentation/17.0/'], 'documentation')
tools.add_source('owl_framework', ['https://github.com/odoo/owl/tree/master/doc'], 'frontend')
"

# Crawl
python -c "
from src.mcp_tools import SourceTools
tools = SourceTools()
tools.crawl_source('odoo_docs')
tools.crawl_source('owl_framework')
"

# Search
python -c "
from src.mcp_tools import SearchTool
search = SearchTool()
results = search.search('OWL component lifecycle', category='frontend')
print(results)
"
```

---

## 7. Quick Reference

### ค้นหาข้อมูลยังไง?

| อยากรู้เรื่อง | ค้นหาใน | ตัวอย่าง Query |
|-------------|---------|---------------|
| ORM Models | odoo_docs | "ORM models fields" |
| OWL Components | owl_framework | "OWL component props" |
| View XML | odoo_docs | "tree view arch" |
| Security | odoo_docs | "access rights groups" |
| OCA Modules | oca_* | "server tools cron" |

---

**พร้อมเพิ่ม sources เหล่านี้เข้าไปใน RAG Pipeline ไหมครับ?**
