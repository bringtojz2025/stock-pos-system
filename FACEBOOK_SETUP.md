# Facebook API Integration Guide

## ขั้นตอนการตั้งค่า Facebook Integration

### 1. สร้าง Facebook App

1. ไปที่ https://developers.facebook.com
2. คลิก "My Apps" → "Create App"
3. เลือก "Business" type
4. กรอกข้อมูล App:
   - App Name: "Stock POS"
   - Purpose: "Manage Business"
5. คลิก "Create App"

### 2. ตั้งค่า Messenger Product

1. ใน Dashboard ไปที่ "Add a Product"
2. ค้นหา "Messenger" แล้วคลิก "Set Up"
3. ใน Messenger Settings:
   - ไปที่ "ACCESS TOKENS"
   - เลือก Facebook Page ของคุณ
   - คลิก "Generate Token"
   - Copy Token และเก็บไว้

### 3. หา Page ID

#### วิธี 1: จาก App Dashboard
1. ใน Messenger Settings หรือ Page Settings
2. ดู "Page ID"

#### วิธี 2: จาก URL
1. ไปที่ Facebook Page ของคุณ
2. ดู URL แล้วค้นหา 4 หลักสุดท้ายหรือชื่อ Page

#### วิธี 3: ใช้ Graph API Explorer
1. ไปที่ https://developers.facebook.com/tools/explorer
2. เลือก App ของคุณ
3. Run query: `/me?fields=id,name`
4. Copy ID ที่ออกมา

### 4. ใส่ Token และ Page ID ในแอป

1. เปิด App
2. ไปที่ Tab "🤖 AI & Social Media"
3. ในส่วน Settings:
   - Facebook Access Token: [ใส่ token ที่ copy]
   - Page ID: [ใส่ Page ID]
4. คลิก "💾 บันทึก"

### 5. ทดสอบการทำงาน

1. ไปที่ Tab "📱 โพส Facebook"
2. พิมพ์ข้อความทดสอบ
3. คลิก "📤 โพสไป Facebook"
4. ตรวจสอบ Facebook Page ของคุณ

---

## Permissions ที่ต้องการ

Facebook App ต้องมี permissions ดังนี้:
- `pages_manage_posts` - สำหรับสร้างโพส
- `pages_read_engagement` - สำหรับอ่าน engagement
- `pages_manage_metadata` - สำหรับ metadata

*อ้างอิง: https://developers.facebook.com/docs/permissions*

---

## Troubleshooting

### "Invalid OAuth access token"
- Token หมดอายุ (มักจะ 60 วัน)
- สร้าง token ใหม่

### "User request limit reached"
- API rate limit
- รอสักครู่แล้วลองใหม่

### "Page does not have capability to post"
- ตรวจสอบว่า App ติดตั้งบน Page หรือไม่
- ไปที่ Page Settings → Apps and Plugins

---

## การใช้งาน Advanced

### สร้างโพสพร้อมรูปหลาย ๆ รูป (Carousel)
*Features ที่อาจจะเพิ่มในภายหลัง*

### Scheduled Posts
*ยังไม่ support แต่เป็น Feature ที่อาจเพิ่มเติม*

### Analytics
*สำหรับอ่าน engagement metrics*

---

**เอกสารอ้างอิง:** https://developers.facebook.com/docs/graph-api/
