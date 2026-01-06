# Stock POS System with AI Content Generator 🤖

ระบบ POS และจัดการสต็อกสินค้า พร้อมตัวสร้างเนื้อหา AI และการโพส Facebook อัตโนมัติ

## ✨ Features

### 📦 1. ระบบ POS (Point of Sale)
- สแกน Barcode เพื่อเพิ่มสินค้าลงตะกร้า
- บัญชีราคาอัตโนมัติ
- ตัดสต็อกอัตโนมัติ
- ระบบการชำระเงิน
- พิมพ์ใบเสร็จ

### 📊 2. คลังสินค้า (Inventory)
- จัดการสินค้า (เพิ่ม/แก้ไข/ลบ)
- ตรวจสอบจำนวนสินค้า
- ประวัติการเปลี่ยนแปลง
- Sync กับ Google Sheets

### 📈 3. ประวัติการขาย (History)
- ดูประวัติการขายทั้งหมด
- กรอกตามวันที่
- ค้นหาตามเลขใบเสร็จ
- ส่งออกรายงาน

### 📉 4. ภาพรวม (Dashboard)
- สถิติการขายรายวัน
- สินค้าขายดี
- ยอดขายรวม
- กราฟแสดงข้อมูล

### 🤖 5. AI & Social Media
#### 📝 สร้างเนื้อหา
- ใช้ Google Gemini API สร้างรายละเอียดสินค้า
- เลือกสไตล์การเขียน (casual, professional, humorous, emotional)
- แสดงผล + Facebook Caption อัตโนมัติ

#### 🎨 สร้างรูปโฆษณา
- เปิด Gemini Web สำหรับสร้างรูปอัตโนมัติ
- หรือเพิ่มข้อความบนรูปสินค้ากำหนดเอง

#### 📱 โพสต่อ Facebook
- โพสข้อความ
- โพสรูปภาพ
- โพสข้อความ + รูป
- ต้องมี Facebook Access Token

## 🚀 Installation

### ข้อกำหนด
- Python 3.8+
- Google Account (สำหรับ Sheets & Drive)
- Google Gemini API Key
- Facebook Developer Token (optional)

### ขั้นตอนการติดตั้ง

1. **Clone Repository**
```bash
git clone https://github.com/yourusername/stock-pos-system.git
cd stock-pos-system
```

2. **ติดตั้ง Dependencies**
```bash
pip install -r requirements.txt
```

หรือใน Windows:
```bash
install.bat
```

3. **ตั้งค่า Google Credentials**
- ไปที่ [Google Cloud Console](https://console.cloud.google.com/)
- สร้าง OAuth 2.0 Client ID (Desktop application)
- ดาวน์โหลด JSON และบันทึกเป็น `client_secret.json`

4. **ตั้งค่า Gemini API Key**
- ไปที่ [Google AI Studio](https://aistudio.google.com/app/apikey)
- สร้าง API Key ใหม่
- คัดลอกไปวาง ในโปรแกรม (Tab 🤖 AI & Social Media → Settings)

5. **ตั้งค่า Facebook (optional)**
- ไปที่ [Facebook Developers](https://developers.facebook.com/)
- สร้าง App และ Page
- ได้ Page Access Token
- คัดลอกไปวาง ในโปรแกรม

6. **รัน Application**
```bash
python app_stock.py
```

## 📋 Usage

### สร้างเนื้อหา AI
1. ไปที่ Tab 🤖 AI & Social Media
2. เลือก "สร้างเนื้อหา"
3. เลือกสินค้าจาก Combo box
4. ระบบจะ auto-fill รายละเอียด
5. เลือกสไตล์การเขียน
6. กดปุ่ม "สร้างเนื้อหา"
7. ข้อมูลจะแสดงรวม ๆ พร้อม Facebook Caption

### สร้างรูปโฆษณา
1. ไปที่ Tab 🤖 AI & Social Media → สร้างรูปโฆษณา
2. เลือกสินค้า
3. วิธี 1: กด "เปิด Gemini Web" → สร้างรูป → Copy บน Web
4. วิธี 2: เลือกรูป → เพิ่มข้อความ → กด "เพิ่มข้อความบนรูป"

### โพสต่อ Facebook
1. ไปที่ Tab 🤖 AI & Social Media → โพส Facebook
2. เลือกประเภทโพส (ข้อความ/รูป/ข้อความ+รูป)
3. กรอกข้อมูล
4. กดปุ่ม "โพสไป Facebook"

## 🗂️ Project Structure

```
stock-pos-system/
├── app_stock.py                 # Main Application
├── ai_content_generator.py      # AI & Social Media Module
├── requirements.txt             # Dependencies
├── README.md                    # This file
├── README_AI_FEATURES.md        # AI Features Documentation
├── FACEBOOK_SETUP.md            # Facebook Setup Guide
├── ai_config_example.json       # Example Config
├── ai_config.json              # Config (not in git)
├── client_secret.json          # Google Auth (not in git)
├── credentials.json            # Google Credentials (not in git)
├── ads_output/                 # Output Ads Folder
└── __pycache__/                # Python Cache
```

## 📦 Dependencies

ดู [requirements.txt](requirements.txt) สำหรับรายละเอียดทั้งหมด

หลัก:
- `customtkinter` - Modern GUI Framework
- `gspread` - Google Sheets API
- `google-generativeai` - Google Gemini API
- `Pillow` - Image Processing
- `matplotlib` - Data Visualization
- `qrcode` - QR Code Generation

## 🔧 Configuration

### ai_config.json
```json
{
    "ai_api_type": "gemini",
    "ai_api_key": "your-gemini-api-key",
    "facebook_access_token": "your-facebook-token",
    "facebook_page_id": "your-page-id"
}
```

## 📖 Documentation

- [AI Features Guide](README_AI_FEATURES.md)
- [Facebook Setup Guide](FACEBOOK_SETUP.md)

## 🐛 Troubleshooting

### Google Sheets Connection Error
- ตรวจสอบไฟล์ `client_secret.json` มีอยู่หรือไม่
- ลบ `token.pickle` แล้ว re-authenticate

### Gemini API Error
- เช็คว่า API Key ถูกต้อง
- ตรวจสอบ quota API
- ลองสร้าง API Key ใหม่

### Facebook Posting Failed
- เช็ค Access Token ยังใช้ได้หรือไม่ (expire ภายใน 60 วัน)
- เช็ค Page ID ถูกต้องหรือไม่

## 📝 License

MIT License - Feel free to use for personal or commercial projects

## 👤 Author

[Your Name/bringtojz]

## 🤝 Contributing

ยินดีต้อนรับ Pull Requests และ Issues!

## 📞 Support

ติดต่อ: bringtojz@gmail.com

---

**Made with ❤️ for Small Business Owners**
