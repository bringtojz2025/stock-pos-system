# 🚀 แผนการแปลง Stock POS System เป็น Next.js Web Application

## 📊 วิเคราะห์ฟังก์ชันจาก app_stock.py (9652 บรรทัด)

### 🎯 ฟีเจอร์หลักที่ต้องแปลง

#### 1. **POS (Point of Sale) - Tab ขายหน้าร้าน** 
**ฟังก์ชัน Python:**
- `setup_pos_tab()`: สร้าง UI สำหรับสแกนสินค้า
- `add_item_to_cart()`: เพิ่มสินค้าลงตะกร้า + ตรวจสอบแคมเปญ
- `process_checkout()`: คำนวณยอดรวม, ส่วนลด, ตรวจสอบคูปอง
- `show_confirm_payment_dialog()`: แสดงหน้ายืนยันการชำระเงิน
- `update_cart_ui()`: อัปเดตตะกร้าสินค้า
- `lookup_customer_by_phone()`: ค้นหาข้อมูลลูกค้า

**Business Logic ที่สำคัญ:**
- ✅ **Campaign System**: ตรวจสอบ 4 เงื่อนไข (stock > 0, campaign_stock > 0, status == 'Active', not expired)
- ✅ **Coupon System**: DISCOUNT05 (5% เมื่อ ≥300฿), DISCOUNT10 (10% เมื่อ ≥500฿)
- ✅ **Real-time Stock Validation**: ตรวจสอบสต็อกก่อนเพิ่มสินค้า
- ✅ **Auto-close Campaign**: ปิดแคมเปญเมื่อสต็อกหมด

**Next.js Implementation:**
```
pages/
├── pos/
│   ├── page.tsx (Main POS Interface)
│   └── components/
│       ├── BarcodeScanner.tsx
│       ├── CartItem.tsx
│       ├── CartSummary.tsx
│       ├── CouponInput.tsx
│       ├── PaymentConfirmDialog.tsx
│       └── CustomerLookup.tsx

api/
├── pos/
│   ├── add-to-cart/route.ts (validateCampaign, checkStock)
│   ├── checkout/route.ts (applyCoupon, processPayment)
│   └── customer/route.ts (lookupCustomer)
```

---

#### 2. **Inventory Management - Tab คลังสินค้า**
**ฟังก์ชัน Python:**
- `setup_inventory_tab()`: แสดงรายการสินค้าทั้งหมด
- `add_product()`: เพิ่มสินค้าใหม่
- `edit_product()`: แก้ไขข้อมูลสินค้า
- `delete_product()`: ลบสินค้า
- `update_stock_manual()`: อัปเดตสต็อก
- `upload_image_to_drive()`: อัปโหลดรูปภาพไป Google Drive
- `load_image_from_drive()`: โหลดรูปภาพจาก Google Drive

**Data Structure:**
```python
Products Sheet: [Barcode, Name, Price, Stock, Category, ImageID, Brand, Model]
```

**Next.js Implementation:**
```
pages/
├── inventory/
│   ├── page.tsx (Product List with DataTable)
│   ├── add/page.tsx (Add Product Form)
│   └── [id]/edit/page.tsx (Edit Product)

components/
├── inventory/
│   ├── ProductTable.tsx (shadcn Table)
│   ├── ProductForm.tsx (Add/Edit Form)
│   ├── ImageUpload.tsx (Drag & Drop)
│   └── StockAdjustment.tsx

api/
├── inventory/
│   ├── products/route.ts (CRUD)
│   ├── upload-image/route.ts (Google Drive API)
│   └── stock/route.ts (Update Stock)
```

---

#### 3. **Sales History - Tab ประวัติการขาย**
**ฟังก์ชัน Python:**
- `setup_history_tab()`: แสดงประวัติการขาย
- `filter_history_by_date()`: กรองตามช่วงวันที่
- `search_by_receipt()`: ค้นหาด้วยเลขใบเสร็จ
- `view_receipt_detail()`: ดูรายละเอียดใบเสร็จ
- `export_history_excel()`: ส่งออก Excel

**Data Structure:**
```python
Sales Sheet: [ReceiptID, Date, Barcode, Qty, Total, UsedCoupon, DiscountAmount, Cancel]
```

