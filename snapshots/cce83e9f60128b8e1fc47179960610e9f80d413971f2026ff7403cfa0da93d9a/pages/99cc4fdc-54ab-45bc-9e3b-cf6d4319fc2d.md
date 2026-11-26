> ข้อมูลจากโค้ด FE ณ 2026-10-16 (branch `develop` commit `4c73f5e`)

**Route:** `/home-design/{สไตล์}/{จังหวัด}` เช่น `/home-design/styles/khonkaen` (สไตล์: `styles` = ทุกแบบ, `modern`, `minimal`, `nordic`, ... ต่อท้ายด้วยตัวกรองใน path และ `/page/{N}` ได้)

**ไฟล์หน้า:** `app/(interface)/(search)/search/[main_service]/[property]/[location]/[[...options]]/page.tsx` → `components/pages/search/home-builder/SearchHomeBuilderPage.tsx` + `HomeBuilderDynamicLayout.tsx`

**TrackingProvider:** `source_type: search` (ตั้งใน `[[...options]]/layout.tsx`, ไม่มี `category`)

`proxy.ts` rewrite URL นี้ไปที่ `/search/home-design/...` route เดียวกันนี้ใช้กับหน้าค้นหาโครงการ มือสอง เช่า และรับสร้างบ้าน ทุกหน้าจึงได้ `source_type: search` เหมือนกัน แยกหน้าได้จาก `page.source` (path) เท่านั้น

หน้านี้ใช้ component เดียวกับหน้าค้นหารับสร้างบ้าน แต่เริ่มที่โหมดแบบบ้าน (ผลการค้นหาเป็นการ์ดแบบบ้าน, VR360Section และ HouseStyleSection อยู่ก่อนผลการค้นหา, FreshlyContent อยู่หลังผลการค้นหา) ถ้าสลับเป็น "รับสร้างบ้าน" จากตัวกรองในหน้า ผลการค้นหา, VR360Section และ HouseStyleSection จะเปลี่ยนเป็นแบบหน้าค้นหารับสร้างบ้าน (ดูเอกสาร "หน้าค้นหารับสร้างบ้าน") ส่วนอื่นคงเดิม

## วิธีอ่านตาราง

* **impression** = การ์ดหรือบล็อกเข้ามาในจอ, **click** = กด, **view** = เปิด modal หรือหน้า
* **section_number** = ลำดับ section บนหน้า, **position** = ลำดับการ์ดใน section (เริ่มที่ 1)
* **entity_id** = id ของสิ่งที่ถูกดูหรือกด เช่น id ประกาศ, id แบนเนอร์
* ⚠️ = ค่าไม่ตรงกับ convention ของส่วนอื่น ควรเช็ก

## สรุป

| \#  | Component | Tracking |
|-----|-----------|----------|
| 0   | ทั้งหน้า + ส่วนกลาง (Navbar, Pop-up, Login) | ✅        |
| 1   | TopBannerSection (แบนเนอร์บนสุด) | ✅        |
| 2   | SearchHeaderSEO (breadcrumb + หัวข้อ + คำอธิบาย, breadcrumb ไม่ได้ส่ง `positionTracking` จึงไม่ยิง) | ❌ ยังไม่มี |
| 3   | SearchCampaignBanner (แคมเปญ, แสดงเมื่อมีแคมเปญ) | ✅        |
| 4   | ReviewHomeSection (รีวิวแบบบ้าน) | ✅        |
| 5   | LeadingCompany (บริษัทรับสร้างบ้านชั้นนำ, 4 ใบ) | ✅        |
| 6   | VR360Section | ✅        |
| 7   | HouseStyleSection (สไตล์บ้าน) | ❌ ยังไม่มี |
| 8   | StickyMenuBar (เมนูเลือกบริการ) | ❌ ยังไม่มี |
| 9   | ResultHomeBuilder (ตัวกรอง + ผลการค้นหาแบบบ้าน) | ✅        |
| 10  | BannerBFirstSection (แบนเนอร์ B, แสดง 3 จุด หลังผลลัพธ์กลุ่มที่ 1, 2 และ 3) | ✅        |
| 11  | FreshlyContent (โพสต์อัปเดต) | ✅        |
| 12  | CTABottomSection (บริการด้านล่าง) | ✅        |
| 13  | SearchBottomSeoContent (เนื้อหา SEO + FAQ) | ❌ ยังไม่มี |

