# ติดตั้งนิติ๊บน Claude

[กลับหน้าเลือก AI](INSTALL_GUIDE_TH.md)

**วิธีแนะนำ: อัปโหลด Standalone Skill ZIP ใน Claude**

## 1. ดาวน์โหลดไฟล์นี้

[ดาวน์โหลด nitii-logic-suite-skill-1.2.0.zip](https://github.com/nitiphoomkk-dev/nitii-logic-suite/releases/download/v1.2.0/nitii-logic-suite-skill-1.2.0.zip)

**เก็บเป็น ZIP ไว้ ไม่ต้องแตกก่อนอัปโหลด** อย่าเลือก ZIP หลักหรือ ZIP ของ Plugin ในขั้นตอนนี้

## 2. เปิด Skills

1. เข้า [Claude](https://claude.ai/) และเข้าสู่ระบบ
2. ตรวจว่า **Code execution and file creation** ใน Settings → Capabilities เปิดใช้งานอยู่
3. เข้า **Customize → Skills**
4. กด **+ → Create skill → Upload a skill** ตามเมนูของรุ่นที่ใช้

## 3. อัปโหลดและเปิดใช้งาน

1. เลือกไฟล์ `nitii-logic-suite-skill-1.2.0.zip`
2. ตรวจชื่อสกิล **nitii-logic-suite** และคำอธิบายก่อนยืนยัน
3. บันทึก/สร้างสกิล แล้วเปิดใช้งานหากมีสวิตช์ให้เลือก

ในรายการจะเห็นสกิลหลักหนึ่งตัว ซึ่งรวม 11 บทบาทและฐานความรู้ไว้ภายใน ไม่จำเป็นต้องเห็น 11 รายการแยกกัน

## 4. เปิดแชตใหม่แล้วทดลอง

```text
ใช้สกิล nitii-logic-suite ค้น Logic Insert Card ของ Center
สรุปกฎพร้อมชื่อหน้า URL และวันที่สำเนาที่ใช้
ถ้าเปิดไฟล์ในสกิลไม่ได้ ให้บอกข้อจำกัดก่อน
```

**พร้อมเริ่มใช้เมื่อ:** สกิลปรากฏและเปิดใช้งาน และ Claude อ่านหลักฐานจากไฟล์ที่บรรจุอยู่ได้ การตอบรับชื่อสกิลอย่างเดียวยังไม่ยืนยันว่าอ่านฐานความรู้แล้ว

## ถ้าไม่พบ Skills หรืออัปโหลดไม่ได้

- ตรวจการเปิด Code execution และสิทธิ์จากผู้ดูแล หากเป็นบัญชีองค์กร
- เช็กว่าเลือกไฟล์ที่ลงท้ายด้วย **skill-1.2.0.zip** ไม่ใช่ ZIP หลัก
- ดูข้อความผิดพลาดจริงก่อนเปลี่ยนไฟล์ แพ็กเกจต้องมีโฟลเดอร์หลักที่มี `SKILL.md` และไฟล์สนับสนุนครบ อย่าอัปโหลดแค่ `SKILL.md` หากต้องการฐานความรู้ด้วย

## สำหรับผู้ใช้ Claude Code — อีกวิธีหนึ่ง

ดาวน์โหลดและแตก [ZIP หลัก](https://github.com/nitiphoomkk-dev/nitii-logic-suite/releases/download/v1.2.0/Nitii_Logic_Suite_1.2.0.zip) เปิด Terminal ในโฟลเดอร์ที่มี `README_TH.md` แล้วรัน:

```sh
claude --plugin-dir ./plugins/nitii-logic-suite
```

วิธีนี้โหลด Plugin สำหรับ session นั้น ต้องมี Claude Code ติดตั้งและเข้าสู่ระบบแล้ว

อ้างอิง: [Claude — Use Skills](https://support.claude.com/en/articles/12512180-use-skills-in-claude), [Claude Code — Create plugins](https://code.claude.com/docs/en/plugins/create) ตรวจ 19 ตุลาคม 2026

## ข้อมูลอัปเดตทุกวัน

รุ่น 1.2 เพิ่มตัวรับข้อมูลจาก GitHub ซึ่งตั้งให้ตรวจ Wiki ทุกวัน **20:00 น. เวลาไทย** ต้องใส่ WIKI_API_KEY ฝั่งผู้ดูแลและมีรอบซิงก์สำเร็จก่อนจึงนับเป็นข้อมูลสด ผู้รับไม่ต้องมี key

AI ที่ใช้ Python/network ได้ ให้ทำตาม [คู่มืออัปเดต](AUTO_UPDATE_TH.md) เพื่อรันตัวอัปเดตครั้งเดียวเมื่อเริ่มใช้ ส่วนไฟล์ที่อัปโหลดใน Project/Gem/Skill ยังเป็นสำเนาและต้องเปลี่ยนไฟล์เอง การลงรุ่น 1.1 ไว้เดิมไม่ทำให้ได้สคริปต์รุ่น 1.2 โดยอัตโนมัติ

