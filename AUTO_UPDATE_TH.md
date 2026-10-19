# อัปเดตความรู้นิติ๊ทุกวัน เวลา 20:00 น.

GitHub ตรวจ Wiki วันละครั้ง **20:00 น. เวลาไทย** และมีปุ่ม Run workflow สำหรับสั่งทันที ตารางนี้แทนคำขอเดิมทุก 12 ชั่วโมง GitHub อาจเริ่มช้ากว่าเวลาที่กำหนด จึงเป็นข้อมูลอัปเดตรายวัน ไม่ใช่ Realtime

## สิ่งที่อัปเดต

- อ่านหน้าที่เผยแพร่ใน Wiki สองชุด: Solution และ Develop รวมหน้าใหม่ในสองชุดนี้
- ใช้ข้อความเดิมของหน้าที่ revision/เวลาแก้ไขไม่เปลี่ยน โดยตรวจ hash ก่อนใช้ ดึงข้อความใหม่เฉพาะหน้าที่เพิ่มหรือเปลี่ยน
- ตรวจรายการหน้าและโครงสร้างก่อน–หลัง หากอ่านไม่ครบ สิทธิ์หาย หรือข้อมูลเปลี่ยนกลางรอบ จะหยุดและเก็บชุดสำเร็จเดิม
- ข้อความ ตาราง และลิงก์คงตาม Wiki ไม่อ่านเอกสารภายนอกหรือดาวน์โหลดไฟล์ภาพที่ลิงก์ไว้
- หากหน้าเดิมหายโดยไม่ยืนยันว่า archive/delete/unpublish จะหยุดรอผู้ดูแลตรวจ ไม่ถือว่า HTTP 404 คือถูกลบ

## ผู้ดูแลเปิดใช้งานครั้งแรก

1. สร้าง API key แบบอ่านใน Wiki จาก Settings → API & Apps ให้เห็น Solution และ Develop ใช้ endpoint scopes `collections.info collections.documents documents.list documents.info` หรือตัวเลือกอ่านเท่านั้นตามรุ่นที่รองรับ
2. เปิด [GitHub Actions Secrets](https://github.com/nitiphoomkk-dev/nitii-logic-suite/settings/secrets/actions) → New repository secret
3. ตั้งชื่อ **WIKI_API_KEY** แล้วใส่ค่า key เองในช่อง Secret ไม่ใส่ในแชต ไฟล์ หรือคู่มือ
4. เปิด [Actions](https://github.com/nitiphoomkk-dev/nitii-logic-suite/actions) → **Update NaYoo knowledge - 20.00 Bangkok** → Run workflow โดยไม่เลือก bootstrap_only
5. เมื่อผลสำเร็จ ให้ดู checkedAtUtc และ syncedAtUtc ใน [latest.json](https://raw.githubusercontent.com/nitiphoomkk-dev/nitii-logic-suite/knowledge/latest.json)

ตัวเลือก bootstrap_only ใช้ตั้งฐานจากแพ็กเกจ v1.1 เดิมครั้งเดียว ผลนั้นมี `bootstrap: true` และ `checkedAtUtc: null` จนกว่าจะซิงก์ Wiki สำเร็จจริง การมีไฟล์ Workflow หรือผลทดสอบผ่านยังไม่หมายถึงเชื่อม Wiki สำเร็จ

## คนติดตั้งรับรุ่นใหม่อย่างไร

**ติดตั้งแพ็กเกจ 1.2 ครั้งเดียวก่อน** รุ่น 1.1 เดิมยังเป็นสำเนาเดิม ไม่ได้รับสคริปต์ใหม่ด้วยตัวเอง

### Codex / Claude / Gemini ที่รัน Python และออกอินเทอร์เน็ตได้

จากโฟลเดอร์สกิล `nitii-knowledge` ให้ AI เรียก:

```sh
python scripts/update_knowledge.py
```

แบบ Standalone ให้ใช้ `modules/nitii-knowledge/scripts/update_knowledge.py` ตัวอัปเดตตรวจไฟล์เล็กก่อน ถ้ารุ่นข้อมูลเดิมไม่ดาวน์โหลดชุดใหญ่อีก ถ้าเปลี่ยนจะตรวจ hash และไฟล์ทุกหน้าแล้วสลับชุดทั้งชุด เก็บไว้ที่ `~/.cache/nitii-logic-suite` สคริปต์ค้น/อ่านในรุ่น 1.2 ใช้ cache ที่ตรวจแล้วโดยอัตโนมัติ ไม่เปลี่ยนโค้ดหรือคำสั่งสกิล และผู้รับไม่ต้องมี Wiki API key

ให้ AI ทำครั้งเดียวเมื่อเริ่มแชตหรือก่อนตอบเรื่องที่ต้องใช้กฎล่าสุด หากเครื่องหรือบัญชีไม่ให้ใช้ Python/network ต้องใช้วิธีไฟล์ด้านล่างและแจ้งวันที่ข้อมูล

### ChatGPT Projects / Claude / Gemini แบบอัปโหลดไฟล์

ไฟล์ที่อัปโหลดไว้ **ยังไม่เปลี่ยนตาม GitHub เอง** วิธีใช้ข้อมูลล่าสุด:

1. เปิด latest.json แล้วดู archivePath
2. ดาวน์โหลด knowledge.zip จากสาขา knowledge ตาม archivePath เช่น `https://raw.githubusercontent.com/nitiphoomkk-dev/nitii-logic-suite/knowledge/` ต่อด้วยค่าของ archivePath
3. แตก ZIP และใช้ไฟล์ `web/NAYOO_WIKI_*.txt` พร้อม `web/UPLOAD_INDEX.txt` แทนไฟล์ความรู้ชุดเก่า เก็บ Methods/Instructions จากแพ็กเกจไว้ตามเดิม

ถ้า AI มีเครื่องมือเปิดเว็บได้ สามารถตรวจ latest.json และอ่าน manifest/หน้าที่เกี่ยวข้องจาก public feed ขณะตอบได้ แต่ต้องบอกข้อจำกัดเมื่อเปิดไม่สำเร็จ ห้ามอ้างว่าอัปเดตไฟล์ใน Project/Gem/Skill ให้แล้ว

## ตรวจสถานะและค่าใช้จ่าย

latest.json ระบุ snapshotId, จำนวนหน้า, เวลาตรวจ Wiki สำเร็จล่าสุด และ hash ของชุดข้อมูล การ publish สลับไฟล์ทั้งชุดพร้อมกัน จึงไม่ปนคนละรุ่น ถ้ารอบใหม่ล้มเหลวจะยังเห็นชุดที่สำเร็จครั้งก่อน

ใช้ standard ubuntu GitHub-hosted runner บน Public repository ซึ่ง [GitHub ระบุว่าใช้งานฟรี](https://docs.github.com/en/billing/concepts/product-billing/github-actions) ไม่มีการเรียก AI API แบบคิดเงินหรือเก็บ Actions artifacts เพิ่ม ใน public repo ที่ไม่มี activity 60 วัน GitHub อาจปิด scheduled workflow; เปิดใหม่ได้ที่ Actions ตาม [เอกสาร schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

API ใช้ [Outline read endpoints](https://www.getoutline.com/developers) และ Secret ใช้ [GitHub encrypted secrets](https://docs.github.com/en/actions/concepts/security/secrets) ควรเพิกถอน key จาก Wiki เมื่อเลิกใช้งาน
