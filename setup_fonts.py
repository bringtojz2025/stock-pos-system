#!/usr/bin/env python3
"""
Script to download and install Kanit font for matplotlib
Run this before using the app if you see 'Font family Kanit not found' warnings
"""

import os
import sys
import urllib.request
import matplotlib.font_manager as fm

def setup_thai_fonts():
    """ดาวน์โหลดและติดตั้ง Thai fonts (Kanit + THSarabunNew)"""
    
    # กำหนดเส้นทางตามระบบปฏิบัติการ
    if sys.platform == 'win32':
        font_dir = os.path.expanduser(r'~\AppData\Local\Microsoft\Windows\Fonts')
    elif sys.platform == 'darwin':  # macOS
        font_dir = os.path.expanduser('~/Library/Fonts')
    else:  # Linux
        font_dir = os.path.expanduser('~/.local/share/fonts')
    
    # รายชื่อฟอนต์ที่ต้องติดตั้ง
    fonts_to_install = [
        {
            'name': 'Kanit-Regular.ttf',
            'url': 'https://github.com/google/fonts/raw/main/ofl/kanit/Kanit-Regular.ttf',
            'display_name': 'Kanit-Regular'
        },
        {
            'name': 'THSarabunNew.ttf',
            'url': 'https://github.com/bringtojz2025/stock-pos-system/raw/main/fonts/THSarabunNew.ttf',
            'display_name': 'TH Sarabun New'
        }
    ]
    
    try:
        print("=" * 60)
        print("📥 Thai Fonts Installer")
        print("=" * 60)
        print(f"Target directory: {font_dir}")
        print()
        
        # สร้างโฟลเดอร์ถ้ายังไม่มี
        os.makedirs(font_dir, exist_ok=True)
        
        installed_count = 0
        
        for font_info in fonts_to_install:
            font_name = font_info['name']
            font_url = font_info['url']
            display_name = font_info['display_name']
            font_path = os.path.join(font_dir, font_name)
            
            # ตรวจสอบว่าฟอนต์มีอยู่แล้วหรือไม่
            if os.path.exists(font_path):
                print(f"✓ {display_name} already exists")
                installed_count += 1
                continue
            
            try:
                print(f"⏳ Downloading {display_name}...")
                print(f"   URL: {font_url}")
                urllib.request.urlretrieve(font_url, font_path)
                print(f"✓ {display_name} installed successfully!")
                installed_count += 1
            except Exception as e:
                print(f"✗ Failed to install {display_name}: {e}")
                continue
        
        print()
        print(f"Installed: {installed_count}/{len(fonts_to_install)} fonts")
        
        print()
        print("=" * 60)
        print("✓ Installation complete!")
        print("=" * 60)
        print()
        print("Note: You may need to restart the app for changes to take effect")
        
        return installed_count > 0
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ Installation failed!")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check your internet connection")
        print("2. Make sure the fonts directory is writable")
        print("3. Try running this script as Administrator (Windows)")
        print()
        
        return False

def check_available_fonts():
    """ตรวจสอบฟอนต์ที่มีสำหรับ matplotlib"""
    print("\n📋 Available fonts for matplotlib:")
    print("-" * 40)
    
    available_fonts = sorted(fm.fontManager.ttflist, key=lambda x: x.name)
    
    found_fonts = []
    for font in available_fonts:
        name_lower = font.name.lower()
        if any(x in name_lower for x in ['kanit', 'sarabun', 'thsarabun']):
            print(f"✓ {font.name}")
            found_fonts.append(font.name)
    
    if not found_fonts:
        print("✗ Thai fonts not found")
        print("\nOther Thai-compatible fonts:")
        for font in available_fonts:
            name_lower = font.name.lower()
            if any(x in name_lower for x in ['dejavu', 'liberation', 'noto', 'ubuntu']):
                print(f"  - {font.name}")

if __name__ == "__main__":
    print()
    setup_thai_fonts()
    check_available_fonts()
    print()
