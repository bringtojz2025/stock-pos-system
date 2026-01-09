#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ทดสอบการสร้าง PDF ใบเสร็จ - standalone"""

import os
import sys
import tempfile
from datetime import datetime
from fpdf import FPDF, XPos, YPos
import qrcode
from PIL import Image

# ตรวจสอบฟอนต์
def test_font_detection():
    """ทดสอบการค้นหาฟอนต์"""
    print("=" * 50)
    print("ทดสอบการค้นหาฟอนต์...")
    print("=" * 50)
    
    if sys.platform == 'win32':
        font_dir = os.path.expanduser(r'~\AppData\Local\Microsoft\Windows\Fonts')
    else:
        font_dir = os.path.expanduser('~/.local/share/fonts')
    
    print(f"📁 ค้นหาฟอนต์ใน: {font_dir}\n")
    
    # ค้นหาฟอนต์ไทยที่มีอยู่
    thai_font = "Helvetica"
    font_names = ['TH SarabunPSK.ttf', 'THSarabunNew.ttf', 'Kanit-Regular.ttf', 'tahoma.ttf']
    
    for font_name in font_names:
        font_path = os.path.join(font_dir, font_name)
        exists = os.path.exists(font_path)
        status = "✓ เจอ" if exists else "✗ ไม่เจอ"
        print(f"{status}: {font_name}")
        if exists:
            thai_font = font_name.replace('.ttf', '').replace(' ', '')
            print(f"   → เลือกใช้: {thai_font}")
            break
    
    print(f"\n✓ ฟอนต์ที่ใช้: {thai_font}\n")
    return thai_font

