# 🔧 เอกสารเชิงเทคนิค - ระบบสร้างและปริ้นใบเสร็จ PDF

## 📐 โครงสร้างทางเทคนิค

### ส่วนประกอบหลัก

```
app_stock.py
├── load_receipt_settings()         # โหลดการตั้งค่าจาก JSON
├── save_receipt_settings()         # บันทึกการตั้งค่าเป็น JSON
├── generate_receipt_pdf()          # สร้าง PDF ใบเสร็จ
├── _generate_barcode_image()       # สร้างบาร์โค้ด
├── show_receipt_preview()          # แสดงพรีวิว PDF
├── print_receipt()                 # ปริ้น PDF
├── process_receipt_after_checkout()# ประมวลผลใบเสร็จหลังชำระเงิน
├── _show_receipt_options()         # แสดงตัวเลือกให้ผู้ใช้
├── get_selected_printer()          # ดึงชื่อเครื่องปริ้น
└── toggle_receipt_auto_print()     # สลับโหมดปริ้นอัตโนมัติ
```

## 🔄 Flow การทำงาน

```
user เลือก "💰 ชำระเงิน"
        ↓
   process_checkout()
        ↓
   run_checkout_thread()  [Thread ต่างหาก]
        ↓
   อัปเดต Google Sheets
        ↓
   process_receipt_after_checkout()
        ↓
   ┌─────────────────────────────────┐
   │  generate_receipt_pdf()         │
   │  + _generate_barcode_image()    │
   │  → บันทึก PDF ลงโฟลเดอร์        │
   └─────────────────────────────────┘
        ↓
   ┌──────────────────────┐
   │ ตรวจสอบ             │
   │ receipt_auto_print? │
   └──────────────────────┘
        ↙          ↘
    [true]       [false]
      ↓            ↓
 print_receipt() _show_receipt_options()
      ↓            ↓
   ปริ้นทันที  ให้ผู้ใช้เลือก
      ↓            ↓
   finish_checkout()
```

## 📁 ไฟล์ที่สร้างใหม่

### `receipts/` - โฟลเดอร์เก็บใบเสร็จ
```
receipts/
├── JZ20260109000001.pdf           # ไฟล์ PDF ใบเสร็จ
├── JZ20260109000001_barcode.png   # บาร์โค้ด
├── JZ20260109000002.pdf
├── JZ20260109000002_barcode.png
└── ...
```

### `receipt_settings.json` - ตั้งค่าปริ้นใบเสร็จ
```json
{
    "auto_print": false
}
```

## 🛠️ Function Details

### `generate_receipt_pdf(receipt_id, timestamp, items, ...)`

**พารามิเตอร์:**
- `receipt_id` (str): เลขที่ใบเสร็จ เช่น "JZ20260109000001"
- `timestamp` (str): วันที่เวลา เช่น "2026-01-09 15:30:45"
- `items` (list): รายการสินค้า
  ```python
  [
      {'name': 'เบรค', 'qty': 1, 'price': 250.00, 'total': 250.00},
      {'name': 'หม้อน้ำ', 'qty': 1, 'price': 180.00, 'total': 180.00},
  ]
  ```
- `total_bill` (float): ยอดรวมก่อนลด
- `discount_amount` (float): ยอดส่วนลด
- `final_total` (float): ยอดสุดท้าย
- `payment_method` (str): วิธีชำระเงิน
- `used_coupon` (str): โค้ตที่ใช้
- `received_coupon` (str): โค้ตที่ได้รับ

**ค่าส่งคืน:**
- `str` หรือ `None`: เส้นทางไฟล์ PDF หรือ None ถ้าเกิดข้อผิดพลาด

**ตัวอย่างการใช้:**
```python
pdf_path = self.generate_receipt_pdf(
    "JZ20260109000001",
    "2026-01-09 15:30:45",
    [{'name': 'เบรค', 'qty': 1, 'price': 250.00, 'total': 250.00}],
    250.00,
    0.00,
    250.00,
    "เงินสด",
    "-",
    "-"
)
```

### `print_receipt(pdf_path, printer_name=None)`

**พารามิเตอร์:**
- `pdf_path` (str): เส้นทางไฟล์ PDF
- `printer_name` (str, optional): ชื่อเครื่องปริ้น

**ค่าส่งคืน:**
- `bool`: True ถ้าสำเร็จ, False ถ้าล้มเหลว

**ตัวอย่างการใช้:**
```python
# ปริ้นโดยใช้เครื่องปริ้นที่บันทึกไว้
success = self.print_receipt("/path/to/receipt.pdf")

# ปริ้นไปยังเครื่องปริ้นเฉพาะ
success = self.print_receipt("/path/to/receipt.pdf", "HP Printer")
```

### `toggle_receipt_auto_print()`

**ฟังก์ชัน:** สลับโหมดปริ้นอัตโนมัติ

**ค่าส่งคืน:** ไม่มี (แต่จะแสดง messagebox)

**ตัวอย่างการใช้:**
```python
# เรียกจากปุ่ม
btn = ctk.CTkButton(frame, command=self.toggle_receipt_auto_print)
```

## 📊 PDF Structure

PDF ใบเสร็จถูกสร้างโดยใช้ ReportLab และมีโครงสร้าง:

