// Google Sheets API Service Layer
// แทนที่ gspread จาก Python version

import { google } from 'googleapis';
import { Product, Sale, Campaign, Customer, Coupon } from '@/types';

const SPREADSHEET_ID = process.env.GOOGLE_SPREADSHEET_ID!;

// Initialize Google Auth
function getAuth() {
  const credentials = JSON.parse(process.env.GOOGLE_CREDENTIALS || '{}');
  
  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: [
      'https://www.googleapis.com/auth/spreadsheets',
      'https://www.googleapis.com/auth/drive',
    ],
  });

  return auth;
}

// Get Google Sheets instance
async function getSheets() {
  const auth = await getAuth();
  return google.sheets({ version: 'v4', auth });
}

// ==================== PRODUCTS ====================

export async function getProducts(): Promise<Product[]> {
  const sheets = await getSheets();
  
  const response = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'Products!A2:J',
  });

  const rows = response.data.values || [];
  
  return rows.map((row) => ({
    barcode: row[0] || '',
    name: row[1] || '',
    price: parseFloat(row[2] || '0'),
    stock: parseInt(row[3] || '0'),
    category: row[4] || '',
    imageId: row[5] || '',
    brand: row[6] || '',
    model: row[7] || '',
    cost: parseFloat(row[8] || '0'),
  }));
}

export async function getProductByBarcode(barcode: string): Promise<Product | null> {
  const products = await getProducts();
  return products.find(p => p.barcode === barcode) || null;
}

export async function addProduct(product: Product): Promise<void> {
  const sheets = await getSheets();
  
  await sheets.spreadsheets.values.append({
    spreadsheetId: SPREADSHEET_ID,
    range: 'Products!A:J',
    valueInputOption: 'USER_ENTERED',
    requestBody: {
      values: [[
        product.barcode,
        product.name,
        product.price,
        product.stock,
        product.category || '',
        product.imageId || '',
        product.brand || '',
        product.model || '',
        product.cost || 0,
      ]],
    },
  });
}

export async function updateProduct(barcode: string, updates: Partial<Product>): Promise<void> {
  const sheets = await getSheets();
  
  // Find row number
  const products = await getProducts();
  const index = products.findIndex(p => p.barcode === barcode);
  
  if (index === -1) throw new Error('Product not found');
  
  const row = index + 2; // +2 because header is row 1, data starts at row 2
  
  // Update specific cells
  const updatedProduct = { ...products[index], ...updates };
  
  await sheets.spreadsheets.values.update({
    spreadsheetId: SPREADSHEET_ID,
    range: `Products!A${row}:J${row}`,
    valueInputOption: 'USER_ENTERED',
    requestBody: {
      values: [[
        updatedProduct.barcode,
        updatedProduct.name,
        updatedProduct.price,
        updatedProduct.stock,
        updatedProduct.category || '',
        updatedProduct.imageId || '',
        updatedProduct.brand || '',
        updatedProduct.model || '',
        updatedProduct.cost || 0,
      ]],
    },
  });
}

export async function updateStock(barcode: string, newStock: number): Promise<void> {
  const sheets = await getSheets();
  const products = await getProducts();
  const index = products.findIndex(p => p.barcode === barcode);
  
  if (index === -1) throw new Error('Product not found');
  
  const row = index + 2;
  
  await sheets.spreadsheets.values.update({
    spreadsheetId: SPREADSHEET_ID,
    range: `Products!D${row}`,
    valueInputOption: 'USER_ENTERED',
    requestBody: {
      values: [[newStock]],
    },
  });
}

export async function deleteProduct(barcode: string): Promise<void> {
  const sheets = await getSheets();
  const products = await getProducts();
  const index = products.findIndex(p => p.barcode === barcode);
  
  if (index === -1) throw new Error('Product not found');
  
  const row = index + 2;
  
  await sheets.spreadsheets.batchUpdate({
    spreadsheetId: SPREADSHEET_ID,
    requestBody: {
      requests: [{
        deleteDimension: {
          range: {
            sheetId: 0, // Products sheet
            dimension: 'ROWS',
            startIndex: row - 1,
            endIndex: row,
          },
        },
      }],
    },
  });
}

// ==================== CAMPAIGNS ====================

