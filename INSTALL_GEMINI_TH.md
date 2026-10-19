# ติดตั้งนิติ๊บน Gemini

[กลับหน้าเลือก AI](INSTALL_GUIDE_TH.md)

เลือกวิธีตามเมนูที่บัญชีของคุณแสดง **ถ้ามี Skills ใช้วิธี A; ถ้ายังใช้ Gems ให้ใช้วิธี B**

## วิธี A — อัปโหลด Skills ZIP

### 1. เตรียมไฟล์

ดาวน์โหลด [nitii-logic-suite-skill-1.2.0.zip](https://github.com/nitiphoomkk-dev/nitii-logic-suite/releases/download/v1.2.0/nitii-logic-suite-skill-1.2.0.zip) เก็บเป็น ZIP ไม่ต้องแตกก่อนอัปโหลด

### 2. เปิดหน้า Skills

1. เข้า [Gemini](https://gemini.google.com/) บนคอมพิวเตอร์และเข้าสู่ระบบ
2. เลือก **Customize → Skills** ถ้าไม่เห็น Customize ให้ดูใน **More**
3. เลือก **Upload** แล้วเลือก ZIP ที่ดาวน์โหลดมา
4. ตรวจชื่อและรายละเอียด แล้วกด **Create**

Google ระบุเงื่อนไขอายุอย่างน้อย 18 ปี และต้องเปิด Keep Activity สำหรับการใช้งาน Skills ตามหน้าช่วยเหลือ หากบัญชีไม่ผ่านเงื่อนไขหรือผู้ดูแลปิดไว้ ให้ตรวจสิทธิ์ของบัญชีนั้นก่อน

### 3. ทดลองใช้

เปิดแชตแล้วพิมพ์:

```text
ใช้สกิล nitii-logic-suite ค้น Logic Insert Card ของ Center
อธิบายสั้น ๆ พร้อมชื่อหน้า URL และวันที่สำเนาที่ใช้
ถ้าอ่านไฟล์ภายในไม่ได้ ให้บอกตามจริง
```

## วิธี B — สร้าง Gem พร้อมไฟล์ความรู้

### 1. ดาวน์โหลดและแตก ZIP หลัก

ดาวน์โหลด [Nitii_Logic_Suite_1.2.0.zip](https://github.com/nitiphoomkk-dev/nitii-logic-suite/releases/download/v1.2.0/Nitii_Logic_Suite_1.2.0.zip) แล้วเปิดโฟลเดอร์ที่มี `README_TH.md`

### 2. สร้าง Gem

ใน Gemini เลือก **Gems / Gem manager → New Gem** ตั้งชื่อ **นิติ๊ NaYoo**

### 3. เพิ่ม Instructions

คัดลอกข้อความทั้งหมดจาก `web-assistants/INSTRUCTIONS_TH.txt` ไปวางในช่อง **Instructions** ของ Gem

### 4. เพิ่ม Knowledge รวม 8 ไฟล์

- `web-assistants/METHODS_REFERENCE.md`
- `web-assistants/knowledge/UPLOAD_INDEX.txt`
- `web-assistants/knowledge/NAYOO_WIKI_01.txt` ถึง `NAYOO_WIKI_06.txt` รวม 6 เล่ม

บันทึก Gem แล้วเปิดแชตจาก Gem นี้ ใช้ข้อความทดลองเดียวกับวิธี A ตรวจว่าอัปโหลดทุกไฟล์สำเร็จและไม่ติดขีดจำกัดของบัญชี หากเพิ่มได้บางเล่ม ให้ระบุขอบเขตนั้น ไม่ถือว่ามี Wiki ครบ 281 หน้า

## ถ้าเมนูไม่ตรงหรือไฟล์ไม่ผ่าน

- Google อยู่ระหว่างปรับ Gems และ Skills ชื่อเมนูจึงอาจต่างตามบัญชีและช่วงเวลา
- วิธี A ใช้ ZIP ของ **skill**; วิธี B ใช้ไฟล์ที่แตกจาก ZIP **หลัก**
- อย่าอัปโหลด ZIP ทั้งก้อนลงช่อง Knowledge แล้วถือว่าอ่านไฟล์ภายในครบ
- อย่าลบสคริปต์หรือแปลงไฟล์เองเพียงเพื่อให้ผ่าน ให้ตรวจข้อความผิดพลาดและรูปแบบที่บัญชีรองรับก่อน

อ้างอิง: [Google — Upload skills](https://support.google.com/gemini/answer/17094296), [Google — Use Gems](https://support.google.com/gemini/answer/15146780), [Google — Gems transition](https://support.google.com/gemini/answer/18560919) ตรวจ 19 ตุลาคม 2026

## ข้อมูลอัปเดตทุกวัน

รุ่น 1.2 เพิ่มตัวรับข้อมูลจาก GitHub ซึ่งตั้งให้ตรวจ Wiki ทุกวัน **20:00 น. เวลาไทย** ต้องใส่ WIKI_API_KEY ฝั่งผู้ดูแลและมีรอบซิงก์สำเร็จก่อนจึงนับเป็นข้อมูลสด ผู้รับไม่ต้องมี key

AI ที่ใช้ Python/network ได้ ให้ทำตาม [คู่มืออัปเดต](AUTO_UPDATE_TH.md) เพื่อรันตัวอัปเดตครั้งเดียวเมื่อเริ่มใช้ ส่วนไฟล์ที่อัปโหลดใน Project/Gem/Skill ยังเป็นสำเนาและต้องเปลี่ยนไฟล์เอง การลงรุ่น 1.1 ไว้เดิมไม่ทำให้ได้สคริปต์รุ่น 1.2 โดยอัตโนมัติ

