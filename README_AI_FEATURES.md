# Stock POS System with AI Content Generator & Facebook Integration

## ✨ ฟีเจอร์ใหม่: AI & Social Media

ระบบสต็อกนี้ได้รับการอัปเกรดด้วยฟีเจอร์สร้างเนื้อหา AI และการโพส Facebook แบบอัตโนมัติ

### 🎯 ฟีเจอร์หลัก

#### 1. 📝 สร้างเนื้อหาสินค้า (AI Content Generation)
- ใช้ AI (OpenAI/Claude) สร้างรายละเอียดสินค้าโดยอัตโนมัติ
- เลือกสไตล์การเขียน: casual, professional, humorous, emotional
- คัดลอกหรือบันทึกเนื้อหาลงไฟล์

#### 2. 🎨 สร้างรูปโฆษณา (Ad Image Creator)
- สร้างรูปโฆษณาจากรูปสินค้า
- เพิ่มชื่อสินค้า ราคา และคำอธิบาย
- บันทึกเป็นรูป PNG พร้อมเพื่อโพส

#### 3. 📱 โพสไป Facebook (Facebook Integration)
- โพสข้อความ หรือ รูปภาพ หรือ ทั้งสองอย่าง
- เชื่อมต่อกับ Facebook Page API
- ตรวจสอบผลลัพธ์การโพสแบบเรียลไทม์

---

## 🚀 การติดตั้ง

### 1. ติดตั้ง Python Packages
```bash
pip install -r requirements.txt
```

### 2. ติดตั้ง AI Service (เลือกหนึ่งอย่าง)

#### ใช้ OpenAI (ChatGPT)
```bash
pip install openai
```
- สมัครสมาชิกที่ https://platform.openai.com
- สร้าง API Key
- นำมาใส่ในตั้งค่า Tab "🤖 AI & Social Media" > "AI Service" > "openai"

#### ใช้ Anthropic Claude
```bash
pip install anthropic
```
- สมัครสมาชิกที่ https://console.anthropic.com
- สร้าง API Key
- นำมาใส่ในตั้งค่า Tab "🤖 AI & Social Media" > "AI Service" > "anthropic"

#### ใช้ Offline Mode (ไม่ต้องมี API)
- เลือก "offline" ในตั้งค่า
- จะสร้างเนื้อหาอย่างง่าย ๆ โดยไม่ใช้ AI จริง

### 3. ตั้งค่า Facebook Integration

#### ขั้นตอนการหา Facebook Access Token:

1. ไปที่ https://developers.facebook.com
2. สร้าง App ใหม่ (Choose "Business" template)
3. เลือก "Messenger" product
4. ไปที่ "Messenger" → "Settings" 
5. ในส่วน "Access Tokens" เลือก Page ของคุณ
6. Click "Generate Token"
7. Copy token และนำมาใส่ในตั้งค่า

**หรือใช้วิธีเร็ว:**
- ไปที่ https://developers.facebook.com/tools/explorer/
- เลือก App ของคุณ
- เลือก Page ของคุณ
- Copy Access Token

#### หา Facebook Page ID:
- ไปที่ Page Settings
- ที่ "Page Information" จะเห็น Page ID

---

## 📖 วิธีการใช้งาน

### Tab "🤖 AI & Social Media"

#### ⚙️ ตั้งค่า API (สำคัญสุด!)
1. เลือก AI Service (openai, anthropic, หรือ offline)
2. ใส่ API Key (ถ้าใช้ openai/anthropic)
3. ใส่ Facebook Access Token และ Page ID
4. คลิก "💾 บันทึก"

#### 📝 สร้างเนื้อหาสินค้า
1. เลือก Tab "📝 สร้างเนื้อหา"
2. เลือกสินค้าจากรายการ
3. เลือกสไตล์การเขียน
4. คลิก "🤖 สร้างเนื้อหา"
5. คัดลอก หรือบันทึกเนื้อหา

#### 🎨 สร้างรูปโฆษณา
1. เลือก Tab "🎨 สร้างรูปโฆษณา"
2. เลือกสินค้า
3. เลือกรูปสินค้า (📁 เลือกรูป)
4. กรอกราคาและคำอธิบาย
5. คลิก "🎨 สร้างรูปโฆษณา"
6. รูปจะบันทึกใน folder "ads_output"
7. ที่ Tab นี้ยังมีปุ่ม "📤 โพส FB" เพื่อโพสไปที่ Facebook

#### 📱 โพสไป Facebook
1. เลือก Tab "📱 โพส Facebook"
2. เลือกประเภทโพส: ข้อความ, รูปภาพ, หรือ ทั้งสอง
3. กรอกข้อความ
4. เลือกรูป (ถ้าจำเป็น)
5. คลิก "📤 โพสไป Facebook"
6. ตรวจสอบผลลัพธ์ที่ช่อง "✅ ผลลัพธ์"

---

## 🔧 ไฟล์ที่เกี่ยวข้อง

### ไฟล์หลัก
- **app_stock.py** - แอปพลิเคชันหลัก
- **ai_content_generator.py** - Module สำหรับ AI generation และ Facebook integration
- **ai_config.json** - ไฟล์บันทึกการตั้งค่า (สร้างอัตโนมัติ)

### โฟลเดอร์
- **ads_output/** - เก็บรูปโฆษณาที่สร้าง

---

## ⚠️ ข้อควรระวัง

1. **API Keys**: อย่าแชร์ API Key กับใครเลย
2. **Facebook Token**: มี Expiration date ประมาณ 60 วัน จึงต้องรีเฟรช
3. **ค่าใช้ AI**: OpenAI มีค่าใช้ (แต่ถูก) ประมาณ $0.001 ต่อครั้ง
4. **อินเทอร์เน็ต**: ต้องมีการเชื่อมต่ออินเทอร์เน็ตดีๆ

---

## 🐛 ปัญหาทั่วไป

### "ModuleNotFoundError: No module named 'openai'"
**วิธีแก้:** `pip install openai`

### "Invalid Facebook Access Token"
**วิธีแก้:** 
- ตรวจสอบ token ยังไม่ Expire
- สร้าง token ใหม่จาก https://developers.facebook.com/tools/explorer/

### "AI returns offline content"
**วิธีแก้:** ตรวจสอบ
- API Key ถูกต้องหรือไม่
- มีการเชื่อมต่ออินเทอร์เน็ตหรือไม่
- API Service ไม่ down

### รูปโฆษณาไม่แสดง
**วิธีแก้:**
- ตรวจสอบรูปสินค้าสนับสนุนรูปแบบ PNG/JPG หรือไม่
- ลองเลือกรูปใหม่

---

## 📝 หมายเหตุ

- Offline mode สร้างเนื้อหาง่าย ๆ โดยไม่ใช้ AI จริง
- Facebook caption ใช้ OpenAI API (ต้อง API Key)
- รูปโฆษณาใช้ Pillow library

---

## 🔜 ฟีเจอร์ที่อาจเพิ่มเติม

- [ ] Instagram integration
- [ ] TikTok integration
- [ ] หลายภาษา
- [ ] Batch processing
- [ ] Template สำหรับโฆษณา
- [ ] AI image generation (DALL-E)

---

## 📞 ติดต่อ / Support

หากมีปัญหา กรุณาตรวจสอบ:
1. Python version >= 3.8
2. ติดตั้ง requirements.txt ครบทุกตัว
3. API Keys ถูกต้อง

---

**Version:** 1.0.0  
**Last Updated:** January 2026