export async function getCampaigns(): Promise<Campaign[]> {
  const sheets = await getSheets();
  
  const response = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'Campaigns!A2:G',
  });

  const rows = response.data.values || [];
  
  return rows.map((row, index) => ({
    barcode: row[0] || '',
    name: row[1] || '',
    status: (row[2] || 'Inactive') as 'Active' | 'Inactive',
    discountPrice: parseFloat(row[3] || '0'),
    discountUntil: row[4] || '',
    stock: parseInt(row[5] || '0'),
    row: index + 2,
  }));
}

export async function getActiveCampaign(barcode: string): Promise<Campaign | null> {
  const campaigns = await getCampaigns();
  const now = new Date();
  
  return campaigns.find(c => 
    c.barcode === barcode && 
    c.status === 'Active' &&
    new Date(c.discountUntil) >= now &&
    c.stock > 0
  ) || null;
}

export async function updateCampaignStock(campaignRow: number, newStock: number): Promise<void> {
  const sheets = await getSheets();
  
  await sheets.spreadsheets.values.update({
    spreadsheetId: SPREADSHEET_ID,
    range: `Campaigns!F${campaignRow}`,
    valueInputOption: 'USER_ENTERED',
    requestBody: {
      values: [[newStock]],
    },
  });
}

export async function closeCampaign(campaignRow: number): Promise<void> {
  const sheets = await getSheets();
  
  await sheets.spreadsheets.values.update({
    spreadsheetId: SPREADSHEET_ID,
    range: `Campaigns!C${campaignRow}`,
    valueInputOption: 'USER_ENTERED',
    requestBody: {
      values: [['Inactive']],
    },
  });
}

// ==================== SALES ====================

export async function addSale(sale: Sale): Promise<void> {
  const sheets = await getSheets();
  
  await sheets.spreadsheets.values.append({
    spreadsheetId: SPREADSHEET_ID,
    range: 'Sales!A:O',
    valueInputOption: 'USER_ENTERED',
    requestBody: {
      values: [[
        sale.receiptId,
        sale.date,
        sale.customerPhone || '',
        sale.customerName || '',
        sale.barcode,
        sale.name,
        sale.qty,
        sale.unitPrice,
        sale.total,
        sale.usedCoupon || '',
        sale.discountAmount,
        sale.paymentMethod,
        sale.receivedCoupon || '',
        sale.vat || 0,
        sale.cancel ? 'Yes' : '',
      ]],
    },
  });
}

export async function getSales(startDate?: string, endDate?: string): Promise<Sale[]> {
  const sheets = await getSheets();
  
  const response = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'Sales!A2:O',
  });

  const rows = response.data.values || [];
  
  let sales = rows.map((row) => ({
    receiptId: row[0] || '',
    date: row[1] || '',
    customerPhone: row[2] || '',
    customerName: row[3] || '',
    barcode: row[4] || '',
    name: row[5] || '',
    qty: parseInt(row[6] || '0'),
    unitPrice: parseFloat(row[7] || '0'),
    total: parseFloat(row[8] || '0'),
    usedCoupon: row[9] || '',
    discountAmount: parseFloat(row[10] || '0'),
    paymentMethod: (row[11] || 'cash') as 'cash' | 'transfer' | 'credit',
    receivedCoupon: row[12] || '',
    vat: parseFloat(row[13] || '0'),
    cancel: row[14] === 'Yes',
  }));

  // Filter by date if provided
  if (startDate || endDate) {
    sales = sales.filter(sale => {
      const saleDate = new Date(sale.date);
      if (startDate && saleDate < new Date(startDate)) return false;
      if (endDate && saleDate > new Date(endDate)) return false;
      return true;
    });
  }

  return sales;
}

export async function getSalesByReceipt(receiptId: string): Promise<Sale[]> {
  const sales = await getSales();
  return sales.filter(s => s.receiptId === receiptId);
}

// ==================== CUSTOMERS ====================

export async function getCustomers(): Promise<Customer[]> {
  const sheets = await getSheets();
  
  const response = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'Customers!A2:E',
  });

  const rows = response.data.values || [];
  
  return rows.map((row) => ({
    phone: row[0] || '',
    name: row[1] || '',
    address: row[2] || '',
    email: row[3] || '',
    totalPurchases: parseFloat(row[4] || '0'),
  }));
}

export async function getCustomerByPhone(phone: string): Promise<Customer | null> {
  const customers = await getCustomers();
  return customers.find(c => c.phone === phone) || null;
}