## 0. ทั้งหน้า + ส่วนกลาง

| Component | Event | ประเภท | ยิงเมื่อ | section_name | หมายเหตุ |
|-----------|-------|--------|----------|--------------|----------|
| PageViewTracker | `page_view` | view   | เปิดหน้า / เปลี่ยน path | `page_section` | 1 ครั้งต่อหน้า |

Navbar, Pop-up และ Login / Register เหมือนทุกหน้า ดูตารางในเอกสาร "หน้า Home จังหวัด"

## 1. TopBannerSection

| Event | ประเภท | ยิงเมื่อ | section_name | section_number | หมายเหตุ |
|-------|--------|----------|--------------|----------------|----------|
| `top_banner` | impression | สไลด์แบนเนอร์เข้าจอ | `top_banner_section` | 1              | position = ลำดับสไลด์, entity_id = id แบนเนอร์, มี `ab_id` |
| `top_banner_ad` | click  | กดแบนเนอร์ | `top_banner_section` | 1              | ⚠️ impression ใช้ `top_banner` แต่ click ใช้ `top_banner_ad` ทุกแบนเนอร์ ไม่ได้แยกตาม ad |

## 3. SearchCampaignBanner

แสดงเฉพาะเมื่อมีแคมเปญที่ใช้กับหน้าค้นหารับสร้างบ้านของจังหวัดนั้น (หน้าแบบบ้านใช้ข้อมูลแคมเปญหมวดรับสร้างบ้าน) เนื้อหามี 3 แบบตามข้อมูลแคมเปญ: มีผู้ร่วมหมวดรับสร้างบ้าน → วิดีโอโปรโมท + การ์ดบริษัทผู้ร่วม / มีหมวดรับสร้างบ้านแต่ยังไม่มีผู้ร่วม → poster แคมเปญ / ไม่มีหมวดรับสร้างบ้าน → บล็อกสถิติผู้ร่วม

