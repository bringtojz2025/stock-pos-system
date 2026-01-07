#!/usr/bin/env python3
"""
Script to download and install Kanit font for matplotlib
Run this before using the app if you see 'Font family Kanit not found' warnings
"""

import os
import sys
import urllib.request
import matplotlib.font_manager as fm

def setup_kanit_font():
    """ดาวน์โหลดและติดตั้ง Kanit font"""
    
    # กำหนดเส้นทางตามระบบปฏิบัติการ
    if sys.platform == 'win32':
        font_dir = os.path.expanduser(r'~\AppData\Local\Microsoft\Windows\Fonts')
        font_name = 'Kanit-Regular.ttf'
    elif sys.platform == 'darwin':  # macOS
        font_dir = os.path.expanduser('~/Library/Fonts')
        font_name = 'Kanit-Regular.ttf'
    else:  # Linux
        font_dir = os.path.expanduser('~/.local/share/fonts')
        font_name = 'Kanit-Regular.ttf'
    
    font_path = os.path.join(font_dir, font_name)
    
    # ตรวจสอบว่าฟอนต์มีอยู่แล้วหรือไม่
    if os.path.exists(font_path):
        print(f"✓ Kanit font already exists at: {font_path}")
        return True
    
    try:
        print("=" * 60)
        print("📥 Kanit Font Installer for Matplotlib")
        print("=" * 60)
        print(f"Target directory: {font_dir}")
        print()
        
        # สร้างโฟลเดอร์ถ้ายังไม่มี
        os.makedirs(font_dir, exist_ok=True)
        
        # ดาวน์โหลด Kanit font จาก Google Fonts
        font_url = "https://github.com/google/fonts/raw/main/ofl/kanit/Kanit-Regular.ttf"
        
        print("⏳ Downloading Kanit-Regular.ttf from Google Fonts...")
        print(f"   URL: {font_url}")
        
        urllib.request.urlretrieve(font_url, font_path)
        print(f"✓ Font downloaded successfully!")
        print(f"   Saved to: {font_path}")
        
        # ลองเพิ่มฟอนต์เข้า matplotlib
        try:
            fm.fontManager.addfont(font_path)
            print("✓ Font registered with matplotlib")
        except:
            print("⚠ Could not register font with matplotlib immediately")
            print("  It will be available after restarting Python/the app")
        
        print()
        print("=" * 60)
        print("✓ Installation complete!")
        print("=" * 60)
        print()
        print("Note: You may need to restart the app for changes to take effect")
        
        return True
        
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
    
    kanit_found = False
    for font in available_fonts:
        if 'kanit' in font.name.lower():
            print(f"✓ {font.name} (Kanit)")
            kanit_found = True
    
    if not kanit_found:
        print("✗ Kanit font not found")
        print("\nOther Thai-compatible fonts:")
        for font in available_fonts:
            name_lower = font.name.lower()
            if any(x in name_lower for x in ['dejavu', 'liberation', 'noto', 'ubuntu']):
                print(f"  - {font.name}")

if __name__ == "__main__":
    print()
    setup_kanit_font()
    check_available_fonts()
    print()
