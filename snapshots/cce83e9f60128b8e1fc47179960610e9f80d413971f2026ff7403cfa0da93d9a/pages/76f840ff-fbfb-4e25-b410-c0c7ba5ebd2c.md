> ข้อมูลจากโค้ด FE ณ 2026-10-16 (branch `develop` commit `4c73f5e`)

**Route:** `/reviews/all/center` และหน้าถัดไป `/reviews/all/center/page/{N}`

**ไฟล์หน้า:** `app/(interface)/(other)/reviews/[category]/[location]/page.tsx` และ `page/[page]/page.tsx` (ทั้งคู่ใช้ `review-listing.tsx`), layout `app/(interface)/(other)/reviews/layout.tsx`

**TrackingProvider:** `source_type: review` (อยู่ใน layout)

## วิธีอ่านตาราง

* **impression** = การ์ดหรือบล็อกเข้ามาในจอ, **click** = กด, **view** = เปิด modal หรือหน้า
* **section_number** = ลำดับ section บนหน้า, **position** = ลำดับการ์ดใน section (เริ่มที่ 1)
* **entity_id** = id ของสิ่งที่ถูกดูหรือกด เช่น id ประกาศ, id แบนเนอร์
* ⚠️ = ค่าไม่ตรงกับ convention ของส่วนอื่น ควรเช็ก

## สรุป

| \#  | Component | Tracking |
|-----|-----------|----------|
| 0   | ทั้งหน้า + ส่วนกลาง (Navbar, Pop-up, Login) | ✅        |
| 1   | ส่วนหัว (H1 + คำอธิบาย) | ❌ ยังไม่มี |
| 2   | ReviewCenterFilterBar (หมวด + ค้นหา) | ❌ ยังไม่มี |
| 3   | ReviewCenterGrid (รีวิวทั้งหมด) | ✅        |
| 4   | Pagination (เลขหน้า) | ❌ ยังไม่มี |

## 0. ทั้งหน้า + ส่วนกลาง

| Component | Event | ประเภท | ยิงเมื่อ | section_name | หมายเหตุ |
|-----------|-------|--------|----------|--------------|----------|
| PageViewTracker | `page_view` | view   | เปิดหน้า / เปลี่ยน path | `page_section` | 1 ครั้งต่อหน้า, เปลี่ยนเลขหน้า (`/page/{N}`) ยิงใหม่ |

Navbar, Pop-up และ Login / Register เหมือนทุกหน้า ดูตารางในเอกสาร "หน้า Home จังหวัด"

## 3. ReviewCenterGrid

| Component | Event | ประเภท | ยิงเมื่อ | section_name | section_number | หมายเหตุ |
|-----------|-------|--------|----------|--------------|----------------|----------|
| การ์ดรีวิว | `review` | impression, click | การ์ดเข้าจอ / กด | `reviews_section` | 3              | entity_id = id รีวิว, destination = ลิงก์บทความ, ⚠️ ไม่ส่ง position |
| VideoAutoplayModal | `review` | view   | เปิด modal วิดีโอ (กดการ์ดที่มีวิดีโอ) | `pop_up_review` | \-             | entity_id = id รีวิว |
| VideoAutoplayModal | `share`, `read_review`, `go_to_post` | click  | กดปุ่มใน modal | `pop_up_review` | \-             | entity_id = id รีวิว |
| VideoAutoplayModal | `close` | click  | ปิด modal (X, คลิกนอกกรอบ, Esc) | `pop_up_review` | \-             | entity_id = id รีวิว |
| SocialShareModal | `copy_link`, `line`, `facebook`, `message`, `email`, `close` | click  | กดในเมนูแชร์ของ modal | `pop_up_share` | 1              | entity_id = id รีวิว |

⚠️ event ของการ์ดเรียก `track` ตรง ไม่ผ่าน TrackingProvider: ไม่มี `source_type`, `user_id` และ `is_logged_in` เป็น false เสมอ

⚠️ ไม่ส่ง position ทุกหน้า จึงแยกลำดับการ์ดในหน้าและข้ามหน้าไม่ได้