**Next.js Implementation:**
```
pages/
├── history/
│   ├── page.tsx (Sales History List)
│   └── [receiptId]/page.tsx (Receipt Detail)

components/
├── history/
│   ├── SalesTable.tsx
│   ├── DateRangeFilter.tsx (shadcn Calendar)
│   ├── ReceiptDetailModal.tsx
│   └── ExportButton.tsx

api/
├── history/
│   ├── sales/route.ts (Get filtered sales)
│   ├── receipt/[id]/route.ts (Get receipt detail)
│   └── export/route.ts (Export Excel - use exceljs)
```

---

#### 4. **Dashboard - Tab ภาพรวม**
**ฟังก์ชัน Python:**
- `setup_dashboard_tab()`: แสดงภาพรวมยอดขาย
- `create_kpi_card()`: การ์ดแสดงสถิติ
- `plot_sales_chart()`: กราฟแสดงยอดขาย (matplotlib)
- `calculate_daily_stats()`: คำนวณสถิติรายวัน

**Metrics:**
- 💰 Total Sales
- 📊 Daily Revenue
- 📦 Low Stock Products
- 🏆 Top Selling Products

**Next.js Implementation:**
```
pages/
├── dashboard/
│   └── page.tsx (Main Dashboard)

components/
├── dashboard/
│   ├── KPICard.tsx
│   ├── SalesChart.tsx (Recharts - Line/Bar Chart)
│   ├── TopProductsTable.tsx
│   ├── LowStockAlert.tsx
│   └── RevenueChart.tsx

api/
├── dashboard/
│   ├── stats/route.ts (Calculate KPIs)
│   ├── sales-trend/route.ts (Chart data)
│   └── low-stock/route.ts (Alert products)
```

---

#### 5. **Campaign Management - Tab แคมเปญ Sale**
**ฟังก์ชัน Python:**
- `setup_campaign_tab()`: จัดการแคมเปญลดราคา
- `add_campaign()`: สร้างแคมเปญใหม่
- `edit_campaign()`: แก้ไขแคมเปญ
- `close_campaign()`: ปิดแคมเปญ (Manual + Auto)
- `validate_campaign_stock()`: ตรวจสอบสต็อกแคมเปญ

**Campaign Logic:**
```python
# เงื่อนไขการใช้ราคาแคมเปญ
if (item_stock > 0 AND 
    campaign_stock > 0 AND 
    status == 'Active' AND 
    datetime.now() <= discount_until):
    use_campaign_price = True
```

**Next.js Implementation:**
```
pages/
├── campaigns/
│   ├── page.tsx (Campaign List)
│   ├── create/page.tsx (Create Campaign)
│   └── [id]/edit/page.tsx (Edit Campaign)

components/
├── campaigns/
│   ├── CampaignCard.tsx
│   ├── CampaignForm.tsx
│   ├── CampaignStatus.tsx (Active/Inactive Badge)
│   └── StockProgress.tsx (Progress bar)

api/
├── campaigns/
│   ├── route.ts (CRUD)
│   ├── validate/route.ts (Check campaign eligibility)
│   └── auto-close/route.ts (Cron job - close expired)
```

---

#### 6. **AI & Social Media - Tab AI Features**
**ฟังก์ชัน Python:**
- `AIContentGenerator`: สร้างคำโฆษณาด้วย Gemini AI
- `AdvertisementImageCreator`: สร้างรูปโฆษณา (PIL)
- `FacebookIntegration`: โพสต์ Facebook

**AI Features:**
- 📝 Generate Product Description
- 🎨 Create Ad Images
- 📱 Post to Facebook Page

**Next.js Implementation:**
```
pages/
├── ai-social/
│   ├── content/page.tsx (Generate Content)
│   ├── ads/page.tsx (Create Ads)
│   └── facebook/page.tsx (Post to FB)

components/
├── ai-social/
│   ├── ContentGenerator.tsx
│   ├── StyleSelector.tsx
│   ├── AdImageCreator.tsx (Canvas API)
│   └── FacebookPoster.tsx

api/
├── ai/
│   ├── generate-content/route.ts (Gemini SDK)
│   ├── create-ad/route.ts (Sharp/Canvas for image)
│   └── facebook-post/route.ts (FB Graph API)
```

---

#### 7. **Settings - Tab ตั้งค่า**
**ฟังก์ชัน Python:**
- `setup_settings_tab()`: ตั้งค่าร้านค้า
- `save_shop_settings()`: บันทึกข้อมูลร้าน
- `configure_printer()`: ตั้งค่าเครื่องพิมพ์
- `manage_coupons()`: จัดการคูปอง

**Settings:**
- 🏪 Shop Information
- 🖨️ Printer Configuration
- 💳 PromptPay QR Code
- 🎫 Coupon Configuration

