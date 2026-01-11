"""
PromptPay QR Code Generator
Generates PromptPay QR codes for receiving payments
Based on EMVCo Standard (https://www.emvco.com)
"""

import qrcode
from io import BytesIO
import re


class PromptPayQR:
    """สร้าง QR Code สำหรับ PromptPay (พร้อมเพย์)"""
    
    # ค่าคงที่ EMVCo
    PAYLOAD_FORMAT_ID = "00"  # QR Code Specification
    POINT_OF_INITIATION_METHOD = "11"  # Static QR
    MERCHANT_CATEGORY_CODE = "5411"  # Retail
    TRANSACTION_CURRENCY = "764"  # THB
    
    # Tag สำหรับ PromptPay
    PROMPTPAY_TAG = "29"
    MOBILE_NUMBER_TAG = "01"
    ID_NUMBER_TAG = "02"
    CREDIT_TRANSFER_TAG = "30"
    
    def __init__(self):
        pass
    
    @staticmethod
    def generate_qr_code(amount, mobile_number=None, id_number=None, merchant_name=""):
        """
        สร้าง QR Code สำหรับ PromptPay
        
        Args:
            amount: ยอดเงินที่ต้องชำระ (เป็นจำนวนเต็มหรือทศนิยม 2 ตำแหน่ง)
            mobile_number: เบอร์โทรศัพท์ (0xxxxxxxxx)
            id_number: เลขประจำตัวประชาชน (13 หลัก) หรือเลขประจำตัวผู้เสียภาษี (13 หลัก)
            merchant_name: ชื่อผู้รับเงิน (ข้อความแจ้งกรรมการ)
        
        Returns:
            PIL.Image object ของ QR Code
        """
        try:
            # สร้าง Payload
            payload = PromptPayQR._generate_payload(
                amount, 
                mobile_number, 
                id_number, 
                merchant_name
            )
            
            # สร้าง QR Code จาก payload
            qr = qrcode.QRCode(
                version=None,  # Auto-detect
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(payload)
            qr.make(fit=True)
            
            # สร้างรูปภาพ
            img = qr.make_image(fill_color="black", back_color="white")
            
            return img
        
        except Exception as e:
            print(f"Error generating PromptPay QR: {e}")
            return None
    
    @staticmethod
    def _generate_payload(amount, mobile_number=None, id_number=None, merchant_name=""):
        """สร้าง Payload ตามมาตรฐาน EMVCo"""
        
        # ตรวจสอบว่าระบุตัวตน (Mobile หรือ ID)
        if not mobile_number and not id_number:
            raise ValueError("Must provide either mobile_number or id_number")
        
        # ทำให้ประเทศ
        merchant_account_info = PromptPayQR._create_merchant_account_info(
            mobile_number, 
            id_number
        )
        
        # สร้าง payload
        payload = ""
        
        # 1. Payload Format Indicator
        payload += PromptPayQR._add_tlv("00", "01")
        
        # 2. Point of Initiation Method
        payload += PromptPayQR._add_tlv("01", PromptPayQR.POINT_OF_INITIATION_METHOD)
        
        # 3. Merchant Account Information (PromptPay)
        payload += PromptPayQR._add_tlv(PromptPayQR.PROMPTPAY_TAG, merchant_account_info)
        
        # 4. Merchant Category Code
        payload += PromptPayQR._add_tlv("52", PromptPayQR.MERCHANT_CATEGORY_CODE)
        
        # 5. Transaction Currency
        payload += PromptPayQR._add_tlv("53", PromptPayQR.TRANSACTION_CURRENCY)
        
        # 6. Transaction Amount (ถ้าระบุ)
        if amount and float(amount) > 0:
            amount_str = f"{float(amount):.2f}"
            payload += PromptPayQR._add_tlv("54", amount_str)
        
        # 7. Country Code
        payload += PromptPayQR._add_tlv("58", "TH")
        
        # 8. Merchant Name (ถ้าระบุ)
        if merchant_name:
            payload += PromptPayQR._add_tlv("59", merchant_name[:25])
        
        # 9. Merchant City
        payload += PromptPayQR._add_tlv("60", "BANGKOK")
        
        # 10. CRC (Checksum) - คำนวณจากข้อมูลทั้งหมด
        payload = PromptPayQR._add_crc(payload)
        
        return payload
    
    @staticmethod
    def _create_merchant_account_info(mobile_number=None, id_number=None):
        """สร้าง Merchant Account Information สำหรับ PromptPay"""
        info = ""
        
        # PromptPay Account ID (Mobile หรือ ID)
        if mobile_number:
            # ทำให้เบอร์โทรเป็นรูปแบบ 0xxxxxxxxx
            mobile = PromptPayQR._normalize_mobile(mobile_number)
            info += PromptPayQR._add_tlv(
                PromptPayQR.MOBILE_NUMBER_TAG, 
                mobile
            )
        
        if id_number:
            # เลขบัตรประชาชน/เลขประจำตัวผู้เสียภาษี (13 หลัก)
            id_norm = PromptPayQR._normalize_id(id_number)
            info += PromptPayQR._add_tlv(
                PromptPayQR.ID_NUMBER_TAG, 
                id_norm
            )
        
        # ทำให้เป็น TLV format
        result = ""
        length = len(info) // 2  # แปลงจากคู่ hex ไปเป็นจำนวน bytes
        result = f"{int(PromptPayQR.PROMPTPAY_TAG):02X}{length:02X}{info}"
        
        return result
    
    @staticmethod
    def _add_tlv(tag, value):
        """เพิ่ม Tag-Length-Value (TLV) format"""
        # แปลง value เป็น hex string
        if isinstance(value, str):
            value_hex = value.encode('utf-8').hex()
        else:
            value_hex = str(value).encode('utf-8').hex()
        
        # คำนวณความยาว
        length = len(value_hex) // 2
        
        # สร้าง TLV
        return f"{tag}{length:02X}{value_hex}"
    
    @staticmethod
    def _normalize_mobile(mobile):
        """ทำให้เบอร์โทรเป็นรูปแบบ 0xxxxxxxxx"""
        # เอาเฉพาะตัวเลข
        mobile = re.sub(r'\D', '', str(mobile))
        
        # ถ้าเริ่มด้วย 66 ให้เปลี่ยนเป็น 0
        if mobile.startswith('66'):
            mobile = '0' + mobile[2:]
        
        # ถ้ายังไม่เริ่มด้วย 0 ให้เพิ่ม 0 ข้างหน้า
        if not mobile.startswith('0'):
            mobile = '0' + mobile
        
        # ตัดให้เหลือ 10 หลัก
        return mobile[:10]
    
    @staticmethod
    def _normalize_id(id_number):
        """ทำให้เลขประจำตัวเป็นรูปแบบ 13 หลัก"""
        # เอาเฉพาะตัวเลข
        id_norm = re.sub(r'\D', '', str(id_number))
        
        # ตัดให้เหลือ 13 หลัก
        return id_norm[:13].rjust(13, '0')
    
    @staticmethod
    def _add_crc(payload):
        """เพิ่ม CRC (Checksum) ที่ท้าย"""
        # สร้าง CRC-16/CCITT-FALSE
        payload_with_crc = payload + "6304"  # Tag 63, Length 04
        
        crc = PromptPayQR._calculate_crc(payload_with_crc)
        
        return payload_with_crc + f"{crc:04X}"
    
    @staticmethod
    def _calculate_crc(data):
        """คำนวณ CRC-16/CCITT-FALSE"""
        # Convert hex string to bytes
        bytes_data = bytes.fromhex(data)
        
        crc = 0xFFFF
        for byte in bytes_data:
            crc ^= (byte << 8)
            for _ in range(8):
                crc <<= 1
                if crc & 0x10000:
                    crc ^= 0x1021
                crc &= 0xFFFF
        
        return crc


def generate_promptpay_qr_image(amount, mobile_number=None, id_number=None, merchant_name=""):
    """
    สะดวก helper function สำหรับสร้าง PromptPay QR Code
    
    Args:
        amount: ยอดเงิน (เช่น 100.00)
        mobile_number: เบอร์โทร (เช่น 0812345678)
        id_number: เลขประจำตัวประชาชน (13 หลัก)
        merchant_name: ชื่อร้าน/ผู้รับเงิน
    
    Returns:
        PIL.Image object
    """
    return PromptPayQR.generate_qr_code(amount, mobile_number, id_number, merchant_name)


def generate_promptpay_payload(id_value, amount=0.0):
    """
    Generate PromptPay payload string (EMVCo)
    id_value: Mobile number (08x...) or Tax ID (13 digits)
    amount: Amount to transfer (optional, 0 = not specified)
    """
    
    # Sanitize ID
    id_value = str(id_value).strip().replace('-', '').replace(' ', '')
    
    # Determine target type
    if len(id_value) == 10 and id_value.startswith('0'):
        # Mobile number: 0812345678 -> 66812345678
        target = '0066' + id_value[1:]
    elif len(id_value) == 13:
        # Tax ID / ID Card
        target = id_value
    else:
        # Try raw (e-Wallet or other) but usually warn
        target = id_value

    # 1. Payload Format Indicator (ID=00, Length=02, Value="01")
    payload = "000201"
    
    # 2. Point of Initiation Method (ID=01, Length=02, Value="11" for dynamic, "12" for static)
    # Use "12" (Static) if amount is 0, "11" (Dynamic) if amount > 0
    if amount > 0:
        payload += "010211" # Dynamic
    else:
        payload += "010212" # Static

    # 3. Merchant Account Information (ID=29, promptpay AID=A000000677010111)
    # Sub-ID 00 (AID)
    app_id = "A000000677010111"
    merchant_info = f"00{len(app_id):02}{app_id}"
    
    # Sub-ID 01 (Target type: 01=Mobile, 02=Tax ID, 03=e-Wallet)
    if len(target) >= 13 and target.isdigit():
        if target.startswith('0066'):  # It's mobile number formatted
             sub_rec = f"0113{target}"
        else:  # Tax ID
             sub_rec = f"0213{target}"
    elif len(target) == 15 and target.isdigit():  # E-Wallet
        sub_rec = f"0315{target}"
    else:
         # Fallback logic for mobile calculated above
         sub_rec = f"0113{target}"

    merchant_info += sub_rec
    payload += f"29{len(merchant_info):02}{merchant_info}"

    # 4. Country Code (ID=58, Length=02, Value="TH")
    payload += "5802TH"

    # 5. Currency (ID=53, Length=03, Value="764" (THB))
    payload += "5303764"

    # 6. Transaction Amount (ID=54, Length=Var)
    if amount > 0:
        amt_str = f"{amount:.2f}"
        payload += f"54{len(amt_str):02}{amt_str}"

    # 7. Checksum (ID=63, Length=04)
    payload += "6304"
    
    # Calculate CRC16 (CCITT-FALSE)
    crc = crc16_ccitt(payload.encode('ascii'))
    payload += f"{crc:04X}"
    
    return payload


def crc16_ccitt(data):
    """Calculate CRC16 CCITT-FALSE"""
    crc = 0xFFFF
    for byte in data:
        x = ((crc >> 8) ^ byte) & 0xFF
        x ^= x >> 4
        crc = ((crc << 8) ^ (x << 12) ^ (x << 5) ^ x) & 0xFFFF
    return crc


def generate_promptpay_qr(id_value, amount=0.0, save_path=None):
    """
    Generate QR Code image object (PIL Image)
    
    Args:
        id_value: Mobile (0812345678) or Tax ID (13 digits)
        amount: Amount to transfer (0 = not specified)
        save_path: Optional path to save the QR image
    
    Returns:
        PIL.Image object or None if error
    """
    try:
        payload = generate_promptpay_payload(id_value, amount)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        if save_path:
            img.save(save_path)
            
        return img
    except Exception as e:
        print(f"Error in generate_promptpay_qr: {e}")
        return None


if __name__ == "__main__":
    # ทดสอบ
    qr_img = generate_promptpay_qr(
        id_value="0812345678",
        amount=100.00
    )
    
    if qr_img:
        qr_img.save("promptpay_test.png")
        print("✓ PromptPay QR Code สร้างเรียบร้อย")
    else:
        print("✗ เกิดข้อผิดพลาดในการสร้าง QR Code")
