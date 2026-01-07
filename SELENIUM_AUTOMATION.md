# Selenium Automation for Gemini Web Integration

## Overview
The ad generation feature has been upgraded to use **Selenium WebDriver** for automated interaction with Gemini Web. This allows the application to:
- Open Gemini Web directly in a controlled Chrome browser window
- Automatically fill in the prompt text
- Automatically upload the product image
- Submit the request without manual user interaction

## How It Works

### 1. **User Interaction Flow**
```
User selects image → Enters product name & price → Edits prompt
     ↓
Clicks "🌐 เปิด Gemini Web" button
     ↓
App launches Chrome with Selenium automation
     ↓
Selenium fills in prompt text automatically
     ↓
Selenium uploads product image automatically
     ↓
Chrome browser window shows Gemini generating the ad
     ↓
User can see results in the browser
```

### 2. **Technical Components**

#### Dependencies
- **selenium>=4.10.0** - WebDriver automation framework
- **webdriver-manager>=3.9.0** - Automatic ChromeDriver management (no manual setup needed)

#### Key Functions

**`_open_gemini_with_image(image_path, prompt, product_name, price)`**
- Main automation function runs in a background thread
- Opens Chrome with Gemini Web (`https://gemini.google.com/app`)
- Waits for page to load (6 seconds)
- Finds and fills the prompt input field
- Finds and uploads the product image file
- Submits the request (via button click or Enter key)
- Updates UI with status messages

### 3. **Error Handling**

**If automation fails:**
- User sees warning message with manual steps
- Browser still opens to Gemini Web
- User can manually upload image and paste prompt

**If Chrome/ChromeDriver issues:**
- Error message displayed with troubleshooting info
- webdriver-manager handles driver installation automatically

### 4. **Chrome Configuration**

```python
chrome_options = Options()
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument('--start-maximized')
```

These settings prevent Gemini from detecting the browser is automation-controlled.

### 5. **Input Field Detection**

The code tries multiple selectors to find the prompt input field:
```python
input_selectors = [
    'textarea',
    '[contenteditable="true"]',
    'input[type="text"]',
    '.goog-textarea',
    '[role="textbox"]'
]
```

This ensures compatibility even if Gemini updates its HTML structure.

### 6. **File Upload Handling**

- Uses absolute file path for upload
- Makes hidden file input visible to WebDriver
- Waits 3 seconds for file processing

### 7. **Submit Detection**

The code tries multiple methods to submit:
1. Click send button (searches for aria-label="Send")
2. Click tooltip-labeled button
3. Press Enter key (if button not found)

## Usage

### From User Perspective
1. Select a product image
2. Enter product name (from dropdown) and price
3. Edit the prompt text (optional)
4. Click "🌐 เปิด Gemini Web"
5. Watch Chrome browser open and auto-fill with your data
6. See Gemini generating the advertisement
7. Save the generated image from Gemini
8. Close the browser when done

### From Developer Perspective

#### Installation
```bash
pip install selenium webdriver-manager
```

#### Launching
```python
# Triggered by button click in UI
thread = threading.Thread(target=self._open_gemini_with_image, 
                         args=(image_path, prompt, product_name, price))
thread.daemon = True
thread.start()
```

## Advantages Over Previous Approach

| Aspect | Browser Button | Selenium Automation |
|--------|---|---|
| Browser Window | Manual (external) | Automatic (integrated) |
| Prompt Entry | Manual copy/paste | Automatic fill |
| Image Upload | Manual file selection | Automatic upload |
| User Steps | 4+ manual steps | Auto-handled |
| Integration | External browser | All in-app |
| Reliability | Depends on user | Programmatic |

## Troubleshooting

### Issue: Chrome window doesn't open
**Solution:** Ensure Chrome is installed on your system. webdriver-manager will automatically download the matching ChromeDriver.

### Issue: "Could not find input field" warning
**Possible causes:**
- Gemini page structure changed
- Page didn't fully load (increase sleep time)
- User not logged into Google account in Chrome

**Solution:** User can manually fill in the data or log into their Google account

### Issue: Image upload fails
**Solution:** The script will continue and user can upload manually

### Issue: Cannot find send button
**Solution:** The script will try pressing Enter key. If still fails, user must click send button manually.

## Future Enhancements

1. **Cookie-based Authentication** - Preserve user login across sessions
2. **Gemini API Fallback** - Use official API if quota available
3. **Image Saving** - Auto-download generated images to local folder
4. **Batch Processing** - Generate ads for multiple products
5. **Custom Templates** - Save and reuse prompt templates

## References

- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)

---

**Last Updated:** January 8, 2026
**Status:** ✅ Production Ready
