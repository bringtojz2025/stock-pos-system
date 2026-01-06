import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk, simpledialog
import gspread
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from datetime import datetime
import threading
import winsound
from PIL import Image, ImageTk
import io
import qrcode
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict
import matplotlib
from ai_content_generator import AIContentGenerator, AdvertisementImageCreator, FacebookIntegration, load_config, save_config

# ตั้งค่าฟอนต์ภาษาไทย
matplotlib.rc('font', family='Tahoma') 

# --- ตั้งค่า ---
GOOGLE_DRIVE_FOLDER_ID = '1eJbph5WYoVALx2a2cAHxeSPyUy6JZwQn' 

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class StockManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ระบบ POS & Stock V.11.1 (History with Barcode)")
        self.geometry("1200x850")
        
        self.app_running = True
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.all_inventory_data = [] 
        self.cart_items = [] 
        self.sales_history_data = {} 
        
        # AI & Social Media Config
        self.ai_config = load_config()
        self.ai_content_gen = AIContentGenerator(
            api_key=self.ai_config.get("ai_api_key", ""),
            api_type=self.ai_config.get("ai_api_type", "openai")
        )
        self.ad_creator = AdvertisementImageCreator()
        self.facebook_api = FacebookIntegration(
            access_token=self.ai_config.get("facebook_access_token", ""),
            page_id=self.ai_config.get("facebook_page_id", "")
        )

        self.creds = self.authenticate()
        self.gc = gspread.authorize(self.creds)
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        
        try:
            self.sh = self.gc.open("StockDB")
            self.sheet_products = self.sh.worksheet("Products")
            try:
                self.sheet_sales = self.sh.worksheet("Sales")
            except:
                try:
                    self.sheet_sales = self.sh.add_worksheet(title="Sales", rows="1000", cols="10")
                    self.sheet_sales.append_row(["ReceiptID", "Date", "Barcode", "Name", "Qty", "UnitPrice", "Total", "PromotionCode"])
                except:
                    self.sheet_sales = self.sh.sheet1
        except Exception as e:
            messagebox.showerror("Connection Error", f"{e}")
            self.destroy()
            return

        self.create_layout()

    def on_closing(self):
        self.app_running = False
        try:
            plt.close('all')
            self.quit()
            self.destroy()
        except: pass

    def authenticate(self):
        creds = None
        if os.path.exists('token.pickle'):
            try:
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            except:
                os.remove('token.pickle')

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except:
                    creds = None
            
            if not creds:
                flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds

    def get_next_receipt_id(self):
        try:
            today_str = datetime.now().strftime("%Y%m%d")
            prefix = f"JZ{today_str}"
            existing_ids = self.sheet_sales.col_values(1)
            max_seq = 0
            for r_id in existing_ids:
                if str(r_id).startswith(prefix):
                    try:
                        suffix = r_id.replace(prefix, "")
                        seq = int(suffix)
                        if seq > max_seq: max_seq = seq
                    except: pass
            next_seq = max_seq + 1
            return f"{prefix}{next_seq:06d}"
        except:
            return datetime.now().strftime("JZ-%Y%m%d-%H%M%S")

    def create_layout(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview._segmented_button.configure(font=("Kanit", 16, "bold"))
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_pos = self.tabview.add("ขายหน้าร้าน (POS)")
        self.tab_inventory = self.tabview.add("คลังสินค้า (Inventory)")
        self.tab_history = self.tabview.add("ประวัติการขาย (History)")
        self.tab_dashboard = self.tabview.add("ภาพรวม (Dashboard)")
        self.tab_ai_social = self.tabview.add("🤖 AI & Social Media")

        self.setup_pos_tab()
        self.setup_inventory_tab()
        self.setup_history_tab()
        self.setup_dashboard_tab()
        self.setup_ai_social_tab()

    # =========================================
    # TAB 1: POS Logic
    # =========================================
    def setup_pos_tab(self):
        paned = ctk.CTkFrame(self.tab_pos, fg_color="transparent")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ctk.CTkFrame(paned, width=400)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)

        ctk.CTkLabel(left_frame, text="🛒 สแกนสินค้า", font=("Kanit", 24, "bold")).pack(pady=15)

        self.pos_barcode = self.create_styled_entry(left_frame, "Scan Barcode Here...", "BARCODE")
        self.pos_barcode.bind('<Return>', self.add_item_to_cart)

        self.lbl_last_scan = ctk.CTkLabel(left_frame, text="-", font=("Kanit", 18), text_color="gray")
        self.lbl_last_scan.pack(pady=10)

        btn_manual_add = ctk.CTkButton(left_frame, text="เพิ่มลงตะกร้า ⬇️", command=self.add_item_to_cart,
                                       font=("Kanit", 16), height=40)
        btn_manual_add.pack(pady=10)

        right_frame = ctk.CTkFrame(paned, width=600)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)

        ctk.CTkLabel(right_frame, text="รายการในใบเสร็จ", font=("Kanit", 20, "bold")).pack(pady=10)

        columns = ("Barcode", "Name", "Qty", "Price", "Total")
        self.cart_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=15)
        self.cart_tree.heading("Barcode", text="Barcode"); self.cart_tree.column("Barcode", width=100)
        self.cart_tree.heading("Name", text="สินค้า"); self.cart_tree.column("Name", width=150)
        self.cart_tree.heading("Qty", text="จำนวน"); self.cart_tree.column("Qty", width=60, anchor="center")
        self.cart_tree.heading("Price", text="ราคา"); self.cart_tree.column("Price", width=80, anchor="e")
        self.cart_tree.heading("Total", text="รวม"); self.cart_tree.column("Total", width=80, anchor="e")
        self.cart_tree.pack(fill="both", expand=True, padx=10)
        
        btn_del_item = ctk.CTkButton(right_frame, text="ลบรายการที่เลือก", command=self.delete_from_cart,
                                     fg_color="#FF474C", height=30)
        btn_del_item.pack(pady=5, padx=10, anchor="e")

        sum_frame = ctk.CTkFrame(right_frame, fg_color="gray20")
        sum_frame.pack(fill="x", padx=10, pady=10)

        self.lbl_total = ctk.CTkLabel(sum_frame, text="ยอดรวม: 0.00 บาท", font=("Kanit", 28, "bold"), text_color="#2CC985")
        self.lbl_total.pack(pady=15)

        self.btn_checkout = ctk.CTkButton(right_frame, text="💰 ชำระเงิน / ตัดสต็อก", command=self.process_checkout,
                                          font=("Kanit", 20, "bold"), height=60, fg_color="#F39C12", hover_color="#D68910")
        self.btn_checkout.pack(fill="x", padx=10, pady=(0, 20))

    def create_styled_entry(self, parent, ph, suffix):
        container = ctk.CTkFrame(parent, height=50, fg_color=("gray95", "gray25")) 
        container.pack(pady=8, padx=20, fill="x")
        ctk.CTkLabel(container, text=suffix, width=80, font=("Arial", 12, "bold")).pack(side="right", padx=10)
        entry = ctk.CTkEntry(container, placeholder_text=ph, height=50, font=("Arial", 18), 
                             border_width=0, fg_color="transparent")
        entry.pack(side="left", fill="both", expand=True, padx=10)
        return entry

    def add_item_to_cart(self, event=None):
        barcode = self.pos_barcode.get().strip()
        if not barcode: return
        if not self.all_inventory_data: self.load_inventory_data()
        found_product = None
        for idx, row in self.all_inventory_data:
            if str(row[1]).strip() == barcode:
                found_product = (idx, row)
                break
        if found_product:
            row_idx, data = found_product
            name = data[2]
            try: price = float(data[5])
            except: price = 0.0
            try: current_stock = int(data[7]) if len(data) > 7 and data[7] else 0
            except: current_stock = 0
            qty_in_cart = sum(item['qty'] for item in self.cart_items if item['barcode'] == barcode)
            if qty_in_cart + 1 > current_stock:
                messagebox.showwarning("สต็อกหมด", f"สินค้า '{name}' เหลือเพียง {current_stock} ชิ้น")
                self.pos_barcode.delete(0, "end")
                return
            existing_item = next((item for item in self.cart_items if item['barcode'] == barcode), None)
            if existing_item:
                existing_item['qty'] += 1
                existing_item['total'] = existing_item['qty'] * existing_item['price']
            else:
                self.cart_items.append({
                    'barcode': barcode, 'name': name, 'qty': 1, 'price': price,
                    'total': price, 'row_idx': row_idx
                })
            self.play_sound("success")
            self.lbl_last_scan.configure(text=f"ล่าสุด: {name} (฿{price})")
            self.update_cart_ui()
            self.pos_barcode.delete(0, "end")
        else:
            self.play_sound("error")
            messagebox.showerror("ไม่พบสินค้า", f"ไม่พบ Barcode: {barcode}")
            self.pos_barcode.delete(0, "end")

    def update_cart_ui(self):
        for i in self.cart_tree.get_children(): self.cart_tree.delete(i)
        total_amount = 0
        for item in self.cart_items:
            self.cart_tree.insert("", "end", values=(item['barcode'], item['name'], item['qty'], 
                                                     f"{item['price']:,.2f}", f"{item['total']:,.2f}"))
            total_amount += item['total']
        self.lbl_total.configure(text=f"ยอดรวม: {total_amount:,.2f} บาท")
        return total_amount

    def delete_from_cart(self):
        selected = self.cart_tree.selection()
        if not selected: return
        for sel in selected:
            item_values = self.cart_tree.item(sel)['values']
            barcode_to_del = str(item_values[0])
            self.cart_items = [item for item in self.cart_items if str(item['barcode']) != barcode_to_del]
        self.update_cart_ui()

    def process_checkout(self):
        if not self.cart_items:
            messagebox.showwarning("เตือน", "ไม่มีสินค้าในตะกร้า")
            return
        total_amount = self.update_cart_ui()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        coupon_code = ""
        if total_amount >= 200:
            coupon_code = f"DISC10-{datetime.now().strftime('%M%S')}"
        self.btn_checkout.configure(state="disabled", text="กำลังบันทึก...")
        threading.Thread(target=self.run_checkout_thread, 
                         args=(timestamp, total_amount, coupon_code), daemon=True).start()

    def run_checkout_thread(self, timestamp, total_amount, coupon_code):
        if not self.app_running: return 
        try:
            receipt_id = self.get_next_receipt_id()
            sales_rows = []
            for item in self.cart_items:
                row = [receipt_id, timestamp, item['barcode'], item['name'], 
                       item['qty'], item['price'], item['total'], coupon_code]
                sales_rows.append(row)
            self.sheet_sales.append_rows(sales_rows)
            for item in self.cart_items:
                current_qty_cell = self.sheet_products.cell(int(item['row_idx']), 8).value
                current_qty = int(current_qty_cell) if current_qty_cell else 0
                new_qty = max(0, current_qty - item['qty'])
                self.sheet_products.update_cell(int(item['row_idx']), 8, new_qty)
            if self.app_running and self.winfo_exists():
                self.after(0, lambda: self.finish_checkout(coupon_code))
        except Exception as e:
            if self.app_running and self.winfo_exists():
                self.after(0, lambda: messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {e}"))
                self.after(0, lambda: self.btn_checkout.configure(state="normal", text="💰 ชำระเงิน / ตัดสต็อก"))

    def finish_checkout(self, coupon_code):
        if not self.app_running: return
        self.cart_items = []
        self.update_cart_ui()
        self.btn_checkout.configure(state="normal", text="💰 ชำระเงิน / ตัดสต็อก")
        self.play_sound("success")
        self.load_inventory_data()
        if coupon_code: self.show_coupon_qr(coupon_code)
        else: messagebox.showinfo("สำเร็จ", "บันทึกรายการขายเรียบร้อย")

    def show_coupon_qr(self, code):
        if not self.app_running: return
        qr_window = ctk.CTkToplevel(self)
        qr_window.title("🎉 คุณได้รับคูปองส่วนลด!")
        qr_window.geometry("400x450")
        qr_window.attributes("-topmost", True)
        ctk.CTkLabel(qr_window, text="ซื้อครบ 200 บาท\nรับคูปองส่วนลด 10% ครั้งถัดไป", 
                     font=("Kanit", 18, "bold"), text_color="#E67E22").pack(pady=20)
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(code)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img_tk = ImageTk.PhotoImage(img)
        lbl_img = ctk.CTkLabel(qr_window, image=img_tk, text="")
        lbl_img.image = img_tk
        lbl_img.pack(pady=10)
        ctk.CTkLabel(qr_window, text=f"CODE: {code}", font=("Arial", 20, "bold")).pack(pady=10)
        ctk.CTkButton(qr_window, text="ปิด", command=qr_window.destroy).pack(pady=10)

    # =========================================
    # TAB 2: INVENTORY Logic
    # =========================================
    def setup_inventory_tab(self):
        paned = ctk.CTkFrame(self.tab_inventory)
        paned.pack(fill="both", expand=True)

        frame_list = ctk.CTkFrame(paned, width=600)
        frame_list.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        frame_top = ctk.CTkFrame(frame_list, fg_color="transparent")
        frame_top.pack(fill="x", pady=5)
        btn_refresh = ctk.CTkButton(frame_top, text="🔄 รีเฟรช", command=self.load_inventory_data, width=100)
        btn_refresh.pack(side="left", padx=5)
        ctk.CTkLabel(frame_top, text="* ดับเบิ้ลคลิกที่จำนวนเพื่อแก้ไขสต็อก", text_color="gray").pack(side="left", padx=10)

        columns = ("ID", "Barcode", "Name", "Detail", "Cost", "Price", "ImageID", "Stock")
        self.tree = ttk.Treeview(frame_list, columns=columns, show="headings")
        headers = ["ID", "Barcode", "Name", "Detail", "Cost", "Price", "ImageID", "Stock"]
        widths = [40, 100, 150, 80, 60, 60, 0, 60]
        for h, w in zip(headers, widths):
            self.tree.heading(h, text=h)
            self.tree.column(h, width=w, anchor="center")
            if h == "ImageID": self.tree.column(h, width=0, stretch=False)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_product_select)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        btn_add = ctk.CTkButton(frame_list, text="➕ เพิ่มสินค้าใหม่", command=self.open_add_product_window, fg_color="#F39C12")
        btn_add.pack(fill="x", pady=5)

        # --- RIGHT PANEL ---
        frame_detail = ctk.CTkFrame(paned, width=400)
        frame_detail.pack(side="right", fill="y", padx=5, pady=5)
        
        self.image_label = ctk.CTkLabel(frame_detail, text="[No Image]", width=200, height=200, fg_color="gray30")
        self.image_label.pack(pady=10)

        self.lbl_info_name = ctk.CTkLabel(frame_detail, text="-", font=("Kanit", 20, "bold"))
        self.lbl_info_name.pack(pady=5)
        
        self.lbl_info_stock = ctk.CTkLabel(frame_detail, text="Stock: -", font=("Arial", 24, "bold"), text_color="#3498DB")
        self.lbl_info_stock.pack(pady=5)

        ctk.CTkLabel(frame_detail, text="รายละเอียดสินค้า:", font=("Kanit", 16, "bold"), anchor="w").pack(fill="x", padx=10, pady=(10,0))
        self.txt_info_detail = ctk.CTkTextbox(frame_detail, height=100, font=("Arial", 16))
        self.txt_info_detail.pack(fill="x", padx=10, pady=5)
        self.txt_info_detail.configure(state="disabled") 

        self.load_inventory_data()

    def on_tree_double_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell": return
        column = self.tree.identify_column(event.x)
        selected_item = self.tree.selection()
        if not selected_item: return
        if column == "#8": 
            item_values = self.tree.item(selected_item[0])['values']
            row_idx = self.tree.item(selected_item[0], "tags")[0]
            new_stock = ctk.CTkInputDialog(text=f"แก้ไขสต็อกสินค้า: {item_values[2]}", title="Update Stock").get_input()
            if new_stock is not None:
                try:
                    val = int(new_stock)
                    if val < 0: raise ValueError
                    threading.Thread(target=self.update_stock_manual, args=(row_idx, val), daemon=True).start()
                except ValueError:
                    messagebox.showerror("Error", "กรุณากรอกตัวเลขจำนวนเต็มที่ถูกต้อง")

    def update_stock_manual(self, row_idx, new_val):
        if not self.app_running: return
        try:
            self.sheet_products.update_cell(int(row_idx), 8, new_val)
            if self.app_running and self.winfo_exists():
                self.after(0, lambda: messagebox.showinfo("สำเร็จ", "อัปเดตสต็อกเรียบร้อย"))
                self.after(0, self.load_inventory_data)
        except Exception as e:
            if self.app_running and self.winfo_exists():
                self.after(0, lambda: messagebox.showerror("Error", f"อัปเดตไม่สำเร็จ: {e}"))

    def load_inventory_data(self):
        try:
            records = self.sheet_products.get_all_values()
            if len(records) > 1:
                self.all_inventory_data = []
                for i in self.tree.get_children(): self.tree.delete(i)
                for idx, row in enumerate(records[1:], start=2):
                    safe_row = (row + [""] * 8)[:8]
                    if safe_row[7] == "": safe_row[7] = "0"
                    self.all_inventory_data.append((str(idx), safe_row))
                    self.tree.insert("", "end", values=safe_row, tags=(str(idx),))
        except Exception as e:
            print(f"Load Error: {e}")

    def on_product_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        vals = self.tree.item(selected)['values']
        safe_vals = list(vals) + [""]*8
        self.lbl_info_name.configure(text=str(safe_vals[2]))
        self.lbl_info_stock.configure(text=f"Stock: {safe_vals[7]} ชิ้น")
        
        detail_txt = str(safe_vals[3])
        self.txt_info_detail.configure(state="normal")
        self.txt_info_detail.delete("0.0", "end")
        self.txt_info_detail.insert("0.0", detail_txt)
        self.txt_info_detail.configure(state="disabled")

        img_id = str(safe_vals[6]).strip()
        self.display_image(img_id)

    def display_image(self, file_id):
        if not file_id or file_id == "None":
            self.image_label.configure(image=None, text="[No Image]")
            return
        threading.Thread(target=self.download_and_show_image, args=(file_id,), daemon=True).start()

    def download_and_show_image(self, file_id):
        if not self.app_running: return
        try:
            request = self.drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                if not self.app_running: return 
                status, done = downloader.next_chunk()
            fh.seek(0)
            temp = Image.open(fh)
            temp.load()
            pil_img = temp.copy()
            pil_img = pil_img.resize((200, 200))
            fh.close(); temp.close()
            if self.app_running and self.winfo_exists():
                self.after(0, self.update_image_ui, pil_img)
        except: pass

    def update_image_ui(self, pil_image):
        if not self.app_running or not self.winfo_exists(): return
        try:
            ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(200, 200))
            self.image_label.configure(image=ctk_img, text="")
            self.current_image_ref = ctk_img
        except: pass

    # =========================================
    # ส่วนเพิ่มสินค้าใหม่
    # =========================================
    def open_add_product_window(self):
        self.add_window = ctk.CTkToplevel(self)
        self.add_window.title("เพิ่มสินค้า")
        self.add_window.geometry("400x700")
        self.add_window.attributes("-topmost", True)
        self.new_barcode = self.create_styled_entry(self.add_window, "Barcode", "BARCODE")
        self.new_name = self.create_styled_entry(self.add_window, "ชื่อสินค้า", "NAME")
        self.new_detail = self.create_styled_entry(self.add_window, "รายละเอียด", "DETAIL")
        self.new_cost = self.create_styled_entry(self.add_window, "ราคาทุน", "COST")
        self.new_price = self.create_styled_entry(self.add_window, "ราคาขาย", "PRICE")
        self.new_stock = self.create_styled_entry(self.add_window, "จำนวนเริ่มต้น", "STOCK")
        self.new_image_path = None
        ctk.CTkButton(self.add_window, text="เลือกรูป", command=self.choose_new_image).pack(pady=5)
        ctk.CTkButton(self.add_window, text="บันทึก", command=self.save_new_product, 
                      fg_color="#2CC985", height=50).pack(pady=20, fill="x", padx=20)

    def choose_new_image(self):
        self.new_image_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.png")])

    def save_new_product(self):
        threading.Thread(target=self.run_save_new_product, daemon=True).start()

    def run_save_new_product(self):
        if not self.app_running: return
        image_id = "" 
        if self.new_image_path:
             try:
                file_metadata = {'name': os.path.basename(self.new_image_path), 'parents': [GOOGLE_DRIVE_FOLDER_ID]}
                media = MediaFileUpload(self.new_image_path, mimetype='image/jpeg')
                f = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                image_id = f.get('id')
             except: pass
        records = self.sheet_products.get_all_values()
        next_id = len(records) if len(records) > 0 else 1
        row = [next_id, self.new_barcode.get(), self.new_name.get(), self.new_detail.get(),
               self.new_cost.get(), self.new_price.get(), image_id, self.new_stock.get()]
        self.sheet_products.append_row(row)
        if self.app_running and self.winfo_exists():
            self.after(0, lambda: messagebox.showinfo("สำเร็จ", "เพิ่มสินค้าแล้ว"))
            self.after(0, self.add_window.destroy)
            self.after(0, self.load_inventory_data)

    # =========================================
    # TAB 3: HISTORY Logic (Updated with Barcode)
    # =========================================
    def setup_history_tab(self):
        paned = ctk.CTkFrame(self.tab_history)
        paned.pack(fill="both", expand=True)

        # LEFT: Receipt List
        left_frame = ctk.CTkFrame(paned, width=400)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkButton(left_frame, text="🔄 โหลดประวัติ", command=self.load_history_data).pack(fill="x", pady=5)
        
        self.tree_receipts = ttk.Treeview(left_frame, columns=("ID", "Date", "Total"), show="headings")
        self.tree_receipts.heading("ID", text="เลขที่ใบเสร็จ"); self.tree_receipts.column("ID", width=120)
        self.tree_receipts.heading("Date", text="วันที่"); self.tree_receipts.column("Date", width=120)
        self.tree_receipts.heading("Total", text="ยอดรวม"); self.tree_receipts.column("Total", width=100, anchor="e")
        self.tree_receipts.pack(fill="both", expand=True)
        self.tree_receipts.bind("<<TreeviewSelect>>", self.on_receipt_select)

        # RIGHT: Receipt Details
        right_frame = ctk.CTkFrame(paned, width=600)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(right_frame, text="รายการสินค้าในบิล", font=("Kanit", 20, "bold")).pack(pady=10)
        
        # ✅ เพิ่มช่อง Barcode ตรงนี้
        self.tree_rec_items = ttk.Treeview(right_frame, columns=("Barcode", "Name", "Qty", "Price", "Total"), show="headings")
        self.tree_rec_items.heading("Barcode", text="Barcode"); self.tree_rec_items.column("Barcode", width=100)
        self.tree_rec_items.heading("Name", text="สินค้า"); self.tree_rec_items.column("Name", width=180)
        self.tree_rec_items.heading("Qty", text="จำนวน"); self.tree_rec_items.column("Qty", width=60, anchor="center")
        self.tree_rec_items.heading("Price", text="ราคา/หน่วย"); self.tree_rec_items.column("Price", width=80, anchor="e")
        self.tree_rec_items.heading("Total", text="รวม"); self.tree_rec_items.column("Total", width=80, anchor="e")
        self.tree_rec_items.pack(fill="both", expand=True)

        self.load_history_data()

    def load_history_data(self):
        threading.Thread(target=self.run_load_history, daemon=True).start()

    def run_load_history(self):
        if not self.app_running: return
        try:
            records = self.sheet_sales.get_all_values()
            self.sales_history_data = {} 
            
            if len(records) > 1:
                for row in records[1:]:
                    if len(row) >= 7:
                        rec_id = row[0]
                        date_str = row[1]
                        
                        if rec_id not in self.sales_history_data:
                            self.sales_history_data[rec_id] = {
                                'date': date_str,
                                'items': [],
                                'total_bill': 0.0
                            }
                        
                        try:
                            # ✅ ดึงค่า Barcode มาด้วย
                            barcode = row[2]
                            qty = int(row[4])
                            price = float(row[5])
                            total = float(row[6].replace(",", ""))
                            
                            self.sales_history_data[rec_id]['items'].append({
                                'barcode': barcode,
                                'name': row[3],
                                'qty': qty,
                                'price': price,
                                'total': total
                            })
                            self.sales_history_data[rec_id]['total_bill'] += total
                        except: pass

            if self.app_running and self.winfo_exists():
                self.after(0, self.update_history_ui)
        except Exception as e:
            print(f"History Load Error: {e}")

    def update_history_ui(self):
        for i in self.tree_receipts.get_children(): self.tree_receipts.delete(i)
        
        sorted_ids = sorted(self.sales_history_data.keys(), reverse=True)
        for r_id in sorted_ids:
            data = self.sales_history_data[r_id]
            self.tree_receipts.insert("", "end", values=(r_id, data['date'], f"{data['total_bill']:,.2f}"))

    def on_receipt_select(self, event):
        selected = self.tree_receipts.selection()
        if not selected: return
        
        r_id = self.tree_receipts.item(selected[0])['values'][0]
        
        for i in self.tree_rec_items.get_children(): self.tree_rec_items.delete(i)
        
        if r_id in self.sales_history_data:
            items = self.sales_history_data[r_id]['items']
            for item in items:
                # ✅ แสดง Barcode ในตาราง
                self.tree_rec_items.insert("", "end", values=(
                    item['barcode'], 
                    item['name'], item['qty'], f"{item['price']:,.2f}", f"{item['total']:,.2f}"
                ))

    # =========================================
    # TAB 4: DASHBOARD Logic
    # =========================================
    def setup_dashboard_tab(self):
        self.dash_frame = ctk.CTkFrame(self.tab_dashboard, fg_color="transparent")
        self.dash_frame.pack(fill="both", expand=True, padx=20, pady=20)
        kpi_frame = ctk.CTkFrame(self.dash_frame, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=10)
        self.card_sales = self.create_kpi_card(kpi_frame, "ยอดขายรวม", "0.00 บาท", "#3498DB")
        self.card_sales.pack(side="left", fill="x", expand=True, padx=10)
        self.card_txn = self.create_kpi_card(kpi_frame, "จำนวนบิลที่ขาย", "0 บิล", "#E67E22")
        self.card_txn.pack(side="left", fill="x", expand=True, padx=10)
        btn_refresh = ctk.CTkButton(self.dash_frame, text="🔄 รีเฟรชข้อมูล", command=self.update_dashboard, font=("Kanit", 16), height=40)
        btn_refresh.pack(pady=10)
        graph_frame = ctk.CTkFrame(self.dash_frame, fg_color="transparent")
        graph_frame.pack(fill="both", expand=True, pady=10)
        self.graph_left = ctk.CTkFrame(graph_frame)
        self.graph_left.pack(side="left", fill="both", expand=True, padx=5)
        self.graph_right = ctk.CTkFrame(graph_frame)
        self.graph_right.pack(side="right", fill="both", expand=True, padx=5)
        self.update_dashboard()

    def create_kpi_card(self, parent, title, value, color):
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=10)
        ctk.CTkLabel(card, text=title, font=("Kanit", 18, "bold"), text_color="white").pack(pady=(15, 5))
        lbl_value = ctk.CTkLabel(card, text=value, font=("Arial", 32, "bold"), text_color="white")
        lbl_value.pack(pady=(0, 15))
        card.lbl_value = lbl_value
        return card

    def update_dashboard(self):
        threading.Thread(target=self.run_dashboard_calc, daemon=True).start()

    def run_dashboard_calc(self):
        if not self.app_running: return
        try:
            records = self.sheet_sales.get_all_values()
            total_revenue = 0.0
            total_bills = set()
            daily_sales = defaultdict(float)
            product_sales = defaultdict(int)

            if len(records) > 1:
                for row in records[1:]:
                    if len(row) >= 7:
                        date_str = row[1].split(" ")[0] 
                        name = row[3]
                        rec_id = row[0]
                        total_str = row[6]
                        if total_str != "-" and total_str.strip() != "":
                            try:
                                amount = float(total_str.replace(",", ""))
                                total_revenue += amount
                                total_bills.add(rec_id)
                                daily_sales[date_str] += amount
                                product_sales[name] += 1
                            except: pass
            sorted_dates = sorted(daily_sales.keys())[-7:]
            y_sales = [daily_sales[d] for d in sorted_dates]
            sorted_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
            top_names = [p[0] for p in sorted_products]
            top_counts = [p[1] for p in sorted_products]

            if self.app_running and self.winfo_exists():
                self.after(0, self.draw_charts, total_revenue, len(total_bills), sorted_dates, y_sales, top_names, top_counts)
        except Exception as e:
            print(f"Dashboard Error: {e}")

    def draw_charts(self, total_revenue, total_bills, dates, sales, top_names, top_counts):
        if not self.app_running or not self.winfo_exists(): return
        try:
            self.card_sales.lbl_value.configure(text=f"{total_revenue:,.2f} บาท")
            self.card_txn.lbl_value.configure(text=f"{total_bills} บิล")
            for widget in self.graph_left.winfo_children(): widget.destroy()
            for widget in self.graph_right.winfo_children(): widget.destroy()

            fig1, ax1 = plt.subplots(figsize=(5, 4), dpi=100)
            ax1.plot(dates, sales, marker='o', linestyle='-', color='#3498DB', linewidth=2)
            ax1.set_title('ยอดขายรายวัน', fontsize=14)
            ax1.tick_params(axis='x', rotation=45)
            ax1.grid(True, linestyle='--', alpha=0.7)
            fig1.tight_layout()
            canvas1 = FigureCanvasTkAgg(fig1, master=self.graph_left)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill="both", expand=True)

            fig2, ax2 = plt.subplots(figsize=(5, 4), dpi=100)
            bars = ax2.bar(top_names, top_counts, color='#2CC985')
            ax2.set_title('5 อันดับสินค้าขายดี', fontsize=14)
            ax2.tick_params(axis='x', rotation=45)
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height, f'{int(height)}', ha='center', va='bottom')
            fig2.tight_layout()
            canvas2 = FigureCanvasTkAgg(fig2, master=self.graph_right)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="both", expand=True)
        except: pass

    # =========================================
    # TAB 5: AI & Social Media
    # =========================================
    def setup_ai_social_tab(self):
        """Setup tab สำหรับ AI content generation และ Social media posting"""
        # ใช้ Scrollable Frame สำหรับหน้านี้
        main_scroll = ctk.CTkScrollableFrame(self.tab_ai_social, fg_color="transparent")
        main_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top: Settings
        settings_frame = ctk.CTkFrame(main_scroll, fg_color="gray30", corner_radius=10)
        settings_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(settings_frame, text="⚙️ ตั้งค่า API", font=("Kanit", 16, "bold")).pack(pady=10, anchor="w", padx=10)
        
        # AI API Settings
        ai_frame = ctk.CTkFrame(settings_frame, fg_color="gray25", corner_radius=8)
        ai_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(ai_frame, text="AI Service:", font=("Kanit", 12)).pack(side="left", padx=10, pady=5)
        self.ai_api_type = ctk.CTkComboBox(ai_frame, values=["gemini", "offline"], 
                                           command=self.update_ai_config, width=150)
        self.ai_api_type.set(self.ai_config.get("ai_api_type", "gemini"))
        self.ai_api_type.pack(side="left", padx=5, pady=5)
        
        ctk.CTkLabel(ai_frame, text="API Key:", font=("Kanit", 12)).pack(side="left", padx=10, pady=5)
        self.ai_api_key_entry = ctk.CTkEntry(ai_frame, placeholder_text="Enter your API key", 
                                             show="*", width=300)
        self.ai_api_key_entry.pack(side="left", padx=5, pady=5)
        self.ai_api_key_entry.insert(0, self.ai_config.get("ai_api_key", ""))
        
        ctk.CTkButton(ai_frame, text="💾 บันทึก", command=self.save_ai_config, width=100, height=30).pack(side="left", padx=5, pady=5)
        
        # Facebook Settings
        fb_frame = ctk.CTkFrame(settings_frame, fg_color="gray25", corner_radius=8)
        fb_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(fb_frame, text="Facebook Access Token:", font=("Kanit", 12)).pack(side="left", padx=10, pady=5)
        self.fb_token_entry = ctk.CTkEntry(fb_frame, placeholder_text="Enter access token", 
                                           show="*", width=350)
        self.fb_token_entry.pack(side="left", padx=5, pady=5)
        self.fb_token_entry.insert(0, self.ai_config.get("facebook_access_token", ""))
        
        ctk.CTkLabel(fb_frame, text="Page ID:", font=("Kanit", 12)).pack(side="left", padx=10, pady=5)
        self.fb_page_id_entry = ctk.CTkEntry(fb_frame, placeholder_text="Page ID", width=150)
        self.fb_page_id_entry.pack(side="left", padx=5, pady=5)
        self.fb_page_id_entry.insert(0, self.ai_config.get("facebook_page_id", ""))
        
        ctk.CTkButton(fb_frame, text="💾 บันทึก", command=self.save_fb_config, width=100, height=30).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(fb_frame, text="🔗 Get Token", command=self.show_fb_token_help, width=100, height=30).pack(side="left", padx=5, pady=5)
        
        # Main content: Notebook-style tabs
        content_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        self.ai_tabview = ctk.CTkTabview(content_frame)
        self.ai_tabview.pack(fill="both", expand=True)
        
        # Tab 1: Generate Content
        tab_content = self.ai_tabview.add("📝 สร้างเนื้อหา")
        self.setup_content_generation_tab(tab_content)
        
        # Tab 2: Create Ad Images
        tab_ads = self.ai_tabview.add("🎨 สร้างรูปโฆษณา")
        self.setup_ad_creation_tab(tab_ads)
        
        # Tab 3: Post to Facebook
        tab_facebook = self.ai_tabview.add("📱 โพส Facebook")
        self.setup_facebook_posting_tab(tab_facebook)
    
    def setup_content_generation_tab(self, tab):
        """สำหรับสร้างเนื้อหา AI"""
        left_frame = ctk.CTkFrame(tab, fg_color="gray30", corner_radius=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(left_frame, text="📝 สร้างเนื้อหาสินค้า", font=("Kanit", 14, "bold")).pack(pady=10, anchor="w", padx=10)
        
        # สินค้า selection
        ctk.CTkLabel(left_frame, text="เลือกสินค้า:", font=("Kanit", 12)).pack(pady=5, anchor="w", padx=10)
        self.content_product_combo = ctk.CTkComboBox(left_frame, values=[], width=250, command=self.load_product_details_for_content)
        self.content_product_combo.pack(padx=10, pady=5, fill="x")
        self.load_product_list_for_ai()
        
        # Product details
        ctk.CTkLabel(left_frame, text="รายละเอียดสินค้า:", font=("Kanit", 11)).pack(pady=(10, 0), anchor="w", padx=10)
        self.content_details_text = ctk.CTkTextbox(left_frame, height=60, width=250)
        self.content_details_text.pack(padx=10, pady=5, fill="both", expand=False)
        
        # Prompt for content generation
        ctk.CTkLabel(left_frame, text="Prompt สำหรับสร้างเนื้อหา:", font=("Kanit", 11)).pack(pady=(10, 0), anchor="w", padx=10)
        self.content_prompt_text = ctk.CTkTextbox(left_frame, height=60, width=250)
        self.content_prompt_text.pack(padx=10, pady=5, fill="both", expand=False)
        
        # Style selection
        ctk.CTkLabel(left_frame, text="สไตล์การเขียน:", font=("Kanit", 12)).pack(pady=5, anchor="w", padx=10)
        self.content_style_combo = ctk.CTkComboBox(left_frame, values=["casual", "professional", "humorous", "emotional"], 
                                                   width=250, command=None)
        self.content_style_combo.set("casual")
        self.content_style_combo.pack(padx=10, pady=5, fill="x")
        
        # Generate button
        ctk.CTkButton(left_frame, text="🤖 สร้างเนื้อหา", command=self.generate_ai_content, 
                     height=40, font=("Kanit", 13), fg_color="#3498DB").pack(padx=10, pady=10, fill="x")
        
        # Output
        right_frame = ctk.CTkFrame(tab, fg_color="gray30", corner_radius=10)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(right_frame, text="📄 ผลลัพธ์", font=("Kanit", 14, "bold")).pack(pady=10, anchor="w", padx=10)
        
        self.content_result_text = ctk.CTkTextbox(right_frame, height=200, width=400)
        self.content_result_text.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Action buttons
        button_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(button_frame, text="📋 คัดลอก", command=self.copy_content, width=150, height=30).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="💾 บันทึก", command=self.save_content, width=150, height=30).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="🔄 สร้างใหม่", command=lambda: self.content_result_text.delete("1.0", "end"), width=150, height=30).pack(side="left", padx=5)
    
    def setup_ad_creation_tab(self, tab):
        """สำหรับสร้างรูปโฆษณา - เปิด Gemini Web"""
        left_frame = ctk.CTkFrame(tab, fg_color="gray30", corner_radius=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(left_frame, text="🎨 สร้างรูปโฆษณา", font=("Kanit", 14, "bold")).pack(pady=10, anchor="w", padx=10)
        
        # สินค้า selection
        ctk.CTkLabel(left_frame, text="เลือกสินค้า:", font=("Kanit", 12)).pack(pady=5, anchor="w", padx=10)
        self.ad_product_combo = ctk.CTkComboBox(left_frame, values=[], width=250, command=self.load_product_details_for_ad)
        self.ad_product_combo.pack(padx=10, pady=5, fill="x")
        self.load_product_list_for_ai()
        
        # รูปสินค้า
        ctk.CTkLabel(left_frame, text="เลือกรูปสินค้า:", font=("Kanit", 12)).pack(pady=(10, 0), anchor="w", padx=10)
        self.ad_image_label = ctk.CTkLabel(left_frame, text="ไม่มีรูป", height=100, fg_color="gray20")
        self.ad_image_label.pack(padx=10, pady=5, fill="x")
        
        ctk.CTkButton(left_frame, text="📁 เลือกรูป", command=self.choose_ad_image, 
                     height=30, width=250).pack(padx=10, pady=5)
        
        self.ad_image_path = ""
        
        # ราคา
        ctk.CTkLabel(left_frame, text="ราคา:", font=("Kanit", 12)).pack(pady=5, anchor="w", padx=10)
        self.ad_price_entry = ctk.CTkEntry(left_frame, placeholder_text="เช่น 299 บาท", width=250)
        self.ad_price_entry.pack(padx=10, pady=5, fill="x")
        
        # Prompt สำหรับ Gemini
        ctk.CTkLabel(left_frame, text="Prompt สำหรับ Gemini:", font=("Kanit", 12)).pack(pady=5, anchor="w", padx=10)
        self.ad_prompt_text = ctk.CTkTextbox(left_frame, height=80, width=250)
        self.ad_prompt_text.pack(padx=10, pady=5, fill="both", expand=False)
        self.ad_prompt_text.insert("1.0", "สร้างรูปโฆษณาสินค้า (ชื่อ: {product}, ราคา: {price}) ที่สวยงาม มีสไตล์สมัยใหม่ บนพื้นหลังที่น่าสนใจ")
        
        # Open Gemini button
        ctk.CTkButton(left_frame, text="🌐 เปิด Gemini Web", command=self.open_gemini_web, 
                     height=40, font=("Kanit", 13), fg_color="#4285F4").pack(padx=10, pady=10, fill="x")
        
        # บันทึกรูป manual
        ctk.CTkLabel(left_frame, text="หรือสร้างโดยเพิ่มข้อความลงรูป:", font=("Kanit", 12)).pack(pady=5, anchor="w", padx=10)
        
        ctk.CTkLabel(left_frame, text="คำอธิบาย:", font=("Kanit", 12)).pack(pady=5, anchor="w", padx=10)
        self.ad_description_text = ctk.CTkTextbox(left_frame, height=60, width=250)
        self.ad_description_text.pack(padx=10, pady=5, fill="both", expand=False)
        
        ctk.CTkButton(left_frame, text="🎨 เพิ่มข้อความบนรูป", command=self.create_simple_ad_manual, 
                     height=35, font=("Kanit", 12), fg_color="#E74C3C").pack(padx=10, pady=10, fill="x")
        
        # Preview
        right_frame = ctk.CTkFrame(tab, fg_color="gray30", corner_radius=10)

        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(right_frame, text="�️ ผลลัพธ์ / คำแนะนำ", font=("Kanit", 14, "bold")).pack(pady=10, anchor="w", padx=10)
        
        self.ad_preview_label = ctk.CTkLabel(right_frame, text="", fg_color="gray20")
        self.ad_preview_label.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Status
        self.ad_status_label = ctk.CTkLabel(right_frame, text="", font=("Kanit", 11), text_color="gray")
        self.ad_status_label.pack(pady=5, anchor="w", padx=10)
        
        # Action buttons
        button_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(button_frame, text="📁 เปิดโฟลเดอร์", command=self.open_ads_folder, width=150, height=30).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="📤 โพส FB", command=self.post_ad_to_facebook, width=150, height=30).pack(side="left", padx=5)
    
    def setup_facebook_posting_tab(self, tab):
        """สำหรับโพสต่อ Facebook"""
        left_frame = ctk.CTkFrame(tab, fg_color="gray30", corner_radius=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(left_frame, text="📱 โพสไป Facebook", font=("Kanit", 14, "bold")).pack(pady=10, anchor="w", padx=10)
        
        # Post type
        ctk.CTkLabel(left_frame, text="ประเภทโพส:", font=("Kanit", 12)).pack(pady=5, anchor="w", padx=10)
        self.fb_post_type = ctk.CTkComboBox(left_frame, values=["ข้อความ", "รูปภาพ", "ข้อความ + รูป"], 
                                            width=250, command=self.update_fb_post_type)
        self.fb_post_type.set("ข้อความ")
        self.fb_post_type.pack(padx=10, pady=5, fill="x")
        
        # Message
        ctk.CTkLabel(left_frame, text="ข้อความ:", font=("Kanit", 12)).pack(pady=5, anchor="w", padx=10)
        self.fb_message_text = ctk.CTkTextbox(left_frame, height=100, width=250)
        self.fb_message_text.pack(padx=10, pady=5, fill="both", expand=False)
        
        # Image selection (hidden initially)
        self.fb_image_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        self.fb_image_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.fb_image_frame, text="เลือกรูป:", font=("Kanit", 12)).pack(anchor="w", pady=5)
        ctk.CTkButton(self.fb_image_frame, text="📁 เลือกรูป", command=self.choose_fb_image, 
                     height=30).pack(fill="x", pady=5)
        self.fb_image_path = ""
        self.fb_image_label = ctk.CTkLabel(self.fb_image_frame, text="ไม่มีรูป", text_color="gray")
        self.fb_image_label.pack(anchor="w", pady=2)
        self.fb_image_frame.pack_forget()  # Hide initially
        
        # Post button
        ctk.CTkButton(left_frame, text="📤 โพสไป Facebook", command=self.post_to_facebook, 
                     height=40, font=("Kanit", 13), fg_color="#4267B2").pack(padx=10, pady=10, fill="x")
        
        # Response
        right_frame = ctk.CTkFrame(tab, fg_color="gray30", corner_radius=10)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(right_frame, text="✅ ผลลัพธ์", font=("Kanit", 14, "bold")).pack(pady=10, anchor="w", padx=10)
        
        self.fb_response_text = ctk.CTkTextbox(right_frame, height=300, width=400)
        self.fb_response_text.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Copy button
        ctk.CTkButton(right_frame, text="📋 คัดลอก Link", command=self.copy_post_link, 
                     height=30).pack(padx=10, pady=5, fill="x")
    
    def load_product_list_for_ai(self):
        """โหลดรายการสินค้าสำหรับ AI"""
        if not self.all_inventory_data:
            self.load_inventory_data()
        
        # แสดงชื่อสินค้า (Barcode) - row[2] คือชื่อสินค้า, row[1] คือ Barcode
        product_list = [f"{row[2]} ({row[1]})" for idx, row in self.all_inventory_data if len(row) > 2]
        
        if hasattr(self, 'content_product_combo'):
            self.content_product_combo.configure(values=product_list)
        if hasattr(self, 'ad_product_combo'):
            self.ad_product_combo.configure(values=product_list)
    
    def load_product_details_for_content(self, choice):
        """โหลดรายละเอียดสินค้าสำหรับสร้างเนื้อหา"""
        if not choice or not self.all_inventory_data:
            return
        
        for idx, row in self.all_inventory_data:
            if f"{row[2]} ({row[1]})" == choice:
                # แสดงชื่อ: Product name, รายละเอียด: Detail, ราคา: Price บาท
                product_name = row[2] if len(row) > 2 else ""
                detail = row[4] if len(row) > 4 else ""
                price = row[5] if len(row) > 5 else "0"
                
                details_text = f"ชื่อ: {product_name}\nรายละเอียด: {detail}\nราคา: {price} บาท"
                self.content_details_text.delete("1.0", "end")
                self.content_details_text.insert("1.0", details_text)
                
                # สร้าง prompt อัตโนมัติ
                auto_prompt = f"สร้างคำอธิบายสินค้า '{product_name}' (ราคา {price} บาท, รายละเอียด: {detail}) ให้น่าสนใจและมีศักยภาพในการขาย สร้างเป็นข้อความที่เหมาะสำหรับโพสต่อ Social Media"
                self.content_prompt_text.delete("1.0", "end")
                self.content_prompt_text.insert("1.0", auto_prompt)
                break
    
    def load_product_details_for_ad(self, choice):
        """โหลดรายละเอียดสินค้าสำหรับสร้างรูปโฆษณา"""
        if not choice or not self.all_inventory_data:
            return
        
        for idx, row in self.all_inventory_data:
            if f"{row[2]} ({row[1]})" == choice:
                product_name = row[2] if len(row) > 2 else ""
                price = row[5] if len(row) > 5 else "0"
                detail = row[3] if len(row) > 4 else ""
                
                # แสดงราคา
                self.ad_price_entry.delete(0, "end")
                self.ad_price_entry.insert(0, f"{price} บาท")
                
                # สร้าง prompt อัตโนมัติสำหรับการทำรูปโฆษณา
                auto_prompt = f"สร้างรูปโฆษณาสินค้า (ชื่อ: {product_name}, ราคา: {price} บาท, รายละเอียด: {detail}) ที่สวยงาม มีสไตล์สมัยใหม่ บนพื้นหลังที่น่าสนใจ และดึงดูดใจ"
                self.ad_prompt_text.delete("1.0", "end")
                self.ad_prompt_text.insert("1.0", auto_prompt)
                
                # ตัวอักษร description
                self.ad_description_text.delete("1.0", "end")
                self.ad_description_text.insert("1.0", f"{product_name} - {price} บาท")
                break
    
    def generate_ai_content(self):
        """สร้างเนื้อหา AI"""
        if not self.content_product_combo.get():
            messagebox.showwarning("ขาดข้อมูล", "กรุณาเลือกสินค้า")
            return
        
        product_name = self.content_product_combo.get().split("(")[0].strip()
        style = self.content_style_combo.get()
        
        self.content_result_text.delete("1.0", "end")
        self.content_result_text.insert("1.0", "🔄 กำลังสร้างเนื้อหา...\n")
        self.update_idletasks()
        
        # Run in thread to prevent UI freeze
        thread = threading.Thread(target=self._generate_content_thread, args=(product_name, style))
        thread.daemon = True
        thread.start()
    
    def _generate_content_thread(self, product_name, style):
        """Generate content in background thread"""
        try:
            # ดึงข้อมูลสินค้า
            product_details = {}
            if self.all_inventory_data:
                for idx, row in self.all_inventory_data:
                    if f"{row[2]}" == product_name or f"{row[2]} ({row[1]})" == product_name:
                        product_details = {
                            'name': row[2] if len(row) > 2 else "",
                            'barcode': row[1] if len(row) > 1 else "",
                            'category': row[3] if len(row) > 3 else "",
                            'detail': row[4] if len(row) > 4 else "",
                            'price': row[5] if len(row) > 5 else "0",
                        }
                        break
            
            # สร้างเนื้อหา AI
            content = self.ai_content_gen.generate_product_description(
                product_name, 
                style=style,
                features=None
            )
            
            # สร้างเนื้อหา Facebook caption
            fb_caption = self.ai_content_gen.generate_facebook_caption(
                product_details.get('name', product_name),
                product_details.get('price', '0'),
                product_details.get('detail', '')
            )
            
            # รวมข้อมูลทั้งหมด
            if self.app_running and self.winfo_exists():
                result_text = f"""📦 ข้อมูลสินค้า
{'='*50}
ชื่อสินค้า: {product_details.get('name', product_name)}
Barcode: {product_details.get('barcode', '-')}
ประเภท: {product_details.get('category', '-')}
ราคา: {product_details.get('price', '-')} บาท
รายละเอียด: {product_details.get('detail', '-')}

📝 รายละเอียดสินค้า (สไตล์ {style})
{'='*50}
{content}

💬 Facebook Caption
{'='*50}
{fb_caption}

💡 เคล็ดลับ:
- ใช้รายละเอียดสินค้าเพื่อสร้างเนื้อหาโพสต่างๆ
- ใช้ Facebook Caption สำหรับโพสใน Facebook
- คัดลอกเนื้อหาด้านบนเพื่อนำไปโพส
"""
                self.content_result_text.delete("1.0", "end")
                self.content_result_text.insert("1.0", result_text)
        except Exception as e:
            if self.app_running and self.winfo_exists():
                self.content_result_text.delete("1.0", "end")
                self.content_result_text.insert("1.0", f"❌ เกิดข้อผิดพลาด:\n{str(e)}")
    
    def copy_content(self):
        """คัดลอกเนื้อหา"""
        content = self.content_result_text.get("1.0", "end").strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)
            messagebox.showinfo("สำเร็จ", "คัดลอกเนื้อหาแล้ว")
    
    def save_content(self):
        """บันทึกเนื้อหา"""
        content = self.content_result_text.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("ขาดข้อมูล", "ไม่มีเนื้อหาที่จะบันทึก")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"content_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            messagebox.showinfo("สำเร็จ", f"บันทึกไฟล์: {filename}")
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"บันทึกไม่สำเร็จ: {str(e)}")
    
    def choose_ad_image(self):
        """เลือกรูปสำหรับโฆษณา"""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            self.ad_image_path = file_path
            self.ad_image_label.configure(text=f"📁 {os.path.basename(file_path)}")
            
            # Show preview
            try:
                img = Image.open(file_path)
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                self.ad_image_label.configure(image=photo, text="")
                self.ad_image_label.image = photo
            except:
                pass
    
    def open_gemini_web(self):
        """เปิด Gemini Web ในเบราว์เซอร์"""
        import webbrowser
        
        product_name = self.ad_product_combo.get().split("(")[0].strip() if self.ad_product_combo.get() else "สินค้า"
        price = self.ad_price_entry.get()
        prompt = self.ad_prompt_text.get("1.0", "end").strip()
        
        # แทนที่ placeholder ในข้อความ
        full_prompt = prompt.format(product=product_name, price=price)
        
        # URL สำหรับ Gemini
        gemini_url = "https://gemini.google.com/"
        
        # เปิด Gemini Web
        webbrowser.open(gemini_url)
        
        messagebox.showinfo("เปิด Gemini", 
f"""✅ เปิด Gemini Web แล้ว

ป้อน Prompt นี้ใน Gemini:

{full_prompt}

หลังจากสร้างรูป:
1. Download รูปจาก Gemini
2. นำมาใส่ในโฟลเดอร์ ads_output/
3. โพสไป Facebook ได้เลย!""")
    
    def create_simple_ad_manual(self):
        """สร้างรูปโฆษณาแบบง่าย (เพิ่มข้อความบนรูป)"""
        if not self.ad_image_path:
            messagebox.showwarning("ขาดข้อมูล", "กรุณาเลือกรูปสินค้า")
            return
        
        product_name = self.ad_product_combo.get().split("(")[0].strip() if self.ad_product_combo.get() else "สินค้า"
        price = self.ad_price_entry.get()
        description = self.ad_description_text.get("1.0", "end").strip()
        
        if not price:
            messagebox.showwarning("ขาดข้อมูล", "กรุณากรอกราคา")
            return
        
        # สร้างข้อมูลที่จะคัดลอกไป clipboard
        product_info = f"สินค้า: {product_name}\nราคา: {price}\nคำอธิบาย: {prompt}"
        
        self.clipboard_clear()
        self.clipboard_append(product_info)
        self.update_idletasks()
        
        # เปิดเว็บตามประเภท
        import webbrowser
        
        try:
            if tool_type == "canva":
                webbrowser.open("https://www.canva.com/create/social-media-graphics/")
                messagebox.showinfo("Canva เปิดแล้ว", f"ข้อมูลสินค้า:\n\n{product_info}\n\n(ได้คัดลอกไปยัง clipboard)")
            elif tool_type == "adobe":
                webbrowser.open("https://www.adobe.com/express/create/social-media")
                messagebox.showinfo("Adobe Express เปิดแล้ว", f"ข้อมูลสินค้า:\n\n{product_info}\n\n(ได้คัดลอกไปยัง clipboard)")
            elif tool_type == "dreamstudio":
                webbrowser.open("https://www.dreamstudio.ai/")
                messagebox.showinfo("DreamStudio เปิดแล้ว", f"ข้อมูลสินค้า:\n\n{product_info}\n\n(ได้คัดลอกไปยัง clipboard)")
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดเว็บได้: {str(e)}")
    
    def update_ad_creation_mode(self, mode):
        """อัพเดตโหมดสร้างรูป"""
        if mode == "AI จากรูป":
            self.ad_image_label.configure(text="📁 เลือกรูป")
            # Show image frame and prompt
            self.ad_ai_prompt_frame.pack(fill="x", padx=10, pady=5)
            self.ad_description_frame.pack_forget()
        elif mode == "AI สร้างใหม่":
            self.ad_image_label.configure(text="(ไม่จำเป็น)")
            # Show prompt only
            self.ad_ai_prompt_frame.pack(fill="x", padx=10, pady=5)
            self.ad_description_frame.pack_forget()
        else:  # แบบง่าย
            self.ad_image_label.configure(text="📁 เลือกรูป")
            # Show description
            self.ad_ai_prompt_frame.pack_forget()
            self.ad_description_frame.pack(fill="x", padx=10, pady=5)
    
    def create_advertisement(self):
        """สร้างรูปโฆษณา"""
        mode = self.ad_create_type.get()
        product_name = self.ad_product_combo.get().split("(")[0].strip() if self.ad_product_combo.get() else "สินค้า"
        price = self.ad_price_entry.get()
        
        if not price:
            messagebox.showwarning("ขาดข้อมูล", "กรุณากรอกราคา")
            return
        
        if mode == "แบบง่าย" and not self.ad_image_path:
            messagebox.showwarning("ขาดข้อมูล", "กรุณาเลือกรูปสินค้า")
            return
        
        self.ad_status_label.configure(text="🔄 กำลังสร้าง...", text_color="gray")
        self.update_idletasks()
        
        if mode == "AI จากรูป":
            thread = threading.Thread(target=self._create_ai_enhanced_ad_thread, args=(product_name, price))
        elif mode == "AI สร้างใหม่":
            thread = threading.Thread(target=self._create_ai_generated_ad_thread, args=(product_name, price))
        else:  # แบบง่าย
            description = self.ad_description_text.get("1.0", "end").strip()
            thread = threading.Thread(target=self._create_simple_ad_thread, args=(self.ad_image_path, product_name, price, description))
        
        thread.daemon = True
        thread.start()
    
    def _create_simple_ad_thread(self, image_path, product_name, price, description):
        """Create simple ad image in background thread"""
        try:
            success, output_path = self.ad_creator.create_simple_ad(
                image_path, product_name, price, description
            )
            
            if success and self.app_running and self.winfo_exists():
                # Show preview
                try:
                    img = Image.open(output_path)
                    img.thumbnail((400, 400))
                    photo = ImageTk.PhotoImage(img)
                    self.ad_preview_label.configure(image=photo)
                    self.ad_preview_label.image = photo
                except:
                    pass
                
                self.ad_status_label.configure(text=f"✅ บันทึก: {os.path.basename(output_path)}", text_color="green")
                self.current_ad_path = output_path
            else:
                self.ad_status_label.configure(text=f"❌ {output_path}", text_color="red")
        except Exception as e:
            if self.app_running and self.winfo_exists():
                self.ad_status_label.configure(text=f"❌ Error: {str(e)}", text_color="red")
    
    def open_ads_folder(self):
        """เปิดโฟลเดอร์รูปโฆษณา"""
        try:
            import subprocess
            ads_dir = os.path.abspath("ads_output")
            os.makedirs(ads_dir, exist_ok=True)
            subprocess.Popen(f'explorer "{ads_dir}"')
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดโฟลเดอร์: {str(e)}")
    
    def post_ad_to_facebook(self):
        """โพสรูปโฆษณาไป Facebook"""
        if not hasattr(self, 'current_ad_path') or not self.current_ad_path:
            messagebox.showwarning("ขาดข้อมูล", "กรุณาสร้างรูปโฆษณาก่อน")
            return
        
        self.fb_message_text.delete("1.0", "end")
        self.fb_message_text.insert("1.0", f"🛍️ สินค้าใหม่: {self.ad_product_combo.get()}\n💰 ราคา: {self.ad_price_entry.get()}")
        self.fb_post_type.set("ข้อความ + รูป")
        self.fb_image_path = self.current_ad_path
        self.fb_image_label.configure(text=f"📁 {os.path.basename(self.current_ad_path)}")
        
        # Switch to Facebook posting tab
        self.ai_tabview.set("📱 โพส Facebook")
    
    def choose_fb_image(self):
        """เลือกรูปสำหรับโพส Facebook"""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            self.fb_image_path = file_path
            self.fb_image_label.configure(text=f"✅ {os.path.basename(file_path)}", text_color="green")
    
    def update_fb_post_type(self, choice):
        """อัปเดต FB post type"""
        if choice in ["รูปภาพ", "ข้อความ + รูป"]:
            self.fb_image_frame.pack(fill="x", padx=10, pady=5)
        else:
            self.fb_image_frame.pack_forget()
    
    def post_to_facebook(self):
        """โพสไป Facebook"""
        if not self.facebook_api.access_token or not self.facebook_api.page_id:
            messagebox.showerror("ข้อผิดพลาด", "กรุณากำหนด Facebook Access Token และ Page ID ก่อน")
            return
        
        message = self.fb_message_text.get("1.0", "end").strip()
        post_type = self.fb_post_type.get()
        
        if not message and post_type in ["ข้อความ", "ข้อความ + รูป"]:
            messagebox.showwarning("ขาดข้อมูล", "กรุณากรอกข้อความ")
            return
        
        self.fb_response_text.delete("1.0", "end")
        self.fb_response_text.insert("1.0", "🔄 กำลังโพส...\n")
        self.update_idletasks()
        
        thread = threading.Thread(target=self._post_to_fb_thread, args=(message, post_type))
        thread.daemon = True
        thread.start()
    
    def _post_to_fb_thread(self, message, post_type):
        """Post to Facebook in background thread"""
        try:
            self.facebook_api.access_token = self.fb_token_entry.get()
            self.facebook_api.page_id = self.fb_page_id_entry.get()
            
            if post_type == "ข้อความ":
                success, response = self.facebook_api.post_text(message)
            elif post_type == "รูปภาพ":
                success, response = self.facebook_api.post_photo(self.fb_image_path)
            else:  # ข้อความ + รูป
                success, response = self.facebook_api.post_photo(self.fb_image_path, message)
            
            if self.app_running and self.winfo_exists():
                self.fb_response_text.delete("1.0", "end")
                if success:
                    self.fb_response_text.insert("1.0", f"✅ โพสสำเร็จ!\n\nResponse:\n{str(response)}")
                    self.play_sound("success")
                else:
                    self.fb_response_text.insert("1.0", f"❌ โพสไม่สำเร็จ!\n\nError:\n{str(response)}")
                    self.play_sound("error")
        except Exception as e:
            if self.app_running and self.winfo_exists():
                self.fb_response_text.delete("1.0", "end")
                self.fb_response_text.insert("1.0", f"❌ เกิดข้อผิดพลาด:\n{str(e)}")
    
    def copy_post_link(self):
        """คัดลอก Post Link"""
        content = self.fb_response_text.get("1.0", "end").strip()
        if "id" in content:
            self.clipboard_clear()
            self.clipboard_append(content)
            messagebox.showinfo("สำเร็จ", "คัดลอก response แล้ว")
    
    def update_ai_config(self, choice):
        """อัปเดต AI config"""
        pass
    
    def save_ai_config(self):
        """บันทึกการตั้งค่า AI"""
        self.ai_config["ai_api_type"] = self.ai_api_type.get()
        self.ai_config["ai_api_key"] = self.ai_api_key_entry.get()
        
        save_config(self.ai_config)
        
        self.ai_content_gen = AIContentGenerator(
            api_key=self.ai_config.get("ai_api_key", ""),
            api_type=self.ai_config.get("ai_api_type", "openai")
        )
        
        messagebox.showinfo("สำเร็จ", "บันทึกการตั้งค่า AI แล้ว")
    
    def save_fb_config(self):
        """บันทึกการตั้งค่า Facebook"""
        self.ai_config["facebook_access_token"] = self.fb_token_entry.get()
        self.ai_config["facebook_page_id"] = self.fb_page_id_entry.get()
        
        save_config(self.ai_config)
        
        self.facebook_api = FacebookIntegration(
            access_token=self.ai_config.get("facebook_access_token", ""),
            page_id=self.ai_config.get("facebook_page_id", "")
        )
        
        messagebox.showinfo("สำเร็จ", "บันทึกการตั้งค่า Facebook แล้ว")
    
    def show_fb_token_help(self):
        """แสดงวิธีการหา Facebook Token"""
        messagebox.showinfo("Facebook Token ยาก", 
f"""ขั้นตอนการขอ Facebook Access Token:

1. ไปที่ https://developers.facebook.com
2. สร้าง App ใหม่ (เลือก Page Engagement)
3. ไปที่ Tab 'Messenger' และตั้งค่า
4. ไปที่ Messenger Tools > Token Generator
5. เลือก Page ของคุณ และ copy access token
6. นำ token มาวาง ที่นี่

หรือเร็วกว่า:
https://developers.facebook.com/tools/explorer/
""")

    def play_sound(self, status):
        try:
            if status == "success": winsound.Beep(2000, 150)
            elif status == "error": winsound.Beep(500, 500)
        except: pass

if __name__ == "__main__":
    app = StockManagerApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.destroy()