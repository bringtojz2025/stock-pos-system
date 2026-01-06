#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for AI Content Generator Module
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("Testing AI Content Generator Module")
print("=" * 50)
print()

# Test imports
try:
    from ai_content_generator import (
        AIContentGenerator, 
        AdvertisementImageCreator, 
        FacebookIntegration,
        load_config,
        save_config
    )
    print("✅ Module imports successful!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test config
print()
print("Testing configuration...")
try:
    config = load_config()
    print(f"✅ Config loaded: {config.keys()}")
    
    # Save test
    test_config = config.copy()
    test_config["test"] = "value"
    save_config(test_config)
    print("✅ Config saved successfully")
except Exception as e:
    print(f"❌ Config error: {e}")

# Test AI Content Generator
print()
print("Testing AI Content Generator...")
try:
    ai = AIContentGenerator(api_key="test_key", api_type="offline")
    
    # Test offline mode
    desc = ai.generate_product_description("Test Product", features=["Feature 1", "Feature 2"])
    print(f"✅ AI Content generated (offline mode):")
    print(f"   {desc[:100]}...")
    
    # Test caption
    caption = ai.generate_facebook_caption("Test Product", 299.00)
    print(f"✅ Facebook caption generated:")
    print(f"   {caption[:100]}...")
except Exception as e:
    print(f"❌ AI Error: {e}")

# Test Advertisement Image Creator
print()
print("Testing Advertisement Image Creator...")
try:
    ad_creator = AdvertisementImageCreator()
    print(f"✅ Ad creator initialized")
    print(f"   Output directory: {os.path.abspath(ad_creator.output_dir)}")
except Exception as e:
    print(f"❌ Ad Creator Error: {e}")

# Test Facebook Integration
print()
print("Testing Facebook Integration...")
try:
    fb = FacebookIntegration(access_token="test_token", page_id="123456")
    print(f"✅ Facebook integration initialized")
    print(f"   Page ID: {fb.page_id}")
except Exception as e:
    print(f"❌ Facebook Error: {e}")

print()
print("=" * 50)
print("All tests completed!")
print("=" * 50)
print()
print("Next steps:")
print("1. Install required packages: pip install -r requirements.txt")
print("2. Install AI service: pip install openai (or anthropic)")
print("3. Configure API keys in the app settings")
print("4. Run: python app_stock.py")
print()
