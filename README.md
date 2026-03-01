# Odoo 19 Documentation Crawler

> 📑 Project Orchestrator: ดึงข้อมูลจาก Official Odoo 19 Documentation (Developer & User Docs) มาเก็บเป็น Local Markdown เพื่อใช้เป็น Dataset สำหรับ RAG

---

## 🎯 เป้าหมาย

ดึงข้อมูลจาก [Official Odoo 19 Documentation](https://www.odoo.com/documentation/19.0/) มาเก็บเป็น Local Markdown format เพื่อใช้เป็น Dataset สำหรับระบบ RAG (Retrieval-Augmented Generation)

---

## 🛠️ Phase 1: Environment Setup

### Requirements

- **Python**: 3.10+
- **Main Libraries**:
  - `requests` / `httpx`: สำหรับดึง HTML
  - `beautifulsoup4`: สำหรับ Parse ข้อมูล
  - `playwright`: สำหรับหน้าเว็บที่มี JavaScript เยอะๆ
  - `html2text`: แปลง HTML เป็น Markdown
  - `pyyaml`: จัดการ configuration
  - `tqdm`: Progress bar

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

---

## 🏗️ Phase 2: Crawler Architecture

### Project Structure

```
RAG_data_Odoo/
├── config/
│   ├── config.yaml          # การตั้งค่าหลัก
│   ├── crawler.log          # Log file
│   ├── metadata.json        # Metadata database
│   ├── crawled_cache.json   # Crawled URLs cache
│   └── failed_urls.json     # Failed URLs log
├── raw_docs/                # เอกสารที่ดึงมา
│   ├── developer/           # Developer documentation
│   ├── functional/          # Functional/User documentation
│   ├── setup/               # Setup/Administration docs
│   └── images/              # Downloaded images (optional)
├── src/
│   ├── __init__.py
│   ├── main.py              # Main entry point
│   ├── config_loader.py     # Configuration management
│   ├── url_discovery.py     # URL discovery from sitemap/sidebar
│   ├── queue_manager.py     # URL queue & duplicate prevention
│   ├── content_extractor.py # HTML to Markdown conversion
│   ├── crawler_engine.py    # Main crawling engine
│   └── metadata_manager.py  # Metadata & quality control
├── requirements.txt
└── README.md
```

### Core Components

| Component | Description |
|-----------|-------------|
| **URL Discovery** | ค้นหา URLs จาก Sitemap, Sidebar navigation |
| **Queue Manager** | จัดการคิว URL, ป้องกันการ crawl ซ้ำ |
| **Content Extractor** | ดึงเนื้อหาหลัก, แปลงเป็น Markdown |
| **Crawler Engine** | Engine หลัก พร้อมรองรับ Playwright |
| **Metadata Manager** | จัดการ Metadata และ Quality Control |

---

## 🚀 Phase 3: Usage Guide

### 1. ค้นหา URLs (Discover)

```bash
# ค้นหา URLs ทั้งหมด
python -m src.main discover --output urls.txt

# ค้นหาเฉพาะ Developer docs
python -m src.main discover --category developer --output dev_urls.txt

# แสดงรายละเอียด
python -m src.main discover --verbose
```

### 2. ทดสอบดึงข้อมูลหน้าเดียว (Test)

```bash
# ทดสอบดึงข้อมูลหน้าเดียว
python -m src.main test https://www.odoo.com/documentation/19.0/developer.html --save test.md --verbose
```

### 3. เริ่ม Crawl

```bash
# Crawl ด้วย auto-discovery
python -m src.main crawl --discover --max-pages 100

# Crawl จากไฟล์ URLs
python -m src.main crawl --urls urls.txt --max-pages 50

# Crawl ทั้งหมด (ไม่จำกัดจำนวน)
python -m src.main crawl --discover
```

### 4. ตรวจสอบสถานะ

```bash
# ดูสถานะ crawler
python -m src.main status
```

### 5. สร้างรายงาน

```bash
# สร้าง quality report
python -m src.main report --output report.txt
```

### 6. รีเซ็ต (Reset)

```bash
# ล้าง cache และเริ่มใหม่
python -m src.main reset --force
```

---

## ⚙️ Configuration

แก้ไขไฟล์ `config/config.yaml` เพื่อปรับแต่งการทำงาน:

```yaml
# Odoo Documentation URLs
odoo:
  base_url: "https://www.odoo.com/documentation/19.0"
  developer_url: "https://www.odoo.com/documentation/19.0/developer.html"
  user_url: "https://www.odoo.com/documentation/19.0/applications.html"

# Crawler Settings
crawler:
  delay: 2                    # วินาทีระหว่าง requests
  timeout: 30                 # Request timeout
  max_retries: 3              # จำนวน retry
  use_playwright: true        # ใช้ Playwright สำหรับ JS-heavy pages

# Storage
storage:
  raw_docs_path: "./raw_docs"
  organize_by_category: true  # จัดเก็บแยกตาม category
```

---

## 📊 Phase 4: Quality Control & Metadata

### Metadata ที่เก็บ

แต่ละเอกสารจะมี metadata ใน YAML frontmatter:

```yaml
---
source_url: https://www.odoo.com/documentation/19.0/developer.html
title: Developer Documentation
version: "19.0"
category: developer
last_crawled: "2026-03-01T10:30:00"
word_count: 1523
headings_structure:
  - Overview
    - Getting Started
    - Installation
---
```

### Quality Score

ระบบจะคำนวณ Quality Score (0-100) ตาม:
- Content length (30 points)
- Has title (10 points)
- Headings structure (20 points)
- Code examples (20 points)
- Formatting quality (20 points)

---

## ⚠️ Phase 5: Constraints & Optimization

### Rate Limiting

```yaml
crawler:
  delay: 2  # รอ 2 วินาทีระหว่าง requests
```

### Error Handling

- ระบบจะ retry อัตโนมัติ 3 ครั้ง หาก request ล้มเหลว
- บันทึก failed URLs ลงไฟล์ `config/failed_urls.json`
- สามารถ retry failed URLs ได้ภายหลัง

### Update Cycle

แนะนำให้ตั้งเวลา crawl ซ้ำทุก 1-2 สัปดาห์:

```bash
# Linux/Mac (cron)
0 0 * * 0 cd /path/to/project && python -m src.main crawl --discover

# Windows (Task Scheduler)
# สร้าง task รัน script ทุกวันอาทิตย์
```

---

## 📁 Output Format

### Markdown Structure

```markdown
---
source_url: https://www.odoo.com/documentation/19.0/developer/tutorials.html
title: Tutorials
version: "19.0"
category: developer
---

# Tutorials

## Building a Module

เนื้อหาหลัก...

### Creating Models

```python
class MyModel(models.Model):
    _name = 'my.model'
    name = fields.Char()
```

## Advanced Topics
...
```

---

## 🔧 Troubleshooting

### Playwright ไม่ทำงาน

```bash
# Reinstall Playwright
pip install --upgrade playwright
playwright install chromium
```

### โดน Block IP

- เพิ่ม `delay` ใน config
- ใช้ Proxy (เพิ่มใน `crawler_engine.py`)
- ลด `max_concurrent`

### Memory Error

- ลด `max_pages` ต่อรอบ
- รัน crawl เป็นช่วงๆ

---

## 📝 License

MIT License - สำหรับการใช้งานส่วนบุคคลและการศึกษา

---

## 🤝 Contributing

1. Fork repository
2. สร้าง feature branch
3. Commit changes
4. Push และสร้าง Pull Request

---

## 📧 Support

หากมีปัญหาในการใช้งาน สามารถ:
- ตรวจสอบ log ที่ `config/crawler.log`
- รัน command `python -m src.main status`
- ทดสอบด้วย `python -m src.main test <url>`
