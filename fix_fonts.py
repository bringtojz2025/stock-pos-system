#!/usr/bin/env python3
"""
Script to fix matplotlib font cache and register Kanit font
Run this if you see 'Font family Kanit not found' warnings
"""

import os
import sys
import shutil
import matplotlib
import matplotlib.font_manager as fm

def clear_font_cache():
    """ลบแคชฟอนต์ของ matplotlib และสร้างใหม่"""
    cache_dir = matplotlib.get_cachedir()
    cache_file = os.path.join(cache_dir, 'fontlist*.json')
    
    print("=" * 60)
    print("🔧 Matplotlib Font Cache Cleaner")
    print("=" * 60)
    print()
    
    print(f"Cache directory: {cache_dir}")
    
    # ลบไฟล์ cache
    font_cache_files = [
        os.path.join(cache_dir, 'fontlist-v330.json'),
        os.path.join(cache_dir, 'fontlist.json'),
    ]
    
    for cache_file in font_cache_files:
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                print(f"✓ Removed: {cache_file}")
            except Exception as e:
                print(f"⚠ Could not remove {cache_file}: {e}")
    
    print()
    print("⏳ Rebuilding font cache...")
    print()
    
    # สร้าง FontManager ใหม่เพื่อให้ matplotlib สแกนฟอนต์ใหม่
    fm.fontManager = fm.FontManager()
    
    print("=" * 60)
    print("✓ Font cache rebuilt!")
    print("=" * 60)
    print()

def check_kanit_font():
    """ตรวจสอบว่า Kanit font พบในระบบหรือไม่"""
    print("📋 Checking for Kanit font...")
    print("-" * 60)
    
    # ค้นหาฟอนต์ Kanit
    for font in fm.fontManager.ttflist:
        if 'kanit' in font.name.lower():
            print(f"✓ Found: {font.name}")
            print(f"  File: {font.fname}")
            return True
    
    print("✗ Kanit font not found in matplotlib")
    
    # ตรวจสอบว่ามีในระบบ
    if sys.platform == 'win32':
        font_path = os.path.expanduser(r'~\AppData\Local\Microsoft\Windows\Fonts\Kanit-Regular.ttf')
    else:
        font_path = os.path.expanduser('~/.local/share/fonts/Kanit-Regular.ttf')
    
    if os.path.exists(font_path):
        print(f"⚠ Kanit font file exists at: {font_path}")
        print("  But matplotlib's cache hasn't picked it up")
        print("  Try running this script again after clearing cache")
    else:
        print(f"✗ Kanit font file not found at: {font_path}")
        print("  You may need to install it first")
    
    return False

def list_thai_fonts():
    """แสดงรายการฟอนต์ที่สามารถใช้สำหรับภาษาไทย"""
    print()
    print("📋 Thai-compatible fonts available:")
    print("-" * 60)
    
    thai_fonts = []
    for font in sorted(fm.fontManager.ttflist, key=lambda x: x.name):
        name_lower = font.name.lower()
        # ค้นหาฟอนต์ที่รองรับภาษาไทย
        if any(x in name_lower for x in ['noto', 'dejavu', 'liberation', 'ubuntu', 'kanit']):
            if font.name not in thai_fonts:
                thai_fonts.append(font.name)
                print(f"  • {font.name}")
    
    if not thai_fonts:
        print("  None found")

if __name__ == "__main__":
    print()
    clear_font_cache()
    check_kanit_font()
    list_thai_fonts()
    print()
    print("💡 TIP: If Kanit is still not found, try:")
    print("   1. Restart your terminal/IDE")
    print("   2. Restart the app")
    print("   3. Or manually install Kanit from Google Fonts")
    print()