def test_pdf_generation():
    """ทดสอบการสร้าง PDF"""
    print("=" * 50)
    print("ทดสอบการสร้าง PDF ใบเสร็จ...")
    print("=" * 50)
    
    # หาฟอนต์
    thai_font = test_font_detection()
    
    # สร้าง folder สำหรับ receipt ใน temp
    receipts_folder = os.path.join(tempfile.gettempdir(), "test_receipts")
    os.makedirs(receipts_folder, exist_ok=True)
    
    # ข้อมูลทดสอบ
    receipt_id = "JZ20260109000034"
    timestamp = "2026-01-09 14:30:00"
    items = [
        {'name': 'สปริง', 'qty': 2, 'price': 150.00, 'total': 300.00},
        {'name': 'แบตเตอรี่', 'qty': 1, 'price': 500.00, 'total': 500.00},
    ]
    total_bill = 800.00
    discount_amount = 50.00
    final_total = 750.00
    payment_method = "เงินสด"
    used_coupon = "-"
    received_coupon = "DISCOUNT50"
    
    try:
        pdf_path = os.path.join(receipts_folder, f"{receipt_id}.pdf")
        
        # สร้าง PDF ด้วย fpdf2
        pdf = FPDF(format=(80, 200), unit="mm")
        pdf.add_page()
        
        # ค้นหาและเพิ่ม font
        if sys.platform == 'win32':
            font_dir = os.path.expanduser(r'~\AppData\Local\Microsoft\Windows\Fonts')
        else:
            font_dir = os.path.expanduser('~/.local/share/fonts')
        
        font_names = ['TH SarabunPSK.ttf', 'THSarabunNew.ttf', 'Kanit-Regular.ttf', 'tahoma.ttf']
        
        for font_name in font_names:
            font_path = os.path.join(font_dir, font_name)
            if os.path.exists(font_path):
                font_clean_name = font_name.replace('.ttf', '').replace(' ', '')
                try:
                    pdf.add_font(font_clean_name, "", font_path)
                    thai_font = font_clean_name
                    print(f"✓ ใช้ฟอนต์: {font_name}")
                    break
                except:
                    continue
        
        # Set margin
        pdf.set_margins(3, 3, 3)
        
        # โลโก้
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "img", "logo.png")
            if os.path.exists(logo_path):
                pdf.image(logo_path, x=30, y=5, w=20, h=20)
                pdf.ln(24)
        except:
            pass
        
        # ชื่อร้าน
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, "JZ Auto Parts", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.set_font(thai_font, "", 8)
        pdf.cell(0, 4, "ร้านอะไหล่รถ JZ", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        
        # เส้นคั่น
        pdf.set_font(thai_font, "", 7)
        pdf.cell(0, 3, "=" * 30, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        
        # ข้อมูลใบเสร็จ - เลขซ้าย เวลาขวา
        date_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        pdf.set_font(thai_font, "", 9)
        pdf.cell(40, 4, f"เลขที่: {receipt_id}", border=0, align="L", new_x=XPos.LEFT, new_y=YPos.TOP)
        pdf.cell(0, 4, f"{date_time.strftime('%d/%m/%Y %H:%M:%S')}", border=0, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.ln(2)
        
        # ตารางรายการสินค้า
        col_widths = [25, 12, 15, 16]
        pdf.set_font(thai_font, "", 7)
        pdf.cell(col_widths[0], 4, "สินค้า", border=1, align="C")
        pdf.cell(col_widths[1], 4, "จำนวน", border=1, align="C")
        pdf.cell(col_widths[2], 4, "ราคา", border=1, align="C")
        pdf.cell(col_widths[3], 4, "รวม", border=1, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # รายการสินค้า
        for item in items:
            name = item['name'][:12] if len(item['name']) > 12 else item['name']
            pdf.cell(col_widths[0], 4, name, border=1, align="C")
            pdf.cell(col_widths[1], 4, str(item['qty']), border=1, align="C")
            pdf.cell(col_widths[2], 4, f"{item['price']:.2f}", border=1, align="R")
            pdf.cell(col_widths[3], 4, f"{item['total']:.2f}", border=1, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.ln(1)
        
        # เส้นคั่น
        pdf.set_font(thai_font, "", 7)
        pdf.cell(0, 3, "=" * 30, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        
        # สรุปยอดขาย
        pdf.set_font(thai_font, "", 8)
        pdf.cell(0, 4, f"ยอดรวม: {total_bill:,.2f} บาท", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
        
        if discount_amount > 0:
            pdf.cell(0, 4, f"ส่วนลด: -{discount_amount:,.2f} บาท", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
        
        pdf.cell(0, 4, f"ยอดที่จ่าย: {final_total:,.2f} บาท", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
        
        if used_coupon and used_coupon != "-":
            pdf.cell(0, 4, f"โค้ตที่ใช้: {used_coupon}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
        
        pdf.ln(2)
        
        # วิธีชำระเงิน
        pdf.set_font(thai_font, "", 8)
        pdf.cell(0, 4, f"วิธีจ่าย: {payment_method}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
        
        if received_coupon and received_coupon != "-":
            pdf.cell(0, 4, f"โค้ตส่วนลดที่ได้รับ: {received_coupon}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
        
        pdf.ln(2)
        
        # ข้อความปิด
        pdf.set_font(thai_font, "", 7)
        pdf.cell(0, 3, "=" * 30, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        
        pdf.set_font(thai_font, "", 9)
        pdf.cell(0, 4, "ขอบคุณสำหรับการใช้บริการ", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 3, "THANK YOU FOR YOUR VISIT", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        
        pdf.set_font(thai_font, "", 7)
        pdf.cell(0, 3, "facebook: PKN เครื่องเลื้อยไม้ เครื่องตัดหญ้า ราคาถูก", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.cell(0, 3, "Tel: 086-283-6944", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        
        # บันทึก PDF
        pdf.output(pdf_path)
        
        print(f"\n✓ สร้างใบเสร็จ PDF สำเร็จ!")
        print(f"📄 ที่อยู่: {pdf_path}")
        return True
        
    except Exception as e:
        print(f"\n✗ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pdf_generation()
    sys.exit(0 if success else 1)