```
┌─────────────────────────────┐
│      SimpleDocTemplate      │  ← Page container (80x300 mm)
│  ┌───────────────────────┐  │
│  │  Title (ชื่อร้าน)     │  │
│  ├───────────────────────┤  │
│  │  Receipt Info         │  │
│  │  (เลขที่, วันที่, เวลา)  │
│  ├───────────────────────┤  │
│  │  Items Table          │  │
│  │  (สินค้า, ราคา, รวม)   │
│  ├───────────────────────┤  │
│  │  Summary              │  │
│  │  (ยอดรวม, ลด, สุดท้าย) │
│  ├───────────────────────┤  │
│  │  Payment Info         │  │
│  │  (วิธีจ่าย, โค้ต)       │
│  ├───────────────────────┤  │
│  │  Barcode              │  │
│  │  [||||||||||||||||]   │  │
│  ├───────────────────────┤  │
│  │  Thank You Message    │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
```

## 🎨 Styling

### Table Style
```python
TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),      # Header bg
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),              # Center align
    ('FONTSIZE', (0, 0), (-1, -1), 7),                  # Font size
    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),      # Grid lines
])
```

### Paragraph Styles
```python
title_style = ParagraphStyle(
    fontName='Helvetica-Bold',
    fontSize=11,
    alignment=TA_CENTER,
)

normal_style = ParagraphStyle(
    fontName='Helvetica',
    fontSize=8,
    alignment=TA_CENTER,
)

summary_style = ParagraphStyle(
    fontName='Helvetica-Bold',
    fontSize=9,
    alignment=TA_RIGHT,
)
```

## 🖨️ Printing Implementation

### Windows Print Command
```python
# วิธีที่ 1: ใช้ os.startfile (ค่าเริ่มต้น)
os.startfile(pdf_path, "print")

# วิธีที่ 2: ใช้ subprocess (fallback)
subprocess.Popen(f'start "{pdf_path}"', shell=True)
```

### Printer Detection
```python
# ดึงชื่อเครื่องปริ้นที่บันทึกไว้
printer_name = self.get_selected_printer()

# บันทึกลง printer_config.json
self.printer_name = printer_name
```

## 🔐 Configuration Files

### receipt_settings.json
```json
{
    "auto_print": false  // false = prompt user, true = auto print
}
```

### printer_config.json
```json
{
    "selected_printer": "Microsoft Print to PDF"
}
```

## 📦 Dependencies

| Package | Version | ใช้สำหรับ |
|---------|---------|---------|
| reportlab | >= 4.0.0 | สร้าง PDF |
| python-barcode | >= 0.15.0 | สร้างบาร์โค้ด |
| Pillow | >= 9.5.0 | จัดการรูปภาพ |
| customtkinter | >= 5.0.0 | GUI |

## 🐛 Error Handling

### Try-Except Blocks
```python
try:
    # สร้าง PDF
    pdf_path = self.generate_receipt_pdf(...)
except Exception as e:
    print(f"✗ สร้าง PDF ไม่สำเร็จ: {e}")
    # Log or handle error
```

### Validation
```python
if not os.path.exists(pdf_path):
    messagebox.showerror("ข้อผิดพลาด", "ไม่พบไฟล์ PDF")
    return False
```

## 🧪 Testing

### Test Case 1: Create Receipt PDF
```python
# Arrange
receipt_id = "TEST000001"
items = [{'name': 'Test Item', 'qty': 1, 'price': 100, 'total': 100}]

# Act
pdf_path = self.generate_receipt_pdf(
    receipt_id, "2026-01-09 15:30:45", items,
    100, 0, 100, "เงินสด", "-", "-"
)

# Assert
assert os.path.exists(pdf_path)
assert pdf_path.endswith(".pdf")
```

### Test Case 2: Print Receipt
```python
# Act
success = self.print_receipt(pdf_path)

# Assert
assert success == True
```

### Test Case 3: Toggle Auto Print
```python
# Before
assert self.receipt_auto_print == False

# Act
self.toggle_receipt_auto_print()

# After
assert self.receipt_auto_print == True
```

## 🚀 Performance Considerations

1. **PDF Generation**: ~1-2 seconds สำหรับใบเสร็จทั่วไป
2. **Barcode Generation**: ~0.5 seconds
3. **Printing**: Depends on printer (usually 3-10 seconds)
4. **Threading**: ใช้ daemon thread เพื่อไม่บล็อก UI

## 🔄 Integration with Checkout Flow

```python
# ใน run_checkout_thread()
1. บันทึกข้อมูลลง Google Sheets
2. อัปเดต inventory
3. เรียก process_receipt_after_checkout()
   ├─ สร้าง PDF
   ├─ ตรวจสอบ receipt_auto_print
   └─ ปริ้นหรือแสดง dialog
4. ล้างตะกร้า (finish_checkout)
```

## 📝 Customization Guide

### เปลี่ยนขนาด PDF
```python
# ไป bรรทัด ~4270
doc = SimpleDocTemplate(
    pdf_path,
    pagesize=(80*mm, 300*mm),  # 80mm กว้าง, 300mm ยาว
    topMargin=3*mm,
    bottomMargin=3*mm,
    leftMargin=3*mm,
    rightMargin=3*mm
)
```

### เปลี่ยน Font
```python
# ทีมแนะนำให้ใช้ 'Helvetica' สำหรับ compatibility
# ถ้าต้องใช้ Thai font ต้องใช้ TrueType font
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('Kanit', 'path/to/Kanit-Regular.ttf'))
```

### เพิ่มข้อมูลลงใบเสร็จ
```python
# ใน generate_receipt_pdf()
# เพิ่ม story.append(...)
story.append(Paragraph("Custom Info", normal_style))
```

## 🎓 Learning Resources

- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [python-barcode](https://python-barcode.readthedocs.io/)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)

---

**Last Updated**: January 9, 2026  
**Version**: 1.0  
**Status**: Production Ready ✓
