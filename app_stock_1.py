import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk
import gspread
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from datetime import datetime, timedelta
import threading
import winsound
from PIL import Image, ImageTk
import io

# --- ส่วนที่เพิ่มมาสำหรับกราฟ ---
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict
import matplotlib

# ตั้งค่าฟอนต์ภาษาไทยให้ Matplotlib (ถ้าไม่มี Tahoma อาจต้องเปลี่ยนเป็น Kanit หรือติดตั้งฟอนต์ไทย)
matplotlib.rc('font', family='Tahoma') 

# --- ตั้งค่า ---
# 🔴 ID โฟลเดอร์ใน Google Drive (ใส่ของตัวเอง)
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
        self.title("ระบบบริหารสต็อก V.9 (Dashboard Added)")
        self.geometry("1200x850") # ขยายจออีกนิดเพื่อกราฟ

        self.all_inventory_data = [] 

        # Authentication
        self.creds = self.authenticate()
        self.gc = gspread.authorize(self.creds)
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        
        try:
            self.sh = self.gc.open("StockDB")
            self.sheet_products = self.sh.worksheet("Products")
            
            try:
                self.sheet_stock = self.sh.worksheet("Stock")
            except:
                self.sheet_stock = self.sh.sheet1
                print("Warning: ไม่พบชีท 'Stock' ระบบจะบันทึกลง Sheet1 แทน")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"{e}")
            self.destroy()
            return

        self.create_layout()

    def authenticate(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds

    def create_layout(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview._segmented_button.configure(font=("Kanit", 16, "bold"))
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_pos = self.tabview.add("หน้าขาย (POS)")
        self.tab_inventory = self.tabview.add("คลังสินค้า (Inventory)")
        self.tab_dashboard = self.tabview.add("ภาพรวม (Dashboard)") # ✅ เพิ่ม Tab ใหม่

        self.setup_pos_tab()
        self.setup_inventory_tab()
        self.setup_dashboard_tab() # ✅ เรียกฟังก์ชันสร้าง Dashboard

    # =========================================
    # TAB 1: POS Logic
    # =========================================
    def setup_pos_tab(self):
        frame = ctk.CTkFrame(self.tab_pos)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="📦 บันทึกรายการประจำวัน", font=("Kanit", 28, "bold")).pack(pady=15)

        self.mode_var = ctk.StringVar(value="IN")
        self.seg_button = ctk.CTkSegmentedButton(frame, values=["   รับเข้า (IN)   ", "   ขายออก (OUT)   "],
                                                 variable=self.mode_var, command=self.change_mode_color,
                                                 font=("Kanit", 16, "bold"), height=40)
        self.seg_button.pack(pady=10)

        self.entry_barcode = self.create_styled_entry(frame, "Scan Barcode...", "BARCODE")
        self.entry_barcode.bind('<Return>', self.pos_scan_barcode)
        
        self.entry_name = self.create_styled_entry(frame, "ชื่อสินค้า...", "NAME")
        self.entry_qty = self.create_styled_entry(frame, "จำนวน...", "QTY")
        self.entry_price = self.create_styled_entry(frame, "ราคา...", "PRICE")
        self.entry_price.bind('<Return>', self.save_transaction)

        self.btn_save = ctk.CTkButton(frame, text="บันทึกรับเข้า (+)", command=self.save_transaction,
                                      height=60, font=("Kanit", 20, "bold"), 
                                      fg_color="#2CC985", hover_color="#229A65")
        self.btn_save.pack(pady=20, fill="x")
        
        self.pos_status = ctk.CTkLabel(frame, text="", text_color="orange", font=("Kanit", 16))
        self.pos_status.pack()

    def create_styled_entry(self, parent, ph, suffix):
        container = ctk.CTkFrame(parent, height=50, fg_color=("gray95", "gray25")) 
        container.pack(pady=8, fill="x")
        ctk.CTkLabel(container, text=suffix, width=80, font=("Kanit", 12, "bold")).pack(side="right", padx=10)
        entry = ctk.CTkEntry(container, placeholder_text=ph, height=50, font=("Kanit", 18), 
                             border_width=0, fg_color="transparent")
        entry.pack(side="left", fill="both", expand=True, padx=10)
        return entry

    def change_mode_color(self, value):
        if "IN" in value:
            self.btn_save.configure(fg_color="#2CC985", text="บันทึกรับเข้า (+)")
        else:
            self.btn_save.configure(fg_color="#FF474C", text="บันทึกขายออก (-)")

    def pos_scan_barcode(self, event=None):
        code = self.entry_barcode.get().strip()
        if not code: return
        self.pos_status.configure(text="🔍 Searching...")
        threading.Thread(target=self.run_pos_search, args=(code,)).start()

    def run_pos_search(self, barcode):
        try:
            rows = self.sheet_products.get_all_values()
            found_row = None
            for row in rows[1:]:
                if len(row) > 1 and str(row[1]).strip() == str(barcode):
                    found_row = row
                    break
            self.after(0, self.update_pos_ui, found_row)
        except Exception as e:
            print(e)

    def update_pos_ui(self, row_data):
        self.pos_status.configure(text="")
        if row_data:
            self.play_sound("success")
            self.entry_name.delete(0, "end"); self.entry_name.insert(0, row_data[2])
            price = row_data[5] if len(row_data) > 5 else "0"
            self.entry_price.delete(0, "end"); self.entry_price.insert(0, price)
            self.entry_qty.focus()
        else:
            self.play_sound("error")
            self.entry_name.focus()

    def save_transaction(self, event=None):
        barcode = self.entry_barcode.get()
        name = self.entry_name.get()
        qty = self.entry_qty.get()
        price = self.entry_price.get()

        if not barcode or not name or not qty or not price:
            messagebox.showwarning("แจ้งเตือน", "กรุณากรอกข้อมูลให้ครบ")
            return
        try:
            qty_val = int(qty)
            price_val = float(price)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_mode = self.mode_var.get()
            
            total_sales = "-"
            if "OUT" in current_mode:
                real_qty = -abs(qty_val)
                total_sales = abs(qty_val) * price_val
            else:
                real_qty = abs(qty_val)

            row = [timestamp, barcode, name, real_qty, price_val, total_sales]
            self.sheet_stock.append_row(row)
            
            self.play_sound("success")
            self.entry_barcode.delete(0, "end"); self.entry_name.delete(0, "end")
            self.entry_qty.delete(0, "end"); self.entry_price.delete(0, "end")
            self.entry_barcode.focus()
            
            msg = f"✅ บันทึก '{name}' ({real_qty})"
            if total_sales != "-": msg += f" | ยอดขาย {total_sales:,.2f} บาท"
            self.pos_status.configure(text=msg, text_color="green")
            
        except ValueError:
            messagebox.showerror("Error", "จำนวนและราคาต้องเป็นตัวเลข")
        except Exception as e:
            self.play_sound("error")
            messagebox.showerror("Error", f"บันทึกไม่สำเร็จ: {e}")

    # =========================================
    # TAB 2: INVENTORY Logic
    # =========================================
    def setup_inventory_tab(self):
        paned = ctk.CTkFrame(self.tab_inventory)
        paned.pack(fill="both", expand=True)

        frame_list = ctk.CTkFrame(paned, width=600)
        frame_list.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        frame_search = ctk.CTkFrame(frame_list, fg_color="transparent")
        frame_search.pack(fill="x", pady=(0, 5))

        self.entry_search = ctk.CTkEntry(frame_search, placeholder_text="🔍 ค้นหา...", font=("Kanit", 16), height=40)
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry_search.bind("<Return>", self.search_inventory)

        btn_search = ctk.CTkButton(frame_search, text="ค้นหา", width=80, height=40, font=("Kanit", 14), 
                                   command=self.search_inventory, fg_color="#3498DB")
        btn_search.pack(side="left", padx=2)
        btn_reset_search = ctk.CTkButton(frame_search, text="❌", width=40, height=40, 
                                         command=self.reset_search, fg_color="gray")
        btn_reset_search.pack(side="left")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Kanit", 16, "bold"), rowheight=40)
        style.configure("Treeview", font=("Kanit", 14), rowheight=35)

        columns = ("ID", "Barcode", "Name", "Detail", "Cost", "Price", "ImageID")
        self.tree = ttk.Treeview(frame_list, columns=columns, show="headings")
        
        self.tree.heading("ID", text="ID"); self.tree.column("ID", width=50, anchor="center")
        self.tree.heading("Barcode", text="Barcode"); self.tree.column("Barcode", width=120, anchor="center")
        self.tree.heading("Name", text="Name"); self.tree.column("Name", width=200, anchor="center")
        self.tree.heading("Detail", text="Detail"); self.tree.column("Detail", width=100, anchor="center")
        self.tree.heading("Cost", text="Cost"); self.tree.column("Cost", width=80, anchor="center")
        self.tree.heading("Price", text="Price"); self.tree.column("Price", width=80, anchor="center")
        self.tree.column("ImageID", width=0, stretch=False) 
        
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_product_select)

        frame_btns = ctk.CTkFrame(frame_list, fg_color="transparent")
        frame_btns.pack(fill="x", pady=5)
        
        btn_refresh = ctk.CTkButton(frame_btns, text="🔄 รีเฟรช", command=self.load_inventory_data, 
                                    width=140, height=45, font=("Kanit", 16))
        btn_refresh.pack(side="left", padx=5, expand=True)

        btn_add = ctk.CTkButton(frame_btns, text="➕ เพิ่มสินค้าใหม่", command=self.open_add_product_window, 
                                fg_color="#F39C12", hover_color="#D68910", width=160, height=45, font=("Kanit", 16, "bold"))
        btn_add.pack(side="left", padx=5, expand=True)

        frame_detail = ctk.CTkFrame(paned, width=400)
        frame_detail.pack(side="right", fill="y", padx=5, pady=5)

        ctk.CTkLabel(frame_detail, text="ข้อมูลสินค้า", font=("Kanit", 24, "bold")).pack(pady=15)

        self.image_label = ctk.CTkLabel(frame_detail, text="[No Image]", width=250, height=250, fg_color="gray30")
        self.image_label.pack(pady=10)
        
        self.btn_upload = ctk.CTkButton(frame_detail, text="📤 อัปเดตรูปภาพ", command=self.upload_image_for_selected, 
                                        state="disabled", height=40, font=("Kanit", 14))
        self.btn_upload.pack(pady=5)

        self.lbl_info_id = ctk.CTkLabel(frame_detail, text="ID: -", text_color="gray", font=("Kanit", 14))
        self.lbl_info_id.pack()
        
        self.lbl_info_name = ctk.CTkLabel(frame_detail, text="-", font=("Kanit", 22, "bold"), wraplength=380)
        self.lbl_info_name.pack(pady=10)

        ctk.CTkLabel(frame_detail, text="รายละเอียด:", anchor="w", font=("Kanit", 16, "bold")).pack(fill="x", padx=20)
        self.txt_detail = ctk.CTkTextbox(frame_detail, height=120, corner_radius=10, font=("Kanit", 16))
        self.txt_detail.pack(fill="x", padx=20, pady=5)
        self.txt_detail.configure(state="disabled")

        frame_price = ctk.CTkFrame(frame_detail, fg_color="transparent")
        frame_price.pack(pady=20)
        self.lbl_info_cost = ctk.CTkLabel(frame_price, text="ทุน: -", font=("Kanit", 18))
        self.lbl_info_cost.pack(side="left", padx=15)
        self.lbl_info_price = ctk.CTkLabel(frame_price, text="ขาย: -", font=("Kanit", 24, "bold"), text_color="#2CC985")
        self.lbl_info_price.pack(side="left", padx=15)
        
        self.selected_product_row = None 
        self.load_inventory_data()

    def load_inventory_data(self):
        try:
            records = self.sheet_products.get_all_values()
            if len(records) > 1:
                self.all_inventory_data = []
                for idx, row in enumerate(records[1:], start=2):
                    safe_row = (row + [""] * 7)[:7]
                    self.all_inventory_data.append((str(idx), safe_row))
                self.update_inventory_table(self.all_inventory_data)
        except Exception as e:
            print(f"Load Error: {e}")

    def update_inventory_table(self, data_list):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for row_index, row_values in data_list:
            self.tree.insert("", "end", values=row_values, tags=(row_index,))

    def search_inventory(self, event=None):
        query = self.entry_search.get().strip().lower()
        if not query:
            self.update_inventory_table(self.all_inventory_data)
            return
        filtered_data = []
        for row_index, row_values in self.all_inventory_data:
            barcode = str(row_values[1]).lower()
            name = str(row_values[2]).lower()
            detail = str(row_values[3]).lower()
            if query in barcode or query in name or query in detail:
                filtered_data.append((row_index, row_values))
        self.update_inventory_table(filtered_data)

    def reset_search(self):
        self.entry_search.delete(0, "end")
        self.update_inventory_table(self.all_inventory_data)

    def on_product_select(self, event):
        selected_item = self.tree.selection()
        if not selected_item: return

        item_values = self.tree.item(selected_item)['values']
        row_index = self.tree.item(selected_item, "tags")[0]
        self.selected_product_row = row_index
        
        safe_values = list(item_values)
        while len(safe_values) < 7:
            safe_values.append("")
            
        self.lbl_info_id.configure(text=f"ID: {safe_values[0]}")
        self.lbl_info_name.configure(text=f"{safe_values[2]}")
        
        self.txt_detail.configure(state="normal")
        self.txt_detail.delete("0.0", "end")
        self.txt_detail.insert("0.0", str(safe_values[3]))
        self.txt_detail.configure(state="disabled")
        
        self.lbl_info_cost.configure(text=f"ทุน: {safe_values[4]}")
        self.lbl_info_price.configure(text=f"ขาย: {safe_values[5]}")
        
        self.btn_upload.configure(state="normal")
        image_id = str(safe_values[6]).strip()
        self.display_image(image_id)

    def display_image(self, file_id):
        if not file_id or file_id == "None" or file_id == "":
            self.image_label.configure(image=None, text="[No Image]")
            return
        self.image_label.configure(text="Loading...", image=None)
        threading.Thread(target=self.download_and_show_image, args=(file_id,)).start()

    def download_and_show_image(self, file_id):
        try:
            request = self.drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            fh.seek(0)
            
            temp_img = Image.open(fh)
            temp_img.load()
            pil_image = temp_img.copy()
            pil_image = pil_image.resize((250, 250), Image.Resampling.LANCZOS)
            
            fh.close()
            temp_img.close()
            self.after(0, self.update_image_ui, pil_image)
        except Exception as e:
            print(f"Image Error: {e}")
            self.after(0, lambda: self.image_label.configure(image=None, text="Error loading image"))

    def update_image_ui(self, pil_image):
        ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(250, 250))
        try:
            self.image_label.configure(image=ctk_image, text="")
            self.current_image_ref = ctk_image
        except Exception as e:
            print(f"Error displaying image: {e}")

    # =========================================
    # TAB 3: DASHBOARD (ส่วนที่เพิ่มใหม่)
    # =========================================
    def setup_dashboard_tab(self):
        self.dash_frame = ctk.CTkFrame(self.tab_dashboard, fg_color="transparent")
        self.dash_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- ส่วนหัว: สรุปตัวเลข (KPI Cards) ---
        kpi_frame = ctk.CTkFrame(self.dash_frame, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=10)

        # Card 1: ยอดขายรวม
        self.card_sales = self.create_kpi_card(kpi_frame, "ยอดขายรวม", "0.00 บาท", "#3498DB")
        self.card_sales.pack(side="left", fill="x", expand=True, padx=10)

        # Card 2: จำนวนรายการขาย
        self.card_txn = self.create_kpi_card(kpi_frame, "จำนวนบิลที่ขาย", "0 บิล", "#E67E22")
        self.card_txn.pack(side="left", fill="x", expand=True, padx=10)

        # ปุ่มรีเฟรช
        btn_refresh = ctk.CTkButton(self.dash_frame, text="🔄 รีเฟรชข้อมูล", command=self.update_dashboard,
                                    font=("Kanit", 16), height=40)
        btn_refresh.pack(pady=10)

        # --- ส่วนกราฟ: แบ่งซ้ายขวา ---
        graph_frame = ctk.CTkFrame(self.dash_frame, fg_color="transparent")
        graph_frame.pack(fill="both", expand=True, pady=10)

        # Frame สำหรับกราฟ 1 (ซ้าย)
        self.graph_left = ctk.CTkFrame(graph_frame)
        self.graph_left.pack(side="left", fill="both", expand=True, padx=5)

        # Frame สำหรับกราฟ 2 (ขวา)
        self.graph_right = ctk.CTkFrame(graph_frame)
        self.graph_right.pack(side="right", fill="both", expand=True, padx=5)

        # โหลดข้อมูลเริ่มต้น
        self.update_dashboard()

    def create_kpi_card(self, parent, title, value, color):
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=10)
        ctk.CTkLabel(card, text=title, font=("Kanit", 18, "bold"), text_color="white").pack(pady=(15, 5))
        lbl_value = ctk.CTkLabel(card, text=value, font=("Kanit", 32, "bold"), text_color="white")
        lbl_value.pack(pady=(0, 15))
        card.lbl_value = lbl_value # เก็บ reference ไว้แก้ยอดทีหลัง
        return card

    def update_dashboard(self):
        # ใช้ Threading เพื่อไม่ให้หน้าจอค้างตอนคำนวณกราฟ
        threading.Thread(target=self.run_dashboard_calc).start()

    def run_dashboard_calc(self):
        try:
            # ดึงข้อมูลจากชีท Stock (Transactions)
            records = self.sheet_stock.get_all_values()
            
            total_revenue = 0.0
            total_bills = 0
            daily_sales = defaultdict(float)
            product_sales = defaultdict(int)

            # ข้าม Header (row 0)
            if len(records) > 1:
                for row in records[1:]:
                    # Structure: [Timestamp, Barcode, Name, Qty, Price, TotalSales]
                    # Index:     0          1        2     3    4      5
                    if len(row) >= 6:
                        date_str = row[0].split(" ")[0] # เอาแค่วันที่ (YYYY-MM-DD)
                        name = row[2]
                        total_str = row[5]

                        # ถ้า TotalSales เป็นตัวเลข (ไม่ใช่ "-") แสดงว่าเป็นยอดขาย
                        if total_str != "-" and total_str.strip() != "":
                            try:
                                amount = float(total_str.replace(",", ""))
                                total_revenue += amount
                                total_bills += 1
                                daily_sales[date_str] += amount
                                product_sales[name] += 1 # นับจำนวนครั้งที่ขาย (หรือจะบวก Qty ก็ได้)
                            except:
                                pass

            # เตรียมข้อมูลสำหรับกราฟ
            # 1. กราฟเส้น (7 วันล่าสุด)
            sorted_dates = sorted(daily_sales.keys())[-7:] # เอา 7 วันล่าสุด
            y_sales = [daily_sales[d] for d in sorted_dates]
            
            # 2. กราฟแท่ง (Top 5 Products)
            sorted_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
            top_names = [p[0] for p in sorted_products]
            top_counts = [p[1] for p in sorted_products]

            # ส่งข้อมูลไปวาดกราฟที่ Main Thread
            self.after(0, self.draw_charts, total_revenue, total_bills, sorted_dates, y_sales, top_names, top_counts)

        except Exception as e:
            print(f"Dashboard Error: {e}")

    def draw_charts(self, total_revenue, total_bills, dates, sales, top_names, top_counts):
        # 1. อัปเดตตัวเลข KPI
        self.card_sales.lbl_value.configure(text=f"{total_revenue:,.2f} บาท")
        self.card_txn.lbl_value.configure(text=f"{total_bills} รายการ")

        # 2. วาดกราฟ (Clear ของเก่าก่อน)
        for widget in self.graph_left.winfo_children(): widget.destroy()
        for widget in self.graph_right.winfo_children(): widget.destroy()

        # กราฟซ้าย: ยอดขายรายวัน (Line Chart)
        fig1, ax1 = plt.subplots(figsize=(5, 4), dpi=100)
        ax1.plot(dates, sales, marker='o', linestyle='-', color='#3498DB', linewidth=2)
        ax1.set_title('ยอดขายรายวัน (7 วันล่าสุด)', fontsize=14)
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, linestyle='--', alpha=0.7)
        fig1.tight_layout()
        
        canvas1 = FigureCanvasTkAgg(fig1, master=self.graph_left)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill="both", expand=True)

        # กราฟขวา: สินค้าขายดี (Bar Chart)
        fig2, ax2 = plt.subplots(figsize=(5, 4), dpi=100)
        bars = ax2.bar(top_names, top_counts, color='#2CC985')
        ax2.set_title('5 อันดับสินค้าขายดี', fontsize=14)
        ax2.tick_params(axis='x', rotation=45)
        
        # ใส่ตัวเลขบนแท่งกราฟ
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                     f'{int(height)}', ha='center', va='bottom')
        
        fig2.tight_layout()
        
        canvas2 = FigureCanvasTkAgg(fig2, master=self.graph_right)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill="both", expand=True)

    # =========================================
    # ส่วนเพิ่มสินค้าใหม่
    # =========================================
    def open_add_product_window(self):
        self.add_window = ctk.CTkToplevel(self)
        self.add_window.title("เพิ่มสินค้าใหม่")
        self.add_window.geometry("500x700")
        self.add_window.attributes("-topmost", True)

        ctk.CTkLabel(self.add_window, text="📝 เพิ่มรายการสินค้า", font=("Kanit", 24, "bold")).pack(pady=20)

        self.new_barcode = self.create_styled_entry(self.add_window, "Barcode", "BARCODE")
        self.new_name = self.create_styled_entry(self.add_window, "ชื่อสินค้า", "NAME")
        self.new_detail = self.create_styled_entry(self.add_window, "รายละเอียด", "DETAIL")
        self.new_cost = self.create_styled_entry(self.add_window, "ราคาทุน", "COST")
        self.new_price = self.create_styled_entry(self.add_window, "ราคาขาย", "PRICE")

        self.new_image_path = None
        frame_img = ctk.CTkFrame(self.add_window, fg_color="transparent")
        frame_img.pack(pady=10, fill="x", padx=20)
        self.lbl_img_status = ctk.CTkLabel(frame_img, text="ยังไม่ได้เลือกรูป", text_color="gray", font=("Kanit", 14))
        self.lbl_img_status.pack(side="left")
        btn_choose_img = ctk.CTkButton(frame_img, text="🖼️ เลือกรูป", command=self.choose_new_image, width=120, font=("Kanit", 14))
        btn_choose_img.pack(side="right")

        btn_confirm = ctk.CTkButton(self.add_window, text="บันทึกข้อมูล", command=self.save_new_product,
                                    height=60, font=("Kanit", 20, "bold"), fg_color="#2CC985", hover_color="#229A65")
        btn_confirm.pack(pady=20, padx=20, fill="x")

    def choose_new_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if file_path:
            self.new_image_path = file_path
            filename = os.path.basename(file_path)
            self.lbl_img_status.configure(text=f"เลือก: {filename}", text_color="blue")

    def save_new_product(self):
        threading.Thread(target=self.run_save_new_product_process).start()

    def run_save_new_product_process(self):
        barcode = self.new_barcode.get().strip()
        name = self.new_name.get().strip()
        detail = self.new_detail.get().strip()
        cost = self.new_cost.get().strip()
        price = self.new_price.get().strip()

        if not barcode or not name or not price:
            messagebox.showwarning("ข้อมูลไม่ครบ", "กรุณากรอก Barcode, ชื่อ และราคาขาย")
            self.add_window.lift()
            return
        try:
            image_id = ""
            if self.new_image_path:
                file_metadata = {
                    'name': os.path.basename(self.new_image_path),
                    'parents': [GOOGLE_DRIVE_FOLDER_ID] if GOOGLE_DRIVE_FOLDER_ID else []
                }
                media = MediaFileUpload(self.new_image_path, mimetype='image/jpeg')
                file = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                image_id = file.get('id')

            records = self.sheet_products.get_all_values()
            if len(records) > 1:
                last_id = records[-1][0] 
                try:
                    next_id = int(last_id) + 1
                except:
                    next_id = len(records)
            else:
                next_id = 1

            row = [next_id, barcode, name, detail, cost, price, image_id]
            self.sheet_products.append_row(row)

            self.after(0, lambda: messagebox.showinfo("สำเร็จ", f"เพิ่มสินค้า '{name}' เรียบร้อย!"))
            self.after(0, self.add_window.destroy)
            self.after(0, self.load_inventory_data)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"บันทึกไม่สำเร็จ: {e}"))

    # =========================================
    # ส่วนอัปโหลดรูปเดิม (Inventory)
    # =========================================
    def upload_image_for_selected(self):
        if not self.selected_product_row: return
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if not file_path: return
        self.btn_upload.configure(state="disabled", text="Uploading...")
        threading.Thread(target=self.run_upload_existing, args=(file_path,)).start()

    def run_upload_existing(self, file_path):
        try:
            file_metadata = {
                'name': os.path.basename(file_path),
                'parents': [GOOGLE_DRIVE_FOLDER_ID] if GOOGLE_DRIVE_FOLDER_ID else []
            }
            media = MediaFileUpload(file_path, mimetype='image/jpeg')
            file = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            file_id = file.get('id')
            
            self.sheet_products.update_cell(int(self.selected_product_row), 7, file_id)
            
            messagebox.showinfo("Success", "อัปโหลดรูปภาพเรียบร้อย!")
            self.after(0, self.finish_upload, file_id)
        except Exception as e:
            messagebox.showerror("Upload Error", f"{e}")
            self.after(0, self.finish_upload, None)

    def finish_upload(self, file_id):
        self.btn_upload.configure(state="normal", text="📤 อัปเดตรูปภาพ")
        if file_id:
            self.load_inventory_data()
            self.display_image(file_id)

    def play_sound(self, status):
        try:
            if status == "success": winsound.Beep(2000, 150)
            elif status == "error": winsound.Beep(500, 500)
        except: pass

if __name__ == "__main__":
    app = StockManagerApp()
    app.mainloop()