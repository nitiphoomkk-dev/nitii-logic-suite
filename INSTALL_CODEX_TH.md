# ติดตั้งนิติ๊บน Codex

[กลับหน้าเลือก AI](INSTALL_GUIDE_TH.md)

**วิธีแนะนำ: คัดลอก 11 โฟลเดอร์สกิลเข้าพื้นที่งานที่ใช้กับ Codex** วิธีนี้ติดตั้งเฉพาะพื้นที่งานนั้น

## 1. ดาวน์โหลดและแตกไฟล์

ดาวน์โหลด [ZIP หลัก v1.2.0](https://github.com/nitiphoomkk-dev/nitii-logic-suite/releases/download/v1.2.0/Nitii_Logic_Suite_1.2.0.zip) แล้วแตกไฟล์ เปิดต่อจนเห็น `README_TH.md`

## 2. เปิดโฟลเดอร์สกิล

เข้าโฟลเดอร์นี้ในชุดที่แตกแล้ว:

```text
plugins/nitii-logic-suite/skills/
```

ข้างในมี 11 โฟลเดอร์ ได้แก่ `nitii-logic`, `nitii-knowledge`, `nitii-solution`, `nitii-qa`, `nitii-sa`, `nitii-po`, `nitii-pm`, `nitii-uxui`, `nitii-backend`, `nitii-frontend` และ `nitii-explain`

## 3. คัดลอกทั้ง 11 โฟลเดอร์

เปิดโฟลเดอร์โปรเจกต์ที่ต้องการใช้ใน Codex แล้วสร้าง `.agents` และโฟลเดอร์ `skills` ภายใน จากนั้นวางทั้ง 11 โฟลเดอร์ไว้ในนั้น

ตัวอย่างโครงสร้างปลายทาง:

```text
โปรเจกต์ของคุณ/
└── .agents/
    └── skills/
        ├── nitii-logic/
        │   ├── SKILL.md
        │   └── references/
        ├── nitii-knowledge/
        │   ├── SKILL.md
        │   ├── scripts/
        │   └── references/
        └── โฟลเดอร์สกิลที่เหลืออีก 9 ตัว
```

**คัดลอกทั้งโฟลเดอร์พร้อมไฟล์ข้างใน** เพราะฐานความรู้และเครื่องมือค้นอยู่ใน `references` และ `scripts` หากมีสกิลชื่อเดียวกันรุ่นเก่า ให้สำรองและจัดการรุ่นซ้ำก่อนแทนที่

## 4. เปิดโปรเจกต์นั้นใน Codex

เริ่มแชตในพื้นที่งานเดียวกับที่วาง `.agents/skills` ตรวจว่าสกิลถูกค้นพบ หากยังไม่ปรากฏให้เริ่มแชตใหม่หรือปิดเปิด Codex ตามเอกสารของรุ่นที่ใช้

## 5. ทดลองเรียกนิติ๊

```text
ใช้ $nitii-logic ค้น Logic Insert Card ของ Center
สรุปพร้อมชื่อหน้า URL และวันที่สำเนาที่ใช้
```

**พร้อมเริ่มใช้เมื่อ:** Codex พบ `nitii-logic` และเข้าถึงหลักฐานใน `nitii-knowledge` ของโปรเจกต์นี้ได้ การมีไฟล์บน GitHub อย่างเดียวยังไม่ติดตั้งลงเครื่อง

หากเครื่องไม่มี Python สำหรับสคริปต์ค้น ให้ Codex ใช้เครื่องมือค้น/อ่านไฟล์ที่มีอยู่กับข้อมูลใน `nitii-knowledge/references` และบอกข้อจำกัดตามจริง

## ทางเลือกสำหรับผู้ใช้ Codex CLI และ Plugin

เปิด Terminal ในโฟลเดอร์ **ที่แตกจาก ZIP หลักและมี `README_TH.md`** แล้วรัน:

```sh
codex plugin marketplace add .
```

จากนั้นใช้ Plugins Directory ในแอปเดสก์ท็อป เลือก source **Nitii Logic Suite** และติดตั้ง Plugin ตาม UI ของรุ่นนั้น

repository GitHub ปัจจุบันเป็นหน้าส่งมอบ ZIP จึงต้องดาวน์โหลด Assets และแตกก่อนใช้คำสั่งนี้ การ clone repository อย่างเดียวไม่มีโฟลเดอร์สกิลครบ หลีกเลี่ยงการติดตั้งทั้งวิธีคัดลอกและ Plugin ซ้ำกันในพื้นที่งานเดียว

อ้างอิง: [OpenAI — Build skills](https://learn.chatgpt.com/docs/build-skills), [OpenAI — Package your plugin](https://developers.openai.com/plugins/build/plugins) ตรวจ 19 ตุลาคม 2026

## ข้อมูลอัปเดตทุกวัน

รุ่น 1.2 เพิ่มตัวรับข้อมูลจาก GitHub ซึ่งตั้งให้ตรวจ Wiki ทุกวัน **20:00 น. เวลาไทย** ต้องใส่ WIKI_API_KEY ฝั่งผู้ดูแลและมีรอบซิงก์สำเร็จก่อนจึงนับเป็นข้อมูลสด ผู้รับไม่ต้องมี key

AI ที่ใช้ Python/network ได้ ให้ทำตาม [คู่มืออัปเดต](AUTO_UPDATE_TH.md) เพื่อรันตัวอัปเดตครั้งเดียวเมื่อเริ่มใช้ ส่วนไฟล์ที่อัปโหลดใน Project/Gem/Skill ยังเป็นสำเนาและต้องเปลี่ยนไฟล์เอง การลงรุ่น 1.1 ไว้เดิมไม่ทำให้ได้สคริปต์รุ่น 1.2 โดยอัตโนมัติ

