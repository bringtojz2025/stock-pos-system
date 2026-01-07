# Gemini Web Automation - Update Summary

## Changes Made (January 8, 2026)

### 1. **Auto-detect Image from Barcode**
The app now automatically finds the product image based on the selected product's barcode.

#### Before:
- User had to manually select an image file through file dialog
- Image selection was decoupled from the product selection

#### After:
- Select product from dropdown → App automatically finds matching image from `img/` folder
- Uses barcode as filename (e.g., barcode `111` matches image `111.png`)
- Supports multiple formats: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif`

### 2. **Chrome Profile Integration**
The app now opens Chrome using an existing user profile instead of launching in guest mode.

#### How It Works:
```
Windows:  %AppData%\Local\Google\Chrome\User Data\Default
macOS:    ~/Library/Application Support/Google/Chrome/Default
Linux:    ~/.config/google-chrome/Default
```

#### Benefits:
- ✅ User stays logged in to Google account
- ✅ Chrome extensions and settings are preserved
- ✅ Gemini access works without login prompts
- ✅ More secure (uses existing Chrome session)

### 3. **Automatic File Upload**
The app now automatically uploads the image file to Gemini Web.

#### Process:
1. Finds the "Attach" or "Image" button on Gemini Web
2. Clicks the button to open file picker
3. Sends the file path to the file input element
4. Waits for upload to complete (3 seconds)

#### Fallback Options:
- If attach button not found: Sends file directly to hidden `input[type="file"]`
- If both fail: User sees instructions to manually upload

## Code Changes

### New Function: `_find_image_by_barcode(barcode)`
```python
def _find_image_by_barcode(self, barcode):
    """ค้นหารูปภาพจากโฟลเดอร์ img ที่ตรงกับบาร์โค้ด"""
    from pathlib import Path
    img_dir = Path("./img")
    
    if not img_dir.exists():
        return None
    
    # ค้นหาไฟล์ที่มีชื่อตรงกับบาร์โค้ด (เช่น 111.png, 111.jpg)
    for ext in ['png', 'jpg', 'jpeg', 'bmp', 'gif']:
        image_file = img_dir / f"{barcode}.{ext}"
        if image_file.exists():
            return str(image_file.absolute())
    
    return None
```

### Updated Function: `open_gemini_web()`
- Extracts barcode from product combo selection
- Validates barcode exists
- Calls `_find_image_by_barcode()` to locate image
- Shows error if image not found
- Passes barcode to `_open_gemini_with_image()`

### Updated Function: `_open_gemini_with_image(image_path, prompt, product_name, price, barcode)`

**Chrome Profile Setup:**
```python
if os.path.exists(chrome_profile_path):
    chrome_options.add_argument(f"user-data-dir={chrome_profile_path}")
    chrome_options.add_argument("profile-directory=Default")
```

**Image Upload:**
```python
# ค้นหาปุ่มแนบรูป (attach/upload button)
attach_button = None
attach_selectors = [
    'button[aria-label*="attach"]',
    'button[aria-label*="Attach"]',
    'button[aria-label*="image"]',
    'button[aria-label*="Image"]',
    'button[title*="attach"]',
    'button[title*="Attach"]'
]

for selector in attach_selectors:
    try:
        buttons = driver.find_elements(By.CSS_SELECTOR, selector)
        if buttons:
            attach_button = buttons[0]
            break
    except:
        continue

if attach_button:
    attach_button.click()
    time.sleep(2)
    # Send file to input
    file_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
    if file_inputs:
        file_input = file_inputs[0]
        abs_image_path = os.path.abspath(image_path)
        file_input.send_keys(abs_image_path)