| Component | Event | ประเภท | ยิงเมื่อ | section_name | section_number | หมายเหตุ |
|-----------|-------|--------|----------|--------------|----------------|----------|
| SearchCampaignModuleTracker | `search_campaign_module` | impression | บล็อกแคมเปญเข้าจอ | `search_campaign_section` | 0              | entity_id = id แคมเปญ, extra_data: `search_category` (= `home-design`), `campaign_phase`, ยิงซ้ำได้ทุกครั้งที่กลับเข้าจอ |
| CampaignLogoLink, VisitCampaignButton | `search_campaign_visit` | click  | กดโลโก้แคมเปญ / ปุ่ม "เข้าชมแคมเปญ" | `search_campaign_section` | \-             | entity_id = id แคมเปญ, destination = `/{จังหวัด}/campaign/landing/{slug}` |
| CampaignRegisterInterestButton | `search_campaign_register` | click  | กดปุ่ม "รับสิทธิพิเศษ" | `search_campaign_section` | \-             | แสดงเฉพาะแบบบล็อกสถิติ, entity_id = id แคมเปญ, destination = `/register-interest/{จังหวัด}?from=direct&category=secondhand&...`, ไม่แสดงที่ `buriram` |
| CampaignVideoBand | `search_campaign_video` | impression | การ์ดวิดีโอเข้าจอ | `search_campaign_section` | 0              | position = ลำดับวิดีโอ, entity_id = id วิดีโอ, extra_data: `search_category`, `slot_position` |
| CampaignVideoBand | `search_campaign_video_play` | click  | กดการ์ดวิดีโอ | `search_campaign_section` | 0              | position = ลำดับวิดีโอ, entity_id = id วิดีโอ, extra_data: `search_category` |
| CampaignVideoBand | `search_campaign_carousel` | click  | เลื่อน carousel วิดีโอ | `search_campaign_section` | 0              | position = สไลด์ปลายทาง, entity_id = id แคมเปญ, extra_data: `content_type`, `direction`, `from_index`, `to_index` |
| VideoAutoplayModal | `search_campaign_video` | view   | เปิด modal วิดีโอ | `search_campaign_section` | \-             | entity_id = id วิดีโอ |
| VideoAutoplayModal | `search_campaign_video` | click  | กดแชร์ / อ่านรีวิว / ไปที่ประกาศ ใน modal | `search_campaign_section` | \-             | แยกด้วย `action_name`: `search_campaign_video_share`, `search_campaign_video_read_review`, `search_campaign_video_go_to_post` |
| VideoAutoplayModal | `search_campaign_video` | click  | ปิด modal (X, คลิกนอกกรอบ, Esc) | `search_campaign_video_play_section` | \-             | `action_name` = `close` |
| PromotionVideoCarousel | `search_campaign_video_progress` | view   | ปิด modal วิดีโอ | `search_campaign_section` | 0              | entity_id = id วิดีโอ, extra_data: `milestone_percent`, position ว่าง |
| SocialShareModal | `copy_link`, `line`, `facebook`, `message`, `email`, `close` | click  | กดในเมนูแชร์ของ modal | `pop_up_share` | 1              | entity_id = id วิดีโอ |
| PostCampaignParticipantBand (การ์ดบริษัทผู้ร่วม) | `post_company_home_builder` / `post_company_home_builder_top_ad` / `super_top_ad` | impression, click | การ์ดเข้าจอ / กด | `search_campaign_section` | 0              | position = ลำดับการ์ด, action_id = ลำดับการ์ด, entity_id = id บริษัท, extra_data: `entity_type` (= `company`), `campaign_id`, `slot_position` |
| PostCampaignParticipantBand | `campaign_recommendations_carousel` | click  | กดลูกศรเลื่อนการ์ด (desktop, เกิน 4 ใบ) | `search_campaign_section` | \-             | position = สไลด์ปลายทาง, entity_id = id แคมเปญ, extra_data: `direction`, `from_index`, `to_index` |
| ParticipationStatisticsSection | `campaign_participation_summary` | impression | บล็อกสถิติเข้าจอ | `search_campaign_section` | 0              | extra_data: `counts_by_category`, ไม่มี entity_id |
| ParticipationStatisticsSwiperIsland | `campaign_participation_category` | click  | กดหมวดในบล็อกสถิติ | `search_campaign_section` | 0              | position = ลำดับหมวด, extra_data: `category` |

ปุ่มบันทึกบนการ์ดไม่แสดง เพราะ flag `SHOW_BOOKMARK = false` event `_save` จึงไม่ยิง

⚠️ ถ้ามีวิดีโอใบเดียว `search_campaign_video_progress` ยิงแค่ครั้งแรกที่ปิด modal เพราะไม่ได้ reset สถานะวิดีโอเมื่อเปิดใหม่

## 4. ReviewHomeSection

