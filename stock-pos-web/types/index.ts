// Type Definitions for Stock POS System

export interface Product {
  barcode: string;
  name: string;
  price: number;
  stock: number;
  category?: string;
  imageId?: string;
  brand?: string;
  model?: string;
  cost?: number;
}

export interface CartItem {
  barcode: string;
  name: string;
  qty: number;
  price: number;
  total: number;
  originalPrice?: number; // For campaign items
  isCampaign?: boolean;
  campaignName?: string;
}

export interface Campaign {
  barcode: string;
  name: string;
  status: 'Active' | 'Inactive';
  discountPrice: number;
  discountUntil: string; // ISO date string
  stock: number;
  row?: number; // Google Sheets row number
}

export interface Coupon {
  code: string;
  type: 'percent' | 'fixed';
  value: number;
  used: number;
  limit: number;
  createdDate: string;
  message?: string;
}

export interface Sale {
  receiptId: string;
  date: string;
  customerPhone?: string;
  customerName?: string;
  barcode: string;
  name: string;
  qty: number;
  unitPrice: number;
  total: number;
  usedCoupon?: string;
  discountAmount: number;
  paymentMethod: 'cash' | 'transfer' | 'credit';
  receivedCoupon?: string;
  vat?: number;
  cancel?: boolean;
}

export interface Customer {
  phone: string;
  name: string;
  address?: string;
  email?: string;
  totalPurchases?: number;
}

export interface AppSettings {
  shopName: string;
  shopAddress: string;
  shopPhone: string;
  thankYouMsg: string;
  vatEnabled: boolean;
  vatRate: number;
  taxId: string;
  promptpayType: 'เบอร์โทรศัพท์' | 'เลขบัตรประชาชน';
  promptpayId: string;
  printerName: string;
  paperSize: '58mm' | '80mm';
  stockAlertEnabled: boolean;
  minimumStock: number;
  discount05Amount: number;
  discount05Message: string;
  discount10Amount: number;
  discount10Message: string;
}

export interface DashboardStats {
  totalSales: number;
  dailyRevenue: number;
  lowStockCount: number;
  totalProducts: number;
  topProducts: Array<{
    name: string;
    qty: number;
    revenue: number;
  }>;
}

export interface SalesChartData {
  date: string;
  revenue: number;
  sales: number;
}
