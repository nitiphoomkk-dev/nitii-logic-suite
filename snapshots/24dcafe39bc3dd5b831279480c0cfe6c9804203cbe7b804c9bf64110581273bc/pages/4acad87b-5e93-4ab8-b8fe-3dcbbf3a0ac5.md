Source: [Google Sheet › Register Interest](https://docs.google.com/spreadsheets/d/19ThOCmAUY7Eqna1-VUfsd_fTI6-HCBSLVKgb5c3MYpo/edit?gid=39107509#gid=39107509)

## Register Interest — Tracking Inventory

14/09/2026 17.07 น.

Runtime events on /register-interest/[location]. Every event emits source=register_interest, source_id=null, source_type=campaign, plus live province=<location> and province_id=<province_id>. No event contains name, phone, or other submitted PII.

| action_name | event_name | action_type | trigger | section_name | source | source_id | source_type | entity_id | component_type | extra_data |
|-------------|------------|-------------|---------|--------------|--------|-----------|-------------|-----------|----------------|------------|
| page_view   | page_view  | view        | เมื่อเปิดหน้าสำเร็จ | page_section | register_interest | <campaign_id> \| null | campaign    | <deal_id> \| null | page           | allowlisted query params เมื่อมี |
| campaign_registration_form | campaign_registration_form | impression  | เมื่อฟอร์มเข้า viewport | register_interest_lead_section | register_interest | <campaign_id> \| null | campaign    | <deal_id> \| null | null           | campaign_id เมื่อมี active campaign, allowlisted query params เมื่อมี |
| campaign_registration_start | campaign_registration_start | click       | เริ่มกรอกชื่อ, เบอร์โทร หรือเปลี่ยน consent ครั้งแรก | register_interest_lead_section | register_interest | <campaign_id> \| null | campaign    | <deal_id> \| null | null           | campaign_id เมื่อมี, form_id=register_interest_lead_form, allowlisted query params เมื่อมี |
| campaign_registration_consent | campaign_registration_consent | click       | เปลี่ยนสถานะ consent | register_interest_lead_section | register_interest | <campaign_id> \| null | campaign    | <deal_id> \| null | null           | campaign_id เมื่อมี, consent=true\|false, allowlisted query params เมื่อมี |
| campaign_registration_submit | campaign_registration_submit | click       | กดส่งข้อมูล | register_interest_lead_section | register_interest | <campaign_id> \| null | campaign    | <deal_id> \| null | null           | campaign_id เมื่อมี, form_id=register_interest_lead_form, allowlisted query params เมื่อมี |
| campaign_registration_success | campaign_registration_success | view        | Lead API สำเร็จและมี registration ID | register_interest_lead_section | register_interest | <campaign_id> \| null | campaign    | <deal_id> \| null | null           | campaign_id เมื่อมี, result_status=success, registration_id, allowlisted query params เมื่อมี |
| campaign_registration_error | campaign_registration_error | view        | validation, Turnstile, API, network หรือ context ผิดพลาด | register_interest_lead_section | register_interest | <campaign_id> \| null | campaign    | <deal_id> \| null | null           | campaign_id เมื่อมี, error_code, failed_field_name เมื่อมี, allowlisted query params เมื่อมี |
| register_interest_back_home | register_interest_back_home | click       | กดปุ่มกลับหน้าหลักใน lead success card | register_interest_success_section | register_interest | <campaign_id> \| null | campaign    | <deal_id> \| null | null           | destination เป็น ?back= หรือ /{location}, allowlisted query params เมื่อมี |
| register_interest_popup | register_interest_popup | impression  | Popup แสดงหลังหน้า mount | register_interest_popup_section | register_interest | <campaign_id> \| null | campaign    | ไม่ส่ง (omitted) | null           | allowlisted query params เมื่อมี |
| register_interest_popup_close | register_interest_popup_close | click       | ปิดผ่าน artwork, X, overlay หรือ Escape | register_interest_popup_section | register_interest | <campaign_id> \| null | campaign    | ไม่ส่ง (omitted) | null           | allowlisted query params เมื่อมี |

### 02/10/2026 14:45 — Deploy Prod 14:45

เก็บ text ปุ่ม สนใจ ลงทะเบียนที่ random

```json
"extra_data": {
  "copy_id": "new_project_v2",
  "button_label": "รับข้อเสนอสุดพิเศษ"
}
```

| action_type | trigger | section_name | source | source_id | source_type | entity_id | component_type | extra_data |
|-------------|---------|--------------|--------|-----------|-------------|-----------|----------------|------------|
| impression  | (event ใหม่) register_post (project) / register_review (secondhand, rent, home_builder) — กล่องติดต่อด้านข้าง (Contact) เข้า viewport ยิงซ้ำทุกครั้งที่กลับเข้า viewport ไม่ยิงบน apartment | brand_section | <pathname> | <post_id> | project \| secondhand \| rent \| builder | <post_id> | null           | copy_id, button_label |
| click       | register_post / register_review — กดปุ่มลงทะเบียนใน Contact | brand_section | <pathname> | <post_id> | project \| secondhand \| rent \| builder | <post_id> | null           | copy_id, button_label |
| null        | register_post / register_review — ส่งฟอร์มใน modal ของ Contact แล้ว API ตอบกลับ (text_input=success\|error) | brand_section | <pathname> | <post_id> | project \| secondhand \| rent \| builder | <post_id> | null           | copy_id, button_label |
| impression  | register_post — แถบติดต่อด้านล่างจอ (ContactBar) เข้า viewport ยิงครั้งเดียว (ui.position=1) ไม่ยิงบน rent apartment | brand_section | <pathname> | <post_id> | project \| secondhand \| rent \| builder | <post_id> | contact_bar    | copy_id, button_label |
| click       | register_post — กดปุ่มลงทะเบียนใน ContactBar (ui.position=1) | brand_section | <pathname> | <post_id> | project \| secondhand \| rent \| builder | <post_id> | contact_bar    | copy_id, button_label |
| null        | register_post — ส่งฟอร์มใน modal ของ ContactBar แล้ว API ตอบกลับ (text_input=success\|error) | brand_section | <pathname> | <post_id> | project \| secondhand \| rent \| builder | <post_id> | contact_bar    | copy_id, button_label |
| click       | register_post — กดปุ่มลงทะเบียนในส่วนเฟสใหม่ (NewPhase) | new_phase_section | <pathname> | <post_id> | project     | <post_id> | null           | copy_id, button_label |
| null        | register_below — ส่งฟอร์มลงทะเบียนในหน้า (RegisterInterest) แล้ว API ตอบกลับ (text_input=success\|error) | register_below_section | <pathname> | <post_id> | project \| secondhand \| builder | <post_id> | null           |            |