| Component | Event | ประเภท | ยิงเมื่อ | section_name | section_number | หมายเหตุ |
|-----------|-------|--------|----------|--------------|----------------|----------|
| การ์ดรีวิว | `style_review` | impression, click | การ์ดเข้าจอ / กด | `style_review_section` | 3              | entity_id = id รีวิว, action_id = ลำดับการ์ด, destination = ลิงก์วิดีโอ, ไม่มี position |
| VideoAutoplayModal | `review` | view   | เปิด modal วิดีโอ | `pop_up_review` | ⚠️ = ลำดับการ์ด (เริ่ม 0) | entity_id = id รีวิว |
| VideoAutoplayModal | `share`, `read_review`, `go_to_post` | click  | กดปุ่มใน modal | `pop_up_review` | ⚠️ = ลำดับการ์ด (เริ่ม 0) | entity_id = id รีวิว, destination = ลิงก์ของปุ่ม |
| VideoAutoplayModal | `close` | click  | ปิด modal (X, คลิกนอกกรอบ, Esc) | `pop_up_review` | ⚠️ = ลำดับการ์ด (เริ่ม 0) | entity_id = id รีวิว |
| SocialShareModal | `copy_link`, `line`, `facebook`, `message`, `email`, `close` | click  | กดในเมนูแชร์ของ modal | `pop_up_share` | 1              | entity_id = id รีวิว |

⚠️ `style_review_ad` ไม่เคยยิง เพราะข้อมูลรีวิวที่หน้านี้ดึงมาไม่มี `is_top_ads`

⚠️ ถ้ามีรีวิวใบเดียว impression ของการ์ดไม่ยิง เพราะการ์ดเดี่ยวไม่ได้ผูก observer (click ยังยิง)

## 5. LeadingCompany

| Event | ประเภท | ยิงเมื่อ | section_name | section_number | หมายเหตุ |
|-------|--------|----------|--------------|----------------|----------|
| `post_company_home_builder` / `post_company_home_builder_top_ad` / `super_top_ad` | impression, click | การ์ดบริษัทเข้าจอ / กด | `company_home_builder_section` | 4              | position = ลำดับการ์ด, action_id = ลำดับการ์ด, entity_id = id บริษัท, destination = ลิงก์บริษัท |

ปุ่มบันทึกบนการ์ดไม่แสดง เพราะ flag `SHOW_BOOKMARK = false` event `_save` จึงไม่ยิง

หน้านี้ซ่อนปุ่ม "ดูทั้งหมด" (`hideSeeMore`) จึงไม่มี `all_company_home_builder`

## 6. VR360Section

| Event | ประเภท | ยิงเมื่อ | section_name | section_number | หมายเหตุ |
|-------|--------|----------|--------------|----------------|----------|
| `vr_360` | impression, click | การ์ด VR เข้าจอ / กด | `vr_360_section` | ⚠️ 5           | position = ลำดับการ์ด, entity_id = id VR (ข้อมูล VR รับสร้างบ้าน), ⚠️ section_number ซ้ำกับ FreshlyContent |
| `all_vr_360` | click  | กด "ดูทั้งหมด" | `vr_360_section` | ⚠️ 5           | ไม่มี destination |
| `vr_360_click_posts` | click  | กดไปประกาศใน pop-up VR | `vr_360_pop_up_section` | \-             |          |
| `vr_360_share` | click  | กดแชร์ใน pop-up VR | `vr_360_pop_up_section` | \-             | เมนูแชร์ที่เปิดตามมาไม่ยิง event |
| `vr_360_close` | click  | ปิด pop-up VR | `vr_360_pop_up_section` | \-             |          |

## 9. ResultHomeBuilder

ผลการค้นหาแบบบ้านแบ่ง 3 กลุ่มตามลำดับในหน้า (นับรวม insert card): 1–12, 13–24, 25 ขึ้นไป ไม่มีแถว Super Top Ad ในโหมดนี้

