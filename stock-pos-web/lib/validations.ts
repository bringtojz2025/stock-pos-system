// Validation and Business Logic Utilities
import { Campaign, Product, CartItem } from '@/types';

// ==================== CAMPAIGN VALIDATION ====================

export function validateCampaign(
  campaign: Campaign,
  productStock: number,
  campaignStock: number
): {
  isValid: boolean;
  usesCampaignPrice: boolean;
  reason?: string;
} {
  // Check 1: Product stock
  if (productStock <= 0) {
    return {
      isValid: false,
      usesCampaignPrice: false,
      reason: 'สินค้าหมดสต็อก',
    };
  }

  // Check 2: Campaign stock
  if (campaignStock <= 0) {
    return {
      isValid: false,
      usesCampaignPrice: false,
      reason: 'สต็อกแคมเปญหมด',
    };
  }

  // Check 3: Campaign status
  if (campaign.status !== 'Active') {
    return {
      isValid: false,
      usesCampaignPrice: false,
      reason: 'แคมเปญไม่เปิดใช้งาน',
    };
  }

  // Check 4: Campaign expiry
  const now = new Date();
  const expiryDate = new Date(campaign.discountUntil);
  
  if (now > expiryDate) {
    return {
      isValid: false,
      usesCampaignPrice: false,
      reason: 'แคมเปญหมดอายุ',
    };
  }

  return {
    isValid: true,
    usesCampaignPrice: true,
  };
}

// ==================== COUPON VALIDATION ====================

export function validateCoupon(
  couponCode: string,
  totalAmount: number,
  discountSettings: {
    discount05Amount: number;
    discount10Amount: number;
  }
): {
  isValid: boolean;
  discountAmount: number;
  discountPercent: number;
  message?: string;
} {
  const code = couponCode.toUpperCase().trim();

  // DISCOUNT05
  if (code === 'DISCOUNT05') {
    if (totalAmount >= discountSettings.discount05Amount) {
      return {
        isValid: true,
        discountAmount: totalAmount * 0.05,
        discountPercent: 5,
        message: `ลด 5% (ขั้นต่ำ ${discountSettings.discount05Amount} บาท)`,
      };
    } else {
      return {
        isValid: false,
        discountAmount: 0,
        discountPercent: 0,
        message: `ยอดซื้อต้องขั้นต่ำ ${discountSettings.discount05Amount} บาท (ปัจจุบัน ${totalAmount.toFixed(2)} บาท)`,
      };
    }
  }

  // DISCOUNT10
  if (code === 'DISCOUNT10') {
    if (totalAmount >= discountSettings.discount10Amount) {
      return {
        isValid: true,
        discountAmount: totalAmount * 0.10,
        discountPercent: 10,
        message: `ลด 10% (ขั้นต่ำ ${discountSettings.discount10Amount} บาท)`,
      };
    } else {
      return {
        isValid: false,
        discountAmount: 0,
        discountPercent: 0,
        message: `ยอดซื้อต้องขั้นต่ำ ${discountSettings.discount10Amount} บาท (ปัจจุบัน ${totalAmount.toFixed(2)} บาท)`,
      };
    }
  }

  // Custom discount codes (DISC10, DISC15, DISC20, etc.)
  if (code.startsWith('DISC')) {
    try {
      const parts = code.split('-');
      const percentStr = parts[0].replace('DISC', '');
      const percent = parseInt(percentStr);

      if (percent > 0 && percent <= 100) {
        return {
          isValid: true,
          discountAmount: totalAmount * (percent / 100),
          discountPercent: percent,
          message: `ลด ${percent}%`,
        };
      }
    } catch (e) {
      // Invalid format
    }
  }

  // SPECIAL code
  if (code === 'SPECIAL') {
    return {
      isValid: true,
      discountAmount: totalAmount * 0.15,
      discountPercent: 15,
      message: 'ลด 15% (โค้ดพิเศษ)',
    };
  }

  return {
    isValid: false,
    discountAmount: 0,
    discountPercent: 0,
    message: 'รหัสคูปองไม่ถูกต้อง',
  };
}

// ==================== RECEIPT CALCULATION ====================

export function calculateReceiptTotal(
  items: CartItem[],
  discountAmount: number = 0,
  vatEnabled: boolean = false,
  vatRate: number = 7
): {
  subtotal: number;
  discount: number;
  vat: number;
  total: number;
} {
  const subtotal = items.reduce((sum, item) => sum + item.total, 0);
  const discount = discountAmount;
  const afterDiscount = subtotal - discount;
  
  const vat = vatEnabled ? afterDiscount * (vatRate / 100) : 0;
  const total = afterDiscount + vat;

  return {
    subtotal,
    discount,
    vat,
    total,
  };
}

// ==================== STOCK CHECK ====================

export function checkStockAvailability(
  product: Product,
  requestedQty: number,
  currentCartQty: number = 0
): {
  available: boolean;
  message?: string;
} {
  const totalRequested = requestedQty + currentCartQty;

  if (product.stock <= 0) {
    return {
      available: false,
      message: 'สินค้าหมดสต็อก',
    };
  }

  if (totalRequested > product.stock) {
    return {
      available: false,
      message: `สต็อกเหลือเพียง ${product.stock} ชิ้น (ในตะกร้า ${currentCartQty} ชิ้น)`,
    };
  }

  return {
    available: true,
  };
}

// ==================== DATE/TIME HELPERS ====================

export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('th-TH', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export function formatDateTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleString('th-TH', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// ==================== RECEIPT ID GENERATION ====================

export function generateReceiptId(prefix: string = 'JZ'): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');
  
  return `${prefix}-${year}${month}${day}-${hours}${minutes}${seconds}`;
}