**Next.js Implementation:**
```
pages/
├── settings/
│   ├── page.tsx (Settings Tabs)
│   ├── shop/page.tsx
│   ├── printer/page.tsx
│   └── coupons/page.tsx

components/
├── settings/
│   ├── ShopInfoForm.tsx
│   ├── PrinterSetup.tsx
│   ├── PromptPayConfig.tsx
│   └── CouponManager.tsx

api/
├── settings/
│   └── route.ts (Update settings.json)
```

---

#### 8. **Receipt Generation - ฟีเจอร์พิมพ์ใบเสร็จ**
**ฟังก์ชัน Python:**
- `generate_receipt_pdf()`: สร้าง PDF ด้วย ReportLab/FPDF2
- `generate_qr_code()`: สร้าง QR Code (PromptPay)
- `generate_barcode()`: สร้าง Barcode
- `print_receipt()`: พิมพ์ใบเสร็จ (Windows only)

**Next.js Implementation:**
```
components/
├── receipt/
│   ├── ReceiptPreview.tsx
│   └── ReceiptPDF.tsx (@react-pdf/renderer)

api/
├── receipt/
│   ├── generate/route.ts (Create PDF)
│   └── download/[id]/route.ts (Download PDF)

utils/
├── receipt/
│   ├── qrcode.ts (qrcode library)
│   └── barcode.ts (jsbarcode library)
```

---

## 🏗️ โครงสร้างโปรเจค Next.js

### Directory Structure
```
stock-pos-nextjs/
├── app/
│   ├── (dashboard)/               # Dashboard Layout
│   │   ├── layout.tsx            # Main Dashboard Layout
│   │   ├── page.tsx              # Dashboard Home
│   │   ├── pos/
│   │   │   └── page.tsx
│   │   ├── inventory/
│   │   │   ├── page.tsx
│   │   │   ├── add/page.tsx
│   │   │   └── [id]/edit/page.tsx
│   │   ├── history/
│   │   │   ├── page.tsx
│   │   │   └── [receiptId]/page.tsx
│   │   ├── campaigns/
│   │   │   ├── page.tsx
│   │   │   ├── create/page.tsx
│   │   │   └── [id]/edit/page.tsx
│   │   ├── ai-social/
│   │   │   ├── content/page.tsx
│   │   │   ├── ads/page.tsx
│   │   │   └── facebook/page.tsx
│   │   └── settings/
│   │       └── page.tsx
│   │
│   ├── api/                       # API Routes
│   │   ├── pos/
│   │   ├── inventory/
│   │   ├── history/
│   │   ├── campaigns/
│   │   ├── ai/
│   │   ├── receipt/
│   │   └── settings/
│   │
│   └── layout.tsx                 # Root Layout
│
├── components/
│   ├── ui/                        # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── input.tsx
│   │   ├── table.tsx
│   │   └── ...
│   ├── layout/
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   ├── pos/
│   ├── inventory/
│   ├── history/
│   ├── dashboard/
│   ├── campaigns/
│   └── ai-social/
│
├── lib/
│   ├── google-sheets.ts           # Google Sheets API client
│   ├── google-drive.ts            # Google Drive API client
│   ├── gemini-ai.ts               # Gemini AI SDK
│   ├── facebook-api.ts            # Facebook Graph API
│   ├── utils.ts                   # Utility functions
│   └── validations.ts             # Zod schemas
│
├── store/
│   ├── cart-store.ts              # Zustand - Cart State
│   ├── inventory-store.ts         # Zustand - Inventory State
│   └── ui-store.ts                # Zustand - UI State (theme, etc)
│
├── types/
│   ├── product.ts
│   ├── sale.ts
│   ├── campaign.ts
│   └── index.ts
│
├── config/
│   ├── sheets.ts                  # Google Sheets config
│   └── site.ts                    # Site metadata
│
└── public/
    ├── images/
    └── fonts/
```

---

## 🔧 Technology Stack

### Frontend
- ⚡ **Next.js 14+** (App Router)
- 📘 **TypeScript** (Strong typing)
- 🎨 **Tailwind CSS** (Styling)
- 🧩 **shadcn/ui** (Component library)
- 🎭 **Lucide React** (Icons)
- 📊 **Recharts** (Charts - แทน matplotlib)
- 🐻 **Zustand** (State Management)

