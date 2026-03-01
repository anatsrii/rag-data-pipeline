# RAG Storage Guide

## ตัวเลือกการจัดเก็บ Vector Database

### 1. เก็บในโปรเจกต์ (Default) ✅

```yaml
# config/config.yaml
rag:
  db_path: "./chroma_db"
```

**เหมาะสำหรับ:**
- เริ่มต้นใช้งาน
- พัฒนาเดี่ยว (single developer)
- ขนาดไม่ใหญ่มาก (< 100 MB)

**ข้อดี:**
- ใช้งานได้ทันที
- ไม่ต้องตั้งค่า
- ย้ายโปรเจกต์ได้ทั้งก้อน

**ข้อเสีย:**
- Git repo ใหญ่ (ต้องใส่ .gitignore)
- สำรองยาก (ต้องสำรองทั้งโปรเจกต์)

---

### 2. เก็บนอกโปรเจกต์ (แนะนำ) ⭐

```yaml
# config/config.yaml
rag:
  db_path: "E:/RAG_Databases/odoo19_chroma_db"
```

**เหมาะสำหรับ:**
- ทีมพัฒนาหลายคน
- ใช้กับหลายโปรเจกต์
- ขนาดใหญ่ (> 100 MB)

**ข้อดี:**
- Git repo เล็ก
- สำรองเฉพาะ DB ได้
- ใช้ร่วมกันได้

**ข้อเสีย:**
- ต้องตั้งค่า path
- ย้ายเครื่องต้องย้าย DB ด้วย

---

### 3. External ChromaDB Server (Production) 🚀

```yaml
# config/config.yaml
rag:
  db_host: "localhost"
  db_port: 8000
```

**เหมาะสำหรับ:**
- Production environment
- หลาย application ใช้ร่วมกัน
- ต้องการ scalability

**ข้อดี:**
- แยก service ชัดเจน
- Scale ได้
- หลาย app ใช้ร่วมกัน

**ข้อเสีย:**
- ต้อง setup server
- ดูแลเพิ่ม

---

## การย้าย Database

### ย้ายจากโปรเจกต์ → นอกโปรเจกต์

```powershell
# 1. หยุดการทำงานก่อน
# 2. คัดลอกโฟลเดอร์
Copy-Item -Path "./chroma_db" -Destination "E:/RAG_Databases/odoo19_chroma_db" -Recurse

# 3. แก้ไข config
# config/config.yaml
# rag:
#   db_path: "E:/RAG_Databases/odoo19_chroma_db"

# 4. ลบของเก่า (ถ้าต้องการ)
Remove-Item -Path "./chroma_db" -Recurse
```

### สำรอง Database

```powershell
# สำรอง
Compress-Archive -Path "./chroma_db" -DestinationPath "backup_chroma_db.zip"

# กู้คืน
Expand-Archive -Path "backup_chroma_db.zip" -DestinationPath "."
```

---

## ขนาด Database ปัจจุบัน

| รายการ | ขนาด |
|--------|-------|
| ChromaDB (907 docs) | ~65 MB |
| Raw Markdown | ~11 MB |
| **รวม** | **~76 MB** |

---

## คำแนะนำ

| สถานการณ์ | แนะนำ |
|-----------|-------|
| เริ่มต้น/พัฒนาคนเดียว | เก็บในโปรเจกต์ |
| ทีมพัฒนา/ขนาดใหญ่ | เก็บนอกโปรเจกต์ |
| Production/Enterprise | External ChromaDB Server |
| ใช้หลายเครื่อง | Cloud Vector DB (Pinecone) |