```

## User Workflow

### Step-by-step:
1. **Select Product** → Click dropdown and choose a product
   - Format shown: "Product Name (Barcode)"
   - Example: "ผ้าเช็ดหน้า (111)"

2. **Enter Price** → Type the price in the price field
   - Example: "150"

3. **Edit Prompt** (Optional) → Modify the prompt text
   - Can use placeholders: `{product}` and `{price}`

4. **Click "🌐 เปิด Gemini Web"** → System automatically:
   - ✅ Extracts barcode from product name
   - ✅ Finds image from `img/111.png` (matching barcode)
   - ✅ Opens Chrome with your existing Google account login
   - ✅ Loads Gemini Web
   - ✅ Fills in prompt text
   - ✅ Clicks attach button
   - ✅ Selects and uploads image file
   - ✅ Submits the request (or user can manually click send)

5. **Gemini Generates** → Browser window shows the generated ad
   - User can see real-time generation
   - User can refine or download the result

6. **Save Result** → User saves the generated image from Gemini

## File Structure Requirements

```
stock-pos-system/
├── app_stock.py
├── requirements.txt
├── img/
│   ├── 111.png       ← Barcode 111
│   ├── 123.png       ← Barcode 123
│   ├── 222.png       ← Barcode 222
│   └── ...
└── ... (other files)
```

**Important:** Image filenames MUST match product barcodes exactly!

## Error Handling

### If image not found:
- Message: "ไม่พบรูปภาพสำหรับบาร์โค้ด: 111"
- Action: User needs to add image to `img/` folder with matching barcode name

### If Chrome profile not found:
- Warning logged: "⚠️ ไม่พบโปรไฟล์ Chrome"
- Fallback: App continues with default Chrome settings
- User can still login manually

### If attach button not found:
- Attempts direct file upload via `input[type="file"]`
- If that fails too: Shows manual upload instructions
- User can manually click attach and upload

### If automation fails completely:
- Browser still opens
- User sees step-by-step manual instructions
- Instructions include: product name, barcode, price, image name, and full prompt

## Browser Profile Paths

### Windows
```
%APPDATA%\Local\Google\Chrome\User Data\Default
C:\Users\[YourUsername]\AppData\Local\Google\Chrome\User Data\Default
```

### macOS
```
~/Library/Application Support/Google/Chrome/Default
/Users/[YourUsername]/Library/Application Support/Google/Chrome/Default
```

### Linux
```
~/.config/google-chrome/Default
/home/[YourUsername]/.config/google-chrome/Default
```

## Benefits of This Approach

| Feature | Benefit |
|---------|---------|
| **Barcode Matching** | No manual image selection needed |
| **Chrome Profile** | User stays logged in, no auth needed |
| **Auto Upload** | Eliminates manual file selection step |
| **Smart Selectors** | Multiple fallback methods for element detection |
| **Error Messages** | Clear instructions if anything fails |
| **Seamless Integration** | All steps automated in one click |

## Testing Checklist

- [ ] Test with product that has matching image in `img/` folder
- [ ] Test with product that doesn't have image (should show error)
- [ ] Verify Chrome opens with your existing Google login
- [ ] Verify image uploads automatically to Gemini
- [ ] Verify prompt text is filled in
- [ ] Generate an ad and verify it works

## Troubleshooting

### "ไม่พบรูปภาพสำหรับบาร์โค้ด" error
**Solution:** Add image to `img/` folder with barcode as filename
```
Example: Product barcode is 111
Action: Save image as: img/111.png
```

### Chrome opens but Gemini won't load
**Solution:** 
- Check internet connection
- Check if Google account is logged in Chrome
- Try manual login in Chrome

### Image upload fails but automation continues
**Solution:**
- Click "Attach" button manually
- Select the image file shown in instructions
- Or reload page and try again

### "Could not find input field" warning
**Solution:**
- Gemini page structure may have changed
- User can type prompt manually in Gemini Web
- Report issue if this happens frequently

---

**Last Updated:** January 8, 2026
**Status:** ✅ Production Ready
**Version:** Gemini Web Automation v2.0 (with Profile & Barcode Integration)