### Backend & APIs
- 🌐 **Next.js API Routes** (RESTful APIs)
- 🔒 **Server Actions** (Form submissions)
- 📊 **Google Sheets API v4** (Database - แทน gspread)
- 📁 **Google Drive API v3** (Image storage)
- 🤖 **Google Gemini SDK** (AI content generation)
- 📱 **Facebook Graph API** (Social media posting)

### Utilities & Libraries
- ✅ **Zod** (Schema validation)
- 📅 **date-fns** (Date manipulation)
- 🔔 **sonner** (Toast notifications)
- 📄 **@react-pdf/renderer** หรือ **jsPDF** (Receipt PDF)
- 📷 **qrcode** (QR Code generation)
- 🔢 **jsbarcode** (Barcode generation)
- 📦 **exceljs** (Excel export)
- 🖼️ **sharp** (Image processing - แทน PIL)

---

## 🎯 ขั้นตอนการพัฒนา (Implementation Steps)

### Phase 1: Project Setup ✅
1. สร้าง Next.js project ด้วย TypeScript
2. ติดตั้ง shadcn/ui + Tailwind CSS
3. Setup Google Sheets API credentials
4. สร้างโครงสร้างโฟลเดอร์

### Phase 2: Core Infrastructure 🔨
1. สร้าง Google Sheets API service layer
2. สร้าง type definitions (Product, Sale, Campaign)
3. Setup Zustand stores
4. สร้าง Dashboard Layout (Navbar, Sidebar)

### Phase 3: POS Module 🛒
1. สร้างหน้า POS Interface
2. Implement Barcode Scanner
3. Implement Cart Management
4. สร้าง Campaign Validation Logic
5. สร้าง Coupon System
6. Implement Checkout Process

### Phase 4: Inventory Module 📦
1. Product List Table (CRUD)
2. Add/Edit Product Forms
3. Image Upload to Google Drive
4. Stock Adjustment

### Phase 5: Dashboard & Reports 📊
1. สร้าง KPI Cards
2. Implement Sales Charts (Recharts)
3. Sales History with Filters
4. Export Excel functionality

### Phase 6: Campaign Management 🎯
1. Campaign CRUD
2. Auto-close expired campaigns
3. Real-time stock validation

### Phase 7: AI & Social Media 🤖
1. Gemini AI Content Generation API
2. Ad Image Creator (Canvas/Sharp)
3. Facebook Posting Integration

### Phase 8: Receipt & Settings ⚙️
1. Receipt PDF Generator
2. Settings Management
3. Printer Configuration (Web Print API)

### Phase 9: Testing & Polish 🧪
1. Error handling
2. Loading states
3. Responsive design
4. Performance optimization

---

## 📝 Key Implementation Notes

### 1. Google Sheets API (แทน gspread)
```typescript
// lib/google-sheets.ts
import { google } from 'googleapis';

const auth = new google.auth.GoogleAuth({
  credentials: JSON.parse(process.env.GOOGLE_CREDENTIALS!),
  scopes: ['https://www.googleapis.com/auth/spreadsheets'],
});

const sheets = google.sheets({ version: 'v4', auth });

export async function getProducts() {
  const response = await sheets.spreadsheets.values.get({
    spreadsheetId: process.env.SPREADSHEET_ID,
    range: 'Products!A2:J',
  });
  return response.data.values;
}
```

### 2. Campaign Validation Logic
```typescript
// lib/validations.ts
export function validateCampaign(
  campaign: Campaign,
  itemStock: number,
  campaignStock: number
): boolean {
  return (
    itemStock > 0 &&
    campaignStock > 0 &&
    campaign.status === 'Active' &&
    new Date() <= new Date(campaign.discountUntil)
  );
}
```

### 3. Zustand Cart Store
```typescript
// store/cart-store.ts
import { create } from 'zustand';

interface CartItem {
  barcode: string;
  name: string;
  price: number;
  qty: number;
  isCampaign?: boolean;
}

interface CartStore {
  items: CartItem[];
  addItem: (item: CartItem) => void;
  removeItem: (barcode: string) => void;
  clearCart: () => void;
}

export const useCartStore = create<CartStore>((set) => ({
  items: [],
  addItem: (item) => set((state) => ({
    items: [...state.items, item]
  })),
  // ...
}));
```

---

## 🚀 Next Steps

ตอนนี้พร้อมเริ่มสร้างโปรเจคแล้ว! เริ่มจาก:
1. ✅ สร้าง Next.js project
2. ✅ Setup shadcn/ui
3. ✅ สร้าง Google Sheets service layer
4. ✅ สร้างหน้า POS แรก

---

**Last Updated:** January 31, 2026
