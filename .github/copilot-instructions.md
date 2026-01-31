# Copilot AI Agent Instructions for Stock POS System

## Project Overview
Python-based POS (Point of Sale) + inventory system with AI content generation and Facebook posting. Main GUI (`app_stock.py`) uses `customtkinter` with Google Sheets as the database backend. This is a production retail system with advanced features: campaigns, coupons, receipt printing, and automated social media posting.

## Architecture & Data Flow

### Core Components
- **`app_stock.py` (9652 lines)**: Monolithic GUI application containing all POS logic, inventory management, dashboard, and AI integration
  - Single class `StockManagerApp(ctk.CTk)` manages entire application state
  - Tab-based interface: POS, Inventory, History, Dashboard, AI & Social Media
- **`ai_content_generator.py`**: Three distinct classes:
  - `AIContentGenerator`: Google Gemini API integration for content creation
  - `AdvertisementImageCreator`: PIL-based ad image generation
  - `FacebookIntegration`: Facebook Graph API for posting

### Data Storage (Google Sheets "StockDB")
All data stored in Google Sheets with these worksheets:
- **Products**: `Barcode, Name, Price, Stock, Category, ImageID` (master inventory)
- **Sales**: `ReceiptID, Date, Barcode, Qty, Total, UsedCoupon, DiscountAmount, Cancel`
- **Campaigns**: `Barcode, Name, Status, Discount Price, Valid Until, Stock` (temporary promotions)
- **Coupons**: `Code, Amount %, Message` (discount codes configuration)
- **Inventory**, **Suppliers**, **Customers** (additional tracking)

**Critical**: Google Sheets is the single source of truth. No local database. All reads/writes use `gspread` API.

### Configuration Files (Git-Ignored)
- **`client_secret.json`**: Google OAuth 2.0 credentials (Desktop App type)
- **`ai_config.json`**: API keys (Gemini, Facebook token/page ID) - use `ai_config_example.json` as template
- **`settings.json`**: Shop info, printer settings, VAT, PromptPay QR, coupon thresholds
- **`coupon_database.json`**: Local coupon state (type, value, usage limits)
- **`token.pickle`**: Cached Google API credentials

## Developer Workflows

### Setup & Installation
```bash
# Windows (recommended)
install.bat  # Installs all dependencies from requirements.txt

# Manual
pip install -r requirements.txt
python app_stock.py
```