| Component | Event | ประเภท | ยิงเมื่อ | section_name | section_number | หมายเหตุ |
|-----------|-------|--------|----------|--------------|----------------|----------|
| PostTileCard (กลุ่ม 1) | `post_style` / `post_style_top_ad` / `post_style_popular` / `post_style_popular_top_ad` / `super_top_ad` | impression, click | การ์ดเข้าจอ / กด | `posts_first_section` | 7              | position = ลำดับนับต่อข้ามหน้า, action_id = ลำดับในหน้า, entity_id = id แบบบ้าน, destination = ลิงก์แบบบ้าน, ใช้ `_popular` เมื่อแบบบ้านเป็นแบบยอดนิยม |
| PostTileCard (กลุ่ม 2) | ชื่อเดียวกับแถวบน | impression, click | การ์ดเข้าจอ / กด | `posts_second_section` | 9              | เหมือนแถวบน |
| PostTileCard (กลุ่ม 3) | ชื่อเดียวกับแถวบน | impression, click | การ์ดเข้าจอ / กด | `posts_third_section` | 13             | เหมือนแถวบน |
| InsertCard | `insert_card_01` … `insert_card_06` | impression, click | การ์ดเข้าจอ / กด | ตามกลุ่มที่การ์ดอยู่ | 7 / 9 / 13     | เลขตามลำดับ insert card ในหน้า (ใบที่ 6 ขึ้นไปใช้ `_06`), position = ลำดับนับต่อข้ามหน้า, entity_id = id การ์ด, extra_data: `card_id`, `slot`, `version`, `category`, `card_type`, มี `ab_id` เมื่อการ์ดมี `slot` |

ปุ่มบันทึกบนการ์ดไม่แสดง เพราะ flag `SHOW_BOOKMARK = false` event `_save` จึงไม่ยิง

ตัวกรอง, เรียงลำดับ, pagination และ modal ของ insert card แบบวิดีโอ (ปุ่มเปิดเสียง / ปิด) ไม่มี event

## 10. BannerBFirstSection

แสดง 3 จุด คือหลังผลลัพธ์กลุ่มที่ 1, 2 และ 3

| Event | ประเภท | ยิงเมื่อ | section_name | section_number | หมายเหตุ |
|-------|--------|----------|--------------|----------------|----------|
| `banner` / `banner_ad` | impression, click | สไลด์เข้าจอ / กด | `banner_first_section` | 8 (จุดที่ 1), ⚠️ 10 (จุดที่ 2), 12 (จุดที่ 3) | position = ลำดับสไลด์, entity_id = id แบนเนอร์, destination = ลิงก์แบนเนอร์, มี `ab_id`, ⚠️ ทุกจุดใช้ section_name เดียวกัน แยกได้จาก section_number เท่านั้น, ⚠️ 10 ซ้ำกับ CTABottomSection |

## 11. FreshlyContent

| Event | ประเภท | ยิงเมื่อ | section_name | section_number | หมายเหตุ |
|-------|--------|----------|--------------|----------------|----------|
| `freshly_content` | impression, click | การ์ดโพสต์เข้าจอ / กด | `freshly_content_section` | ⚠️ 5           | position = ลำดับการ์ด, entity_id = id โพสต์ (`feedId`), click: destination = ลิงก์โพสต์, ⚠️ section_number ซ้ำกับ VR360Section |
| `feed_media` | click  | กดรูป / วิดีโอในการ์ด | `freshly_content_section` | ⚠️ 5           | extra_data: `media_type`, `media_index` |
| `feed_media` | impression | รูป / วิดีโอแสดงใน modal | `freshly_content_section` | ⚠️ 5           | extra_data: `media_type`, `media_index` |
| `feed_media_close` | close  | ปิด modal รูป / วิดีโอ | `freshly_content_section` | ⚠️ 5           | extra_data: `media_type`, `media_index` |

## 12. CTABottomSection

| Event | ประเภท | ยิงเมื่อ | section_name | section_number | หมายเหตุ |
|-------|--------|----------|--------------|----------------|----------|
| `service_below` | impression | บล็อกบริการเข้าจอ | `service_below_section` | ⚠️ 10          | ⚠️ section_number ซ้ำกับ BannerBFirstSection จุดที่ 2 |
| `service_below` | click  | กดปุ่มบริการ | `service_below_section` | ⚠️ 10          | entity_id: 1 = โครงการ, 2 = มือสอง, 3 = เช่า, 4 = รับสร้างบ้าน |