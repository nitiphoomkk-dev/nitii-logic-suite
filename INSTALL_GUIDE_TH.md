# ติดตั้งนิติ๊ — เลือก AI ที่คุณใช้

คู่มือสำหรับ **Nitii Logic Suite v1.1.0** ตรวจขั้นตอนกับเอกสารทางการวันที่ **19 ตุลาคม 2026**

## เริ่มตรงนี้

| คุณใช้ AI ตัวไหน | เปิดคู่มือ | วิธีหลัก |
|---|---|---|
| ChatGPT | [ติดตั้งบน ChatGPT](INSTALL_CHATGPT_TH.md) | สร้าง Project แล้วเพิ่ม Instructions และไฟล์ความรู้ |
| Claude | [ติดตั้งบน Claude](INSTALL_CLAUDE_TH.md) | อัปโหลด ZIP ของ Standalone Skill |
| Gemini | [ติดตั้งบน Gemini](INSTALL_GEMINI_TH.md) | อัปโหลด ZIP ใน Skills; ถ้าบัญชีใช้ Gems ให้ทำตามวิธี Gems |
| Codex | [ติดตั้งบน Codex](INSTALL_CODEX_TH.md) | แตก ZIP แล้วคัดลอก 11 โฟลเดอร์สกิลเข้าพื้นที่งาน |

**เลือกเฉพาะ AI ที่คุณใช้ ไม่ต้องทำครบทั้ง 4 แบบ** เปิดลิงก์ GitHub อย่างเดียวจะยังไม่ติดตั้ง ต้องทำขั้นตอนในคู่มือของ AI นั้นต่อ

## ดาวน์โหลดให้ถูกไฟล์

[เปิดหน้า Release v1.1.0](https://github.com/nitiphoomkk-dev/nitii-logic-suite/releases/tag/v1.1.0) แล้วดูส่วน **Assets**

| ไฟล์ | ใช้เมื่อไร |
|---|---|
| [Nitii_Logic_Suite_1.1.0.zip](https://github.com/nitiphoomkk-dev/nitii-logic-suite/releases/download/v1.1.0/Nitii_Logic_Suite_1.1.0.zip) | ชุดครบทุกแบบ เหมาะกับ ChatGPT, Gems, Codex และคนที่ต้องการเก็บสำรอง |
| [nitii-logic-suite-skill-1.1.0.zip](https://github.com/nitiphoomkk-dev/nitii-logic-suite/releases/download/v1.1.0/nitii-logic-suite-skill-1.1.0.zip) | ใช้อัปโหลดเข้า Skills ของ Claude หรือ Gemini ตามเมนูที่บัญชีมี |
| [nitii-logic-suite-plugin-1.1.0.zip](https://github.com/nitiphoomkk-dev/nitii-logic-suite/releases/download/v1.1.0/nitii-logic-suite-plugin-1.1.0.zip) | สำหรับคนที่เลือกติดตั้งแบบ Plugin โดยเฉพาะ |

**อย่าเลือก `Source code (zip)` หรือ `Source code (tar.gz)`** เพราะ repository นี้เก็บหน้าแนะนำและคู่มือ ส่วนแพ็กเกจติดตั้งอยู่ใน Assets

## ติดตั้งแล้วลองถาม

```text
นิติ๊ ค้น Logic Insert Card ของ Center จากฐานความรู้ที่มี
สรุปสั้น ๆ และระบุชื่อหน้า URL และวันที่สำเนาที่ใช้
ถ้าข้อมูลไม่พอ ให้บอกตรงไหนยังไม่ทราบ
```

เช็กว่าคำตอบใช้แหล่งที่มีจริง ไม่ใช่เพียงตอบว่า “ติดตั้งสำเร็จ” การทดสอบนี้ยังไม่ใช่การตรวจว่าทุกกฎและทุกภาพในฐานความรู้ถูกอ่านครบแล้ว

## สิ่งที่ควรรู้

- ชุดนี้มี 11 ทักษะและสำเนาข้อความ/ตาราง Wiki 281 หน้า ณ วันที่ 19 ตุลาคม 2026
- ข้อมูลไม่อัปเดตจาก Wiki อัตโนมัติ ภาพที่เป็นลิงก์ยังต้องใช้สิทธิ์เปิดแหล่งนั้น
- ไม่มีบัญชี แชตส่วนตัว หรือ API key ของผู้สร้างติดมาด้วย วิธีหลักในคู่มือไม่ต้องสร้าง API key เพิ่ม แต่ต้องมีบัญชี AI และใช้ได้ตามสิทธิ์/โควตาของบัญชีนั้น
- เมนูอาจต่างตามภาษา บัญชีและเวอร์ชัน คู่มือนี้อิงเอกสารทางการและตรวจโครงสร้างแพ็กเกจแล้ว ยังไม่ได้ติดตั้งจริงบนทุก AI และทุกบัญชี

ถ้าติดตั้งรุ่นใหม่ ให้ปิดหรือเอารุ่นเก่าที่ชื่อซ้ำออกตามวิธีของ AI นั้นก่อนใช้รุ่นใหม่ และเก็บงาน/ผลทดสอบเดิมที่ต้องการไว้
