// Zustand Store for POS Cart Management
import { create } from 'zustand';
import { CartItem, Coupon } from '@/types';

interface CartStore {
  items: CartItem[];
  couponCode: string;
  customerPhone: string;
  customerName: string;
  
  // Actions
  addItem: (item: CartItem) => void;
  removeItem: (barcode: string) => void;
  updateItemQty: (barcode: string, qty: number) => void;
  clearCart: () => void;
  setCoupon: (code: string) => void;
  setCustomer: (phone: string, name: string) => void;
  
  // Computed
  getTotalAmount: () => number;
  getItemCount: () => number;
}

export const useCartStore = create<CartStore>((set, get) => ({
  items: [],
  couponCode: '',
  customerPhone: '',
  customerName: '',

  addItem: (newItem) => set((state) => {
    const existingIndex = state.items.findIndex(item => item.barcode === newItem.barcode);
    
    if (existingIndex > -1) {
      // Update existing item
      const updatedItems = [...state.items];
      updatedItems[existingIndex].qty += newItem.qty;
      updatedItems[existingIndex].total = updatedItems[existingIndex].qty * updatedItems[existingIndex].price;
      return { items: updatedItems };
    } else {
      // Add new item
      return { items: [...state.items, newItem] };
    }
  }),

  removeItem: (barcode) => set((state) => ({
    items: state.items.filter(item => item.barcode !== barcode),
  })),

  updateItemQty: (barcode, qty) => set((state) => {
    const updatedItems = state.items.map(item => {
      if (item.barcode === barcode) {
        return {
          ...item,
          qty,
          total: qty * item.price,
        };
      }
      return item;
    });
    return { items: updatedItems };
  }),

  clearCart: () => set({
    items: [],
    couponCode: '',
    customerPhone: '',
    customerName: '',
  }),

  setCoupon: (code) => set({ couponCode: code }),

  setCustomer: (phone, name) => set({ 
    customerPhone: phone, 
    customerName: name 
  }),

  getTotalAmount: () => {
    const { items } = get();
    return items.reduce((sum, item) => sum + item.total, 0);
  },

  getItemCount: () => {
    const { items } = get();
    return items.reduce((sum, item) => sum + item.qty, 0);
  },
}));
