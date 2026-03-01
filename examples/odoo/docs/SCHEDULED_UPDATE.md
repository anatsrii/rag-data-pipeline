# Scheduled Update Guide

คู่มือการใช้งานระบบอัพเดตข้อมูลแบบ Manual สำหรับ Odoo 19 Documentation

---

## 📋 สารบัญ

1. [ภาพรวม](#ภาพรวม)
2. [การติดตั้ง](#การติดตั้ง)
3. [การใช้งาน](#การใช้งาน)
4. [ตัวเลือกต่างๆ](#ตัวเลือกต่างๆ)
5. [ตัวอย่างการใช้งาน](#ตัวอย่างการใช้งาน)
6. [การแก้ไขปัญหา](#การแก้ไขปัญหา)
7. [การตั้งค่า Cron (Optional)](#การตั้งค่า-cron-optional)

---

## ภาพรวม

ระบบ `scheduled_update.py` เป็นเครื่องมือสำหรับอัพเดตข้อมูลเอกสาร Odoo 19 แบบ **manual** โดย:

- **ไม่บังคับใช้**: ผู้ใช้สามารถเลือกได้ว่าจะอัพเดตหรือไม่
- **Flexible**: อัพเดตทั้งหมดหรือบางส่วนก็ได้
- **Safe**: มี dry-run mode สำหรับทดสอบก่อน

### กระบวนการทำงาน

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Crawl URLs    │────▶│  Index to DB    │────▶│ Update Metadata │
│  (ดึงข้อมูลใหม่)  │     │ (สร้าง vector)   │     │  (อัพเดตรายงาน)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## การติดตั้ง

### 1. ตรวจสอบ Dependencies

```bash
# ตรวจสอบว่าติดตั้งครบแล้ว
pip install -r requirements.txt
```

### 2. ตรวจสอบ Path ฐานข้อมูล

```yaml
# config/config.yaml
rag:
  db_path: "E:/sandbox_claude/data/odoo19_chroma_db"  # ตรวจสอบว่าถูกต้อง
```

### 3. สิทธิ์การเข้าถึง

- ต้องมีสิทธิ์ **read/write** ที่ `raw_docs/`
- ต้องมีสิทธิ์ **read/write** ที่ `E:/sandbox_claude/data/odoo19_chroma_db/`

---

## การใช้งาน

### คำสั่งพื้นฐาน

```bash
# อัพเดตทั้งหมด (crawl + index)
python scheduled_update.py --full

# หรือใช้ short option
python scheduled_update.py -f
```

### โครงสร้างคำสั่ง

```bash
python scheduled_update.py [ACTION] [OPTIONS]
```

#### Actions (เลือกอย่างน้อย 1 อย่าง)

| Option | Description |
|--------|-------------|
| `--full` | อัพเดตทั้งหมด: crawl + index |
| `--crawl-only` | Crawl อย่างเดียว |
| `--index-only` | Index อย่างเดียว |

#### Options (optional)

| Option | Description | Default |
|--------|-------------|---------|
| `--max-pages N` | จำกัดจำนวนหน้า | ทั้งหมด |
| `--dry-run` | ทดสอบโดยไม่บันทึก | False |

---

## ตัวเลือกต่างๆ

### 1. `--full` - อัพเดตทั้งหมด

```bash
python scheduled_update.py --full
```

**เหมาะสำหรับ**: อัพเดตครั้งแรก หรือต้องการข้อมูลล่าสุดทั้งหมด

**ผลลัพธ์**:
- Crawl ทุก URL จาก `urls.txt`
- Index ข้อมูลใหม่ทั้งหมด
- อัพเดต metadata และ report

**เวลา**: ~30-60 นาที (ขึ้นกับจำนวน URL)

---

### 2. `--crawl-only` - Crawl อย่างเดียว

```bash
python scheduled_update.py --crawl-only
```

**เหมาะสำหรับ**: ต้องการดึงข้อมูลใหม่แต่ยังไม่ต้องการ index

**ผลลัพธ์**:
- Crawl ทุก URL
- บันทึกไฟล์ Markdown ที่ `raw_docs/`
- **ไม่** index

**ใช้เมื่อ**:
- ต้องการตรวจสอบคุณภาพข้อมูลก่อน
- จะ index ทีหลังด้วย `--index-only`

---

### 3. `--index-only` - Index อย่างเดียว

```bash
python scheduled_update.py --index-only
```

**เหมาะสำหรับ**: Re-index ข้อมูลที่มีอยู่

**ผลลัพธ์**:
- ลบ index เก่าทั้งหมด
- Index ไฟล์ใน `raw_docs/` ใหม่
- อัพเดต metadata

**ใช้เมื่อ**:
- ฐานข้อมูลเสียหาย
- ต้องการเปลี่ยน embedding model
- ไฟล์ Markdown มีปัญหา

---

### 4. `--max-pages N` - จำกัดจำนวนหน้า

```bash
# อัพเดตแค่ 100 หน้าแรก
python scheduled_update.py --full --max-pages 100
```

**เหมาะสำหรับ**: ทดสอบระบบ หรืออัพเดตเฉพาะส่วน

**ผลลัพธ์**:
- Crawl แค่ N หน้าแรกจาก `urls.txt`
- Index เฉพาะหน้าที่ crawl ได้

---

### 5. `--dry-run` - ทดสอบ

```bash
python scheduled_update.py --full --dry-run
```

**เหมาะสำหรับ**: ทดสอบก่อนรัน

**ผลลัพธ์**:
- แสดงขั้นตอนที่จะทำ
- **ไม่บันทึก** อะไรลง disk
- **ไม่เปลี่ยนแปลง** ฐานข้อมูล

---

## ตัวอย่างการใช้งาน

### ตัวอย่างที่ 1: อัพเดตครั้งแรก

```bash
# 1. ทดสอบก่อน
python scheduled_update.py --full --dry-run

# 2. รันจริง
python scheduled_update.py --full
```

### ตัวอย่างที่ 2: อัพเดตบางส่วน

```bash
# อัพเดตแค่ 50 หน้าใหม่
python scheduled_update.py --full --max-pages 50
```

### ตัวอย่างที่ 3: Re-index หลังแก้ไขไฟล์

```bash
# สมมติแก้ไขไฟล์ใน raw_docs/ ด้วยมือ
# ต้องการ index ใหม่

python scheduled_update.py --index-only
```

### ตัวอย่างที่ 4: อัพเดตแบบขั้นตอน

```bash
# 1. Crawl ก่อน
python scheduled_update.py --crawl-only --max-pages 200

# 2. ตรวจสอบคุณภาพไฟล์ที่ raw_docs/

# 3. Index ถ้าพอใจ
python scheduled_update.py --index-only
```

---

## การแก้ไขปัญหา

### ปัญหาที่ 1: Permission Denied

**อาการ**:
```
PermissionError: [Errno 13] Permission denied: 'raw_docs/...'
```

**แก้ไข**:
```bash
# Windows - รัน PowerShell แบบ Administrator
# หรือตรวจสอบสิทธิ์ folder

# Linux/Mac
chmod -R 755 raw_docs/
chmod -R 755 E:/sandbox_claude/data/odoo19_chroma_db/
```

---

### ปัญหาที่ 2: Database Locked

**อาการ**:
```
chromadb.errors.ChromaError: Database is locked
```

**แก้ไข**:
```bash
# 1. ปิดโปรแกรมที่ใช้ database อยู่
# 2. รอ 10 วินาที
# 3. รันใหม่

# หรือลบ lock file (ระวัง!)
rm E:/sandbox_claude/data/odoo19_chroma_db/chroma.sqlite3-journal
```

---

### ปัญหาที่ 3: Out of Memory

**อาการ**:
```
MemoryError: Unable to allocate array
```

**แก้ไข**:
```bash
# ใช้ --max-pages จำกัดจำนวน
python scheduled_update.py --full --max-pages 100

# หรือ crawl ทีละส่วน
python scheduled_update.py --crawl-only --max-pages 100
python scheduled_update.py --index-only
```

---

### ปัญหาที่ 4: Network Timeout

**อาการ**:
```
TimeoutError: Connection timed out
```

**แก้ไข**:
```bash
# ตรวจสอบ internet connection
ping www.odoo.com

# รันใหม่ (ระบบจะ resume อัตโนมัติ)
python scheduled_update.py --full
```

---

### ปัญหาที่ 5: Import Error

**อาการ**:
```
ModuleNotFoundError: No module named 'chromadb'
```

**แก้ไข**:
```bash
pip install -r requirements.txt
```

---

## การตั้งค่า Cron (Optional)

ถ้าต้องการให้อัพเดตอัตโนมัติ (ไม่ใช่ manual):

### Windows (Task Scheduler)

```powershell
# สร้าง scheduled task
schtasks /create /tn "OdooDocsUpdate" /tr "python E:\sandbox_claude\odoo\RAG_data_Odoo\scheduled_update.py --full" /sc weekly /d SUN /st 02:00
```

### Linux/Mac (Cron)

```bash
# แก้ไข crontab
crontab -e

# เพิ่มบรรทัดนี้ (อัพเดตทุกวันอาทิตย์ ตี 2)
0 2 * * 0 cd /path/to/RAG_data_Odoo && python scheduled_update.py --full >> logs/update.log 2>&1
```

### หมายเหตุ

- ตั้งค่า cron **optional** เท่านั้น
- ค่าเริ่มต้น: **manual update**
- แนะนำให้ตั้งค่าไม่บ่อยเกินไป (เช่น อาทิตย์ละครั้ง) เพราะเอกสาร Odoo ไม่เปลี่ยนบ่อย

---

## ไฟล์ที่เกี่ยวข้อง

| ไฟล์ | คำอธิบาย |
|------|---------|
| `scheduled_update.py` | สคริปต์หลักสำหรับอัพเดต |
| `config/update_log.json` | ประวัติการอัพเดต (10 ครั้งล่าสุด) |
| `raw_docs/` | โฟลเดอร์เก็บ Markdown files |
| `E:/sandbox_claude/data/odoo19_chroma_db/` | Vector database |

---

## Checklist ก่อนอัพเดต

- [ ] ตรวจสอบว่ามีพื้นที่ disk เพียงพอ (> 500 MB)
- [ ] ตรวจสอบ internet connection
- [ ] ปิดโปรแกรมที่ใช้ database อยู่
- [ ] ทดสอบด้วย `--dry-run` ก่อน (แนะนำ)
- [ ] Backup ข้อมูลสำคัญ (ถ้ามี)

---

## สรุป

| สถานการณ์ | คำสั่ง |
|-----------|--------|
| อัพเดตครั้งแรก | `python scheduled_update.py --full` |
| อัพเดตทั้งหมด | `python scheduled_update.py --full` |
| อัพเดตบางส่วน | `python scheduled_update.py --full --max-pages 100` |
| Re-index | `python scheduled_update.py --index-only` |
| ทดสอบ | `python scheduled_update.py --full --dry-run` |

---

## การสนับสนุน

หากพบปัญหา:

1. ตรวจสอบ log ที่ `config/update_log.json`
2. รันด้วย `--dry-run` เพื่อทดสอบ
3. ตรวจสอบสิทธิ์การเข้าถึงไฟล์
