#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test fpdf2 receipt generation with Thai text support"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fpdf import FPDF
import qrcode

def test_generate_receipt_pdf():
    """Test the new fpdf2-based PDF generation"""
    
    # Create test data
    receipt_id = "TEST001"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items = [
        {"name": "น้ำหล่อเย็น", "qty": 2, "price": 150.00, "total": 300.00},
        {"name": "โอ่ลเครื่องยนต์", "qty": 1, "price": 250.00, "total": 250.00},
        {"name": "แผ่นเบรค", "qty": 4, "price": 80.00, "total": 320.00},
    ]
    total_bill = 870.00
    discount_amount = 50.00
    final_total = 820.00
    payment_method = "เงินสด"
    used_coupon = "NEW2024"
    received_coupon = "SAVE50"
    
    # Create receipts folder if needed
    receipts_folder = "Receipts"
    os.makedirs(receipts_folder, exist_ok=True)
    
    try:
        pdf_path = os.path.join(receipts_folder, f"{receipt_id}.pdf")
        
        # Create PDF with fpdf2
        pdf = FPDF(format=(80, 200), unit="mm")
        pdf.add_page()
        
        # Try to add Kanit font for Thai support
        font_dir = os.path.expanduser(r'~\AppData\Local\Microsoft\Windows\Fonts')
        font_path = os.path.join(font_dir, 'Kanit-Regular.ttf')
        
        thai_font = "Arial"  # Default to Arial
        if os.path.exists(font_path):
            pdf.add_font("Kanit", "", font_path)
            thai_font = "Kanit"
            print(f"✓ Using Kanit font from: {font_path}")
        else:
            print(f"✗ Kanit font not found at {font_path}, using Arial")
        
        # Set margins
        pdf.set_margins(3, 3, 3)
        
        # Header
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 6, "JZ Auto Parts", ln=True, align="C")
        pdf.set_font(thai_font, "", 8)
        pdf.cell(0, 4, "ร้านอะไหล่รถ JZ", ln=True, align="C")
        
        # Separator
        pdf.set_font(thai_font, "", 7)
        pdf.cell(0, 3, "=" * 30, ln=True, align="C")
        
        # Receipt info
        date_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        pdf.set_font(thai_font, "", 8)
        pdf.cell(0, 4, f"เลขที่ใบเสร็จ: {receipt_id}", ln=True, align="C")
        pdf.cell(0, 4, f"วันที่: {date_time.strftime('%d/%m/%Y')}", ln=True, align="C")
        pdf.cell(0, 4, f"เวลา: {date_time.strftime('%H:%M:%S')}", ln=True, align="C")
        
        pdf.ln(2)
        
        # Table header
        col_widths = [25, 12, 15, 16]
        pdf.set_font(thai_font, "", 7)
        pdf.cell(col_widths[0], 4, "สินค้า", border=0, align="C")
        pdf.cell(col_widths[1], 4, "จำนวน", border=0, align="C")
        pdf.cell(col_widths[2], 4, "ราคา", border=0, align="C")
        pdf.cell(col_widths[3], 4, "รวม", border=0, align="C", ln=True)
        
        # Items
        pdf.set_font(thai_font, "", 7)
        for item in items:
            name = item['name'][:12] if len(item['name']) > 12 else item['name']
            pdf.cell(col_widths[0], 4, name, border=1, align="C")
            pdf.cell(col_widths[1], 4, str(item['qty']), border=1, align="C")
            pdf.cell(col_widths[2], 4, f"{item['price']:.2f}", border=1, align="R")
            pdf.cell(col_widths[3], 4, f"{item['total']:.2f}", border=1, align="R", ln=True)
        
        pdf.ln(1)
        
        # Separator
        pdf.set_font(thai_font, "", 7)
        pdf.cell(0, 3, "=" * 30, ln=True, align="C")
        
        # Summary
        pdf.set_font(thai_font, "", 8)
        pdf.cell(0, 4, f"ยอดรวม: {total_bill:,.2f} บาท", ln=True, align="R")
        
        if discount_amount > 0:
            pdf.cell(0, 4, f"ส่วนลด: -{discount_amount:,.2f} บาท", ln=True, align="R")
        
        pdf.cell(0, 4, f"ยอดที่จ่าย: {final_total:,.2f} บาท", ln=True, align="R")
        
        pdf.ln(2)
        
        # Payment info
        pdf.set_font(thai_font, "", 8)
        pdf.cell(0, 4, f"วิธีจ่าย: {payment_method}", ln=True, align="C")
        
        if used_coupon and used_coupon != "-":
            pdf.cell(0, 4, f"โค้ตที่ใช้: {used_coupon}", ln=True, align="C")
        
        if received_coupon and received_coupon != "-":
            pdf.cell(0, 4, f"โค้ตส่วนลดใหม่ที่ได้รับ: {received_coupon}", ln=True, align="C")
        
        pdf.ln(2)
        
        # QR Code
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(receipt_id)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_path = os.path.join(receipts_folder, f"{receipt_id}_qr.png")
            qr_img.save(qr_path)
            
            pdf.set_font(thai_font, "", 8)
            pdf.cell(0, 4, receipt_id, ln=True, align="C")
            
            # Center the QR code
            pdf.image(qr_path, x=20, y=pdf.get_y(), w=40, h=40)
            pdf.ln(42)
            
            print(f"✓ QR code generated and embedded")
        except Exception as e:
            print(f"✗ QR code generation failed: {e}")
        
        pdf.ln(2)
        
        # Footer
        pdf.set_font(thai_font, "", 7)
        pdf.cell(0, 3, "=" * 30, ln=True, align="C")
        
        pdf.set_font(thai_font, "", 9)
        pdf.cell(0, 4, "ขอบคุณสำหรับการใช้บริการ", ln=True, align="C")
        
        pdf.set_font("Arial", "", 8)
        pdf.cell(0, 3, "THANK YOU FOR YOUR VISIT", ln=True, align="C")
        
        pdf.set_font("Arial", "", 7)
        pdf.cell(0, 3, "Facebook : PKN เครื่องเลื้อยไม้ เครื่องตัดหญ้า ราคาถูก", ln=True, align="C")
        pdf.cell(0, 3, "เบอร์โทรศัพท์: 086-283-6944", ln=True, align="C")
        
        # Save PDF
        pdf.output(pdf_path)
        
        print(f"✓ PDF generated successfully: {pdf_path}")
        print(f"✓ File size: {os.path.getsize(pdf_path)} bytes")
        
        # Try to open it
        import subprocess
        try:
            subprocess.Popen(['start', pdf_path], shell=True)
            print("✓ PDF preview opened")
        except:
            print(f"✓ PDF saved but couldn't auto-open. Open manually: {pdf_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing fpdf2 receipt generation with Thai text support...")
    print("=" * 60)
    
    success = test_generate_receipt_pdf()
    
    print("=" * 60)
    if success:
        print("✓ Test PASSED - fpdf2 receipt generation working with Thai text!")
    else:
        print("✗ Test FAILED - check errors above")
    
    sys.exit(0 if success else 1)
