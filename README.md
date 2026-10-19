# Nitii Logic Suite — v1.2.0

ชุดทักษะ “นิติ๊” สำหรับค้น Business Logic, ทำ Solution, AC, Test Case และส่งต่องาน Dev มี 11 ทักษะ พร้อมฐานข้อความ NaYoo Wiki เดิม 281 หน้า และตัวรับข้อมูลรุ่นใหม่

## อัปเดตความรู้ทุกวัน 20:00 น. เวลาไทย

GitHub Actions อ่าน Wiki เฉพาะ Solution และ Develop รวมหน้าเพิ่มใหม่ในสองชุดนี้ ใช้ข้อความเดิมที่ไม่เปลี่ยนและดึงหน้าใหม่/แก้ไขใหม่ ตรวจทั้งชุดก่อนเผยแพร่ หากอ่านไม่ครบเก็บชุดสำเร็จเดิม กด Run workflow เองได้ด้วย

**เปิดใช้งานจริงเมื่อผู้ดูแลใส่ WIKI_API_KEY และรอบซิงก์ Wiki สำเร็จแล้ว** ผล bootstrap เป็นฐานเก่าเท่านั้น ตรวจ `bootstrap`, `checkedAtUtc` และ `syncedAtUtc` ใน [latest.json](https://raw.githubusercontent.com/nitiphoomkk-dev/nitii-logic-suite/knowledge/latest.json) ไม่ใช่ Realtime

[คู่มือเปิดระบบและรับข้อมูลอัปเดต](AUTO_UPDATE_TH.md) · [ดูผล Actions](https://github.com/nitiphoomkk-dev/nitii-logic-suite/actions)

## ดาวน์โหลดและติดตั้ง

[ดาวน์โหลด Release v1.2.0](https://github.com/nitiphoomkk-dev/nitii-logic-suite/releases/tag/v1.2.0) แล้วเลือกไฟล์ ZIP ใน Assets

| AI | คู่มือ |
|---|---|
| ChatGPT | [Project และไฟล์ความรู้](INSTALL_CHATGPT_TH.md) |
| Claude | [Standalone Skill](INSTALL_CLAUDE_TH.md) |
| Gemini | [Skills หรือ Gems](INSTALL_GEMINI_TH.md) |
| Codex | [ทักษะในพื้นที่งาน](INSTALL_CODEX_TH.md) |

[เริ่มจากหน้าเลือก AI](INSTALL_GUIDE_TH.md) ผู้ใช้รุ่น 1.1 ต้องลงรุ่น 1.2 ครั้งเดียวเพื่อได้ตัวอัปเดต

## การรับข้อมูลใหม่

- AI ที่รัน Python และออกอินเทอร์เน็ตได้: ใช้ `update_knowledge.py` ในสกิล ข้อมูลใหม่ผ่าน hash และสลับทั้งชุด จากนั้นตัวค้น/อ่านใช้ cache ที่ตรวจแล้ว ผู้รับไม่ต้องมี Wiki key
- AI ที่ใช้เว็บได้: ตรวจ public feed และอ่านหน้าที่เกี่ยวข้องตามสิทธิ์เครื่องมือ
- AI ที่ใช้เฉพาะไฟล์อัปโหลด: ดาวน์โหลด knowledge.zip รุ่นล่าสุด แล้วเปลี่ยนไฟล์ `web/*.txt` เอง ไฟล์ใน Project/Gem/Skill ไม่ถูกแทนที่อัตโนมัติ

ตัวรับอัปเดตเฉพาะข้อมูล ไม่ดาวน์โหลดหรือรันโค้ดจาก Wiki ไม่โหลด corpus ทั้งชุดเข้า context ของ AI เพื่อเช็กสถานะ ผู้รับควรค้นก่อนอ่านและอ่านเฉพาะหลักฐานที่เกี่ยวข้อง

## ขอบเขต

ฐานเริ่มต้นคัดข้อความจาก Wiki วันที่ 19 ตุลาคม 2026 ส่วนเวลาตรวจครั้งต่อไปอยู่ใน feed เนื้อหาอาจมีร่าง ข้อเสนอ กฎเก่า และข้อขัดแย้ง ต้องแยกสถานะหลักฐานก่อนสรุป ไม่ตามอ่าน Google Docs/Figma/Canva ภายนอก ไม่รวมไฟล์ภาพจากลิงก์ ไม่ส่ง credential หรือประวัติแชต ไม่มีการให้สัญญาอนุญาตแบบ Open Source แก่ข้อมูลภายใน

โค้ด sync/updater อยู่ใน repository นี้ แต่ชุดสกิลครบยังดาวน์โหลดจาก Release Assets การ clone source อย่างเดียวไม่ติดตั้งสกิลลง AI