### API Configuration
1. **Google Sheets/Drive**: Get OAuth credentials from [Google Cloud Console](https://console.cloud.google.com/)
   - Create Desktop Application OAuth 2.0 client → Download JSON → Save as `client_secret.json`
   - First run will open browser for authentication → Saves `token.pickle`
2. **Gemini API**: Get key from [AI Studio](https://aistudio.google.com/app/apikey) → Add to `ai_config.json`
3. **Facebook** (optional): See `FACEBOOK_SETUP.md` for access token generation

### Testing
- **AI Module**: `python test_ai_module.py` (tests content generation, ad creation, config)
- **Receipt PDF**: `python test_fpdf2_receipt.py` or `python test_receipt.py`
- **Font setup**: `python setup_fonts.py` (downloads Kanit Thai font)

### Common Tasks
- **Add new coupon type**: Modify coupon validation logic in `process_checkout()` and `update_discount_display()` methods
- **Add AI content style**: Update `AIContentGenerator.generate_product_description()` with new style in prompt
- **Campaign logic**: See `add_item_to_cart()` for real-time stock checking and auto-close behavior

## Project-Specific Patterns

### Threading & Async Operations
- Image loading from Google Drive uses daemon threads to prevent UI blocking
- `current_image_thread` and `image_thread_lock` prevent race conditions when loading product images
- Checkout process runs in separate thread (`run_checkout_thread()`) for stock updates

### Google Sheets Integration
```python
# Pattern: Read all records at startup
products = self.sheet_products.get_all_records()

# Pattern: Append new sale (entire row)
self.sheet_sales.append_row([receipt_id, date, barcode, ...])

# Pattern: Update specific cell
self.sheet_campaigns.update_cell(row, col, new_value)
```

### Campaign System (Advanced Feature)
**Critical business logic**: When scanning campaign items:
1. Check 4 conditions: `item_stock > 0`, `campaign_stock > 0`, `status == 'Active'`, `not expired`
2. If ANY condition fails → Use regular price (not campaign price)
3. Real-time auto-close: Campaign closes immediately when `campaign_stock == 0` during scan
4. Post-checkout close: Additional check after stock deduction

**Implementation**: See `add_item_to_cart()` lines ~1500-1700

### Coupon System
Two-tier percentage-based system defined in `settings.json`:
- `DISCOUNT05`: 5% off when total ≥ `discount05_amount` (default 300฿)
- `DISCOUNT10`: 10% off when total ≥ `discount10_amount` (default 500฿)
- Real-time validation in `update_discount_display()` - shows eligibility as user types
- Separate from JSON-based coupons in `coupon_database.json` (fixed amount or %)

### Font Handling (Thai Language)
App auto-downloads Kanit font from Google Fonts on first run (`setup_kanit_font()`). Fallback to DejaVu Sans if download fails. Used for:
- Matplotlib charts (dashboard)
- ReportLab PDFs (receipt generation)
- FPDF2 (alternative receipt system)

## Integration Points

### Google Services (Required)
- **Sheets API**: All data persistence - scopes: `spreadsheets`, `drive`
- **Drive API**: Product image storage/retrieval by ImageID
- **Gemini API**: Content generation (`gemini-3-flash-preview` model)

### Facebook Graph API (Optional)
- Posts text, images, or both to Facebook Page
- Requires Page Access Token (not User Token) - see `FACEBOOK_SETUP.md`
- Uses `requests` library directly (no official SDK)

### Receipt Printing
- Windows-only: Uses `win32print` and `win32api` for direct printer access
- PDF generation: ReportLab (main) or FPDF2 (alternative) - see `RECEIPT_TECHNICAL_DOCS.md`
- Config: `printer_config.json` and `receipt_settings.json`

## Critical Gotchas

1. **Socket timeouts**: `socket.setdefaulttimeout(30)` required for Google Drive operations on slow networks
2. **SSL certificate issues**: App disables SSL verification (`ssl._create_unverified_context`) - temporary workaround
3. **Image caching**: Product images saved to `img/` folder to reduce Drive API calls
4. **Monolithic architecture**: 9652-line single file - UI and business logic tightly coupled
5. **Thai text**: Requires Unicode-capable fonts - Kanit auto-setup handles this
6. **Gemini model**: Currently uses `gemini-3-flash-preview` - update in `ai_content_generator.py` if deprecated

## Documentation Reference
- **`README.md`**: User guide, feature overview, installation steps
- **`CHANGELOG.md`**: Detailed campaign/coupon system implementation notes with code flow diagrams
- **`README_AI_FEATURES.md`**: AI content generation and Facebook integration guide
- **`FACEBOOK_SETUP.md`**: Step-by-step Facebook API token setup
- **`RECEIPT_TECHNICAL_DOCS.md`**: PDF receipt generation internals
- **`SELENIUM_AUTOMATION.md`**: Browser automation for Gemini web interface (experimental)

## Quick Examples

**Add new product to inventory**:
```python
self.sheet_products.append_row([barcode, name, price, stock, category, image_id])
```

**Query campaign status**:
```python
campaigns = self.sh.worksheet("Campaigns").get_all_records()
active_campaigns = [c for c in campaigns if c['Status'] == 'Active']
```

**Generate AI content**:
```python
ai = AIContentGenerator(api_key, "gemini")
content = ai.generate_product_description(name, category, features, style="professional")
```

---
**Contact**: bringtojz@gmail.com | **Language**: Thai (primary) + English comments
