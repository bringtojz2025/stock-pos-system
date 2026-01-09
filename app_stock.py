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
from PIL import Image, ImageTk, ImageDraw, ImageFont
import io
import qrcode
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict
import matplotlib
from ai_content_generator import AIContentGenerator, AdvertisementImageCreator, FacebookIntegration, load_config, save_config
import socket
from tkcalendar import DateEntry
import urllib.request
import zipfile
import shutil
import ssl
import urllib3
import time
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import json
import subprocess
import barcode as pybarcode
from barcode.writer import ImageWriter
from fpdf import FPDF

# ติดตั้งไลบรารี่สำหรับปริ้น
try:
    import win32print
    import win32api
except ImportError:
    pass  # ถ้าไม่ติดตั้ง จะติดตั้งอัตโนมัติเมื่อใช้

# ตั้งค่า socket timeout สำหรับการเชื่อมต่อ Google Drive
socket.setdefaulttimeout(30)

# แก้ไข SSL verification issues (ชั่วคราว)
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception:
    pass

# Disable urllib3 SSL warnings (เมื่อใช้ unverified context)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ฟังก์ชันเพื่อดাวน์โหลดและติดตั้ง Kanit font
def setup_kanit_font():
    """ดาวน์โหลด Kanit font จาก Google Fonts และติดตั้งให้ matplotlib"""
    import sys
    
    # เส้นทางฟอนต์สำหรับ Windows
    if sys.platform == 'win32':
        font_dir = os.path.expanduser(r'~\AppData\Local\Microsoft\Windows\Fonts')
        font_name = 'Kanit-Regular.ttf'
    elif sys.platform == 'darwin':  # macOS
        font_dir = os.path.expanduser('~/Library/Fonts')
        font_name = 'Kanit-Regular.ttf'
    else:  # Linux
        font_dir = os.path.expanduser('~/.local/share/fonts')
        font_name = 'Kanit-Regular.ttf'
    
    font_path = os.path.join(font_dir, font_name)
    
    # ตรวจสอบว่าฟอนต์มีอยู่แล้วหรือไม่
    if os.path.exists(font_path):
        print(f"✓ Kanit font found at {font_path}")
        return True
    
    try:
        print("⏳ Downloading Kanit font from Google Fonts...")
        
        # URL ของ Kanit font จาก GitHub (Google Fonts mirror)
        font_url = "https://github.com/google/fonts/raw/main/ofl/kanit/Kanit-Regular.ttf"
        
        # สร้างโฟลเดอร์ถ้ายังไม่มี
        os.makedirs(font_dir, exist_ok=True)
        
        # ดาวน์โหลดฟอนต์
        urllib.request.urlretrieve(font_url, font_path)
        print(f"✓ Kanit font installed to {font_path}")
        
        # บอก matplotlib ให้ใช้ฟอนต์ใหม่
        matplotlib.font_manager.fontManager.addfont(font_path)
        print("✓ Kanit font registered with matplotlib")
        return True
        
    except Exception as e:
        print(f"⚠ Could not download Kanit font: {e}")
        print("⚠ Falling back to default font (DejaVu Sans)")
        return False

# ลองติดตั้ง Kanit font
try:
    setup_kanit_font()
except Exception as e:
    print(f"Font setup error: {e}")

# ปิดการแสดง warnings เกี่ยวกับฟอนต์ที่ matplotlib ไม่เจอ
import warnings
warnings.filterwarnings('ignore', message='.*Kanit.*')
warnings.filterwarnings('ignore', message='.*findfont.*')

# ตั้งค่าฟอนต์ภาษาไทย - ลอง Kanit ก่อน แล้วลอง DejaVu Sans ถ้าไม่เจอ
import matplotlib.font_manager as fm
available_fonts = [f.name.lower() for f in fm.fontManager.ttflist]

if 'kanit' in available_fonts:
    matplotlib.rc('font', family='Kanit')
elif 'noto sans' in available_fonts:
    matplotlib.rc('font', family='Noto Sans')
else:
    matplotlib.rc('font', family='DejaVu Sans')

# ลงทะเบียน font สำหรับ ReportLab (สำหรับ PDF)
try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    # ลองหา Kanit font
    import sys
    if sys.platform == 'win32':
        font_dir = os.path.expanduser(r'~\AppData\Local\Microsoft\Windows\Fonts')
    elif sys.platform == 'darwin':
        font_dir = os.path.expanduser('~/Library/Fonts')
    else:
        font_dir = os.path.expanduser('~/.local/share/fonts')
    
    font_path = os.path.join(font_dir, 'Kanit-Regular.ttf')
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('KanitRegular', font_path))
        print("✓ Kanit font registered for ReportLab PDF")
    else:
        print("⚠ Kanit font not found for ReportLab, will use Helvetica")
except Exception as e:
    print(f"⚠ Could not register Kanit for ReportLab: {e}")

# ฟังก์ชันเพื่อตรวจสอบว่า Kanit font ถูกลงทะเบียนสำเร็จหรือไม่
def _is_kanit_registered():
    """ตรวจสอบว่า KanitRegular font ถูกลงทะเบียนสำเร็จแล้ว"""
    try:
        from reportlab.pdfbase import pdfmetrics
        # ลองสร้างไฟล์ทดสอบด้วย font ที่ลงทะเบียน
        return 'KanitRegular' in pdfmetrics.standardFonts or hasattr(pdfmetrics.getFont, 'KanitRegular')
    except:
        return False

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

        # สร้างโฟลเดอร์เก็บรูปถ้ายังไม่มี
        self.img_folder = "img"
        os.makedirs(self.img_folder, exist_ok=True)

        self.all_inventory_data = [] 
        self.cart_items = [] 
        self.enable_image_loading = True  # สามารถปิดได้หากมีปัญหา network
        self.last_coupon_checked = ""  # เก็บโค้ตที่ตรวจสอบไปแล้ว เพื่อแสดงเตือน 1 ครั้ง
        self.sales_history_data = {} 
        
        # Image loading thread management
        self.current_image_thread = None  # เก็บ thread ปัจจุบันสำหรับยกเลิก
        self.current_image_id = None
        self.current_product_barcode = None  # เก็บ barcode สำหรับใช้เป็นชื่อไฟล์
        self.image_thread_lock = threading.Lock()  # ป้องกัน race condition
        
        # Printer Settings
        self.printer_name = ""  # ชื่อเครื่องปริ้น
        self.selected_barcode_data = None  # เก็บข้อมูลบาร์โค้ดที่เลือก
        self.load_printer_settings()  # โหลดการตั้งค่าเครื่องปริ้นที่บันทึกไว้
        
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
                    self.sheet_sales = self.sh.add_worksheet(title="Sales", rows="1000", cols="12")
                    self.sheet_sales.append_row(["ReceiptID", "Date", "Barcode", "Name", "Qty", "UnitPrice", "Total", "UsedCoupon", "DiscountAmount", "PaymentMethod", "ReceivedCoupon", "Cancel"])
                except:
                    self.sheet_sales = self.sh.sheet1
            
            # เพิ่ม Suppliers sheet
            try:
                self.sheet_suppliers = self.sh.worksheet("Suppliers")
            except:
                try:
                    self.sheet_suppliers = self.sh.add_worksheet(title="Suppliers", rows="500", cols="5")
                    self.sheet_suppliers.append_row(["SupplierID", "Name", "Phone", "Address", "Note"])
                except:
                    self.sheet_suppliers = None
            
            # เพิ่ม Inventory sheet
            try:
                self.sheet_inventory = self.sh.worksheet("Inventory")
            except:
                try:
                    self.sheet_inventory = self.sh.add_worksheet(title="Inventory", rows="500", cols="15")
                    self.sheet_inventory.append_row(["ProductID", "Barcode", "Name", "Brand", "Car Model", "Detail", "Cost", "Stock", "Price", "ImageID"])
                except:
                    self.sheet_inventory = None
            
            # เพิ่ม Customers sheet
            try:
                self.sheet_customers = self.sh.worksheet("Customers")
            except:
                try:
                    self.sheet_customers = self.sh.add_worksheet(title="Customers", rows="1000", cols="12")
                    self.sheet_customers.append_row(["CustomerID", "FullName", "Nickname", "Birthday", "Phone", "Address", "Vehicle", "LicensePlate", "LastVisit", "TotalSpent", "AvailableCoupons", "Notes"])
                except:
                    self.sheet_customers = None
        except Exception as e:
            print(f"Connection Error: {e}")
            import traceback; traceback.print_exc()
            messagebox.showerror("Connection Error", f"{e}")
            self.destroy()
            return

        # สร้างโฟลเดอร์สำหรับบันทึกใบเสร็จ
        self.receipts_folder = os.path.join(os.getcwd(), "receipts")
        if not os.path.exists(self.receipts_folder):
            os.makedirs(self.receipts_folder)
        
        # ตั้งค่าเริ่มต้นสำหรับปริ้นใบเสร็จ
        self.receipt_auto_print = False  # ปริ้นอัตโนมัติหรือไม่
        self.load_receipt_settings()

        # ตั้งขนาด window เริ่มต้น
        self.geometry("1200x900")
        
        # คำนวณตำแหน่งตรงกลางจอ
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 1200
        window_height = 900
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # ตั้งให้ window อยู่บนสุดเสมอ
        self.attributes('-topmost', True)
        
        # Minimize โปรแกรมอื่นๆ (Show Desktop effect)
        self.minimize_other_windows()
        
        # ยก window นี้ไปด้านหน้า
        self.lift()
        self.focus_force()
        
        # ซ่อน window หลัก ก่อน (ยังไม่ขึ้นมา)
        self.withdraw()
        
        # แสดง Loading screen ก่อน
        self.show_loading_screen()
        
        # โหลด UI ด้วย delay เล็กน้อยเพื่อให้ Loading screen แสดง
        self.after(300, self.create_layout_and_load_data)

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
        self.tabview._segmented_button.configure(font=("Kanit", 13, "bold"))
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_pos = self.tabview.add("🛒 ขายหน้าร้าน (POS)")
        self.tab_history = self.tabview.add("📜 ประวัติการขาย (History)")
        self.tab_inventory = self.tabview.add("📦 คลังสินค้า (Inventory)")
        self.tab_dashboard = self.tabview.add("📊 ภาพรวม (Dashboard)")
        self.tab_reports = self.tabview.add("📈 รายงาน (Reports)")
        self.tab_suppliers = self.tabview.add("🏭 ซัพพลายเออร์ (Suppliers)")
        self.tab_ai_social = self.tabview.add("🤖 AI & Social Media")

        self.setup_pos_tab()
        self.setup_history_tab()
        self.setup_inventory_tab()
        self.setup_dashboard_tab()
        self.setup_reports_tab()
        self.setup_suppliers_tab()
        self.setup_ai_social_tab()

    def create_layout_and_load_data(self):
        """สร้าง layout และโหลดข้อมูล"""
        self.create_layout()
        # โหลดข้อมูลต่างๆ ในเธรดแยก
        threading.Thread(target=self.load_all_data_background, daemon=True).start()

    def load_all_data_background(self):
        """โหลดข้อมูลทั้งหมดในเบื้องหลัง"""
        if not self.app_running:
            return
        try:
            # โหลดข้อมูล inventory
            self.load_inventory_data()
            # โหลด history
            self.load_history_data()
            # อัปเดต dashboard
            self.update_dashboard()
            
            # ซ่อน loading screen
            if self.app_running and self.winfo_exists():
                self.after(0, self.hide_loading_screen)
        except Exception as e:
            print(f"⚠ Error loading data: {e}")
            if self.app_running and self.winfo_exists():
                self.after(0, self.hide_loading_screen)

    def minimize_other_windows(self):
        """Minimize โปรแกรมอื่นๆ (เหมือน Show Desktop)"""
        try:
            import subprocess
            # ใช้ VB Script เพื่อ minimize ทั้งหมด
            vbs_code = '''Set objShell = CreateObject("Shell.Application")
objShell.MinimizeAll()
'''
            vbs_path = os.path.join(os.getenv('TEMP'), 'minimize_all.vbs')
            with open(vbs_path, 'w') as f:
                f.write(vbs_code)
            os.system(f'cscript.exe {vbs_path}')
            
            # ลบ VB script
            try:
                os.remove(vbs_path)
            except:
                pass
        except Exception as e:
            print(f"⚠ Minimize windows error: {e}")

    def show_loading_screen(self):
        """แสดง Loading screen แบบ popup ตรงกลาง"""
        try:
            # สร้าง Toplevel window (popup)
            self.loading_window = ctk.CTkToplevel(self)
            self.loading_window.title("Loading")
            self.loading_window.geometry("400x380")
            self.loading_window.resizable(False, False)
            
            # ตั้งให้อยู่ตรงกลางจอ
            self.loading_window.grab_set()
            self.loading_window.attributes('-topmost', True)
            
            # ปิด window decoration (title bar ขนาดเล็ก)
            # self.loading_window.overrideredirect(True)  # ถ้าอยากไม่มี title bar เลย
            
            # ตั้งสีพื้นหลัง
            self.loading_window.configure(fg_color="#1a1a1a")
            
            # สร้าง main frame ในโปรแกรม
            loading_frame = ctk.CTkFrame(self.loading_window, fg_color="#1a1a1a")
            loading_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # เพิ่มโลโก้
            try:
                logo_path = os.path.join(os.path.dirname(__file__), "img", "logo.png")
                if os.path.exists(logo_path):
                    from PIL import Image
                    logo_img = Image.open(logo_path)
                    # ปรับขนาดรูป
                    logo_img = logo_img.resize((100, 100), Image.Resampling.LANCZOS)
                    ctk_logo = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(100, 100))
                    logo_label = ctk.CTkLabel(loading_frame, image=ctk_logo, text="")
                    logo_label.image = ctk_logo
                    logo_label.pack(pady=(10, 5))
            except:
                pass
            
            # โลโก้/ชื่อ
            title = ctk.CTkLabel(
                loading_frame, 
                text="📊 Stock POS",
                font=("Kanit", 32, "bold"),
                text_color="#2CC985"
            )
            title.pack(pady=(10, 5))
            
            # ข้อความ
            loading_text = ctk.CTkLabel(
                loading_frame,
                text="⏳ กำลังโหลดข้อมูล...",
                font=("Kanit", 14),
                text_color="#F39C12"
            )
            loading_text.pack(pady=10)
            
            # Animation dots
            self.loading_dots = ctk.CTkLabel(
                loading_frame,
                text="",
                font=("Kanit", 16),
                text_color="#3498DB"
            )
            self.loading_dots.pack(pady=10)
            
            # Progress bar (optional)
            self.loading_progress = ctk.CTkProgressBar(
                loading_frame,
                mode="indeterminate"
            )
            self.loading_progress.pack(pady=15, padx=10, fill="x")
            self.loading_progress.start()
            
            # เริ่ม animation
            self.loading_animation_counter = 0
            self.animate_loading()
            
            # คำนวณตำแหน่งให้อยู่ตรงกลาง
            self.loading_window.update_idletasks()
            x = (self.loading_window.winfo_screenwidth() // 2) - (400 // 2)
            y = (self.loading_window.winfo_screenheight() // 2) - (380 // 2)
            self.loading_window.geometry(f"+{x}+{y}")
            
        except Exception as e:
            print(f"Loading screen error: {e}")

    def animate_loading(self):
        """แอนิเมชั่น loading dots"""
        if not self.app_running or not hasattr(self, 'loading_dots'):
            return
        
        try:
            dots = ["◐", "◓", "◑", "◒"]
            self.loading_animation_counter = (self.loading_animation_counter + 1) % 4
            self.loading_dots.configure(text=dots[self.loading_animation_counter])
            self.after(200, self.animate_loading)
        except:
            pass

    def hide_loading_screen(self):
        """ซ่อน Loading screen และแสดง UI หลัก"""
        try:
            # ปิด loading window
            if hasattr(self, 'loading_window') and self.loading_window.winfo_exists():
                self.loading_window.destroy()
            
            # แสดง window หลัก (ตำแหน่งตั้งไว้แล้ว)
            if self.app_running and self.winfo_exists():
                self.deiconify()  # แสดง window
                self.lift()  # ยก ด้านหน้า
                self.focus_force()  # โฟกัสแรง (force focus)
                self.after(100, lambda: self.attributes('-topmost', False))  # ยกเลิก topmost หลังแสดง
            
            print("✓ โหลดข้อมูลเสร็จสิ้น")
        except:
            pass


    # =========================================
    # TAB 1: POS Logic
    # =========================================
    def setup_pos_tab(self):
        paned = ctk.CTkFrame(self.tab_pos, fg_color="transparent")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # LEFT FRAME - สำหรับสแกนและโค้ตส่วนลด
        left_frame = ctk.CTkScrollableFrame(paned, width=320, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=False, padx=5, pady=5)

        ctk.CTkLabel(left_frame, text="🛒 สแกนสินค้า", font=("Kanit", 24, "bold")).pack(pady=15)

        self.pos_barcode = self.create_styled_entry(left_frame, "Scan Barcode Here...", "BARCODE")
        self.pos_barcode.bind('<Return>', self.add_item_to_cart)

        self.lbl_last_scan = ctk.CTkLabel(left_frame, text="-", font=("Kanit", 18), text_color="gray")
        self.lbl_last_scan.pack(pady=10)

        btn_manual_add = ctk.CTkButton(left_frame, text="🛒 เพิ่มลงตะกร้า ⬇️", command=self.add_item_to_cart,
                                       font=("Kanit", 16), height=40)
        btn_manual_add.pack(pady=10, fill="x", padx=10)
        
        # ปุ่มเพิ่มรายการแบบ manual (ค่าบริการ, อื่นๆ)
        btn_add_manual = ctk.CTkButton(left_frame, text="➕ เพิ่มรายการอื่นๆ", command=self.add_manual_item,
                                       font=("Kanit", 14), height=40, fg_color="#8E44AD", hover_color="#7D3C98")
        btn_add_manual.pack(pady=10, fill="x", padx=10)
        
        # --- เพิ่มส่วนโค้ตส่วนลดลงฝั่งซ้าย ---
        ctk.CTkLabel(left_frame, text="ตัวเลือกชำระเงิน", font=("Kanit", 16, "bold")).pack(pady=(20, 10))
        
        # เพิ่มส่วนโค้ตส่วนลด
        discount_frame = ctk.CTkFrame(left_frame, fg_color="gray25")
        discount_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(discount_frame, text="โค้ตส่วนลด:", font=("Kanit", 11)).pack(anchor="w", padx=10, pady=5)
        self.discount_code_entry = ctk.CTkEntry(discount_frame, placeholder_text="ใส่โค้ตส่วนลด", font=("Kanit", 11))
        self.discount_code_entry.pack(fill="x", padx=10, pady=5)
        self.discount_code_entry.bind("<KeyRelease>", self.update_discount_display)
        
        # แสดงสถานะของโค้ตว่าใช้ได้หรือไม่
        status_frame = ctk.CTkFrame(discount_frame, fg_color="gray25")
        status_frame.pack(fill="x", padx=10, pady=5)
        self.lbl_coupon_status = ctk.CTkLabel(status_frame, text="✓", font=("Kanit", 11), text_color="#27AE60")
        self.lbl_coupon_status.pack(side="left", padx=5)
        
        # เพิ่มส่วนประเภทการจ่าย
        payment_frame = ctk.CTkFrame(left_frame, fg_color="gray25")
        payment_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(payment_frame, text="ประเภทการจ่าย:", font=("Kanit", 11)).pack(anchor="w", padx=10, pady=5)
        self.payment_method = ctk.CTkComboBox(payment_frame, values=["เงินสด", "QR Code", "Credit Card"], 
                                              font=("Kanit", 11))
        self.payment_method.set("เงินสด")
        self.payment_method.pack(fill="x", padx=10, pady=5)

        # เพิ่มส่วนตั้งค่าใบเสร็จ
        receipt_frame = ctk.CTkFrame(left_frame, fg_color="gray25")
        receipt_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(receipt_frame, text="⚙️ ตั้งค่าใบเสร็จ", font=("Kanit", 11, "bold")).pack(anchor="w", padx=10, pady=(5, 0))
        
        # Frame สำหรับปุ่มปริ้นอัตโนมัติและตัวบ่งชี้สถานะ
        auto_print_frame = ctk.CTkFrame(receipt_frame, fg_color="transparent")
        auto_print_frame.pack(fill="x", padx=10, pady=5)
        
        # สลับโหมดปริ้นอัตโนมัติ
        btn_auto_print = ctk.CTkButton(auto_print_frame, text="🖨️ สลับปริ้นอัตโนมัติ", 
                                       command=self.toggle_receipt_auto_print,
                                       font=("Kanit", 10), height=30)
        btn_auto_print.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # ตัวบ่งชี้สถานะปริ้นอัตโนมัติ
        self.lbl_auto_print_status = ctk.CTkLabel(auto_print_frame, text="⭕ ปิด",
                                                   font=("Kanit", 11, "bold"),
                                                   text_color="#E74C3C",
                                                   width=60)
        self.lbl_auto_print_status.pack(side="left", padx=5)
        
        # ปุ่มดูโฟลเดอร์ใบเสร็จ
        btn_open_receipts = ctk.CTkButton(receipt_frame, text="📁 เปิดโฟลเดอร์ใบเสร็จ", 
                                          command=lambda: os.startfile(self.receipts_folder) if os.path.exists(self.receipts_folder) else messagebox.showwarning("แจ้งเตือน", "ยังไม่มีใบเสร็จ"),
                                          font=("Kanit", 10), height=30)
        btn_open_receipts.pack(fill="x", padx=10, pady=5)

        # CENTER/RIGHT FRAME - สำหรับตะกร้าและชำระเงิน
        right_frame = ctk.CTkScrollableFrame(paned, fg_color="transparent")
        right_frame.pack(side="right", fill="both", expand=True, padx=5)

        ctk.CTkLabel(right_frame, text="รายการในใบเสร็จ", font=("Kanit", 20, "bold")).pack(pady=10)

        columns = ("Barcode", "Name", "Qty", "Price", "Total")
        self.cart_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=5)
        self.cart_tree.heading("Barcode", text="Barcode"); self.cart_tree.column("Barcode", width=80, stretch=True)
        self.cart_tree.heading("Name", text="สินค้า"); self.cart_tree.column("Name", width=150, stretch=True)
        self.cart_tree.heading("Qty", text="จำนวน"); self.cart_tree.column("Qty", width=50, anchor="center", stretch=True)
        self.cart_tree.heading("Price", text="ราคา"); self.cart_tree.column("Price", width=70, anchor="e", stretch=True)
        self.cart_tree.heading("Total", text="รวม"); self.cart_tree.column("Total", width=70, anchor="e", stretch=True)
        self.cart_tree.pack(fill="both", expand=True, padx=10)
        
        btn_del_item = ctk.CTkButton(right_frame, text="❌ ลบรายการที่เลือก", command=self.delete_from_cart,
                                     fg_color="#FF474C", height=30, border_width=2, border_color="#CC0000")
        btn_del_item.pack(pady=5, padx=10, anchor="e")

        sum_frame = ctk.CTkFrame(right_frame, fg_color="gray20")
        sum_frame.pack(fill="x", padx=10, pady=10)

        self.lbl_total = ctk.CTkLabel(sum_frame, text="ยอดรวม: 0.00 บาท", font=("Kanit", 28, "bold"), text_color="#2CC985")
        self.lbl_total.pack(pady=15)

        # แสดงยอดส่วนลด
        discount_info_frame = ctk.CTkFrame(right_frame, fg_color="gray20")
        discount_info_frame.pack(fill="x", padx=10, pady=5)
        self.lbl_discount_amount = ctk.CTkLabel(discount_info_frame, text="ส่วนลด: 0.00 บาท", font=("Kanit", 14), text_color="#E74C3C")
        self.lbl_discount_amount.pack(pady=5)
        self.lbl_final_price = ctk.CTkLabel(discount_info_frame, text="ราคาสุดท้าย: 0.00 บาท", font=("Kanit", 16, "bold"), text_color="#F39C12")
        self.lbl_final_price.pack(pady=5)

        self.btn_checkout = ctk.CTkButton(right_frame, text="💰 ชำระเงิน / ตัดสต็อก", command=self.process_checkout,
                                          font=("Kanit", 20, "bold"), height=60, fg_color="#F39C12", hover_color="#D68910",
                                          border_width=3, border_color="#D4860D")
        self.btn_checkout.pack(fill="x", padx=10, pady=(0, 20))

    def create_styled_entry(self, parent, ph, suffix):
        container = ctk.CTkFrame(parent, height=50, fg_color=("gray95", "gray25")) 
        container.pack(pady=8, padx=20, fill="x")
        ctk.CTkLabel(container, text=suffix, width=80, font=("Kanit", 12, "bold")).pack(side="right", padx=10)
        entry = ctk.CTkEntry(container, placeholder_text=ph, height=50, font=("Kanit", 14), 
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
            try: price = float(data[8]) if len(data) > 8 else 0.0
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

    def add_manual_item(self):
        """เพิ่มรายการแบบ manual เช่น ค่าบริการ, ค่าอื่นๆ"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("เพิ่มรายการอื่นๆ")
        dialog.geometry("450x320")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        # ชื่อรายการ
        ctk.CTkLabel(dialog, text="ชื่อรายการ:", font=("Kanit", 12, "bold")).pack(pady=(20, 5), padx=20, anchor="w")
        entry_name = ctk.CTkEntry(dialog, placeholder_text="เช่น ค่าบริการ, ค่าส่วน, ค่าจัดเรียง", font=("Kanit", 11))
        entry_name.pack(pady=(0, 15), padx=20, fill="x")
        
        # ราคา
        ctk.CTkLabel(dialog, text="ราคา (บาท):", font=("Kanit", 12, "bold")).pack(pady=(0, 5), padx=20, anchor="w")
        entry_price = ctk.CTkEntry(dialog, placeholder_text="ใส่ราคา", font=("Kanit", 11))
        entry_price.pack(pady=(0, 15), padx=20, fill="x")
        
        # จำนวน (ค่าเริ่มต้น 1)
        ctk.CTkLabel(dialog, text="จำนวน:", font=("Kanit", 12, "bold")).pack(pady=(0, 5), padx=20, anchor="w")
        entry_qty = ctk.CTkEntry(dialog, placeholder_text="1", font=("Kanit", 11))
        entry_qty.insert(0, "1")
        entry_qty.pack(pady=(0, 20), padx=20, fill="x")
        
        def save_manual_item():
            name = entry_name.get().strip()
            price_str = entry_price.get().strip()
            qty_str = entry_qty.get().strip()
            
            if not name:
                messagebox.showwarning("แจ้งเตือน", "กรุณาใส่ชื่อรายการ")
                return
            
            try:
                price = float(price_str)
            except:
                messagebox.showerror("ข้อผิดพลาด", "กรุณาใส่ราคาเป็นตัวเลข")
                return
            
            try:
                qty = int(qty_str) if qty_str else 1
                if qty <= 0:
                    qty = 1
            except:
                qty = 1
            
            # ใช้ "Sevice-" เป็น barcode สำหรับรายการแบบ manual
            barcode = f"Sevice-{len(self.cart_items)+1}"
            
            self.cart_items.append({
                'barcode': barcode,
                'name': name,
                'qty': qty,
                'price': price,
                'total': qty * price,
                'row_idx': -1  # ไม่มี row index เนื่องจากไม่ได้มาจาก inventory
            })
            
            self.play_sound("success")
            self.lbl_last_scan.configure(text=f"เพิ่ม: {name} (฿{price})")
            self.update_cart_ui()
            dialog.destroy()
        
        # ปุ่มบันทึก
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkButton(btn_frame, text="✓ บันทึก", command=save_manual_item, 
                     font=("Kanit", 12), fg_color="#27AE60", hover_color="#1E8449").pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(btn_frame, text="✕ ยกเลิก", command=dialog.destroy, 
                     font=("Kanit", 12), fg_color="#E74C3C", hover_color="#C0392B").pack(side="left", fill="x", expand=True)

    def update_cart_ui(self):
        for i in self.cart_tree.get_children(): self.cart_tree.delete(i)
        total_amount = 0
        for item in self.cart_items:
            self.cart_tree.insert("", "end", values=(item['barcode'], item['name'], item['qty'], 
                                                     f"{item['price']:,.2f}", f"{item['total']:,.2f}"))
            total_amount += item['total']
        self.lbl_total.configure(text=f"ยอดรวม: {total_amount:,.2f} บาท")
        
        # อัปเดตการแสดงผลส่วนลด
        discount_code = self.discount_code_entry.get().strip()
        discount_amount = 0.0
        
        if discount_code:
            # ตรวจสอบเงื่อนไขส่วนลด
            if discount_code.startswith("DISC10"):
                discount_amount = total_amount * 0.10
            elif discount_code.upper() == "SPECIAL":
                discount_amount = total_amount * 0.15
            elif discount_code.upper().startswith("DISC"):
                try:
                    percent = int(discount_code.split("-")[0].replace("DISC", ""))
                    discount_amount = total_amount * (percent / 100)
                except:
                    discount_amount = 0.0
        
        final_price = max(0, total_amount - discount_amount)
        
        # อัปเดตการแสดงผล
        if hasattr(self, 'lbl_discount_amount'):
            self.lbl_discount_amount.configure(text=f"ส่วนลด: {discount_amount:,.2f} บาท" if discount_amount > 0 else "ส่วนลด: 0.00 บาท")
            self.lbl_final_price.configure(text=f"ราคาสุดท้าย: {final_price:,.2f} บาท")
            
            # เปลี่ยนสีตามสถานะส่วนลด
            if discount_amount > 0:
                self.lbl_discount_amount.configure(text_color="#27AE60")
                self.lbl_final_price.configure(text_color="#27AE60")
            else:
                self.lbl_discount_amount.configure(text_color="#E74C3C")
                self.lbl_final_price.configure(text_color="#F39C12")
        
        return total_amount

    def delete_from_cart(self):
        selected = self.cart_tree.selection()
        if not selected: return
        for sel in selected:
            item_values = self.cart_tree.item(sel)['values']
            barcode_to_del = str(item_values[0])
            self.cart_items = [item for item in self.cart_items if str(item['barcode']) != barcode_to_del]
        self.update_cart_ui()

    def check_used_coupons(self):
        """ตรวจสอบโค้ตที่เคยใช้แล้ว - ตรวจสอบจาก column 8 (used_coupon) เท่านั้น
        
        โครงสร้าง Google Sheet (Sales) - 11 columns:
        Index 0: ReceiptID (column 1)
        Index 1: Date (column 2)
        Index 2: Barcode (column 3)
        Index 3: Name (column 4)
        Index 4: Qty (column 5)
        Index 5: UnitPrice (column 6)
        Index 6: Total (column 7)
        Index 7: used_coupon (column 8) ← ตรวจสอบที่นี่ (โค้ตที่ใช้ไปแล้ว)
        Index 8: discount_amount (column 9)
        Index 9: payment_method (column 10)
        Index 10: received_coupon (column 11) ← ข้ามนี้ (โค้ตที่ได้รับเป็นส่วนลด)
        
        Note: Column 11 (received_coupon) = โค้ตที่ลูกค้าได้รับมา ไม่ใช่โค้ตที่ใช้ไปแล้ว
        """
        used_coupons = set()
        try:
            # ลองใช้ self.sheet_sales ถ้าไม่ได้ก็ลองใช้ self.worksheet
            sheet = self.sheet_sales if hasattr(self, 'sheet_sales') and self.sheet_sales else self.worksheet
            if not sheet:
                print("❌ No sheet available")
                return used_coupons
            
            records = sheet.get_all_values()
            
            if len(records) > 1:
                # Skip header row (records[0])
                for idx, row in enumerate(records[1:], start=1):
                    # ข้ามแถวว่าง
                    if not row or all(cell.strip() == "" for cell in row):
                        continue
                    
                    # ตรวจสอบ index 7 = column 8 (used_coupon) เท่านั้น
                    if len(row) > 7 and row[7]:
                        coupon = row[7].strip()
                        if coupon and coupon.upper() not in ["-", "", "NONE"]:
                            coupon_upper = coupon.upper()
                            used_coupons.add(coupon_upper)
            
        except Exception as e:
            print(f"❌ ERROR in check_used_coupons: {e}")
            import traceback
            traceback.print_exc()
        
        return used_coupons

    def update_discount_display(self, event=None):
        """อัปเดตการแสดงผลส่วนลดและตรวจสอบสถานะโค้ต"""
        total_amount = self.update_cart_ui()
        discount_code = self.discount_code_entry.get().strip().upper()
        discount_amount = 0.0
        
        coupon_status = ""
        status_color = "#27AE60"
        show_warning = False
        is_used_coupon = False
        
        if discount_code:
            # ตรวจสอบว่าเป็นโค้ตที่เคยใช้แล้วหรือไม่
            # เฉพาะถ้าเป็น "DISC10-XXXXX", "SPECIAL", "DISCXX" หรือ custom code ที่ไม่เป็นตัวเลขเพียงอย่างเดียว
            used_coupons = self.check_used_coupons()
            
            if discount_code in used_coupons:
                # โค้ตนี้เคยใช้แล้ว
                coupon_status = "✗ ใช้แล้ว"
                status_color = "#E74C3C"
                discount_amount = 0.0
                is_used_coupon = True
                if discount_code != self.last_coupon_checked:
                    show_warning = True
                    self.last_coupon_checked = discount_code
            
            elif discount_code.startswith("DISC10"):
                # DISC10 ยังไม่เคยใช้
                discount_amount = total_amount * 0.10
                coupon_status = "✓ DISC10"
            
            elif discount_code == "SPECIAL":
                # SPECIAL ยังไม่เคยใช้
                discount_amount = total_amount * 0.15
                coupon_status = "✓ SPECIAL"
            
            elif discount_code.startswith("DISC"):
                # DISCXX format
                try:
                    percent = int(discount_code.split("-")[0].replace("DISC", ""))
                    discount_amount = total_amount * (percent / 100)
                    coupon_status = f"✓ DISC{percent}"
                except:
                    discount_amount = 0.0
                    coupon_status = "✗ ไม่ถูกต้อง"
                    status_color = "#E74C3C"
            
            else:
                # โค้ตที่ไม่รู้จัก
                coupon_status = "⚠ ไม่รู้จัก"
                status_color = "#F39C12"
                discount_amount = 0.0
                self.last_coupon_checked = discount_code
        
        else:
            self.last_coupon_checked = ""
        
        final_price = max(0, total_amount - discount_amount)
        
        # อัปเดตการแสดงผล
        self.lbl_discount_amount.configure(text=f"ส่วนลด: {discount_amount:,.2f} บาท" if discount_amount > 0 else "ส่วนลด: 0.00 บาท")
        self.lbl_final_price.configure(text=f"ราคาสุดท้าย: {final_price:,.2f} บาท")
        self.lbl_coupon_status.configure(text=coupon_status, text_color=status_color)
        
        # เปลี่ยนสีตามสถานะส่วนลด
        if discount_amount > 0:
            self.lbl_discount_amount.configure(text_color="#27AE60")
            self.lbl_final_price.configure(text_color="#27AE60")
        elif is_used_coupon:
            self.lbl_discount_amount.configure(text_color="#E74C3C")
            self.lbl_final_price.configure(text_color="#E74C3C")
        else:
            self.lbl_discount_amount.configure(text_color="#E74C3C")
            self.lbl_final_price.configure(text_color="#F39C12")
        
        # แสดงเตือนเมื่อพบโค้ตที่ใช้แล้ว
        if show_warning and self.app_running and self.winfo_exists():
            self.after(100, lambda: messagebox.showwarning(
                "⚠️ คูปองนี้ใช้ไปแล้ว!", 
                f"❌ โค้ต '{discount_code}' ได้ถูกใช้งานไปแล้ว\n\n"
                f"💡 คูปองแต่ละใบสามารถใช้ได้แค่ครั้งเดียวเท่านั้น\n\n"
                f"กรุณาตรวจสอบโค้ตของลูกค้าอีกครั้ง"
            ))
        
        # ปิดใช้งานปุ่ม checkout ถ้ามีโค้ตที่ใช้แล้ว
        if is_used_coupon:
            self.btn_checkout.configure(state="disabled", text="❌ ไม่สามารถใช้โค้ตนี้ได้")
        elif self.cart_items:
            self.btn_checkout.configure(state="normal", text="💰 ชำระเงิน / ตัดสต็อก")
        else:
            self.btn_checkout.configure(state="disabled", text="💰 ชำระเงิน / ตัดสต็อก")

    def process_checkout(self):
        if not self.cart_items:
            messagebox.showwarning("เตือน", "ไม่มีสินค้าในตะกร้า")
            return
        total_amount = self.update_cart_ui()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        coupon_code = self.discount_code_entry.get().strip().upper()
        payment_method = self.payment_method.get()
        
        # ตรวจสอบว่าโค้ตถูกใช้แล้วหรือไม่ (ทั้งหมด DISC10, SPECIAL, DISCX และโค้ตอื่นๆ)
        if coupon_code:
            used_coupons = self.check_used_coupons()
            if coupon_code in used_coupons:
                messagebox.showerror("⚠️ โค้ตถูกใช้แล้ว", 
                    f"โค้ต '{coupon_code}' ได้ถูกใช้แล้ว\n❌ สามารถใช้ได้แค่ครั้งเดียวเท่านั้น\n\n"
                    f"กรุณาตรวจสอบโค้ตอีกครั้ง")
                self.discount_code_entry.delete(0, "end")
                return
        
        # คำนวณยอดส่วนลด
        discount_amount = 0.0
        used_coupon = ""  # โค้ตที่ใช้สำหรับส่วนลด
        received_coupon = ""  # โค้ตที่ได้รับ
        
        if coupon_code:
            used_coupon = coupon_code
            if coupon_code.startswith("DISC10"):
                discount_amount = total_amount * 0.10
            elif coupon_code == "SPECIAL":
                discount_amount = total_amount * 0.15
            elif coupon_code.startswith("DISC"):
                try:
                    percent = int(coupon_code.split("-")[0].replace("DISC", ""))
                    discount_amount = total_amount * (percent / 100)
                except:
                    discount_amount = 0.0
        
        # ตรวจสอบว่าลูกค้าได้รับโค้ตใหม่หรือไม่ (ซื้อครบ 200 บาท)
        final_amount = total_amount - discount_amount
        if final_amount >= 200:
            received_coupon = f"DISC10-{datetime.now().strftime('%M%S')}"
        
        self.btn_checkout.configure(state="disabled", text="กำลังบันทึก...")
        threading.Thread(target=self.run_checkout_thread, 
                         args=(timestamp, total_amount, used_coupon, discount_amount, payment_method, received_coupon), daemon=True).start()

    def run_checkout_thread(self, timestamp, total_amount, used_coupon, discount_amount, payment_method, received_coupon):
        if not self.app_running: return 
        try:
            receipt_id = self.get_next_receipt_id()
            sales_rows = []
            items_for_receipt = []  # เก็บข้อมูลสินค้าสำหรับใบเสร็จ
            
            for item in self.cart_items:
                # คอลัมน์ที่ 7: โค้ตที่ใช้สำหรับส่วนลด
                # คอลัมน์ที่ 8: ยอดส่วนลด
                # คอลัมน์ที่ 9: วิธีการจ่าย
                # คอลัมน์ที่ 10: โค้ตที่ได้รับ
                # คอลัมน์ที่ 11: สถานะการยกเลิก (Cancel)
                row = [receipt_id, timestamp, item['barcode'], item['name'], 
                       item['qty'], item['price'], item['total'], used_coupon, discount_amount, 
                       payment_method, received_coupon, "No"]  # "No" สำหรับ Cancel column
                sales_rows.append(row)
                
                # เก็บข้อมูลสำหรับ PDF ใบเสร็จ
                items_for_receipt.append({
                    'name': item['name'],
                    'qty': item['qty'],
                    'price': item['price'],
                    'total': item['total']
                })
            
            self.sheet_sales.append_rows(sales_rows)
            for item in self.cart_items:
                # ไม่ลดสต็อกสำหรับรายการแบบ manual (barcode เริ่มต้นด้วย MANUAL-)
                if item['barcode'].startswith('MANUAL-'):
                    continue
                current_qty_cell = self.sheet_products.cell(int(item['row_idx']), 8).value
                current_qty = int(current_qty_cell) if current_qty_cell else 0
                new_qty = max(0, current_qty - item['qty'])
                self.sheet_products.update_cell(int(item['row_idx']), 8, new_qty)
            
            # สร้างและปริ้นใบเสร็จ
            self.process_receipt_after_checkout(
                receipt_id, timestamp, items_for_receipt, 
                total_amount, discount_amount, total_amount - discount_amount,
                payment_method, used_coupon, received_coupon
            )
            
            if self.app_running and self.winfo_exists():
                self.after(0, lambda: self.finish_checkout(received_coupon))
        except Exception as e:
            if self.app_running and self.winfo_exists():
                self.after(0, lambda: messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {e}"))
                self.after(0, lambda: self.btn_checkout.configure(state="normal", text="💰 ชำระเงิน / ตัดสต็อก"))

    def finish_checkout(self, received_coupon):
        if not self.app_running: return
        self.cart_items = []
        self.discount_code_entry.delete(0, "end")
        self.payment_method.set("เงินสด")
        self.update_cart_ui()
        self.btn_checkout.configure(state="normal", text="💰 ชำระเงิน / ตัดสต็อก")
        self.play_sound("success")
        self.load_inventory_data()
        if received_coupon: self.show_coupon_qr(received_coupon)
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
        ctk.CTkLabel(qr_window, text=f"CODE: {code}", font=("Kanit", 20, "bold")).pack(pady=10)
        ctk.CTkButton(qr_window, text="✓ ปิด", command=qr_window.destroy, border_width=2, border_color="#2CC985").pack(pady=10)

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
        btn_refresh = ctk.CTkButton(frame_top, text="🔄 รีเฟรช", command=self.load_inventory_data, width=100,
                                   border_width=2, border_color="#3498DB")
        btn_refresh.pack(side="left", padx=5)
        
        # ปุ่ม toggle image loading
        self.btn_toggle_images = ctk.CTkButton(frame_top, text="🖼️ โหลดรูป: เปิด", command=self.toggle_image_loading, 
                                               width=150, border_width=2, border_color="#27AE60")
        self.btn_toggle_images.pack(side="left", padx=5)
        
        ctk.CTkLabel(frame_top, text="* ดับเบิ้ลคลิกที่จำนวนเพื่อแก้ไขสต็อก", text_color="gray").pack(side="left", padx=10)

        columns = ("ID", "Barcode", "Name", "Brand", "Car Model", "Detail", "Cost", "Stock", "Price", "ImageID")
        self.tree = ttk.Treeview(frame_list, columns=columns, show="headings")
        headers = ["ID", "Barcode", "Name", "Brand", "Car Model", "Detail", "Cost", "Stock", "Price", "ImageID"]
        widths = [40, 100, 150, 80, 80, 80, 60, 60, 60, 0]  # 10 columns total, ImageID hidden (width=0)
        for h, w in zip(headers, widths):
            self.tree.heading(h, text=h)
            self.tree.column(h, width=w, anchor="center")
            if h == "ImageID": self.tree.column(h, width=0, stretch=False)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_product_select)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        btn_add = ctk.CTkButton(frame_list, text="➕ เพิ่มสินค้าใหม่", command=self.open_add_product_window, 
                                fg_color="#F39C12", border_width=2, border_color="#D4860D")
        btn_add.pack(fill="x", pady=5)

        # ปุ่มปริ้นลาเบล
        print_frame = ctk.CTkFrame(frame_list, fg_color="transparent")
        print_frame.pack(fill="x", pady=5)
        
        btn_print_label = ctk.CTkButton(print_frame, text="🖨️ ปริ้นลาเบล", command=self.print_barcode_label,
                                       fg_color="#2E86C1", border_width=2, border_color="#1E5BA8")
        btn_print_label.pack(side="left", fill="x", expand=True, padx=2)
        
        btn_printer_settings = ctk.CTkButton(print_frame, text="⚙️ ตั้งค่าปริ้น", command=self.open_printer_settings,
                                            fg_color="#7D3C98", border_width=2, border_color="#5B2C78", width=120)
        btn_printer_settings.pack(side="left", padx=2)

        # --- RIGHT PANEL ---
        frame_detail = ctk.CTkFrame(paned, width=400)
        frame_detail.pack(side="right", fill="y", padx=5, pady=5)
        
        self.image_label = ctk.CTkLabel(frame_detail, text="[No Image]", width=200, height=200, fg_color="gray30")
        self.image_label.pack(pady=10)
        
        # ปุ่ม retry โหลดรูป
        self.current_image_id = None
        btn_retry_image = ctk.CTkButton(frame_detail, text="🔄 โหลดรูปใหม่", command=self.retry_load_image,
                                       height=30, border_width=2, border_color="#3498DB")
        btn_retry_image.pack(pady=5, padx=10, fill="x")
        
        # ปุ่มปริ้นลาเบลรายการเดียว
        btn_print_single = ctk.CTkButton(frame_detail, text="🖨️ ปริ้นลาเบลสินค้านี้", command=self.print_single_barcode,
                                        height=30, border_width=2, border_color="#2E86C1", fg_color="#2E86C1")
        btn_print_single.pack(pady=5, padx=10, fill="x")

        # ====== Product Details Box ======
        detail_box = ctk.CTkFrame(frame_detail, fg_color="gray25", corner_radius=8)
        detail_box.pack(fill="both", expand=True, padx=5, pady=10)

        # Row 1: Name + Brand
        row1_frame = ctk.CTkFrame(detail_box, fg_color="transparent")
        row1_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        left1_frame = ctk.CTkFrame(row1_frame, fg_color="transparent")
        left1_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        ctk.CTkLabel(left1_frame, text="ชื่อสินค้า:", font=("Kanit", 16, "bold"), text_color="#FFD700").pack(anchor="w", pady=(0, 2))
        self.lbl_info_name = ctk.CTkLabel(left1_frame, text="-", font=("Kanit", 16, "bold"), text_color="#FFFFFF")
        self.lbl_info_name.pack(anchor="w")
        
        right1_frame = ctk.CTkFrame(row1_frame, fg_color="transparent")
        right1_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        ctk.CTkLabel(right1_frame, text="ยี่ห้อ:", font=("Kanit", 16, "bold"), text_color="#FFD700").pack(anchor="w", pady=(0, 2))
        self.lbl_info_brand = ctk.CTkLabel(right1_frame, text="-", font=("Kanit", 16), text_color="#E0E0E0")
        self.lbl_info_brand.pack(anchor="w")
        
        # Row 2: Car Model + Cost
        row2_frame = ctk.CTkFrame(detail_box, fg_color="transparent")
        row2_frame.pack(fill="x", padx=10, pady=5)
        
        left2_frame = ctk.CTkFrame(row2_frame, fg_color="transparent")
        left2_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        ctk.CTkLabel(left2_frame, text="รุ่นที่ใช้:", font=("Kanit", 16, "bold"), text_color="#FFD700").pack(anchor="w", pady=(0, 2))
        self.lbl_info_car_model = ctk.CTkLabel(left2_frame, text="-", font=("Kanit", 16), text_color="#E0E0E0")
        self.lbl_info_car_model.pack(anchor="w")
        
        right2_frame = ctk.CTkFrame(row2_frame, fg_color="transparent")
        right2_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        ctk.CTkLabel(right2_frame, text="ราคาทุน:", font=("Kanit", 16, "bold"), text_color="#FFD700").pack(anchor="w", pady=(0, 2))
        self.lbl_info_cost = ctk.CTkLabel(right2_frame, text="-", font=("Kanit", 16), text_color="#E0E0E0")
        self.lbl_info_cost.pack(anchor="w")
        
        # Row 3: Stock + Price
        row3_frame = ctk.CTkFrame(detail_box, fg_color="transparent")
        row3_frame.pack(fill="x", padx=10, pady=5)
        
        left3_frame = ctk.CTkFrame(row3_frame, fg_color="transparent")
        left3_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        ctk.CTkLabel(left3_frame, text="จำนวนสต็อก:", font=("Kanit", 16, "bold"), text_color="#FFD700").pack(anchor="w", pady=(0, 2))
        self.lbl_info_stock = ctk.CTkLabel(left3_frame, text="- ชิ้น", font=("Kanit", 16, "bold"), text_color="#00FFFF")
        self.lbl_info_stock.pack(anchor="w")
        
        right3_frame = ctk.CTkFrame(row3_frame, fg_color="transparent")
        right3_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        ctk.CTkLabel(right3_frame, text="ราคาขาย:", font=("Kanit", 16, "bold"), text_color="#FFD700").pack(anchor="w", pady=(0, 2))
        self.lbl_info_price = ctk.CTkLabel(right3_frame, text="-", font=("Kanit", 16, "bold"), text_color="#00FF00")
        self.lbl_info_price.pack(anchor="w")
        
        # Row 4: Detail (Full width)
        ctk.CTkLabel(detail_box, text="รายละเอียด:", font=("Kanit", 16, "bold"), text_color="#FFD700").pack(anchor="w", padx=10, pady=(5, 2))
        self.txt_info_detail = ctk.CTkTextbox(detail_box, height=70, font=("Kanit", 16))
        self.txt_info_detail.pack(fill="both", expand=True, padx=10, pady=(0, 10))
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
            new_stock = ctk.CTkInputDialog(text=f"แก้ไขสต็อกสินค้า: {item_values[2]}", title="Update Stock", font=("Kanit", 16, "bold")).get_input()
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
                    safe_row = (row + [""] * 10)[:10]  # 10 columns: ID, Barcode, Name, Brand, Car Model, Detail, Cost, Stock, Price, ImageID
                    if safe_row[7] == "": safe_row[7] = "0"  # Stock
                    self.all_inventory_data.append((str(idx), safe_row))
                    self.tree.insert("", "end", values=safe_row, tags=(str(idx),))
        except Exception as e:
            print(f"Load Error: {e}")

    def on_product_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        vals = self.tree.item(selected)['values']
        safe_vals = list(vals) + [""]*10
        # Column indices: 0=ID, 1=Barcode, 2=Name, 3=Brand, 4=CarModel, 5=Detail, 6=Cost, 7=Stock, 8=Price, 9=ImageID
        
        # Update all labels
        self.lbl_info_name.configure(text=str(safe_vals[2]))  # Name
        self.lbl_info_brand.configure(text=str(safe_vals[3]) if safe_vals[3] else "-")  # Brand
        self.lbl_info_car_model.configure(text=str(safe_vals[4]) if safe_vals[4] else "-")  # Car Model
        self.lbl_info_cost.configure(text=f"฿{float(safe_vals[6]) if safe_vals[6] else 0:,.2f}")  # Cost
        self.lbl_info_stock.configure(text=f"{safe_vals[7]} ชิ้น")  # Stock
        
        try:
            price_val = float(safe_vals[8]) if safe_vals[8] else 0
            self.lbl_info_price.configure(text=f"฿{price_val:,.2f}")  # Price
        except:
            self.lbl_info_price.configure(text="-")
        
        detail_txt = str(safe_vals[5]) if safe_vals[5] else "-"  # Detail
        self.txt_info_detail.configure(state="normal")
        self.txt_info_detail.delete("0.0", "end")
        self.txt_info_detail.insert("0.0", detail_txt)
        self.txt_info_detail.configure(state="disabled")

        # เก็บ product_barcode (safe_vals[1]) สำหรับใช้เป็นชื่อไฟล์รูป
        product_barcode = str(safe_vals[1]).strip()  # Barcode อยู่ที่ index 1
        img_id = str(safe_vals[9]).strip()  # Google Drive file ID อยู่ที่ index 9
        
        self.display_image(img_id, product_barcode)

    def display_image(self, file_id, product_barcode=None):
        if not file_id or file_id == "None":
            self.image_label.configure(image=None, text="[No Image]")
            self.current_image_id = None
            self.current_product_barcode = None
            return
        
        # ถ้าปิด image loading
        if not self.enable_image_loading:
            self.image_label.configure(image=None, text="[โหลดรูปปิดไว้]")
            return
        
        self.current_image_id = file_id
        self.current_product_barcode = product_barcode
        # สร้าง thread ใหม่
        new_thread = threading.Thread(target=self.download_and_show_image, args=(file_id, product_barcode), daemon=True)
        with self.image_thread_lock:
            self.current_image_thread = new_thread
        new_thread.start()

    def get_local_image_path(self, product_barcode):
        """หาเส้นทางไฟล์รูปท้องถิ่น"""
        if not product_barcode:
            return None
        
        # ลองหาไฟล์กับนามสกุล png, jpg, jpeg
        for ext in ['.png', '.jpg', '.jpeg']:
            path = os.path.join(self.img_folder, f"{product_barcode}{ext}")
            if os.path.exists(path):
                return path
        return None

    def _save_local_image(self, pil_image, product_barcode):
        """บันทึกรูปลงโฟลเดอร์ img สำหรับใช้ครั้งต่อไป"""
        if not pil_image or not product_barcode:
            return False
        
        try:
            # สร้างโฟลเดอร์ img ถ้ายังไม่มี
            os.makedirs(self.img_folder, exist_ok=True)
            
            # บันทึกเป็น PNG
            filename = f"{product_barcode}.png"
            filepath = os.path.join(self.img_folder, filename)
            
            pil_image.save(filepath, 'PNG')
            print(f"💾 บันทึกรูปลงโฟลเดอร์ local: {filepath}")
            return True
            
        except Exception as e:
            print(f"⚠ ไม่สามารถบันทึกรูป local: {e}")
            return False

    def retry_load_image(self):
        """ลองโหลดรูปใหม่"""
        if self.current_image_id:
            with self.image_thread_lock:
                # ยกเลิก thread เก่า
                if self.current_image_thread is not None and self.current_image_thread.is_alive():
                    # รอให้ thread เก่าหยุด (max 1 วินาที)
                    pass
            
            self.image_label.configure(text="[กำลังโหลด...]")
            # สร้าง thread ใหม่
            new_thread = threading.Thread(target=self.download_and_show_image, args=(self.current_image_id, self.current_product_barcode), daemon=True)
            with self.image_thread_lock:
                self.current_image_thread = new_thread
            new_thread.start()

    def toggle_image_loading(self):
        """เปิด/ปิด การโหลดรูป"""
        self.enable_image_loading = not self.enable_image_loading
        status = "เปิด" if self.enable_image_loading else "ปิด"
        color = "#27AE60" if self.enable_image_loading else "#E74C3C"
        self.btn_toggle_images.configure(text=f"🖼️ โหลดรูป: {status}", fg_color=color)
        
        # ถ้าเปิดก็ลองโหลดรูปใหม่
        if self.enable_image_loading and self.current_image_id:
            self.display_image(self.current_image_id, self.current_product_barcode)

    def download_and_show_image(self, file_id, product_barcode=None):
        # ตรวจสอบว่า thread นี้ยังเป็น thread ปัจจุบันหรือไม่
        with self.image_thread_lock:
            if file_id != self.current_image_id:
                # thread นี้ถูกแทนที่แล้ว ให้หยุด
                return
        
        if not self.app_running: return
        if not file_id or file_id == "None" or file_id.strip() == "":
            return
        
        # ลองโหลดรูปจากเครื่องก่อน
        local_image_path = self.get_local_image_path(product_barcode)
        if local_image_path:
            try:
                print(f"💾 โหลดรูปจากโฟลเดอร์ local: {local_image_path}")
                with open(local_image_path, 'rb') as f:
                    img_data = f.read()
                pil_img = Image.open(io.BytesIO(img_data))
                pil_img.load()
                pil_img = pil_img.resize((200, 200))
                if self.app_running and self.winfo_exists():
                    self.after(0, self.update_image_ui, pil_img)
                return
            except Exception as e:
                print(f"⚠ ไม่สามารถโหลดรูปจาก local: {e}")
        
        # ถ้าไม่มีในเครื่อง ดาวน์โหลดจาก Google Drive
        print(f"📥 ดาวน์โหลดรูปจาก Google Drive...")
        if not self.enable_image_loading:
            self.image_label.configure(image=None, text="[โหลดรูปปิดไว้]")
            return
        
        # ลองดาวน์โหลดพร้อม retry mechanism
        max_retries = 3
        import time
        
        for attempt in range(max_retries):
            # ตรวจสอบอีกครั้งว่า thread นี้ยังเป็น current หรือไม่
            with self.image_thread_lock:
                if file_id != self.current_image_id:
                    return  # ถูกแทนที่แล้ว
            
            wait_time = 2 + (attempt * 3)  # wait 2, 5, 8 วินาที
            
            try:
                # ลองดาวน์โหลดแบบ chunked ก่อน
                if self._try_chunked_download(file_id, product_barcode):
                    return
                # ถ้า chunked ไม่ได้ ลอง direct download
                elif self._try_direct_download(file_id, product_barcode):
                    return
                
                # ถ้าทั้งสองวิธีไม่ได้
                if attempt < max_retries - 1:
                    print(f"  ⏳ กำลังลองใหม่ใน {wait_time} วินาที...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                error_str = str(e).upper()
                if "SSL" in error_str or "DECRYPTION" in error_str or "WRONG_VERSION" in error_str:
                    print(f"⚠ ข้อผิดพลาด SSL/Network (ครั้งที่ {attempt+1}/{max_retries}): {e}")
                elif "416" in error_str or "RANGE" in error_str:
                    print(f"⚠ ข้อผิดพลาด Range (ครั้งที่ {attempt+1}/{max_retries}): {e}")
                elif "NONETYPE" in error_str:
                    print(f"⚠ ข้อผิดพลาด Resource (ครั้งที่ {attempt+1}/{max_retries}): {e}")
                else:
                    print(f"⚠ ข้อผิดพลาดการโหลดรูป (ครั้งที่ {attempt+1}/{max_retries}): {e}")
                
                if attempt == max_retries - 1:
                    # ลองครั้งสุดท้ายแล้ว แสดง error
                    print(f"❌ ไม่สามารถโหลดรูปได้หลังจากพยายาม {max_retries} ครั้ง")
                    print(f"💡 แนะนำ: ลองปิดการโหลดรูป หรือตรวจสอบ network connection")
                    if self.app_running and self.winfo_exists():
                        self.after(0, lambda: self.image_label.configure(image=None, text="[เครือข่ายขัดข้อง]"))
                        # ปิดการโหลดรูปอัตโนมัติ
                        self.after(0, lambda: self.btn_toggle_images.configure(text=f"🖼️ โหลดรูป: ปิด", fg_color="#E74C3C"))
                        self.enable_image_loading = False
                else:
                    print(f"  ⏳ กำลังลองใหม่ใน {wait_time} วินาที...")
                    time.sleep(wait_time)
                    if not self.app_running: 
                        return
        if not file_id or file_id == "None" or file_id.strip() == "":
            return
        
        # ถ้าปิด image loading ให้ skip
        if not self.enable_image_loading:
            self.image_label.configure(image=None, text="[โหลดรูปปิดไว้]")
            return
        
        # ลองดาวน์โหลดพร้อม retry mechanism
        max_retries = 3
        import time
        
        for attempt in range(max_retries):
            # ตรวจสอบอีกครั้งว่า thread นี้ยังเป็น current หรือไม่
            with self.image_thread_lock:
                if file_id != self.current_image_id:
                    return  # ถูกแทนที่แล้ว
            
            wait_time = 2 + (attempt * 3)  # wait 2, 5, 8 วินาที
            
            try:
                # ลองดาวน์โหลดแบบ chunked ก่อน
                if self._try_chunked_download(file_id, product_barcode):
                    return
                # ถ้า chunked ไม่ได้ ลอง direct download
                elif self._try_direct_download(file_id, product_barcode):
                    return
                
                # ถ้าทั้งสองวิธีไม่ได้
                if attempt < max_retries - 1:
                    print(f"  ⏳ กำลังลองใหม่ใน {wait_time} วินาที...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                error_str = str(e).upper()
                if "SSL" in error_str or "DECRYPTION" in error_str or "WRONG_VERSION" in error_str:
                    print(f"⚠ ข้อผิดพลาด SSL/Network (ครั้งที่ {attempt+1}/{max_retries}): {e}")
                elif "416" in error_str or "RANGE" in error_str:
                    print(f"⚠ ข้อผิดพลาด Range (ครั้งที่ {attempt+1}/{max_retries}): {e}")
                elif "NONETYPE" in error_str:
                    print(f"⚠ ข้อผิดพลาด Resource (ครั้งที่ {attempt+1}/{max_retries}): {e}")
                else:
                    print(f"⚠ ข้อผิดพลาดการโหลดรูป (ครั้งที่ {attempt+1}/{max_retries}): {e}")
                
                if attempt == max_retries - 1:
                    # ลองครั้งสุดท้ายแล้ว แสดง error
                    print(f"❌ ไม่สามารถโหลดรูปได้หลังจากพยายาม {max_retries} ครั้ง")
                    print(f"💡 แนะนำ: ลองปิดการโหลดรูป หรือตรวจสอบ network connection")
                    if self.app_running and self.winfo_exists():
                        self.after(0, lambda: self.image_label.configure(image=None, text="[เครือข่ายขัดข้อง]"))
                        # ปิดการโหลดรูปอัตโนมัติ
                        self.after(0, lambda: self.btn_toggle_images.configure(text=f"🖼️ โหลดรูป: ปิด", fg_color="#E74C3C"))
                        self.enable_image_loading = False
                else:
                    print(f"  ⏳ กำลังลองใหม่ใน {wait_time} วินาที...")
                    time.sleep(wait_time)

    def _try_chunked_download(self, file_id, product_barcode=None):
        """ลองดาวน์โหลดแบบ chunked (128KB) - ใช้สำหรับไฟล์ขนาดใหญ่"""
        fh = None
        temp = None
        try:
            import ssl
            # สร้าง SSL context ที่ไม่มีการตรวจสอบ certificate (ชั่วคราว)
            try:
                ssl._create_default_https_context = ssl._create_unverified_context
            except:
                pass
                
            request = self.drive_service.files().get_media(fileId=file_id)
            request.http.timeout = 30
            
            fh = io.BytesIO()
            # ตั้งค่า chunksize เป็น 128KB (ลดลงมากเพื่อหลีกเลี่ยง SSL issues)
            downloader = MediaIoBaseDownload(fh, request, chunksize=128*1024)
            done = False
            
            while done is False:
                if not self.app_running: 
                    return False
                try:
                    status, done = downloader.next_chunk()
                except Exception as chunk_error:
                    error_str = str(chunk_error).upper()
                    if "416" in error_str or "RANGE" in error_str:
                        # File range error - อาจจะเป็นไฟล์ที่ไม่รองรับ chunked download
                        print(f"ไฟล์นี้ไม่รองรับ chunked download: {chunk_error}")
                        return False
                    raise
            
            # สำเร็จ - บันทึกรูป
            fh.seek(0)
            temp = Image.open(fh)
            temp.load()
            pil_img = temp.copy()
            pil_img = pil_img.resize((200, 200))
            
            # บันทึกลงเครื่องสำหรับใช้ครั้งต่อไป
            if product_barcode:
                self._save_local_image(pil_img, product_barcode)
            
            print(f"✓ โหลดรูปสำเร็จ (วิธี Chunked)")
            if self.app_running and self.winfo_exists():
                self.after(0, self.update_image_ui, pil_img)
            return True
            
        except Exception as e:
            error_str = str(e).upper()
            # ถ้าไม่ใช่ range error ให้ raise
            if "416" not in error_str and "RANGE" not in error_str:
                raise
            return False
        finally:
            # ทำความสะอาด resource อย่างปลอดภัย - ไม่ close temp เพราะ PIL image ยังใช้
            pass

    def _try_direct_download(self, file_id, product_barcode=None):
        """ดาวน์โหลดรูปแบบตรง (ไม่ใช้ chunked) - สำหรับ SSL retry"""
        try:
            if not self.app_running or not self.drive_service:
                return False
                
            # Download โดยไม่ใช้ MediaIoBaseDownload
            request = self.drive_service.files().get_media(fileId=file_id)
            request.http.timeout = 60  # timeout นานขึ้นสำหรับ direct download
            
            fh = io.BytesIO()
            # ใช้ execute() เพื่อ download ทั้งไฟล์พร้อม
            media_file = request.execute()
            
            fh.write(media_file)
            fh.seek(0)
            
            temp = Image.open(fh)
            temp.load()
            pil_img = temp.copy()
            pil_img = pil_img.resize((200, 200))
            
            # บันทึกลงเครื่องสำหรับใช้ครั้งต่อไป
            if product_barcode:
                self._save_local_image(pil_img, product_barcode)
            
            print(f"✓ โหลดรูปสำเร็จ (วิธี Direct)")
            if self.app_running and self.winfo_exists():
                self.after(0, self.update_image_ui, pil_img)
            return True
            
        except Exception as e:
            error_str = str(e).upper()
            if "SSL" in error_str or "DECRYPTION" in error_str:
                print(f"⚠ ข้อผิดพลาด SSL ในการโหลดแบบ direct: {e}")
            else:
                print(f"❌ โหลดแบบ direct ล้มเหลว: {e}")
            return False
        finally:
            # ทำความสะอาด resource อย่างปลอดภัย - ไม่ close temp เพราะ PIL image ยังใช้
            pass

    def update_image_ui(self, pil_image):
        """อัปเดต UI ด้วยรูป (ต้องเรียกจาก main thread via after)"""
        if not self.app_running or not self.winfo_exists(): 
            return
        try:
            # ตรวจสอบว่า pil_image ยังใช้ได้หรือไม่
            if pil_image is None:
                self.image_label.configure(image=None, text="[ไม่สามารถแสดงรูป]")
                return
            
            # สร้าง CTkImage ที่ถูกต้องสำหรับ HighDPI displays
            ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(200, 200))
            self.image_label.configure(image=ctk_img, text="")
            # เก็บ reference เพื่อป้องกัน garbage collection
            self.current_image_ref = ctk_img
        except Exception as e:
            print(f"Error updating image UI: {e}")
            self.image_label.configure(image=None, text="[ไม่สามารถแสดงรูป]")

    # =========================================
    # ส่วนเพิ่มสินค้าใหม่
    # =========================================
    def open_add_product_window(self):
        self.add_window = ctk.CTkToplevel(self)
        self.add_window.title("เพิ่มสินค้า")
        self.add_window.geometry("450x750")
        self.add_window.attributes("-topmost", True)
        
        # Frame สำหรับ Barcode + ปุ่มสร้าง
        barcode_frame = ctk.CTkFrame(self.add_window, fg_color="transparent")
        barcode_frame.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(barcode_frame, text="Barcode:", font=("Kanit", 12)).pack(side="left", padx=5)
        self.new_barcode = ctk.CTkEntry(barcode_frame, placeholder_text="Barcode (ว่างเว้น = auto gen)")
        self.new_barcode.pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkButton(barcode_frame, text="🔄 Gen", command=self.generate_barcode_for_product,
                     width=60, height=32, border_width=2, border_color="#FF9800").pack(side="left", padx=5)
        
        self.new_name = self.create_styled_entry(self.add_window, "ชื่อสินค้า", "NAME")
        self.new_brand = self.create_styled_entry(self.add_window, "ยี่ห้อ", "BRAND")
        self.new_car_model = self.create_styled_entry(self.add_window, "รุ่นรถ", "CAR MODEL")
        self.new_detail = self.create_styled_entry(self.add_window, "รายละเอียด", "DETAIL")
        self.new_cost = self.create_styled_entry(self.add_window, "ราคาทุน", "COST")
        self.new_stock = self.create_styled_entry(self.add_window, "จำนวนเริ่มต้น", "STOCK")
        self.new_price = self.create_styled_entry(self.add_window, "ราคาขาย", "PRICE")
        self.new_image_path = None
        ctk.CTkButton(self.add_window, text="📁 เลือกรูป", command=self.choose_new_image,
                 border_width=2, border_color="#3498DB").pack(pady=5)
        ctk.CTkButton(self.add_window, text="✓ บันทึก", command=self.save_new_product, 
                  fg_color="#2CC985", height=50, border_width=2, border_color="#229954").pack(pady=20, fill="x", padx=20)

    def choose_new_image(self):
        self.new_image_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.png")])

    def generate_barcode_for_product(self):
        """สร้าง Barcode 10 หลักแบบตัวเลขล้วน"""
        import random
        # สร้าง barcode 10 หลักแบบสุ่ม
        new_barcode = ''.join([str(random.randint(0, 9)) for _ in range(10)])
        
        # เคลียร์ช่อง barcode เดิมแล้วกรอก barcode ใหม่
        self.new_barcode.delete(0, "end")
        self.new_barcode.insert(0, new_barcode)
        print(f"✓ สร้าง Barcode: {new_barcode}")

    def save_new_product(self):
        threading.Thread(target=self.run_save_new_product, daemon=True).start()

    def run_save_new_product(self):
        if not self.app_running: return
        
        # ดึง Barcode จากช่องข้อมูล
        barcode = self.new_barcode.get().strip()
        
        # ถ้า Barcode ว่างเว้น ให้สร้างใหม่อัตโนมัติ
        if not barcode:
            import random
            barcode = ''.join([str(random.randint(0, 9)) for _ in range(10)])
            print(f"✓ สร้าง Barcode อัตโนมัติ: {barcode}")
        
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
        # ตรงกับ Google Sheet: ID, Barcode, Name, Brand, Car Model, Detail, Cost, Stock, Price, ImageID
        row = [
            next_id,
            barcode,
            self.new_name.get(),
            self.new_brand.get(),
            self.new_car_model.get(),
            self.new_detail.get(),
            self.new_cost.get(),
            self.new_stock.get(),
            self.new_price.get(),
            image_id
        ]
        self.sheet_products.append_row(row)
        if self.app_running and self.winfo_exists():
            self.after(0, lambda: messagebox.showinfo("สำเร็จ", f"เพิ่มสินค้าแล้ว (Barcode: {barcode})"))
            self.after(0, self.add_window.destroy)
            self.after(0, self.load_inventory_data)

    # =========================================
    # TAB 3: HISTORY Logic (Updated with Barcode)
    # =========================================
    def setup_history_tab(self):
        # เพิ่มการรีเฟรชข้อมูลเมื่อกดแท็บ
        try:
            original_select_tab = self.tabview._segmented_button.configure
            def on_tab_change(*args):
                if self.tabview.get() == "📜 ประวัติการขาย (History)":
                    self.load_history_data()
            self.tabview.bind("<Button-1>", lambda e: self.after(100, lambda: on_tab_change()))
        except:
            pass
        
        # TOP: Filter Frame
        filter_frame = ctk.CTkFrame(self.tab_history, fg_color="gray20")
        filter_frame.pack(fill="x", padx=5, pady=5)
        
        # Single row: Search by Receipt ID + Filter by Date
        filter_search_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        filter_search_frame.pack(fill="x", pady=5)
        
        # Receipt ID Search
        ctk.CTkLabel(filter_search_frame, text="🔍 ค้นหาใบเสร็จ:", font=("Kanit", 12, "bold")).pack(side="left", padx=5)
        
        self.search_receipt_entry = ctk.CTkEntry(filter_search_frame, placeholder_text="ป้อนเลขที่ใบเสร็จ...", width=150, height=32)
        self.search_receipt_entry.pack(side="left", padx=3)
        self.search_receipt_entry.bind("<Return>", lambda e: self.search_receipt_by_id())
        
        ctk.CTkButton(filter_search_frame, text="🔎 ค้นหา", command=self.search_receipt_by_id, 
                     width=85, height=32, border_width=2, border_color="#3498DB").pack(side="left", padx=3)
        
        # Separator
        ctk.CTkLabel(filter_search_frame, text="|", font=("Kanit", 12)).pack(side="left", padx=5)
        
        # Date Filter
        ctk.CTkLabel(filter_search_frame, text="📅 เลือกวันที่ :", font=("Kanit", 12, "bold")).pack(side="left", padx=5)
        
        # ใช้ DateEntry (Calendar Picker) จาก tkcalendar
        self.date_picker = DateEntry(filter_search_frame, width=15, background='blue',
                                     foreground='white', borderwidth=2, year=datetime.now().year,
                                     month=datetime.now().month, day=datetime.now().day)
        self.date_picker.pack(side="left", padx=3)
        
        ctk.CTkButton(filter_search_frame, text="🔍 ค้นหาตามวันที่", command=self.apply_date_filter, 
                     width=130, height=32, border_width=2, border_color="#3498DB").pack(side="left", padx=3)
        
        ctk.CTkButton(filter_search_frame, text="📋 ดูทั้งหมด", command=self.show_all_history, 
                     width=100, height=32, border_width=2, border_color="#27AE60").pack(side="left", padx=3)
        
        paned = ctk.CTkFrame(self.tab_history)
        paned.pack(fill="both", expand=True)

        # LEFT: Receipt List
        left_frame = ctk.CTkFrame(paned, width=400)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkButton(left_frame, text="🔄 โหลดประวัติ", command=self.load_history_data, 
                     border_width=2, border_color="#3498DB").pack(fill="x", pady=5)
        
        self.tree_receipts = ttk.Treeview(left_frame, columns=("ID", "Date", "Payment", "Total"), show="headings")
        self.tree_receipts.heading("ID", text="เลขที่ใบเสร็จ"); self.tree_receipts.column("ID", width=100)
        self.tree_receipts.heading("Date", text="วันที่"); self.tree_receipts.column("Date", width=100)
        self.tree_receipts.heading("Payment", text="การจ่าย"); self.tree_receipts.column("Payment", width=80, anchor="center")
        self.tree_receipts.heading("Total", text="ยอดรวม"); self.tree_receipts.column("Total", width=80, anchor="e")
        self.tree_receipts.pack(fill="both", expand=True)
        self.tree_receipts.bind("<<TreeviewSelect>>", self.on_receipt_select)

        # RIGHT: Receipt Details
        right_frame = ctk.CTkFrame(paned, width=600)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(right_frame, text="รายการสินค้าในบิล", font=("Kanit", 20, "bold")).pack(pady=10)
        
        # เพิ่มช่อง Barcode
        self.tree_rec_items = ttk.Treeview(right_frame, columns=("Barcode", "Name", "Qty", "Price", "Total"), show="headings")
        self.tree_rec_items.heading("Barcode", text="Barcode"); self.tree_rec_items.column("Barcode", width=100)
        self.tree_rec_items.heading("Name", text="สินค้า"); self.tree_rec_items.column("Name", width=180)
        self.tree_rec_items.heading("Qty", text="จำนวน"); self.tree_rec_items.column("Qty", width=60, anchor="center")
        self.tree_rec_items.heading("Price", text="ราคา/หน่วย"); self.tree_rec_items.column("Price", width=80, anchor="e")
        self.tree_rec_items.heading("Total", text="รวม"); self.tree_rec_items.column("Total", width=80, anchor="e")
        self.tree_rec_items.pack(fill="both", expand=True, pady=10)
        
        # เพิ่มส่วนแสดงข้อมูลใบเสร็จ (ยอดรวม, ส่วนลด, โค้ต)
        receipt_info_frame = ctk.CTkFrame(right_frame, fg_color="gray25", corner_radius=8)
        receipt_info_frame.pack(fill="x", padx=5, pady=5)
        
        self.lbl_receipt_coupon_used = ctk.CTkLabel(receipt_info_frame, text="โค้ตที่ใช้: -", 
                                                    font=("Kanit", 12), text_color="#E74C3C")
        self.lbl_receipt_coupon_used.pack(pady=3, padx=10, anchor="w")
        
        self.lbl_receipt_coupon_received = ctk.CTkLabel(receipt_info_frame, text="โค้ตที่ได้รับ: -", 
                                                        font=("Kanit", 12), text_color="#27AE60")
        self.lbl_receipt_coupon_received.pack(pady=3, padx=10, anchor="w")
        
        self.lbl_receipt_summary = ctk.CTkLabel(receipt_info_frame, text="ยอดรวม: 0.00 บาท | ส่วนลด: 0.00 บาท | ยอดสุดท้าย: 0.00 บาท",
                                                font=("Kanit", 13, "bold"), text_color="#2CC985")
        self.lbl_receipt_summary.pack(pady=8, padx=10, anchor="w")
        
        # สถานะการยกเลิก
        self.lbl_receipt_cancelled = ctk.CTkLabel(receipt_info_frame, text="สถานะ: ปกติ", 
                                                  font=("Kanit", 13, "bold"), text_color="#27AE60")
        self.lbl_receipt_cancelled.pack(pady=5, padx=10, anchor="w")
        
        # สร้าง Frame สำหรับปุ่มต่างๆ - ปรับให้มองเห็นได้ชัดเจน
        buttons_frame = ctk.CTkFrame(receipt_info_frame, fg_color="transparent")
        buttons_frame.pack(pady=15, padx=10, fill="both", expand=False)
        
        # ปุ่มรีปริ้นใบเสร็จ
        self.btn_reprint_receipt = ctk.CTkButton(buttons_frame, text="🖨️ รีปริ้นใบเสร็จ", 
                                          command=self.reprint_receipt,
                                          fg_color="#3498DB", hover_color="#2980B9",
                                          font=("Kanit", 12),
                                          height=45,
                                          corner_radius=8)
        self.btn_reprint_receipt.pack(side="left", pady=5, padx=5, fill="both", expand=True)
        
        # ปุ่มยกเลิกใบเสร็จ
        self.btn_cancel_receipt = ctk.CTkButton(buttons_frame, text="🚫 ยกเลิกใบเสร็จ", 
                                          command=self.cancel_receipt,
                                          fg_color="#E74C3C", hover_color="#C0392B",
                                          font=("Kanit", 12),
                                          height=45,
                                          corner_radius=8)
        self.btn_cancel_receipt.pack(side="left", pady=5, padx=5, fill="both", expand=True)

        # โหลด history data ด้วย delay เล็กน้อยเพื่อให้ GUI โหลดเสร็จก่อน
        self.after(500, self.load_history_data)

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
                            # ดึงค่า payment_method (column 9 = index 9)
                            payment_method = row[9] if len(row) > 9 and row[9] else '-'
                            
                            self.sales_history_data[rec_id] = {
                                'date': date_str,
                                'items': [],
                                'total_bill': 0.0,
                                'discount_total': 0.0,
                                'final_total': 0.0,
                                'payment_method': payment_method,  # ประเภทการจ่าย
                                'coupon_used': '-',      # โค้ตที่ใช้สำหรับส่วนลด
                                'coupon_received': '-',  # โค้ตที่ได้รับ
                                'is_cancelled': False  # สถานะการยกเลิก (จะอัปเดตในส่วน try)
                            }
                        
                        try:
                            barcode = row[2]
                            qty = int(row[4])
                            price = float(row[5])
                            total = float(row[6].replace(",", ""))
                            
                            # ดึงค่าโค้ตที่ใช้ (column 8 = index 7)
                            coupon_used = row[7] if len(row) > 7 and row[7] else '-'
                            self.sales_history_data[rec_id]['coupon_used'] = coupon_used
                            
                            # ดึงค่าส่วนลด (column 9 = index 8)
                            discount_amount = 0.0
                            if len(row) > 8:
                                try:
                                    discount_amount = float(row[8]) if row[8] else 0.0
                                except:
                                    discount_amount = 0.0
                            
                            # ดึงค่า payment_method (column 10 = index 9)
                            payment_method = row[9] if len(row) > 9 and row[9] else '-'
                            self.sales_history_data[rec_id]['payment_method'] = payment_method
                            
                            # ดึงค่าโค้ตที่ได้รับ (column 11 = index 10)
                            coupon_received = row[10] if len(row) > 10 and row[10] else '-'
                            self.sales_history_data[rec_id]['coupon_received'] = coupon_received
                            
                            # ดึงค่า is_cancelled (column 12 = index 11) - ตรวจสอบว่า "Yes" หรือไม่
                            is_cancelled = False
                            if len(row) > 11 and row[11]:
                                cancel_value = row[11].strip().lower()
                                is_cancelled = cancel_value == 'yes'
                                print(f"DEBUG: Receipt {rec_id}, Cancel column value: '{row[11]}', is_cancelled: {is_cancelled}")
                            self.sales_history_data[rec_id]['is_cancelled'] = is_cancelled
                            
                            self.sales_history_data[rec_id]['items'].append({
                                'barcode': barcode,
                                'name': row[3],
                                'qty': qty,
                                'price': price,
                                'total': total,
                                'discount_amount': discount_amount
                            })
                            self.sales_history_data[rec_id]['total_bill'] += total
                            # บันทึกยอดส่วนลดจากบรรทัดแรก
                            if len(self.sales_history_data[rec_id]['items']) == 1:
                                self.sales_history_data[rec_id]['discount_total'] = discount_amount
                        except: pass
                
                # คำนวณยอดสุดท้าย (ยอดรวม - ส่วนลด)
                for rec_id in self.sales_history_data:
                    total = self.sales_history_data[rec_id]['total_bill']
                    discount = self.sales_history_data[rec_id]['discount_total']
                    self.sales_history_data[rec_id]['final_total'] = max(0, total - discount)

            if self.app_running and self.winfo_exists():
                self.after(0, self.update_history_ui)
        except Exception as e:
            print(f"History Load Error: {e}")

    def update_history_ui(self):
        for i in self.tree_receipts.get_children(): self.tree_receipts.delete(i)
        
        sorted_ids = sorted(self.sales_history_data.keys(), reverse=True)
        for r_id in sorted_ids:
            data = self.sales_history_data[r_id]
            # แสดงยอดสุดท้าย (ยอดรวม - ส่วนลด)
            final_total = data.get('final_total', data.get('total_bill', 0.0))
            payment_method = data.get('payment_method', '-')
            
            # ถ้าใบเสร็จยกเลิก ให้แสดง "ยกเลิก" และสีแดง
            is_cancelled = data.get('is_cancelled', False)
            if is_cancelled:
                display_id = f"{r_id} (ยกเลิก)"
                item = self.tree_receipts.insert("", "end", values=(display_id, data['date'], payment_method, f"{final_total:,.2f}"))
                self.tree_receipts.item(item, tags=('cancelled',))
            else:
                self.tree_receipts.insert("", "end", values=(r_id, data['date'], payment_method, f"{final_total:,.2f}"))
        
        # กำหนดสี tag สำหรับแถวที่ยกเลิก
        self.tree_receipts.tag_configure('cancelled', foreground='#E74C3C')

    def on_receipt_select(self, event):
        selected = self.tree_receipts.selection()
        if not selected: return
        
        r_id = self.tree_receipts.item(selected[0])['values'][0]
        # ลบ " (ยกเลิก)" จาก ID ถ้ามี (สำหรับรับแสดงข้อมูลที่ถูกต้อง)
        r_id = r_id.replace(" (ยกเลิก)", "")
        
        for i in self.tree_rec_items.get_children(): self.tree_rec_items.delete(i)
        
        if r_id in self.sales_history_data:
            items = self.sales_history_data[r_id]['items']
            for item in items:
                # แสดง Barcode ในตาราง
                self.tree_rec_items.insert("", "end", values=(
                    item['barcode'], 
                    item['name'], item['qty'], f"{item['price']:,.2f}", f"{item['total']:,.2f}"
                ))
            
            # แสดงข้อมูลใบเสร็จ (โค้ต, ยอดรวม, ส่วนลด, ยอดสุดท้าย)
            data = self.sales_history_data[r_id]
            coupon_used = data.get('coupon_used', '-')
            coupon_received = data.get('coupon_received', '-')
            discount_total = data.get('discount_total', 0.0)
            final_total = data.get('final_total', data.get('total_bill', 0.0))
            raw_total = data.get('total_bill', 0.0)
            
            # แสดงโค้ตที่ใช้
            coupon_used_display = f"โค้ตที่ใช้: {coupon_used}" if coupon_used != '-' else "โค้ตที่ใช้: ไม่มี"
            self.lbl_receipt_coupon_used.configure(text=coupon_used_display)
            
            # แสดงโค้ตที่ได้รับ
            coupon_received_display = f"โค้ตที่ได้รับ: {coupon_received}" if coupon_received != '-' else "โค้ตที่ได้รับ: ไม่มี"
            self.lbl_receipt_coupon_received.configure(text=coupon_received_display)
            
            # แสดงสรุปยอดขาย
            summary = f"ยอดรวม: {raw_total:,.2f} บาท | ส่วนลด: {discount_total:,.2f} บาท | ยอดสุดท้าย: {final_total:,.2f} บาท"
            self.lbl_receipt_summary.configure(text=summary)
            
            # แสดงสถานะการยกเลิก
            is_cancelled = data.get('is_cancelled', False)
            if is_cancelled:
                self.lbl_receipt_cancelled.configure(text="สถานะ: ยกเลิกแล้ว ❌", text_color="#E74C3C")
                # ปิดใช้งานปุ่มยกเลิก
                self.btn_cancel_receipt.configure(state="disabled", text="🚫 ยกเลิกแล้ว")
            else:
                self.lbl_receipt_cancelled.configure(text="สถานะ: ปกติ ✓", text_color="#27AE60")
                # เปิดใช้งานปุ่มยกเลิก
                self.btn_cancel_receipt.configure(state="normal", text="🚫 ยกเลิกใบเสร็จ")

    def cancel_receipt(self):
        """ยกเลิกใบเสร็จและอัปเดต Google Sheet"""
        # ตรวจสอบว่ามีการเลือกใบเสร็จในตาราง
        selected = self.tree_receipts.selection()
        if not selected:
            messagebox.showwarning("เลือกใบเสร็จ", "กรุณาเลือกใบเสร็จที่ต้องการยกเลิก")
            return
        
        # ดึง ID จากที่เลือกในตาราง
        r_id_display = self.tree_receipts.item(selected[0])['values'][0]
        # ลบ " (ยกเลิก)" จาก ID ถ้ามี
        r_id = r_id_display.replace(" (ยกเลิก)", "")
        
        # ถามยืนยันการยกเลิก
        if r_id in self.sales_history_data:
            data = self.sales_history_data[r_id]
            if data.get('is_cancelled', False):
                messagebox.showinfo("ยกเลิกแล้ว", f"ใบเสร็จ {r_id} ได้ยกเลิกไปแล้ว")
                return
            
            confirm = messagebox.askyesno("ยืนยันการยกเลิก", 
                                         f"ยืนยันการยกเลิกใบเสร็จ {r_id}?\n\n"
                                         f"ยอดรวม: {data.get('final_total', 0.0):,.2f} บาท")
            
            if confirm:
                # อัปเดต Google Sheet
                threading.Thread(target=self.run_cancel_receipt, args=(r_id,), daemon=True).start()

    def reprint_receipt(self):
        """รีปริ้นใบเสร็จที่เลือก หรือสร้างใหม่ถ้าไม่พบไฟล์"""
        # ตรวจสอบว่ามีการเลือกใบเสร็จในตาราง
        selected = self.tree_receipts.selection()
        if not selected:
            messagebox.showwarning("เลือกใบเสร็จ", "กรุณาเลือกใบเสร็จที่ต้องการปริ้น")
            return
        
        # ดึง ID จากที่เลือกในตาราง
        r_id_display = self.tree_receipts.item(selected[0])['values'][0]
        # ลบ " (ยกเลิก)" จาก ID ถ้ามี
        r_id = r_id_display.replace(" (ยกเลิก)", "")
        
        # หา PDF ของใบเสร็จนี้
        pdf_path = os.path.join(self.receipts_folder, f"{r_id}.pdf")
        
        if not os.path.exists(pdf_path):
            # ถ้าไม่พบไฟล์ PDF ให้สร้างใบเสร็จใหม่
            if r_id in self.sales_history_data:
                data = self.sales_history_data[r_id]
                items = data.get('items', [])
                timestamp = data.get('timestamp', '')
                total_bill = data.get('total_bill', 0.0)
                discount_amount = data.get('discount_amount', 0.0)
                final_total = data.get('final_total', 0.0)
                payment_method = data.get('payment_method', 'เงินสด')
                used_coupon = data.get('used_coupon', '')
                received_coupon = data.get('received_coupon', '')
                
                try:
                    # สร้างใบเสร็จใหม่
                    self.generate_receipt_pdf(r_id, timestamp, items, total_bill, discount_amount, 
                                            final_total, payment_method, used_coupon, received_coupon)
                    messagebox.showinfo("สร้างใบเสร็จ", f"สร้างใบเสร็จ {r_id} เรียบร้อย")
                    pdf_path = os.path.join(self.receipts_folder, f"{r_id}.pdf")
                except Exception as e:
                    messagebox.showerror("ผิดพลาด", f"เกิดข้อผิดพลาดในการสร้างใบเสร็จ: {e}")
                    return
            else:
                messagebox.showerror("ไม่พบข้อมูล", f"ไม่พบข้อมูลใบเสร็จ {r_id}")
                return
        
        # ปริ้นใบเสร็จ
        try:
            self.print_receipt(pdf_path)
            messagebox.showinfo("ปริ้น", f"ปริ้นใบเสร็จ {r_id} เรียบร้อย")
        except Exception as e:
            messagebox.showerror("ผิดพลาด", f"เกิดข้อผิดพลาดในการปริ้น: {e}")


    def run_cancel_receipt(self, r_id):
        """ฟังก์ชันสำหรับอัปเดต Google Sheet ในส่วน thread"""
        try:
            records = self.sheet_sales.get_all_values()
            
            # หาแถวที่มี ReceiptID เท่ากับ r_id และอัปเดต column 12 (Cancel) เป็น "Yes"
            updated = False
            for row_idx, row in enumerate(records, start=1):  # row_idx เริ่มจาก 1 (header อยู่ที่ 1)
                if len(row) > 0 and row[0] == r_id:
                    # อัปเดต column 12 (L) = Cancel column (index 11)
                    self.sheet_sales.update_cell(row_idx, 12, "Yes")  # column 12 = Cancel
                    updated = True
            
            if updated:
                # อัปเดตข้อมูลในหน่วยความจำ
                self.sales_history_data[r_id]['is_cancelled'] = True
                
                if self.app_running and self.winfo_exists():
                    # อัปเดต UI ทันที
                    self.after(0, self.update_history_ui)
                    # แสดง message หลังจาก 500ms
                    self.after(500, lambda: messagebox.showinfo("สำเร็จ", f"ยกเลิกใบเสร็จ {r_id} เรียบร้อย"))
                    # รีเฟรชการแสดงผลรายละเอียดหลังปิด dialog
                    self.after(1500, self.refresh_receipt_detail)
            else:
                if self.app_running and self.winfo_exists():
                    self.after(0, lambda: messagebox.showerror("ผิดพลาด", f"ไม่พบใบเสร็จ {r_id}"))
        
        except Exception as e:
            print(f"Error cancelling receipt: {e}")
            if self.app_running and self.winfo_exists():
                self.after(0, lambda: messagebox.showerror("ผิดพลาด", f"เกิดข้อผิดพลาด: {e}"))
    
    def refresh_receipt_detail(self):
        """รีเฟรชการแสดงผลรายละเอียดใบเสร็จ"""
        selected = self.tree_receipts.selection()
        if not selected: return
        
        r_id_display = self.tree_receipts.item(selected[0])['values'][0]
        # ลบ " (ยกเลิก)" จาก ID ถ้ามี
        r_id = r_id_display.replace(" (ยกเลิก)", "")
        
        if r_id in self.sales_history_data:
            data = self.sales_history_data[r_id]
            # แสดงสถานะการยกเลิก
            is_cancelled = data.get('is_cancelled', False)
            if is_cancelled:
                self.lbl_receipt_cancelled.configure(text="สถานะ: ยกเลิกแล้ว ❌", text_color="#E74C3C")
                # ปิดใช้งานปุ่มยกเลิก
                self.btn_cancel_receipt.configure(state="disabled", text="🚫 ยกเลิกแล้ว")
            else:
                self.lbl_receipt_cancelled.configure(text="สถานะ: ปกติ ✓", text_color="#27AE60")
                # เปิดใช้งานปุ่มยกเลิก
                self.btn_cancel_receipt.configure(state="normal", text="🚫 ยกเลิกใบเสร็จ")

    def apply_date_filter(self):
        """กรองประวัติตามวันที่ที่เลือกจากปฏิทิน"""
        # ดึงวันที่จาก DateEntry
        selected_date = self.date_picker.get_date()
        date_input = selected_date.strftime("%Y-%m-%d")
        
        # ล้าง treeview
        for i in self.tree_receipts.get_children(): 
            self.tree_receipts.delete(i)
        
        filtered_count = 0
        sorted_ids = sorted(self.sales_history_data.keys(), reverse=True)
        
        for r_id in sorted_ids:
            data = self.sales_history_data[r_id]
            date_str = data['date']
            
            # ตรวจสอบว่าวันที่เริ่มต้นด้วยวันที่ที่ค้นหา
            if date_str.startswith(date_input):
                final_total = data.get('final_total', data.get('total_bill', 0.0))
                payment_method = data.get('payment_method', '-')
                
                # ถ้าใบเสร็จยกเลิก ให้แสดง "ยกเลิก" และสีแดง
                is_cancelled = data.get('is_cancelled', False)
                if is_cancelled:
                    display_id = f"{r_id} (ยกเลิก)"
                    item = self.tree_receipts.insert("", "end", values=(display_id, data['date'], payment_method, f"{final_total:,.2f}"))
                    self.tree_receipts.item(item, tags=('cancelled',))
                else:
                    self.tree_receipts.insert("", "end", values=(r_id, data['date'], payment_method, f"{final_total:,.2f}"))
                
                filtered_count += 1
        
        # กำหนดสี tag สำหรับแถวที่ยกเลิก
        self.tree_receipts.tag_configure('cancelled', foreground='#E74C3C')
        
        if filtered_count == 0:
            messagebox.showinfo("ผลการค้นหา", f"ไม่พบรายการขายในวันที่ {date_input}")


    def show_all_history(self):
        """แสดงประวัติขายทั้งหมด"""
        # ตั้งค่าปฏิทินให้กับวันปัจจุบัน
        self.date_picker.set_date(datetime.now())
        self.update_history_ui()
        messagebox.showinfo("แสดงทั้งหมด", "แสดงประวัติการขายทั้งหมด")

    def search_receipt_by_id(self):
        """ค้นหาใบเสร็จตามเลขที่ใบเสร็จ"""
        search_text = self.search_receipt_entry.get().strip()
        
        if not search_text:
            messagebox.showwarning("ข้อผิดพลาด", "กรุณาป้อนเลขที่ใบเสร็จ")
            return
        
        # ล้างตาราง
        for item in self.tree_receipts.get_children():
            self.tree_receipts.delete(item)
        
        found_count = 0
        search_lower = search_text.lower()
        
        if hasattr(self, 'sales_history_data'):
            for r_id, data in self.sales_history_data.items():
                # ค้นหาทั้งแบบ contain และ exact match
                if search_lower in r_id.lower():
                    final_total = data.get('final_total', 0.0)
                    payment_method = data.get('payment_method', '-')
                    is_cancelled = data.get('is_cancelled', False)
                    
                    if is_cancelled:
                        display_id = f"[ยกเลิก] {r_id}"
                        item = self.tree_receipts.insert("", "end", values=(display_id, data['date'], payment_method, f"{final_total:,.2f}"))
                        self.tree_receipts.item(item, tags=('cancelled',))
                    else:
                        self.tree_receipts.insert("", "end", values=(r_id, data['date'], payment_method, f"{final_total:,.2f}"))
                    
                    found_count += 1
        
        # กำหนดสี tag สำหรับแถวที่ยกเลิก
        self.tree_receipts.tag_configure('cancelled', foreground='#E74C3C')

    # =========================================
    # TAB 4: DASHBOARD Logic
    # =========================================
    def setup_dashboard_tab(self):
        self.dash_frame = ctk.CTkFrame(self.tab_dashboard, fg_color="transparent")
        self.dash_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # เพิ่มส่วนฟิลเตอร์
        filter_frame = ctk.CTkFrame(self.dash_frame, fg_color="gray25")
        filter_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(filter_frame, text="ดูข้อมูล:", font=("Kanit", 12)).pack(side="left", padx=10, pady=5)
        self.dashboard_filter = ctk.CTkComboBox(filter_frame, values=["รายวัน", "รายเดือน"], 
                                               width=150, font=("Kanit", 12), command=self.update_dashboard)
        self.dashboard_filter.set("รายวัน")
        self.dashboard_filter.pack(side="left", padx=5, pady=5)
        
        kpi_frame = ctk.CTkFrame(self.dash_frame, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=10)
        self.card_sales = self.create_kpi_card(kpi_frame, "ยอดขายรวม", "0.00 บาท", "#3498DB")
        self.card_sales.pack(side="left", fill="x", expand=True, padx=10)
        self.card_txn = self.create_kpi_card(kpi_frame, "จำนวนบิลที่ขาย", "0 บิล", "#E67E22")
        self.card_txn.pack(side="left", fill="x", expand=True, padx=10)
        btn_refresh = ctk.CTkButton(self.dash_frame, text="🔄 รีเฟรชข้อมูล", command=self.update_dashboard, 
                                   font=("Kanit", 16), height=40, border_width=2, border_color="#3498DB")
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
        lbl_value = ctk.CTkLabel(card, text=value, font=("Kanit", 32, "bold"), text_color="white")
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
            
            filter_type = self.dashboard_filter.get() if hasattr(self, 'dashboard_filter') else "รายวัน"

            if len(records) > 1:
                for row in records[1:]:
                    if len(row) >= 7:
                        full_date = row[1]
                        date_str = full_date.split(" ")[0]
                        
                        # สำหรับรายเดือน ให้ใช้ YYYY-MM
                        if filter_type == "รายเดือน":
                            date_key = date_str[:7]  # YYYY-MM
                        else:
                            date_key = date_str
                        
                        name = row[3]
                        rec_id = row[0]
                        total_str = row[6]
                        if total_str != "-" and total_str.strip() != "":
                            try:
                                amount = float(total_str.replace(",", ""))
                                total_revenue += amount
                                total_bills.add(rec_id)
                                daily_sales[date_key] += amount
                                product_sales[name] += 1
                            except: pass
            
            sorted_dates = sorted(daily_sales.keys())[-7:]
            y_sales = [daily_sales[d] for d in sorted_dates]
            sorted_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
            top_names = [p[0] for p in sorted_products]
            top_counts = [p[1] for p in sorted_products]

            if self.app_running and self.winfo_exists():
                try:
                    self.after(0, self.draw_charts, total_revenue, len(total_bills), sorted_dates, y_sales, top_names, top_counts)
                except:
                    pass  # Ignore if window is being destroyed
        except Exception as e:
            # Suppress dashboard errors as they're not critical
            pass

    def draw_charts(self, total_revenue, total_bills, dates, sales, top_names, top_counts):
        if not self.app_running or not self.winfo_exists(): 
            return
        try:
            self.card_sales.lbl_value.configure(text=f"{total_revenue:,.2f} บาท")
            self.card_txn.lbl_value.configure(text=f"{total_bills} บิล")
            for widget in self.graph_left.winfo_children(): widget.destroy()
            for widget in self.graph_right.winfo_children(): widget.destroy()

            fig1, ax1 = plt.subplots(figsize=(5, 4), dpi=100)
            ax1.plot(dates, sales, marker='o', linestyle='-', color='#3498DB', linewidth=2)
            ax1.set_title('Daily Sales', fontsize=14)
            ax1.tick_params(axis='x', rotation=45)
            ax1.grid(True, linestyle='--', alpha=0.7)
            fig1.tight_layout()
            canvas1 = FigureCanvasTkAgg(fig1, master=self.graph_left)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill="both", expand=True)

            fig2, ax2 = plt.subplots(figsize=(5, 4), dpi=100)
            # สร้าง legend สำหรับแสดงชื่อสินค้า
            legend_labels = [f'#{i+1}: {top_names[i][:20]}' for i in range(len(top_names))]
            bars = ax2.bar(range(len(top_names)), top_counts, color='#2CC985', label=legend_labels)
            ax2.set_title('Top 5 Best Sellers', fontsize=14)
            ax2.set_xticks(range(len(top_names)))
            ax2.set_xticklabels([f'#{i+1}' for i in range(len(top_names))])
            ax2.tick_params(axis='x', rotation=0)
            for i, bar in enumerate(bars):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height, f'{int(height)}', ha='center', va='bottom', fontsize=9)
            # เพิ่ม legend แสดงชื่อสินค้า - ใช้ Tahoma font ที่รองรับภาษาไทย
            from matplotlib import font_manager
            try:
                thai_font = font_manager.FontProperties(fname='C:/Windows/Fonts/tahoma.ttf')
                ax2.text(0.5, -0.35, '\n'.join(legend_labels), transform=ax2.transAxes, 
                        fontsize=8, ha='center', va='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3),
                        fontproperties=thai_font)
            except:
                # Fallback ถ้า font ไม่ได้
                ax2.text(0.5, -0.35, '\n'.join(legend_labels), transform=ax2.transAxes, 
                        fontsize=8, ha='center', va='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
            fig2.tight_layout()
            canvas2 = FigureCanvasTkAgg(fig2, master=self.graph_right)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="both", expand=True)
        except: pass

    # =========================================
    # TAB 5: Reports (รายงาน)
    # =========================================
    def setup_reports_tab(self):
        """Setup tab สำหรับรายงานการขายและวิเคราะห์ข้อมูล"""
        main_scroll = ctk.CTkScrollableFrame(self.tab_reports, fg_color="transparent")
        main_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # หัวข้อ
        ctk.CTkLabel(main_scroll, text="📈 รายงาน (Reports)", font=("Kanit", 24, "bold")).pack(pady=15)
        
        # ฟิลเตอร์วันที่ด้วยปฏิทิน
        filter_frame = ctk.CTkFrame(main_scroll, fg_color="gray30", corner_radius=10)
        filter_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(filter_frame, text="เลือกช่วงวันที่:", font=("Kanit", 12, "bold")).pack(side="left", padx=10, pady=10)
        
        # ปฏิทินเริ่มต้น
        try:
            self.report_date_from_cal = DateEntry(filter_frame, font=("Kanit", 10), 
                                                  year=datetime.now().year, 
                                                  month=datetime.now().month, 
                                                  day=datetime.now().day)
            self.report_date_from_cal.pack(side="left", padx=5, pady=10)
        except:
            self.report_date_from_cal = ctk.CTkEntry(filter_frame, placeholder_text="2026-01-01", width=120)
            self.report_date_from_cal.pack(side="left", padx=5, pady=10)
        
        ctk.CTkLabel(filter_frame, text="ถึง", font=("Kanit", 12)).pack(side="left", padx=5)
        
        # ปฏิทินสิ้นสุด
        try:
            self.report_date_to_cal = DateEntry(filter_frame, font=("Kanit", 10),
                                               year=datetime.now().year, 
                                               month=datetime.now().month, 
                                               day=datetime.now().day)
            self.report_date_to_cal.pack(side="left", padx=5, pady=10)
        except:
            self.report_date_to_cal = ctk.CTkEntry(filter_frame, placeholder_text="2026-01-31", width=120)
            self.report_date_to_cal.pack(side="left", padx=5, pady=10)
        
        btn_generate = ctk.CTkButton(filter_frame, text="🔄 สร้างรายงาน", command=self.generate_all_reports, 
                                     font=("Kanit", 12, "bold"), width=150, height=35)
        btn_generate.pack(side="left", padx=10, pady=10)
        
        # ปุ่มรายงานต่าง ๆ
        reports_frame = ctk.CTkFrame(main_scroll, fg_color="gray30", corner_radius=10)
        reports_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(reports_frame, text="เลือกรายงาน:", font=("Kanit", 14, "bold")).pack(pady=10, anchor="w", padx=10)
        
        btn_daily = ctk.CTkButton(reports_frame, text="📅 รายงานยอดขายรายวัน", 
                                  command=lambda: self.show_report_type("daily"), 
                                  font=("Kanit", 13, "bold"), height=45)
        btn_daily.pack(fill="x", padx=10, pady=5)
        
        btn_monthly = ctk.CTkButton(reports_frame, text="📊 รายงานยอดขายรายเดือน", 
                                    command=lambda: self.show_report_type("monthly"), 
                                    font=("Kanit", 13, "bold"), height=45)
        btn_monthly.pack(fill="x", padx=10, pady=5)
        
        btn_best_seller = ctk.CTkButton(reports_frame, text="⭐ รายงานสินค้าขายดี", 
                                        command=lambda: self.show_report_type("best_seller"), 
                                        font=("Kanit", 13, "bold"), height=45)
        btn_best_seller.pack(fill="x", padx=10, pady=5)
        
        btn_stock = ctk.CTkButton(reports_frame, text="📦 รายงานสต็อกคงเหลือ", 
                                  command=lambda: self.show_report_type("stock"), 
                                  font=("Kanit", 13, "bold"), height=45)
        btn_stock.pack(fill="x", padx=10, pady=5)
        
        btn_profit = ctk.CTkButton(reports_frame, text="💰 รายงานกำไรขาดทุน", 
                                   command=lambda: self.show_report_type("profit"), 
                                   font=("Kanit", 13, "bold"), height=45)
        btn_profit.pack(fill="x", padx=10, pady=5)
        
        # พื้นที่แสดงผลรายงาน
        report_display_frame = ctk.CTkFrame(main_scroll, fg_color="gray25", corner_radius=10)
        report_display_frame.pack(fill="both", expand=True, pady=10, padx=5)
        
        ctk.CTkLabel(report_display_frame, text="ผลลัพธ์รายงาน", font=("Kanit", 14, "bold")).pack(pady=10, anchor="w", padx=10)
        
        self.report_text = ctk.CTkTextbox(report_display_frame, font=("Kanit", 12), height=300)
        self.report_text.pack(fill="both", expand=True, padx=10, pady=10)

    def generate_all_reports(self):
        """สร้างรายงานทั้งหมดตามช่วงวันที่ที่เลือก"""
        try:
            # ดึงวันที่จาก DateEntry หรือ Entry
            if hasattr(self.report_date_from_cal, 'get_date'):
                date_from = self.report_date_from_cal.get_date().strftime("%Y-%m-%d")
                date_to = self.report_date_to_cal.get_date().strftime("%Y-%m-%d")
            else:
                date_from = self.report_date_from_cal.get()
                date_to = self.report_date_to_cal.get()
            
            self.report_text.delete("1.0", "end")
            self.report_text.insert("1.0", f"📊 กำลังสร้างรายงาน (จาก {date_from} ถึง {date_to})...\n\n")
            self.report_text.insert("end", "⏳ ระบบกำลังประมวลผล โปรดรอสักครู่...\n\n")
            
            # เรียกทำงานในเธรดเพื่อไม่ให้ UI เมิน
            threading.Thread(target=self.run_generate_reports, args=(date_from, date_to), daemon=True).start()
        except Exception as e:
            self.report_text.delete("1.0", "end")
            self.report_text.insert("1.0", f"❌ เกิดข้อผิดพลาด: {str(e)}")

    def run_generate_reports(self, date_from, date_to):
        """ดึงข้อมูลจาก Google Sheet และสร้างรายงาน"""
        try:
            records = self.sheet_sales.get_all_values()
            
            total_sales = 0.0
            unique_bills = set()  # ใช้ set เพื่อนับใบเสร็จไม่ซ้ำ
            daily_sales = defaultdict(lambda: {"total": 0.0, "count": 0})
            product_sales = defaultdict(lambda: {"qty": 0, "total": 0.0})
            cancelled_count = 0
            
            if len(records) > 1:
                for row in records[1:]:
                    if len(row) >= 12:
                        rec_date = row[1].split(" ")[0]  # ดึงเฉพาะวันที่
                        
                        # ตรวจสอบว่าอยู่ในช่วงวันที่หรือไม่
                        if rec_date < date_from or rec_date > date_to:
                            continue
                        
                        # ตรวจสอบว่ายกเลิกหรือไม่
                        is_cancelled = row[11].strip().lower() == 'yes' if len(row) > 11 else False
                        if is_cancelled:
                            cancelled_count += 1
                            continue
                        
                        # คำนวณยอดขาย
                        total_str = row[6]
                        try:
                            total = float(total_str) if total_str else 0.0
                        except:
                            total = 0.0
                        
                        # เพิ่มใบเสร็จไปยัง set เพื่อนับใบเสร็จที่ไม่ซ้ำ
                        receipt_id = row[0]  # ReceiptID ที่คอลัมน์แรก
                        unique_bills.add(receipt_id)
                        
                        total_sales += total
                        
                        # จำแนกตามวันที่
                        daily_sales[rec_date]["total"] += total
                        daily_sales[rec_date]["count"] += 1
                        
                        # จำแนกตามสินค้า
                        name = row[3]
                        qty_str = row[4]
                        try:
                            qty = int(qty_str) if qty_str else 0
                        except:
                            qty = 0
                        
                        product_sales[name]["qty"] += qty
                        product_sales[name]["total"] += total
            
            # แสดงผลรายงาน
            if self.app_running and self.winfo_exists():
                self.after(0, self.display_report_results, date_from, date_to, total_sales, 
                          unique_bills, daily_sales, product_sales, cancelled_count)
        except Exception as e:
            if self.app_running and self.winfo_exists():
                self.after(0, lambda: (self.report_text.delete("1.0", "end"), 
                                      self.report_text.insert("1.0", f"❌ เกิดข้อผิดพลาด: {str(e)}")))

    def display_report_results(self, date_from, date_to, total_sales, unique_bills, daily_sales, product_sales, cancelled_count):
        """แสดงผลรายงาน"""
        self.report_text.delete("1.0", "end")
        
        # นับจำนวนใบเสร็จที่ไม่ซ้ำ
        bill_count = len(unique_bills)
        
        report_text = f"📊 รายงานสรุปยอดขาย\n"
        report_text += f"{'='*60}\n"
        report_text += f"ช่วงวันที่: {date_from} ถึง {date_to}\n\n"
        
        report_text += f"💰 ยอดขายรวม: {total_sales:,.2f} บาท\n"
        report_text += f"📋 จำนวนใบเสร็จ: {bill_count} ใบ\n"
        report_text += f"❌ ใบเสร็จที่ยกเลิก: {cancelled_count} ใบ\n"
        report_text += f"📈 เฉลี่ยต่อใบเสร็จ: {(total_sales/bill_count if bill_count > 0 else 0):,.2f} บาท\n\n"
        
        report_text += f"📅 ยอดขายรายวัน:\n"
        report_text += f"{'-'*60}\n"
        for date_key in sorted(daily_sales.keys()):
            data = daily_sales[date_key]
            report_text += f"  {date_key}: {data['total']:>10,.2f} บาท ({data['count']} ใบ)\n"
        
        report_text += f"\n⭐ สินค้าขายดี TOP 10:\n"
        report_text += f"{'-'*60}\n"
        sorted_products = sorted(product_sales.items(), key=lambda x: x[1]["qty"], reverse=True)[:10]
        for i, (name, data) in enumerate(sorted_products, 1):
            report_text += f"  {i}. {name[:20]:20} - {data['qty']} ชิ้น ({data['total']:,.2f} บาท)\n"
        
        self.report_text.insert("1.0", report_text)

    def show_report_type(self, report_type):
        """แสดงรายงานตามประเภท"""
        self.report_text.delete("1.0", "end")
        self.report_text.insert("1.0", f"⏳ กำลังประมวลผล {report_type}...\n")
        
        # ใช้ thread เพื่อดึงข้อมูล
        threading.Thread(target=self.run_show_report_type, args=(report_type,), daemon=True).start()
    
    def run_show_report_type(self, report_type):
        """ดึงข้อมูลและแสดงรายงานตามประเภท"""
        try:
            records = self.sheet_sales.get_all_values()
            
            if report_type == "daily":
                self.show_daily_report(records)
            elif report_type == "monthly":
                self.show_monthly_report(records)
            elif report_type == "best_seller":
                self.show_best_seller_report(records)
            elif report_type == "stock":
                self.show_stock_report()
            elif report_type == "profit":
                self.show_profit_report(records)
        except Exception as e:
            if self.app_running and self.winfo_exists():
                self.after(0, lambda: (self.report_text.delete("1.0", "end"), 
                                      self.report_text.insert("1.0", f"❌ เกิดข้อผิดพลาด: {str(e)}")))
    
    def show_daily_report(self, records):
        """รายงานยอดขายรายวัน (เฉพาะวันปัจจุบัน) (นับ 1 ใบเสร็จ = 1 ReceiptID)"""
        try:
            # Get today's date in YYYY-MM-DD format
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Group by receipt_id for today only
            today_receipts = set()
            today_total = 0.0
            
            if len(records) > 1:
                for row in records[1:]:
                    safe_row = (row + [""] * 12)[:12]
                    receipt_id = safe_row[0]  # column 1 = ReceiptID
                    rec_date = safe_row[1]    # column 2 = Date
                    total_str = safe_row[6]   # column 7 = Total
                    
                    if not rec_date or not receipt_id:
                        continue
                    
                    # ดึงเฉพาะวันที่ (ลบเวลา)
                    date_part = rec_date.split(" ")[0] if " " in rec_date else rec_date
                    
                    # ตรวจสอบว่าเป็นวันปัจจุบันหรือไม่
                    if date_part != today:
                        continue
                    
                    try:
                        total = float(total_str) if total_str else 0.0
                    except:
                        total = 0.0
                    
                    today_receipts.add(receipt_id)
                    today_total += total
            
            receipt_count = len(today_receipts)
            avg_per_receipt = today_total / receipt_count if receipt_count > 0 else 0
            
            report_text = f"📅 รายงานยอดขายประจำวัน ({today})\n" + "="*60 + "\n\n"
            
            if today_receipts:
                report_text += f"📌 ข้อมูลวันนี้\n"
                report_text += f"   ยอดขาย: {today_total:>12,.2f} บาท\n"
                report_text += f"   ใบเสร็จ: {receipt_count:>12} ใบ\n"
                report_text += f"   เฉลี่ย: {avg_per_receipt:>12,.2f} บาท/ใบ\n\n"
                report_text += "📋 รายการใบเสร็จ:\n"
                for i, rec_id in enumerate(sorted(today_receipts), 1):
                    report_text += f"  {i}. {rec_id}\n"
            else:
                report_text += "ไม่มีข้อมูลขายสำหรับวันนี้\n"
            
            if self.app_running and self.winfo_exists():
                self.after(0, lambda: (self.report_text.delete("1.0", "end"), 
                                      self.report_text.insert("1.0", report_text)))
        except Exception as e:
            print(f"Error in show_daily_report: {e}")
    
    def show_monthly_report(self, records):
        """รายงานยอดขายรายเดือน (นับ 1 ใบเสร็จ = 1 ReceiptID)"""
        try:
            # Group by (month, receipt_id) to count unique receipts
            monthly_receipts = defaultdict(lambda: {"receipts": set(), "total": 0.0})
            
            if len(records) > 1:
                for row in records[1:]:
                    safe_row = (row + [""] * 12)[:12]
                    receipt_id = safe_row[0]  # column 1 = ReceiptID
                    rec_date = safe_row[1]    # column 2 = Date
                    total_str = safe_row[6]   # column 7 = Total
                    
                    if not rec_date or not receipt_id:
                        continue
                    
                    # แยกเอาเดือนจากวันที่ (เช่น 2026-01-15 -> 2026-01)
                    month_key = rec_date[:7] if len(rec_date) >= 7 else rec_date
                    
                    try:
                        total = float(total_str) if total_str else 0.0
                    except:
                        total = 0.0
                    
                    monthly_receipts[month_key]["receipts"].add(receipt_id)
                    monthly_receipts[month_key]["total"] += total
            
            report_text = "📊 รายงานยอดขายรายเดือน\n" + "="*60 + "\n\n"
            
            if monthly_receipts:
                for month_key in sorted(monthly_receipts.keys(), reverse=True):
                    data = monthly_receipts[month_key]
                    receipt_count = len(data["receipts"])
                    avg_per_receipt = data['total'] / receipt_count if receipt_count > 0 else 0
                    report_text += f"📌 {month_key}\n"
                    report_text += f"   ยอดขาย: {data['total']:>12,.2f} บาท\n"
                    report_text += f"   ใบเสร็จ: {receipt_count:>12} ใบ\n"
                    report_text += f"   เฉลี่ย: {avg_per_receipt:>12,.2f} บาท/ใบ\n\n"
            else:
                report_text += "ไม่มีข้อมูล\n"
            
            if self.app_running and self.winfo_exists():
                self.after(0, lambda: (self.report_text.delete("1.0", "end"), 
                                      self.report_text.insert("1.0", report_text)))
        except Exception as e:
            print(f"Error in show_monthly_report: {e}")
    
    def show_best_seller_report(self, records):
        """รายงานสินค้าขายดี TOP 20"""
        try:
            product_sales = defaultdict(lambda: {"qty": 0, "total": 0.0})
            
            if len(records) > 1:
                for row in records[1:]:
                    safe_row = (row + [""] * 10)[:10]
                    name = safe_row[3]  # column 4 = Name
                    qty_str = safe_row[4]  # column 5 = Qty
                    total_str = safe_row[6]  # column 7 = Total
                    
                    if not name:
                        continue
                    
                    try:
                        qty = int(qty_str) if qty_str else 0
                    except:
                        qty = 0
                    
                    try:
                        total = float(total_str) if total_str else 0.0
                    except:
                        total = 0.0
                    
                    product_sales[name]["qty"] += qty
                    product_sales[name]["total"] += total
            
            report_text = "⭐ รายงานสินค้าขายดี TOP 20\n" + "="*60 + "\n\n"
            
            sorted_products = sorted(product_sales.items(), key=lambda x: x[1]["qty"], reverse=True)[:20]
            
            if sorted_products:
                for i, (name, data) in enumerate(sorted_products, 1):
                    report_text += f"{i:2}. {name[:30]:30} - {data['qty']:>6} ชิ้น ({data['total']:>10,.2f} บาท)\n"
            else:
                report_text += "ไม่มีข้อมูล\n"
            
            if self.app_running and self.winfo_exists():
                self.after(0, lambda: (self.report_text.delete("1.0", "end"), 
                                      self.report_text.insert("1.0", report_text)))
        except Exception as e:
            print(f"Error in show_best_seller_report: {e}")
    
    def show_stock_report(self):
        """รายงานสต็อกคงเหลือ"""
        try:
            if not hasattr(self, 'sheet_products') or not self.sheet_products:
                if self.app_running and self.winfo_exists():
                    self.after(0, lambda: (self.report_text.delete("1.0", "end"), 
                                          self.report_text.insert("1.0", "❌ ไม่พบ Sheet Products")))
                return
            
            records = self.sheet_products.get_all_values()
            
            # ตั้งค่าพื้นฐาน
            report_text = "📦 รายงานสต็อกคงเหลือ\n"
            report_text += "=" * 90 + "\n\n"
            
            total_qty = 0
            total_value = 0.0
            stock_items = []
            
            if len(records) > 1:
                # รวบรวมข้อมูลสินค้า
                for i, row in enumerate(records[1:], 1):
                    safe_row = (row + [""] * 15)[:15]
                    barcode = safe_row[1] if len(safe_row) > 1 else ""  # column 2 = Barcode
                    name = safe_row[2] if len(safe_row) > 2 else ""  # column 3 = Name
                    price_str = safe_row[8] if len(safe_row) > 8 else ""  # column 9 = Price (ขาย)
                    stock_str = safe_row[7] if len(safe_row) > 7 else ""  # column 8 = Stock
                    
                    if not name:
                        continue
                    
                    try:
                        price = float(price_str) if price_str else 0.0
                    except:
                        price = 0.0
                    
                    try:
                        stock = int(stock_str) if stock_str else 0
                    except:
                        stock = 0
                    
                    value = price * stock
                    total_qty += stock
                    total_value += value
                    
                    stock_items.append({
                        'no': i,
                        'barcode': barcode,
                        'name': name,
                        'price': price,
                        'stock': stock,
                        'value': value
                    })
                
                # แสดงส่วนหัวตาราง
                report_text += "=" * 90 + "\n"
                report_text += f"{'ลำดับ':<5} {'บาร์โค้ด':<15} {'ชื่อสินค้า':<35} {'ราคา':<12} {'จำนวน':<8} {'มูลค่า':<15}\n"
                report_text += "=" * 90 + "\n"
                
                # แสดงรายการสินค้า
                for item in stock_items:
                    name_display = item['name'][:35] if len(item['name']) > 35 else item['name']
                    report_text += f"{item['no']:<5} {item['barcode']:<15} {name_display:<35} "
                    report_text += f"฿{item['price']:<11,.2f} {item['stock']:<8} ฿{item['value']:>13,.2f}\n"
                
                # แสดงรายการสรุป
                report_text += "-" * 90 + "\n"
                report_text += f"{'รวมทั้งหมด':<5} {'':<15} {'':<35} "
                report_text += f"{'':<12} {total_qty:<8} ฿{total_value:>13,.2f}\n"
                report_text += "=" * 90 + "\n\n"
                
                # เพิ่มสรุปสถิติ
                low_stock_items = [item for item in stock_items if item['stock'] < 5]
                report_text += f"📊 สรุปสถิติ:\n"
                report_text += f"  • รวมทั้งสิ้น: {len(stock_items)} ชิ้นประเภท\n"
                report_text += f"  • จำนวนสินค้าทั้งสิ้น: {total_qty} ชิ้น\n"
                report_text += f"  • มูลค่าสต็อก: ฿{total_value:,.2f}\n"
                report_text += f"  • สินค้าเหลือน้อย (< 5 ชิ้น): {len(low_stock_items)} รายการ\n"
                
                if low_stock_items:
                    report_text += f"\n⚠️  สินค้าเหลือน้อย:\n"
                    for item in low_stock_items:
                        report_text += f"  • {item['name'][:40]} - เหลือเพียง {item['stock']} ชิ้น\n"
            else:
                report_text += "ไม่มีข้อมูล\n"
            
            if self.app_running and self.winfo_exists():
                self.after(0, lambda: (self.report_text.delete("1.0", "end"), 
                                      self.report_text.insert("1.0", report_text)))
        except Exception as e:
            if self.app_running and self.winfo_exists():
                self.after(0, lambda: (self.report_text.delete("1.0", "end"), 
                                      self.report_text.insert("1.0", f"❌ เกิดข้อผิดพลาด: {str(e)}")))
            print(f"Error in show_stock_report: {e}")
    
    def show_profit_report(self, records):
        """รายงานกำไรขาดทุน - คำนวณจากสินค้าที่ขายจริงๆ"""
        try:
            total_sales = 0.0
            total_cost = 0.0
            
            # สร้าง dict เก็บต้นทุนของแต่ละสินค้า
            product_costs = {}
            if hasattr(self, 'sheet_products') and self.sheet_products:
                try:
                    inv_records = self.sheet_products.get_all_values()
                    if len(inv_records) > 1:
                        for row in inv_records[1:]:
                            safe_row = (row + [""] * 15)[:15]
                            name = safe_row[2] if len(safe_row) > 2 else ""  # column 3 = Name
                            cost_str = safe_row[6] if len(safe_row) > 6 else ""  # column 7 = Cost
                            
                            if name:
                                try:
                                    cost = float(cost_str) if cost_str else 0.0
                                except:
                                    cost = 0.0
                                product_costs[name] = cost
                except:
                    pass
            
            # ดึงยอดขายและคำนวณต้นทุนจากสินค้าที่ขายไป
            if len(records) > 1:
                for row in records[1:]:
                    safe_row = (row + [""] * 12)[:12]
                    # column 7 = Total ยอดขาย
                    total_str = safe_row[6] if len(safe_row) > 6 else ""
                    # ดึงชื่อสินค้าและจำนวน (ถ้ามีใน record)
                    # ปกติใน Sales sheet อาจมีรายการสินค้าแยกต่างหาก หรืออาจต้องประมาณจากยอดขาย
                    
                    try:
                        total = float(total_str) if total_str else 0.0
                    except:
                        total = 0.0
                    
                    total_sales += total
                    
                    # หากต้องการความแม่นยำ สามารถข้ามข้างบน
                    # แล้วดึงข้อมูลรายการสินค้าที่ขายจาก Items/Details ใน Google Sheet
            
            # หากต้องการคำนวณต้นทุนจากยอดขายโดยประมาณ (ถ้าไม่มีข้อมูล qty)
            # สามารถใช้อัตราราคาขายต่อต้นทุน แต่เป็นการประมาณ
            # วิธีที่ดีที่สุดคือดึงข้อมูลรายการขายจริงๆ
            
            # ลองดึงข้อมูลรายละเอียดสินค้าที่ขายจาก Sales Items (ถ้ามี)
            total_cost = 0.0
            if hasattr(self, 'sheet_sales_items') and self.sheet_sales_items:
                try:
                    items_records = self.sheet_sales_items.get_all_values()
                    if len(items_records) > 1:
                        for row in items_records[1:]:
                            safe_row = (row + [""] * 10)[:10]
                            name = safe_row[1] if len(safe_row) > 1 else ""  # สินค้า
                            qty_str = safe_row[2] if len(safe_row) > 2 else ""  # จำนวน
                            
                            if name and qty_str:
                                try:
                                    qty = int(qty_str) if qty_str else 0
                                except:
                                    qty = 0
                                
                                cost_per_unit = product_costs.get(name, 0.0)
                                item_cost = cost_per_unit * qty
                                total_cost += item_cost
                except:
                    # ถ้าไม่มี sheet_sales_items ให้ใช้วิธี fallback
                    pass
            
            # Fallback: ถ้าดึงเรคคอร์ดขายเป็นสินค้า เราจะคำนวณจากนั้น
            # เก็บรายละเอียดสินค้าที่ขาย (รวมรายการที่ซ้ำกัน)
            sales_details_dict = {}  # {name: {qty, price, total, cost, profit}}
            total_qty = 0
            
            if total_cost == 0.0 and hasattr(self, 'sales_history_data'):
                # ดึงจากข้อมูลที่โหลดไปแล้ว
                for r_id, receipt_data in self.sales_history_data.items():
                    items = receipt_data.get('items', [])
                    for item in items:
                        name = item.get('name', '')
                        qty = item.get('qty', 0)
                        price = item.get('price', 0.0)
                        item_total = item.get('total', 0.0)
                        cost_per_unit = product_costs.get(name, 0.0)
                        item_cost = cost_per_unit * qty
                        item_profit = item_total - item_cost
                        total_cost += item_cost
                        total_qty += qty
                        
                        # รวมรายการที่มีชื่อเดียวกัน
                        if name in sales_details_dict:
                            sales_details_dict[name]['qty'] += qty
                            sales_details_dict[name]['total'] += item_total
                            sales_details_dict[name]['cost'] += item_cost
                            sales_details_dict[name]['profit'] += item_profit
                        else:
                            sales_details_dict[name] = {
                                'qty': qty,
                                'price': price,
                                'total': item_total,
                                'cost': item_cost,
                                'profit': item_profit
                            }
                
                # แปลง dict เป็น list และเรียงลำดับ
                sales_details = [
                    {
                        'name': name,
                        'qty': data['qty'],
                        'price': data['price'],
                        'total': data['total'],
                        'cost': data['cost'],
                        'profit': data['profit']
                    }
                    for name, data in sorted(sales_details_dict.items())
                ]
            else:
                sales_details = []
            
            profit = total_sales - total_cost
            profit_margin = (profit / total_sales * 100) if total_sales > 0 else 0
            
            # สร้างรายงาน
            report_text = "💰 รายงานกำไรขาดทุน\n"
            report_text += "=" * 100 + "\n\n"
            
            # ส่วนที่ 1: สรุปข้อมูล
            report_text += "📊 สรุปข้อมูลการขาย\n"
            report_text += "-" * 100 + "\n"
            report_text += f"  รวมจำนวนรายการที่ขาย: {len(sales_details)} รายการ\n"
            report_text += f"  รวมจำนวนสินค้า:       {total_qty} ชิ้น\n"
            report_text += f"  ยอดรวมขาย:            ฿{total_sales:>15,.2f}\n"
            report_text += f"  ต้นทุนสินค้าขาย:       ฿{total_cost:>15,.2f}\n"
            report_text += "\n"
            
            # ส่วนที่ 2: ผลลัพธ์
            report_text += "📈 ผลลัพธ์\n"
            report_text += "-" * 100 + "\n"
            
            if profit >= 0:
                report_text += f"  ✅ กำไรสุทธิ:     ฿{profit:>15,.2f}\n"
            else:
                report_text += f"  ❌ ขาดทุน:        ฿{abs(profit):>15,.2f}\n"
            
            report_text += f"  อัตราผลกำไร:     {profit_margin:>16.2f}%\n"
            report_text += "\n" + "=" * 100 + "\n\n"
            
            # ส่วนที่ 3: รายละเอียดรายการขาย (แบบตาราง)
            if sales_details:
                report_text += "📋 รายละเอียดสินค้าที่ขาย\n"
                report_text += "=" * 100 + "\n"
                report_text += f"{'ลำดับ':<5} {'สินค้า':<30} {'จำนวน':<8} {'ราคา/หน่วย':<15} {'ยอดขาย':<15} {'ต้นทุน':<15} {'กำไร':<15}\n"
                report_text += "-" * 100 + "\n"
                
                for i, detail in enumerate(sales_details, 1):
                    name_display = detail['name'][:30] if len(detail['name']) > 30 else detail['name']
                    report_text += f"{i:<5} {name_display:<30} {detail['qty']:<8} "
                    report_text += f"฿{detail['price']:<14,.2f} ฿{detail['total']:<14,.2f} "
                    report_text += f"฿{detail['cost']:<14,.2f} ฿{detail['profit']:<14,.2f}\n"
                
                report_text += "-" * 100 + "\n"
                report_text += f"{'รวม':<5} {'':<30} {total_qty:<8} "
                report_text += f"{'':<15} ฿{total_sales:<14,.2f} ฿{total_cost:<14,.2f} ฿{profit:<14,.2f}\n"
                report_text += "=" * 100 + "\n\n"
            
            # ส่วนที่ 4: สรุปผล
            report_text += "💡 สรุปผล\n"
            if profit > 0:
                report_text += f"✅ ธุรกิจมีกำไร {profit_margin:.2f}%\n"
                report_text += f"   ทำรายได้ ฿{profit:,.2f} จากการขาย {len(sales_details)} รายการ\n"
                report_text += f"   เฉลี่ยกำไรต่อรายการ: ฿{(profit / len(sales_details) if len(sales_details) > 0 else 0):,.2f}\n"
            elif profit < 0:
                report_text += f"⚠️  ธุรกิจขาดทุน {abs(profit_margin):.2f}%\n"
                report_text += f"   ขาดทุน ฿{abs(profit):,.2f} ต้องตรวจสอบต้นทุน\n"
            else:
                report_text += "⚖️  ยอดขายและต้นทุนสมดุลกัน (ไม่กำไร-ไม่ขาดทุน)\n"
            
            if self.app_running and self.winfo_exists():
                self.after(0, lambda: (self.report_text.delete("1.0", "end"), 
                                      self.report_text.insert("1.0", report_text)))
        except Exception as e:
            if self.app_running and self.winfo_exists():
                self.after(0, lambda: (self.report_text.delete("1.0", "end"), 
                                      self.report_text.insert("1.0", f"❌ เกิดข้อผิดพลาด: {str(e)}")))
            print(f"Error in show_profit_report: {e}")

    # =========================================
    # TAB 6: Suppliers (ซัพพลายเออร์)
    # =========================================
    def setup_suppliers_tab(self):
        """Setup tab สำหรับจัดการข้อมูลซัพพลายเออร์"""
        main_scroll = ctk.CTkScrollableFrame(self.tab_suppliers, fg_color="transparent")
        main_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # หัวข้อ
        ctk.CTkLabel(main_scroll, text="🏭 ซัพพลายเออร์ (Suppliers)", font=("Kanit", 24, "bold")).pack(pady=15)
        
        # ปุ่มเพิ่มซัพพลายเออร์
        action_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        action_frame.pack(fill="x", pady=10)
        
        btn_add_supplier = ctk.CTkButton(action_frame, text="➕ เพิ่มซัพพลายเออร์ใหม่", 
                                         command=self.add_supplier_dialog, 
                                         font=("Kanit", 12, "bold"), height=35)
        btn_add_supplier.pack(side="left", padx=5)
        
        btn_refresh_suppliers = ctk.CTkButton(action_frame, text="🔄 รีเฟรช", 
                                              command=self.load_suppliers, 
                                              font=("Kanit", 12, "bold"), height=35)
        btn_refresh_suppliers.pack(side="left", padx=5)
        
        # ตารางแสดงซัพพลายเออร์
        table_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, pady=10, padx=5)
        
        # สร้าง Treeview สำหรับแสดงข้อมูลซัพพลายเออร์
        columns = ("รหัส", "ชื่อซัพพลายเออร์", "เบอร์โทร", "หมายเหตุ", "จัดการ")
        self.suppliers_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # ตั้งค่า style สำหรับ treeview
        style = ttk.Style()
        style.configure("Treeview", rowheight=40, font=("Kanit", 10))
        style.configure("Treeview.Heading", font=("Kanit", 11, "bold"))
        
        # ตั้งค่าหัวคอลัมน์
        self.suppliers_tree.heading("รหัส", text="รหัส")
        self.suppliers_tree.column("รหัส", width=90, anchor="center")
        
        self.suppliers_tree.heading("ชื่อซัพพลายเออร์", text="ชื่อซัพพลายเออร์")
        self.suppliers_tree.column("ชื่อซัพพลายเออร์", width=180, anchor="center")
        
        self.suppliers_tree.heading("เบอร์โทร", text="เบอร์โทร")
        self.suppliers_tree.column("เบอร์โทร", width=130, anchor="center")
        
        self.suppliers_tree.heading("หมายเหตุ", text="หมายเหตุ")
        self.suppliers_tree.column("หมายเหตุ", width=200, anchor="center")
        
        self.suppliers_tree.heading("จัดการ", text="จัดการ")
        self.suppliers_tree.column("จัดการ", width=70, anchor="center")
        
        self.suppliers_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar สำหรับ treeview
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.suppliers_tree.yview)
        self.suppliers_tree.configure(yscroll=scrollbar.set)
        
        self.suppliers_tree_map = {}  # Mapping จาก tree item ไป supplier data
        self.load_suppliers()

    def load_suppliers(self):
        """โหลดรายชื่อซัพพลายเออร์จาก Google Sheet"""
        # ล้างข้อมูลเก่า
        for item in self.suppliers_tree.get_children():
            self.suppliers_tree.delete(item)
        
        self.suppliers_tree_map.clear()
        
        try:
            if not self.sheet_suppliers:
                return
            
            records = self.sheet_suppliers.get_all_values()
            
            if len(records) <= 1:
                return
            
            # แสดงข้อมูลซัพพลายเออร์
            for row_idx, row in enumerate(records[1:], start=2):  # ข้าม header
                safe_row = (row + [""] * 6)[:6]  # ให้แน่ใจว่ามี 5 columns (index 0-4) + space
                sup_id = safe_row[0]
                sup_name = safe_row[1]
                sup_phone = safe_row[2]
                sup_address = safe_row[3]
                sup_note = safe_row[4]
                
                # เพิ่มแถวไปยัง treeview พร้อมปุ่ม ⋯ (จะเพิ่มทีหลัง)
                item_id = self.suppliers_tree.insert("", "end", values=(sup_id, sup_name, sup_phone, sup_note, "⋯"))
                
                # เก็บข้อมูลสำหรับการแก้ไข/ลบ
                self.suppliers_tree_map[item_id] = {
                    "row_idx": row_idx,
                    "data": (sup_id, sup_name, sup_phone, sup_address, sup_note)
                }
            
            # เพิ่ม event handler สำหรับคลิกที่ปุ่ม ⋯
            self.suppliers_tree.bind("<Button-1>", self.on_supplier_tree_click)
        except Exception as e:
            print(f"Error loading suppliers: {e}")
    
    def on_supplier_tree_click(self, event):
        """จัดการการคลิกที่แถวในตาราง suppliers"""
        # หาแถวที่ถูกคลิก
        item = self.suppliers_tree.identify("item", event.x, event.y)
        col = self.suppliers_tree.identify("column", event.x, event.y)
        
        if not item or col != "#5":  # #5 คือคอลัมน์ "จัดการ"
            return
        
        if item not in self.suppliers_tree_map:
            return
        
        info = self.suppliers_tree_map[item]
        row_idx = info["row_idx"]
        supplier_data = info["data"]
        
        self.show_supplier_tree_menu(event, item, row_idx, supplier_data)
    
    def show_supplier_tree_menu(self, event, tree_item, row_idx, supplier_data):
        """แสดงเมนู popup สำหรับแก้ไขหรือลบซัพพลายเออร์ (สำหรับ treeview)"""
        sup_id = supplier_data[0]
        
        # สร้าง popup menu
        popup_menu = ctk.CTkToplevel(self)
        popup_menu.wm_overrideredirect(True)  # ลบ title bar
        popup_menu.geometry(f"+{event.x_root}+{event.y_root}")
        popup_menu.attributes('-topmost', True)  # ให้ popup อยู่ด้านบนสุด
        
        frame = ctk.CTkFrame(popup_menu, fg_color="gray30", border_width=1, border_color="gray50")
        frame.pack(fill="both", expand=True)
        
        def close_popup():
            try:
                popup_menu.destroy()
            except:
                pass
        
        btn_edit = ctk.CTkButton(frame, text="✏️ แก้ไข", font=("Kanit", 12), fg_color="gray40", hover_color="gray50",
                                 command=lambda: [close_popup(), self.edit_supplier(row_idx, supplier_data)])
        btn_edit.pack(fill="x", padx=5, pady=5)
        
        btn_delete = ctk.CTkButton(frame, text="🗑️ ลบ", font=("Kanit", 12), fg_color="#E74C3C", hover_color="#C0392B",
                                   command=lambda: [close_popup(), self.delete_supplier(row_idx, sup_id)])
        btn_delete.pack(fill="x", padx=5, pady=5)
        
        # ปิด popup เมื่อกดนอก
        def on_key_press(e):
            if e.keysym == 'Escape':
                close_popup()
        
        def on_focus_out(e):
            popup_menu.after(100, lambda: close_popup())
        
        popup_menu.bind("<Escape>", on_key_press)
        popup_menu.bind("<Button-1>", lambda e: close_popup() if e.widget == popup_menu else None)
        
        # ใช้ grab_set เพื่อให้ popup capture mouse events
        try:
            popup_menu.grab_set()
        except:
            pass

    def show_supplier_menu(self, btn, row_idx, supplier_data):
        """แสดงเมนู popup สำหรับแก้ไขหรือลบซัพพลายเออร์"""
        sup_id = supplier_data[0]
        
        # สร้าง popup menu
        popup_menu = ctk.CTkToplevel(self)
        popup_menu.wm_overrideredirect(True)  # ลบ title bar
        
        # ตั้งตำแหน่งเหนือปุ่ม
        btn.update()
        x = btn.winfo_rootx()
        y = btn.winfo_rooty() - 90
        popup_menu.geometry(f"+{x}+{y}")
        
        frame = ctk.CTkFrame(popup_menu, fg_color="gray30", border_width=1, border_color="gray50")
        frame.pack(fill="both", expand=True)
        
        btn_edit = ctk.CTkButton(frame, text="✏️ แก้ไข", font=("Kanit", 12), fg_color="gray40", hover_color="gray50",
                                 command=lambda: [popup_menu.destroy(), self.edit_supplier(row_idx, supplier_data)])
        btn_edit.pack(fill="x", padx=5, pady=5)
        
        btn_delete = ctk.CTkButton(frame, text="🗑️ ลบ", font=("Kanit", 12), fg_color="#E74C3C", hover_color="#C0392B",
                                   command=lambda: [popup_menu.destroy(), self.delete_supplier(row_idx, sup_id)])
        btn_delete.pack(fill="x", padx=5, pady=5)
        
        # ปิด popup เมื่อคลิกนอก
        def close_popup(event=None):
            try:
                popup_menu.destroy()
            except:
                pass
        
        popup_menu.bind("<FocusOut>", close_popup)

    def add_supplier_dialog(self):
        """เปิด dialog สำหรับเพิ่มซัพพลายเออร์ใหม่"""
        # สร้าง window ใหม่
        dialog = ctk.CTkToplevel(self)
        dialog.title("เพิ่มซัพพลายเออร์ใหม่")
        dialog.geometry("400x450")
        dialog.resizable(False, False)
        
        ctk.CTkLabel(dialog, text="เพิ่มซัพพลายเออร์ใหม่", font=("Kanit", 16, "bold")).pack(pady=15)
        
        ctk.CTkLabel(dialog, text="ชื่อซัพพลายเออร์:", font=("Kanit", 11)).pack(anchor="w", padx=15, pady=5)
        entry_name = ctk.CTkEntry(dialog, placeholder_text="ชื่อบริษัท", width=350)
        entry_name.pack(padx=15, pady=5)
        
        ctk.CTkLabel(dialog, text="เบอร์โทร:", font=("Kanit", 11)).pack(anchor="w", padx=15, pady=5)
        entry_phone = ctk.CTkEntry(dialog, placeholder_text="เช่น 02-123-4567", width=350)
        entry_phone.pack(padx=15, pady=5)
        
        ctk.CTkLabel(dialog, text="ที่อยู่:", font=("Kanit", 11)).pack(anchor="w", padx=15, pady=5)
        entry_address = ctk.CTkEntry(dialog, placeholder_text="ที่อยู่ซัพพลายเออร์", width=350)
        entry_address.pack(padx=15, pady=5)
        
        ctk.CTkLabel(dialog, text="หมายเหตุ:", font=("Kanit", 11)).pack(anchor="w", padx=15, pady=5)
        entry_note = ctk.CTkEntry(dialog, placeholder_text="หมายเหตุเพิ่มเติม", width=350)
        entry_note.pack(padx=15, pady=5)
        
        def save_supplier():
            name = entry_name.get().strip()
            phone = entry_phone.get().strip()
            address = entry_address.get().strip()
            note = entry_note.get().strip()
            
            if not name:
                messagebox.showwarning("ข้อมูลไม่ครบ", "กรุณาใส่ชื่อซัพพลายเออร์")
                return
            
            try:
                # สร้าง ID อัตโนมัติ (SUP + timestamp)
                import time
                sup_id = f"SUP{int(time.time()) % 100000}"
                
                # เพิ่มลงใน Google Sheet (5 columns: ID, Name, Phone, Address, Note)
                self.sheet_suppliers.append_row([sup_id, name, phone, address, note])
                messagebox.showinfo("สำเร็จ", f"เพิ่มซัพพลายเออร์ {name} เรียบร้อย!")
                dialog.destroy()
                self.load_suppliers()
            except Exception as e:
                messagebox.showerror("เกิดข้อผิดพลาด", str(e))
        
        btn_save = ctk.CTkButton(dialog, text="💾 บันทึก", command=save_supplier, 
                                 font=("Kanit", 12, "bold"), height=40)
        btn_save.pack(padx=15, pady=20, fill="x")

    def edit_supplier(self, row_idx, supplier_data):
        """แก้ไขข้อมูลซัพพลายเออร์"""
        sup_id, sup_name, sup_phone, sup_address, sup_note = supplier_data
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("แก้ไขซัพพลายเออร์")
        dialog.geometry("400x470")
        dialog.resizable(False, False)
        
        ctk.CTkLabel(dialog, text="แก้ไขซัพพลายเออร์", font=("Kanit", 16, "bold")).pack(pady=15)
        
        ctk.CTkLabel(dialog, text=f"รหัส: {sup_id}", font=("Kanit", 11)).pack(anchor="w", padx=15, pady=5)
        
        ctk.CTkLabel(dialog, text="ชื่อซัพพลายเออร์:", font=("Kanit", 11)).pack(anchor="w", padx=15, pady=5)
        entry_name = ctk.CTkEntry(dialog, width=350)
        entry_name.insert(0, sup_name)
        entry_name.pack(padx=15, pady=5)
        
        ctk.CTkLabel(dialog, text="เบอร์โทร:", font=("Kanit", 11)).pack(anchor="w", padx=15, pady=5)
        entry_phone = ctk.CTkEntry(dialog, width=350)
        entry_phone.insert(0, sup_phone)
        entry_phone.pack(padx=15, pady=5)
        
        ctk.CTkLabel(dialog, text="ที่อยู่:", font=("Kanit", 11)).pack(anchor="w", padx=15, pady=5)
        entry_address = ctk.CTkEntry(dialog, width=350)
        entry_address.insert(0, sup_address)
        entry_address.pack(padx=15, pady=5)
        
        ctk.CTkLabel(dialog, text="หมายเหตุ:", font=("Kanit", 11)).pack(anchor="w", padx=15, pady=5)
        entry_note = ctk.CTkEntry(dialog, width=350)
        entry_note.insert(0, sup_note)
        entry_note.pack(padx=15, pady=5)
        
        def save_changes():
            name = entry_name.get().strip()
            phone = entry_phone.get().strip()
            address = entry_address.get().strip()
            note = entry_note.get().strip()
            
            try:
                # อัปเดตใน Google Sheet (5 columns: ID, Name, Phone, Address, Note)
                self.sheet_suppliers.update_cell(row_idx, 2, name)  # column 2 = Name
                self.sheet_suppliers.update_cell(row_idx, 3, phone)  # column 3 = Phone
                self.sheet_suppliers.update_cell(row_idx, 4, address)  # column 4 = Address
                self.sheet_suppliers.update_cell(row_idx, 5, note)  # column 5 = Note
                messagebox.showinfo("สำเร็จ", "อัปเดตข้อมูลซัพพลายเออร์เรียบร้อย!")
                dialog.destroy()
                self.load_suppliers()
            except Exception as e:
                messagebox.showerror("เกิดข้อผิดพลาด", str(e))
        
        btn_save = ctk.CTkButton(dialog, text="💾 บันทึก", command=save_changes, 
                                 font=("Kanit", 12, "bold"), height=40)
        btn_save.pack(padx=15, pady=15, fill="x")

    def delete_supplier(self, row_idx, sup_id):
        """ลบซัพพลายเออร์"""
        confirm = messagebox.askyesno("ยืนยันการลบ", f"คุณแน่ใจหรือว่าต้องการลบซัพพลายเออร์ {sup_id}?")
        if confirm:
            try:
                self.sheet_suppliers.delete_rows(row_idx)
                messagebox.showinfo("สำเร็จ", "ลบซัพพลายเออร์เรียบร้อย!")
                self.load_suppliers()
            except Exception as e:
                messagebox.showerror("เกิดข้อผิดพลาด", str(e))

    # =========================================
    # TAB 7: AI & Social Media
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
        
        ctk.CTkButton(ai_frame, text="💾 บันทึก", command=self.save_ai_config, width=100, height=30,
                     border_width=2, border_color="#229954").pack(side="left", padx=5, pady=5)
        
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
        
        ctk.CTkButton(fb_frame, text="💾 บันทึก", command=self.save_fb_config, width=100, height=30,
                     border_width=2, border_color="#229954").pack(side="left", padx=5, pady=5)
        ctk.CTkButton(fb_frame, text="🔗 Get Token", command=self.show_fb_token_help, width=100, height=30,
                     border_width=2, border_color="#3498DB").pack(side="left", padx=5, pady=5)
        
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
        self.content_details_text = ctk.CTkTextbox(left_frame, height=60, width=250, font=("Kanit", 12))
        self.content_details_text.pack(padx=10, pady=5, fill="both", expand=False)
        
        # Prompt for content generation
        ctk.CTkLabel(left_frame, text="Prompt สำหรับสร้างเนื้อหา:", font=("Kanit", 11)).pack(pady=(10, 0), anchor="w", padx=10)
        self.content_prompt_text = ctk.CTkTextbox(left_frame, height=60, width=250, font=("Kanit", 12))
        self.content_prompt_text.pack(padx=10, pady=5, fill="both", expand=False)
        
        # Style selection
        ctk.CTkLabel(left_frame, text="สไตล์การเขียน:", font=("Kanit", 12)).pack(pady=5, anchor="w", padx=10)
        self.content_style_combo = ctk.CTkComboBox(left_frame, values=["casual", "professional", "humorous", "emotional"], 
                                                   width=250, command=None)
        self.content_style_combo.set("casual")
        self.content_style_combo.pack(padx=10, pady=5, fill="x")
        
        # Generate button
        ctk.CTkButton(left_frame, text="🤖 สร้างเนื้อหา", command=self.generate_ai_content, 
                     height=40, font=("Kanit", 13), fg_color="#3498DB", border_width=2, border_color="#2980B9").pack(padx=10, pady=10, fill="x")
        
        # Output
        right_frame = ctk.CTkFrame(tab, fg_color="gray30", corner_radius=10)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(right_frame, text="📄 ผลลัพธ์", font=("Kanit", 14, "bold")).pack(pady=10, anchor="w", padx=10)
        
        self.content_result_text = ctk.CTkTextbox(right_frame, height=200, width=400, font=("Kanit", 12))
        self.content_result_text.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Action buttons
        button_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(button_frame, text="📋 คัดลอก", command=self.copy_content, width=150, height=30,
                     border_width=2, border_color="#3498DB").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="💾 บันทึก", command=self.save_content, width=150, height=30,
                     border_width=2, border_color="#3498DB").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="🔄 สร้างใหม่", command=lambda: self.content_result_text.delete("1.0", "end"), 
                     width=150, height=30, border_width=2, border_color="#3498DB").pack(side="left", padx=5)
    
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
        self.ad_prompt_text = ctk.CTkTextbox(left_frame, height=80, width=250, font=("Kanit", 12))
        self.ad_prompt_text.pack(padx=10, pady=5, fill="both", expand=False)
        self.ad_prompt_text.insert("1.0", "สร้างรูปโฆษณาสินค้า (ชื่อ: {product}, ราคา: {price}) ที่สวยงาม มีสไตล์สมัยใหม่ บนพื้นหลังที่น่าสนใจ")
        
        # Open Gemini button
        ctk.CTkButton(left_frame, text="🌐 เปิด Gemini Web", command=self.open_gemini_web, 
                     height=40, font=("Kanit", 13), fg_color="#4285F4", border_width=2, border_color="#1F73E6").pack(padx=10, pady=10, fill="x")
        
        # บันทึกรูป manual
        ctk.CTkLabel(left_frame, text="หรือสร้างโดยเพิ่มข้อความลงรูป:", font=("Kanit", 12)).pack(pady=5, anchor="w", padx=10)
        
        ctk.CTkLabel(left_frame, text="คำอธิบาย:", font=("Kanit", 12)).pack(pady=5, anchor="w", padx=10)
        self.ad_description_text = ctk.CTkTextbox(left_frame, height=60, width=250, font=("Kanit", 12))
        self.ad_description_text.pack(padx=10, pady=5, fill="both", expand=False)
        
        ctk.CTkButton(left_frame, text="🎨 เพิ่มข้อความบนรูป", command=self.create_simple_ad_manual, 
                     height=35, font=("Kanit", 12), fg_color="#E74C3C", border_width=2, border_color="#C0392B").pack(padx=10, pady=10, fill="x")
        
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
        
        ctk.CTkButton(button_frame, text="📁 เปิดโฟลเดอร์", command=self.open_ads_folder, width=150, height=30,
                     border_width=2, border_color="#3498DB").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="📤 โพส FB", command=self.post_ad_to_facebook, width=150, height=30,
                     border_width=2, border_color="#4267B2").pack(side="left", padx=5)
    
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
        self.fb_message_text = ctk.CTkTextbox(left_frame, height=100, width=250, font=("Kanit", 12))
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
        
        self.fb_response_text = ctk.CTkTextbox(right_frame, height=300, width=400, font=("Kanit", 12))
        self.fb_response_text.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Copy button
        ctk.CTkButton(right_frame, text="📋 คัดลอก Link", command=self.copy_post_link, 
                     height=30, border_width=2, border_color="#3498DB").pack(padx=10, pady=5, fill="x")
    
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
                detail = row[3] if len(row) > 3 else ""
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
        """เปิด Gemini Web และส่งรูป + prompt ไปให้"""
        # ดึง product combo value
        product_combo_value = self.ad_product_combo.get()
        if not product_combo_value:
            messagebox.showwarning("ขาดข้อมูล", "กรุณาเลือกสินค้า")
            return
        
        # แยก product name และ barcode จาก combo value (format: "Name (Barcode)")
        product_name = product_combo_value.split("(")[0].strip()
        barcode = product_combo_value.split("(")[1].rstrip(")").strip() if "(" in product_combo_value else ""
        
        if not barcode:
            messagebox.showwarning("ขาดข้อมูล", "ไม่พบบาร์โค้ดสินค้า")
            return
        
        # ค้นหารูปภาพจากโฟลเดอร์ img ที่ตรงกับบาร์โค้ด
        image_path = self._find_image_by_barcode(barcode)
        if not image_path:
            messagebox.showwarning("ขาดข้อมูล", f"ไม่พบรูปภาพสำหรับบาร์โค้ด: {barcode}\n\nตรวจสอบโฟลเดอร์ img")
            return
        
        price = self.ad_price_entry.get()
        prompt = self.ad_prompt_text.get("1.0", "end").strip()
        
        if not price:
            messagebox.showwarning("ขาดข้อมูล", "กรุณากรอกราคา")
            return
        
        # แทนที่ placeholder ในข้อความ
        full_prompt = prompt.format(product=product_name, price=price)
        
        # อัปเดต UI
        self.ad_status_label.configure(text="⏳ กำลังเปิด Gemini Web...")
        self.ad_preview_label.configure(text="")
        self.update_idletasks()
        
        # รัน in thread เพื่อไม่ให้ UI ค้าง
        thread = threading.Thread(target=self._open_gemini_with_image, args=(image_path, full_prompt, product_name, price, barcode))
        thread.daemon = True
        thread.start()
    
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
    
    def _open_gemini_with_image(self, image_path, prompt, product_name, price, barcode):
        """เปิด Gemini Web และส่งรูป + prompt ไปให้อัตโนมัติผ่าน Selenium"""
        try:
            from pathlib import Path
            import subprocess
            import os
            import platform
            
            self.after(0, lambda: self.ad_status_label.configure(text="⏳ เตรียมเปิด Gemini Web..."))
            
            # ปิด Chrome processes ที่เปิดอยู่เพื่อหลีกเลี่ยงการล็อคโปรไฟล์
            if platform.system() == "Windows":
                try:
                    self.after(0, lambda: print("🔄 ปิด Chrome ที่เปิดอยู่..."))
                    os.system("taskkill /im chrome.exe /f /t 2>nul")
                    time.sleep(3)  # รอให้ Chrome ปิดสมบูรณ์
                    self.after(0, lambda: print("✅ Chrome ปิดสำเร็จ"))
                except:
                    pass
            
            # ตั้งค่า Chrome options
            from selenium.webdriver.chrome.options import Options
            chrome_options = Options()
            
            print("DEBUG: เตรียม Chrome options...")
            
            # ใช้ temporary directory ระหว่าง test เพื่อหลีกเลี่ยง profile lock
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix="chrome_profile_")
            print(f"DEBUG: ใช้ temporary profile dir: {temp_dir}")
            
            # Fallback: ใช้ temp directory หากไม่สามารถใช้ real profile ได้
            chrome_user_data = temp_dir
            
            # เพิ่ม flags สำหรับป้องกันการล็อค
            print("DEBUG: เพิ่ม Chrome flags...")
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--no-default-browser-check')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--disable-extensions')
            
            print("DEBUG: ตั้งค่า profile...")
            # ลองใช้โปรไฟล์ Default จริง
            try:
                chrome_options.add_argument(f"user-data-dir={chrome_user_data}")
                self.after(0, lambda: print(f"✅ ใช้โปรไฟล์ Chrome จริง: {chrome_user_data}"))
            except Exception as e:
                print(f"⚠️ ไม่สามารถตั้งโปรไฟล์: {str(e)}")
            
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--start-maximized')
            
            # สร้าง driver ด้วย webdriver-manager
            print("DEBUG: import Selenium classes...")
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            from selenium import webdriver
            
            print("DEBUG: สร้าง ChromeDriver service...")
            service = Service(ChromeDriverManager().install())
            
            # Try to create driver
            driver = None
            try:
                print("DEBUG: สร้าง WebDriver instance...")
                self.after(0, lambda: self.ad_status_label.configure(text="⏳ เปิด Chrome..."))
                print("DEBUG: เรียก webdriver.Chrome()...")
                driver = webdriver.Chrome(service=service, options=chrome_options)
                print("DEBUG: Chrome created successfully!")
                self.after(0, lambda: print("✅ Chrome เปิดสำเร็จ (ใช้โปรไฟล์จริง)"))
            except Exception as e:
                error_msg = str(e)
                print(f"❌ ไม่สามารถเปิด Chrome ด้วยโปรไฟล์: {error_msg}")
                self.after(0, lambda msg=error_msg: (
                    self.ad_preview_label.configure(text=f"❌ เกิดข้อผิดพลาด: {msg}"),
                    self.ad_status_label.configure(text="❌ ข้อผิดพลาด Chrome"),
                    messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิด Chrome ได้\n\n{msg}")
                ))
                return
            
            if driver:
                import sys
                driver.set_window_size(1400, 900)
                
                # Update UI status
                self.after(0, lambda: self.ad_status_label.configure(text="⏳ โหลด Gemini Web..."))
                
                # Open Gemini Web
                print("🔄 เปิด Gemini Web...")
                sys.stdout.flush()
                driver.get('https://gemini.google.com/app')
                
                # Wait for page to load
                print("⏳ รอให้หน้าโหลด...")
                sys.stdout.flush()
                time.sleep(8)
                print("✅ หน้าโหลดเสร็จ กำลังค้นหา input field...")
                sys.stdout.flush()
                
                # Import Selenium support classes
                try:
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    print("✅ Import Selenium classes สำเร็จ")
                    sys.stdout.flush()
                except Exception as e:
                    print(f"❌ ไม่สามารถ import Selenium: {str(e)}")
                    sys.stdout.flush()
                    raise
                
                try:
                    # Update UI status
                    self.after(0, lambda: self.ad_status_label.configure(text="⏳ ค้นหา input field..."))
                    
                    print("🔍 เริ่มค้นหา input field...")
                    sys.stdout.flush()
                    
                    # Wait for input field to be ready
                    print("🔍 สร้าง WebDriverWait...")
                    sys.stdout.flush()
                    wait = WebDriverWait(driver, 20)
                    print("🔍 สร้าง WebDriverWait สำเร็จ")
                    sys.stdout.flush()
                    
                    # Try to find text input areas
                    input_selectors = [
                        'textarea',
                        '[contenteditable="true"]',
                        'input[type="text"]',
                        '.goog-textarea',
                        '[role="textbox"]',
                        '[data-tooltip*="message"]',
                        '[data-tooltip*="Message"]',
                        '.input-field',
                        '#input',
                        '.prompt-input',
                        '[class*="input"]',
                        '[class*="text"]',
                        '[data-test-id*="input"]',
                        'div[contenteditable]',
                        '.gemini-input',
                        '[placeholder*="prompt"]',
                        '[placeholder*="message"]',
                        'div[class*="textarea"]',
                        '[data-tooltip*="Send"]'
                    ]
                    
                    input_field = None
                    for selector in input_selectors:
                        try:
                            print(f"🔍 ลองค้นหา: {selector}")
                            sys.stdout.flush()
                            input_field = wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector)),
                                timeout=5
                            )
                            if input_field:
                                print(f"✅ พบ input field: {selector}")
                                sys.stdout.flush()
                                break
                        except:
                            continue
                    
                    if input_field:
                        # Send prompt to input
                        print("🖊️ กำลังกรอก prompt...")
                        sys.stdout.flush()
                        try:
                            input_field.click()
                            time.sleep(1)
                            input_field.clear()
                        except:
                            # If clear() doesn't work, try selecting all and delete
                            try:
                                input_field.send_keys(u'\ue000' + 'a')  # Ctrl+A
                                input_field.send_keys(u'\ue061')  # Delete
                            except:
                                pass
                        
                        # Send the prompt text
                        try:
                            input_field.send_keys(prompt)
                        except:
                            # If send_keys fails, try using JavaScript
                            try:
                                driver.execute_script("arguments[0].textContent = arguments[1];", input_field, prompt)
                                driver.execute_script("arguments[0].innerHTML = arguments[1];", input_field, prompt)
                            except:
                                pass
                        print("✅ กรอก prompt สำเร็จ")
                        sys.stdout.flush()
                        
                        self.after(0, lambda: self.ad_status_label.configure(text="⏳ อัพโหลดรูปภาพ..."))
                        time.sleep(2)
                    else:
                        print("⚠️ ไม่พบ input field")
                        sys.stdout.flush()
                    
                    # Find attach/upload button
                    print("🔍 ค้นหาปุ่มแนบรูป...")
                    sys.stdout.flush()
                    attach_button = None
                    attach_selectors = [
                        'button[aria-label*="attach"]',
                        'button[aria-label*="Attach"]',
                        'button[aria-label*="image"]',
                        'button[aria-label*="Image"]',
                        'button[aria-label*="upload"]',
                        'button[aria-label*="Upload"]',
                        'button[title*="attach"]',
                        'button[title*="Attach"]',
                        'button[title*="image"]',
                        'button[title*="Image"]',
                        '[role="button"][aria-label*="attach"]',
                        '[role="button"][aria-label*="image"]',
                        '[role="button"][aria-label*="upload"]',
                        'button[data-tooltip*="attach"]',
                        'button[data-tooltip*="image"]',
                        'button[aria-label*="add"]',
                        'button[aria-label*="Add"]',
                        'button[class*="attachment"]',
                        'button[class*="upload"]'
                    ]
                    
                    for selector in attach_selectors:
                        try:
                            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                            if buttons and len(buttons) > 0:
                                attach_button = buttons[0]
                                print(f"✅ พบปุ่มแนบรูป: {selector}")
                                sys.stdout.flush()
                                break
                        except:
                            continue
                    
                    # If attach button not found, try direct file input
                    if not attach_button:
                        print("⚠️ ไม่พบปุ่มแนบรูป ลองส่งไฟล์โดยตรง...")
                        sys.stdout.flush()
                        file_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
                        if file_inputs and len(file_inputs) > 0:
                            # Send file directly to file input
                            file_input = file_inputs[0]
                            abs_image_path = os.path.abspath(image_path)
                            print(f"📁 ส่งไฟล์: {abs_image_path}")
                            sys.stdout.flush()
                            driver.execute_script("arguments[0].style.display='block';", file_input)
                            file_input.send_keys(abs_image_path)
                            print("✅ ส่งไฟล์สำเร็จ")
                            sys.stdout.flush()
                            time.sleep(3)
                    else:
                        # Click attach button and select file
                        print("🖱️ กำลังคลิกปุ่มแนบรูป...")
                        sys.stdout.flush()
                        attach_button.click()
                        time.sleep(2)
                        
                        # Find and send file
                        file_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
                        if file_inputs and len(file_inputs) > 0:
                            file_input = file_inputs[0]
                            abs_image_path = os.path.abspath(image_path)
                            print(f"📁 ส่งไฟล์: {abs_image_path}")
                            sys.stdout.flush()
                            file_input.send_keys(abs_image_path)
                            print("✅ ส่งไฟล์สำเร็จ")
                            sys.stdout.flush()
                            time.sleep(3)
                    
                    # Try to send (find send button)
                    print("🔍 ค้นหาปุ่มส่ง...")
                    sys.stdout.flush()
                    send_selectors = [
                        'button[aria-label*="Send"]',
                        'button[aria-label*="send"]',
                        'button[aria-label*="submit"]',
                        'button[aria-label*="Submit"]',
                        '[data-tooltip*="Send"]',
                        '[data-tooltip*="send"]',
                        'button[title*="Send"]',
                        'button[title*="send"]',
                        '[role="button"][aria-label*="send"]',
                        '[role="button"][aria-label*="Submit"]',
                        'button[data-tooltip*="Send"]',
                        'button[data-tooltip*="send"]',
                        'button[class*="send"]',
                        'button[class*="submit"]',
                        '[class*="send-button"]',
                        '[class*="submit-button"]',
                        'button:last-child',  # Sometimes send button is last
                        'div[role="button"][aria-label*="Send"]'
                    ]
                    
                    sent = False
                    for selector in send_selectors:
                        try:
                            send_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                            if send_buttons and len(send_buttons) > 0:
                                print(f"🖱️ พบปุ่มส่ง กำลังคลิก: {selector}")
                                sys.stdout.flush()
                                send_buttons[0].click()
                                time.sleep(2)
                                sent = True
                                print("✅ ส่งสำเร็จ")
                                sys.stdout.flush()
                                break
                        except Exception as e:
                            print(f"⚠️ ไม่สามารถคลิก {selector}: {str(e)}")
                            sys.stdout.flush()
                            continue
                    
                    if not sent:
                        # Try pressing Enter
                        print("⏎ ลองกดปุ่ม Enter...")
                        sys.stdout.flush()
                        try:
                            if input_field:
                                input_field.send_keys(u'\ue007')  # Enter key
                            print("✅ ส่งสำเร็จ (Enter)")
                            sys.stdout.flush()
                        except Exception as e:
                            print(f"⚠️ ไม่สามารถกด Enter: {str(e)}")
                            sys.stdout.flush()
                            pass
                    
                    image_name = Path(image_path).name
                    success_text = f"""✅ ส่งข้อมูลไปยัง Gemini Web แล้ว

📋 ข้อมูลที่ส่ง:
• สินค้า: {product_name}
• บาร์โค้ด: {barcode}
• ราคา: {price}
• รูป: {image_name}

📍 Gemini กำลังสร้างรูปโฆษณา...

ปิดหน้าต่างเบราว์เซอร์เมื่อเสร็จ
"""
                    
                    self.after(0, lambda: (
                        self.ad_status_label.configure(text="✅ ส่งข้อมูลสำเร็จ"),
                        self.ad_preview_label.configure(text=success_text)
                    ))
                    print("✅ การทำงาน automation เสร็จสิ้น")
                    sys.stdout.flush()
                    
                    # Clean up temp directory
                    try:
                        if os.path.exists(temp_dir):
                            import shutil
                            shutil.rmtree(temp_dir, ignore_errors=True)
                            print(f"✅ ลบ temporary profile: {temp_dir}")
                    except:
                        pass
                    
                    # Close browser after completion (not closing - let user see results)
                    # driver.quit()
                    
                except Exception as e:
                    print(f"❌ Error during automation: {e}")
                    sys.stdout.flush()
                    import traceback
                    traceback.print_exc()
                    
                    # Clean up temp directory
                    try:
                        if os.path.exists(temp_dir):
                            import shutil
                            shutil.rmtree(temp_dir, ignore_errors=True)
                    except:
                        pass
                    
                    # ปิด driver ถ้าเกิด error
                    if driver:
                        try:
                            driver.quit()
                        except:
                            pass
                    
                    image_name = Path(image_path).name
                    # ถ้าอัตโนมัติล้มเหลว ให้ดำเนินการด้วยตนเอง
                    manual_text = f"""⚠️ ไม่สามารถสั่งการอัตโนมัติได้

กรุณากรอกข้อมูลด้วยตนเอง:
• สินค้า: {product_name}
• บาร์โค้ด: {barcode}
• ราคา: {price}
• รูป: {image_name}

📝 Prompt:
{prompt}

ขั้นตอน:
1️⃣  กดปุ่มแนบรูป (Attach/Image)
2️⃣  เลือกรูป: {image_name}
3️⃣  วาง Prompt ลงในช่องข้อความ
4️⃣  ให้ Gemini สร้างรูปโฆษณา
"""
                    
                    self.after(0, lambda: (
                        self.ad_status_label.configure(text="⚠️ กรุณากรอกด้วยตนเอง"),
                        self.ad_preview_label.configure(text=manual_text)
                    ))
            else:
                error_msg = "❌ Driver ไม่ได้สร้าง"
                print(error_msg)
                self.after(0, lambda: (
                    self.ad_preview_label.configure(text=error_msg),
                    self.ad_status_label.configure(text="❌ เกิดข้อผิดพลาด"),
                    messagebox.showerror("Error", error_msg)
                ))
        
        except Exception as e:
            error_msg = f"❌ เกิดข้อผิดพลาด:\n{str(e)}"
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            
            # ปิด driver ถ้ามี
            if 'driver' in locals() and driver:
                try:
                    driver.quit()
                except:
                    pass
            
            self.after(0, lambda: (
                self.ad_preview_label.configure(text=error_msg),
                self.ad_status_label.configure(text="❌ เกิดข้อผิดพลาด"),
                messagebox.showerror("Error", error_msg)
            ))
    
    def _call_gemini_api(self, image_path, prompt, product_name, price):
        """เรียก Gemini API สำหรับสร้างรูปโฆษณา (ใช้ไม่ได้ - สำรองไว้)"""
        try:
            import warnings
            warnings.filterwarnings('ignore', category=FutureWarning)
            import google.generativeai as genai
            import time
            
            # ตรวจสอบ API key
            api_key = self.ai_config.get("ai_api_key", "")
            if not api_key:
                self.after(0, lambda: (
                    self.ad_status_label.configure(text="❌ ไม่มี API Key กำหนด"),
                    messagebox.showerror("ไม่มี API Key", "กรุณาตั้งค่า Gemini API Key ก่อน")
                ))
                return
            
            genai.configure(api_key=api_key)
            
            # โหลดรูป
            from PIL import Image
            img = Image.open(image_path)
            
            # ใช้ Gemini 1.5 Flash (มี free quota ดี)
            model = genai.GenerativeModel('models/gemini-1.5-flash')
            
            # สร้าง prompt ที่ง่ายและสั้น
            enhanced_prompt = f"""สร้างรูปโฆษณาสินค้า:
- ชื่อ: {product_name}
- ราคา: {price}

{prompt}

ขนาด: 1200x628 pixels"""
            
            # ส่งคำขอไปยัง Gemini พร้อมรูปภาพ (retry 3 ครั้ง)
            max_retries = 3
            response = None
            
            for attempt in range(max_retries):
                try:
                    response = model.generate_content([enhanced_prompt, img])
                    break  # สำเร็จ
                except Exception as e:
                    if "quota" in str(e).lower() and attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # exponential backoff
                        self.after(0, lambda t=wait_time: 
                            self.ad_status_label.configure(text=f"⏳ Quota ครบแล้ว รอ {t} วินาทีแล้วลอง..."))
                        time.sleep(wait_time)
                    else:
                        raise
            
            if response and response.text:
                result_text = response.text
                
                # แสดงผล
                self.after(0, lambda: (
                    self.ad_preview_label.configure(text=f"✅ สร้างสำเร็จ!\n\n{result_text}"),
                    self.ad_status_label.configure(text="✅ Gemini สร้างโฆษณาสำเร็จ!")
                ))
            else:
                self.after(0, lambda: (
                    self.ad_preview_label.configure(text="⚠️ Gemini ตอบกลับแต่ไม่มีผล"),
                    self.ad_status_label.configure(text="⚠️ ไม่มีผลออกมา")
                ))
        
        except Exception as e:
            error_msg = f"❌ เกิดข้อผิดพลาด:\n{str(e)}"
            
            # แสดงคำแนะนำเพิ่มเติมสำหรับ quota
            if "quota" in str(e).lower():
                error_msg += "\n\n💡 Quota ครบแล้ว:\n- รอเรื่อย ๆ แล้วลองใหม่\n- หรือใช้ Paid API Key"
            
            self.after(0, lambda: (
                self.ad_preview_label.configure(text=error_msg),
                self.ad_status_label.configure(text="❌ เกิดข้อผิดพลาด"),
                messagebox.showerror("Gemini API Error", error_msg)
            ))
            print(f"Gemini API Error: {e}")

    
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
        
        try:
            img = Image.open(self.ad_image_path)
            width, height = img.size
            img_with_text = img.copy()
            draw = ImageDraw.Draw(img_with_text)
            
            try:
                font = ImageFont.truetype("kanit.ttf", 40)
            except:
                font = ImageFont.load_default()
            
            text = f"{description}\n{price}"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y = height - text_height - 20
            
            draw.rectangle([(x-10, y-10), (x+text_width+10, y+text_height+10)], fill=(255, 255, 255, 200))
            draw.text((x, y), text, fill=(0, 0, 0), font=font)
            
            os.makedirs("ads_output", exist_ok=True)
            output_path = f"ads_output/ad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            img_with_text.save(output_path)
            
            messagebox.showinfo("สำเร็จ", f"สร้างรูปโฆษณาแล้ว\n{output_path}")
            self.ad_status_label.configure(text=f"บันทึก: {output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"สร้างรูปไม่สำเร็จ: {e}")
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

    # =========================================
    # PRINTER LABEL Functions
    # =========================================
    def load_printer_settings(self):
        """โหลดการตั้งค่าเครื่องปริ้นจากไฟล์ config"""
        try:
            if os.path.exists('printer_config.json'):
                import json
                with open('printer_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.printer_name = config.get('printer_name', '')
                    print(f"✓ โหลดเครื่องปริ้น: {self.printer_name}")
        except Exception as e:
            print(f"⚠️ ไม่สามารถโหลด printer_config.json: {e}")
            self.printer_name = ''
    
    def save_printer_settings(self):
        """บันทึกการตั้งค่าเครื่องปริ้นลงไฟล์ config"""
        try:
            import json
            config = {'printer_name': self.printer_name}
            with open('printer_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                print(f"✓ บันทึกเครื่องปริ้น: {self.printer_name}")
        except Exception as e:
            print(f"❌ ไม่สามารถบันทึก printer_config.json: {e}")

    def open_printer_settings(self):
        """เปิดหน้าต่างตั้งค่าเครื่องปริ้น"""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("⚙️ ตั้งค่าเครื่องปริ้น")
        settings_window.geometry("400x300")
        settings_window.attributes("-topmost", True)
        
        ctk.CTkLabel(settings_window, text="⚙️ ตั้งค่าเครื่องปริ้น", 
                    font=("Kanit", 20, "bold")).pack(pady=20)
        
        # ดึงรายชื่อเครื่องปริ้น Windows
        import win32print
        try:
            printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)
            printer_names = [p[2] for p in printers]
        except:
            printer_names = ["Default Printer"]
        
        if not printer_names:
            printer_names = ["Default Printer"]
        
        ctk.CTkLabel(settings_window, text="เลือกเครื่องปริ้น:", 
                    font=("Kanit", 14)).pack(pady=10)
        
        printer_combo = ctk.CTkComboBox(settings_window, values=printer_names, 
                                       font=("Kanit", 12), width=300)
        printer_combo.set(self.printer_name if self.printer_name in printer_names else printer_names[0])
        printer_combo.pack(pady=10, padx=20)
        
        # ขนาดลาเบล
        ctk.CTkLabel(settings_window, text="ขนาดลาเบล: 1 × 2 นิ้ว (25.4 × 50.8 มม.)", 
                    font=("Kanit", 12)).pack(pady=10)
        
        def save_settings():
            self.printer_name = printer_combo.get()
            self.save_printer_settings()  # บันทึกลงไฟล์
            messagebox.showinfo("สำเร็จ", f"บันทึกเครื่องปริ้น: {self.printer_name}")
            settings_window.destroy()
        
        btn_save = ctk.CTkButton(settings_window, text="✓ บันทึก", command=save_settings,
                                fg_color="#2CC985", height=40, font=("Kanit", 14, "bold"))
        btn_save.pack(pady=20, padx=20, fill="x")

    def print_barcode_label(self):
        """ปริ้นลาเบลบาร์โค้ดของสินค้าที่เลือก"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("เตือน", "กรุณาเลือกสินค้าที่ต้องการปริ้น")
            return
        
        item_values = self.tree.item(selected[0])['values']
        # Column indices: 0=ID, 1=Barcode, 2=Name, 3=Brand, 4=CarModel, 5=Detail, 6=Cost, 7=Stock, 8=Price, 9=ImageID
        barcode = str(item_values[1]).strip()
        product_name = str(item_values[2]).strip()
        car_model = str(item_values[4]).strip() if len(item_values) > 4 else '-'
        price = str(item_values[8]).strip() if len(item_values) > 8 else '0'
        
        self.selected_barcode_data = {
            'barcode': barcode,
            'name': product_name,
            'car_model': car_model,
            'price': price
        }
        
        threading.Thread(target=self.run_print_label, daemon=True).start()

    def print_single_barcode(self):
        """ปริ้นลาเบลจากปุ่มด้านขวา"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("เตือน", "กรุณาเลือกสินค้าที่ต้องการปริ้น")
            return
        
        item_values = self.tree.item(selected[0])['values']
        # Column indices: 0=ID, 1=Barcode, 2=Name, 3=Brand, 4=CarModel, 5=Detail, 6=Cost, 7=Stock, 8=Price, 9=ImageID
        barcode = str(item_values[1]).strip()
        product_name = str(item_values[2]).strip()
        car_model = str(item_values[4]).strip() if len(item_values) > 4 else '-'
        price = str(item_values[8]).strip() if len(item_values) > 8 else '0'
        
        self.selected_barcode_data = {
            'barcode': barcode,
            'name': product_name,
            'car_model': car_model,
            'price': price
        }
        
        threading.Thread(target=self.run_print_label, daemon=True).start()

    def run_print_label(self):
        """สร้างและแสดงพรีวิวลาเบล 1x2 นิ้ว"""
        if not self.selected_barcode_data:
            return
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            import tempfile
        except ImportError:
            messagebox.showerror("ข้อผิดพลาด", "ต้องติดตั้ง Pillow\nพิมพ์: pip install Pillow")
            return
        
        barcode = self.selected_barcode_data['barcode']
        product_name = self.selected_barcode_data['name']
        car_model = self.selected_barcode_data.get('car_model', '-')
        price = self.selected_barcode_data['price']
        
        try:
            # สร้างลาเบล 1x2 นิ้ว (300 DPI = 300x600 pixels)
            width, height = 300, 600
            dpi = 300
            
            # สร้างรูปภาพ
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # โหลดฟอนต์ - ใช้ Kanit ที่มีในระบบ (ขนาดใหญ่ขึ้น)
            try:
                font_kanit_title = ImageFont.truetype("C:\\Users\\BRINGTOJZ\\AppData\\Local\\Microsoft\\Windows\\Fonts\\Kanit-Bold.ttf", 18)
                font_kanit_label = ImageFont.truetype("C:\\Users\\BRINGTOJZ\\AppData\\Local\\Microsoft\\Windows\\Fonts\\Kanit-Regular.ttf", 13)
                font_kanit_value = ImageFont.truetype("C:\\Users\\BRINGTOJZ\\AppData\\Local\\Microsoft\\Windows\\Fonts\\Kanit-Regular.ttf", 14)
                font_kanit_barcode = ImageFont.truetype("C:\\Users\\BRINGTOJZ\\AppData\\Local\\Microsoft\\Windows\\Fonts\\Kanit-Bold.ttf", 13)
            except:
                # Fallback ถ้าไม่มี Kanit
                font_kanit_title = ImageFont.load_default()
                font_kanit_label = ImageFont.load_default()
                font_kanit_value = ImageFont.load_default()
                font_kanit_barcode = ImageFont.load_default()
            
            # วาดขอบสีน้ำเงิน
            border_color = (51, 102, 153)
            draw.rectangle([8, 8, width-8, height-8], outline=border_color, width=2)
            
            # ข้อมูลต่างๆ
            y_pos = 15
            line_height = 42
            
            # ชื่อสินค้า
            draw.text((12, y_pos), "ชื่อสินค้า :", fill='black', font=font_kanit_label, anchor='lm')
            draw.text((155, y_pos), product_name, fill=(0, 102, 204), font=font_kanit_value, anchor='lm')
            y_pos += line_height
            
            # รุ่นที่ใช้
            draw.text((12, y_pos), "รุ่นที่ใช้ :", fill='black', font=font_kanit_label, anchor='lm')
            draw.text((155, y_pos), car_model, fill=(0, 102, 204), font=font_kanit_value, anchor='lm')
            y_pos += line_height
            
            # ราคา
            draw.text((12, y_pos), "ราคา :", fill='black', font=font_kanit_label, anchor='lm')
            price_text = f"฿ {price}"
            draw.text((155, y_pos), price_text, fill=(220, 20, 60), font=font_kanit_value, anchor='lm')
            y_pos += line_height + 5
            
            # เส้นคั่น
            draw.line([(12, y_pos), (width-12, y_pos)], fill='black', width=2)
            y_pos += 15
            
            # Barcode label
            draw.text((width//2, y_pos), "Barcode", fill='black', font=font_kanit_label, anchor='mm')
            y_pos += 30
            
            # วาดบาร์โค้ด Code-128 แบบเล็ก ตรงกลาง
            barcode_height = 50
            self._draw_code128_barcode_small(draw, barcode, width//2 - 45, y_pos, 90)
            y_pos += barcode_height + 8
            
            # เลขบาร์โค้ดด้านล่าง
            draw.text((width//2, y_pos), barcode, fill='black', font=font_kanit_barcode, anchor='mm')
            
            # บันทึกลาเบลชั่วคราว
            temp_label_path = os.path.join(tempfile.gettempdir(), f"label_preview_{barcode}.png")
            img.save(temp_label_path, 'PNG')
            print(f"✓ สร้างพรีวิวลาเบล 1x2 นิ้ว: {temp_label_path}")
            
            # เปิดหน้าต่าง preview
            self.show_label_preview(temp_label_path, barcode)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            messagebox.showerror("ข้อผิดพลาด", f"สร้างลาเบลไม่สำเร็จ: {str(e)}")

    def _draw_code128_barcode_small(self, draw, barcode_text, x, y, max_width):
        """วาดบาร์โค้ด Code-128 แบบเล็ก สำหรับลาเบล 1x2 นิ้ว (อยู่ตรงกลาง)"""
        try:
            bars = self._encode_code128(barcode_text)
            if bars:
                bar_width = 2  # เพิ่มความหนา
                bar_height = 50  # สูงขึ้น
                
                # คำนวณตำแหน่งให้อยู่ตรงกลาง
                total_bars_width = len(bars) * bar_width
                x_start = x + (max_width - total_bars_width) // 2
                
                x_pos = x_start
                for i, bar in enumerate(bars):
                    if bar == '1':  # สีดำ
                        draw.rectangle([x_pos, y, x_pos + bar_width, y + bar_height], fill='black')
                    x_pos += bar_width
                    if x_pos > x + max_width:  # ป้องกัน overflow
                        break
        except Exception as e:
            print(f"⚠️ ไม่สามารถวาด barcode: {e}")

    def _encode_code128(self, text):
        """Encode text เป็น Code-128 bars (simplified version)"""
        # สร้างรูปแบบบาร์โค้ดแบบง่าย
        bars = ""
        for char in text:
            # แต่ละตัวอักษรสร้างเป็น 11 bars
            code = ord(char) % 100  # ลดความซับซ้อน
            for i in range(11):
                bars += str((code >> i) & 1)
        return bars

    def show_label_preview(self, image_path, barcode):
        """แสดงพรีวิวลาเบลในหน้าต่างใหม่พร้อมปุ่มปริ้น"""
        if not self.app_running or not self.winfo_exists():
            return
        
        preview_window = ctk.CTkToplevel(self)
        preview_window.title(f"🖨️ พรีวิวลาเบล - {barcode}")
        preview_window.geometry("360x650")
        preview_window.attributes("-topmost", True)
        
        try:
            # โหลดและแสดงรูปภาพ
            from PIL import Image, ImageTk
            
            pil_image = Image.open(image_path)
            # ปรับขนาดให้ตรงกับลาเบล 1x2 นิ้ว (300x600 pixels แบบสมบูรณ์)
            pil_image = pil_image.resize((300, 600), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(pil_image)
            
            # แสดงรูป
            img_label = ctk.CTkLabel(preview_window, image=photo, text="")
            img_label.image = photo
            img_label.pack(pady=3, padx=3)
            
            # Frame ปุ่ม
            btn_frame = ctk.CTkFrame(preview_window, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=10)
            
            def print_now():
                """ปริ้นทันที"""
                if self.printer_name:
                    try:
                        import win32api
                        win32api.ShellExecute(0, "print", image_path, f'"{self.printer_name}"', ".", 0)
                        messagebox.showinfo("สำเร็จ", f"ส่งปริ้นลาเบล: {barcode}")
                        preview_window.destroy()
                    except Exception as e:
                        messagebox.showerror("ข้อผิดพลาด", f"ปริ้นไม่สำเร็จ: {str(e)}")
                else:
                    messagebox.showwarning("เตือน", "กรุณาตั้งค่าเครื่องปริ้นก่อน")
            
            btn_print = ctk.CTkButton(btn_frame, text="🖨️ ปริ้น", command=print_now,
                                     fg_color="#2E86C1", height=40, font=("Kanit", 14, "bold"))
            btn_print.pack(side="left", fill="x", expand=True, padx=5)
            
            btn_close = ctk.CTkButton(btn_frame, text="✕ ปิด", command=preview_window.destroy,
                                     fg_color="#E74C3C", height=40, font=("Kanit", 14, "bold"))
            btn_close.pack(side="left", padx=5)
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"แสดงพรีวิวไม่สำเร็จ: {str(e)}")
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"แสดงพรีวิวไม่สำเร็จ: {str(e)}")

    # =========================================
    # RECEIPT GENERATION (ระบบสร้างใบเสร็จ)
    # =========================================
    def load_receipt_settings(self):
        """โหลดการตั้งค่าใบเสร็จ"""
        try:
            if os.path.exists("receipt_settings.json"):
                with open("receipt_settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.receipt_auto_print = settings.get("auto_print", False)
        except:
            self.receipt_auto_print = False

    def save_receipt_settings(self):
        """บันทึกการตั้งค่าใบเสร็จ"""
        try:
            settings = {"auto_print": self.receipt_auto_print}
            with open("receipt_settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except:
            pass

    def generate_receipt_pdf(self, receipt_id, timestamp, items, total_bill, discount_amount, 
                            final_total, payment_method, used_coupon, received_coupon):
        """สร้างไฟล์ PDF ใบเสร็จด้วย fpdf2 รองรับภาษาไทย
        
        Args:
            receipt_id: เลขที่ใบเสร็จ
            timestamp: วันที่เวลา
            items: รายการสินค้า [{'name', 'qty', 'price', 'total'}, ...]
            total_bill: ยอดรวมก่อนลด
            discount_amount: ยอดส่วนลด
            final_total: ยอดสุดท้าย
            payment_method: วิธีชำระเงิน
            used_coupon: โค้ตที่ใช้
            received_coupon: โค้ตที่ได้รับ
        """
        try:
            pdf_path = os.path.join(self.receipts_folder, f"{receipt_id}.pdf")
            
            # สร้าง PDF ด้วย fpdf2
            from fpdf import XPos, YPos
            pdf = FPDF(format=(80, 200), unit="mm")
            pdf.add_page()
            
            # เพิ่ม Kanit font สำหรับภาษาไทย
            import sys
            if sys.platform == 'win32':
                font_dir = os.path.expanduser(r'~\AppData\Local\Microsoft\Windows\Fonts')
            else:
                font_dir = os.path.expanduser('~/.local/share/fonts')
            
            # ค้นหาฟอนต์ไทยที่มีอยู่ - ลองแต่ละตัวตามลำดับ
            thai_font = None
            font_names = ['TH SarabunPSK.ttf', 'THSarabunNew.ttf', 'Kanit-Regular.ttf', 'tahoma.ttf']
            
            for font_name in font_names:
                font_path = os.path.join(font_dir, font_name)
                if os.path.exists(font_path):
                    font_clean_name = font_name.replace('.ttf', '').replace(' ', '')
                    try:
                        pdf.add_font(font_clean_name, "", font_path)
                        thai_font = font_clean_name
                        break
                    except:
                        continue
            
            # ถ้าไม่เจอฟอนต์ไทย ให้แจ้ง error แทนใช้ fallback เสียหายหาย
            if thai_font is None:
                raise Exception(f"ไม่พบฟอนต์ไทยใน {font_dir}. โปรดติดตั้ง Kanit หรือ TH Sarabun PSK")
            
            # Set margin
            pdf.set_margins(3, 3, 3)
            
            # เพิ่มโลโก้บนหัวใบเสร็จ
            try:
                logo_path = os.path.join(os.path.dirname(__file__), "img", "logo.png")
                if os.path.exists(logo_path):
                    pdf.image(logo_path, x=30, y=5, w=20, h=20)
                    pdf.ln(24)  # เพิ่มระยะห่างให้เพียงพอ (โลโก้สูง 20mm)
            except:
                pass
            
            # ชื่อร้าน - use Helvetica for English
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 6, "JZ Auto Parts", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            pdf.set_font(thai_font, "", 9)
            pdf.cell(0, 4, "ร้านอะไหล่รถ JZ", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            
            # เส้นคั่น
            pdf.set_font(thai_font, "", 7)
            pdf.cell(0, 3, "=" * 30, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            
            # ข้อมูลใบเสร็จ - เลขซ้าย เวลาขวา
            # จัดการกรณี timestamp เป็นค่าว่าง
            if timestamp and timestamp.strip():
                try:
                    date_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    # ถ้า format ไม่ตรง ใช้เวลาปัจจุบัน
                    date_time = datetime.now()
            else:
                # ถ้า timestamp เป็นค่าว่าง ใช้เวลาปัจจุบัน (เวลาออกใบเสร็จจริง)
                date_time = datetime.now()
            
            pdf.set_font(thai_font, "", 9)
            pdf.cell(40, 4, f"เลขที่ใบเสร็จ : {receipt_id}", border=0, align="L", new_x=XPos.LEFT, new_y=YPos.TOP)
            pdf.cell(0, 4, f"เวลา : {date_time.strftime('%d/%m/%Y %H:%M:%S')}", border=0, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            pdf.ln(2)
            
            # ตารางรายการสินค้า
            col_widths = [25, 12, 15, 16]
            pdf.set_font(thai_font, "", 10)
            # หัวตารางพื้นหลังสีเทา (ทดแทน bold)
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(col_widths[0], 4, "สินค้า", border=1, align="C", fill=True)
            pdf.cell(col_widths[1], 4, "จำนวน", border=1, align="C", fill=True) 
            pdf.cell(col_widths[2], 4, "ราคา", border=1, align="C", fill=True)
            pdf.cell(col_widths[3], 4, "รวม", border=1, align="C", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_fill_color(255, 255, 255)
            
            # รายการสินค้า
            pdf.set_font(thai_font, "", 10)
            for item in items:
                name = item['name'][:12] if len(item['name']) > 12 else item['name']
                pdf.cell(col_widths[0], 4, name, border=1, align="C")
                pdf.cell(col_widths[1], 4, str(item['qty']), border=1, align="C")
                pdf.cell(col_widths[2], 4, f"{item['price']:.2f}", border=1, align="C")
                pdf.cell(col_widths[3], 4, f"{item['total']:.2f}", border=1, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            pdf.ln(1)
            
            # เส้นคั่น
            pdf.set_font(thai_font, "", 7)
            pdf.cell(0, 3, "=" * 30, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            
            # สรุปยอดขาย
            pdf.set_font(thai_font, "", 9)
            pdf.cell(0, 4, f"ยอดรวม : {total_bill:,.2f} บาท", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
            
            if discount_amount > 0:
                pdf.cell(0, 4, f"ส่วนลด : -{discount_amount:,.2f} บาท", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
            
            pdf.cell(0, 4, f"ยอดที่จ่าย : {final_total:,.2f} บาท", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

            if used_coupon and used_coupon != "-":
                pdf.cell(0, 4, f"โค้ตที่ใช้ : {used_coupon}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
            
            pdf.ln(2)
            
            # วิธีชำระเงิน
            pdf.set_font(thai_font, "", 9)
            pdf.cell(0, 4, f"วิธีจ่าย : {payment_method}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
            
            # โค้ต
            
            if received_coupon and received_coupon != "-":
                pdf.cell(0, 4, f"โค้ตส่วนลดที่ได้รับ : {received_coupon}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
            
            pdf.ln(2)
            
            # QR Code - ส่วนลดที่ได้รับ
            try:
                # ถ้ามีโค้ตที่ได้รับ ให้แสดง QR Code ของโค้ตนั้น
                qr_code_data = received_coupon if (received_coupon and received_coupon != "-") else receipt_id
                qr_img = self._generate_barcode_image(qr_code_data)
                if qr_img:
                    # วาง QR Code ตรงกลาง (ขนาด 38x38mm)
                    # บันทึก QR Code ลงไฟล์ temp เพื่อการประมวลผล
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        qr_img.save(tmp.name)
                        tmp_qr_path = tmp.name
                    
                    # ไม่แสดงเลขใบเสร็จด้านบน เอาไปแล้ว
                    pdf.image(tmp_qr_path, x=21, y=pdf.get_y(), w=38, h=38)
                    pdf.ln(40)
                    
                    # ลบไฟล์ temp หลังเสร็จ
                    try:
                        os.remove(tmp_qr_path)
                    except:
                        pass
            except:
                pass
            
            pdf.ln(1)
            
            # ข้อความปิด
            pdf.set_font(thai_font, "", 10)
            pdf.cell(0, 3, "=" * 30, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            
            pdf.set_font(thai_font, "", 10)
            pdf.cell(0, 4, "ขอบคุณสำหรับการใช้บริการ", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            
            
            pdf.set_font(thai_font, "", 10)
            pdf.cell(0, 3, "FACEBOOK: PKN เครื่องเลื้อยไม้ เครื่องตัดหญ้า ราคาถูก", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            pdf.cell(0, 3, "TEL: 086-283-6944", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            
            # บันทึก PDF
            pdf.output(pdf_path)
            
            print(f"✓ สร้างใบเสร็จ PDF: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            print(f"✗ สร้างใบเสร็จ PDF ไม่สำเร็จ: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _generate_barcode_image(self, barcode_text):
        """สร้าง QR Code รูปภาพ"""
        try:
            # ใช้ QR Code แทน Barcode
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(barcode_text)
            qr.make(fit=True)
            
            # สร้างรูปภาพ QR Code
            qr_img = qr.make_image(fill_color="black", back_color="white")
            return qr_img
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return None

    def show_receipt_preview(self, pdf_path):
        """แสดงตัวอย่าง PDF ใบเสร็จ"""
        try:
            # หลังจากสร้าง PDF สำเร็จ สามารถแสดงพรีวิว
            import subprocess
            subprocess.Popen(['start', pdf_path], shell=True)
        except:
            messagebox.showinfo("ใบเสร็จ", f"บันทึกใบเสร็จแล้ว:\n{pdf_path}")

    def print_receipt(self, pdf_path, printer_name=None):
        """ปริ้นใบเสร็จ PDF ผ่านเครื่องปริ้น + แสดงพรีวิว
        
        Args:
            pdf_path: เส้นทางไฟล์ PDF
            printer_name: ชื่อเครื่องปริ้น (ถ้าเป็น None ใช้เครื่องปริ้นเริ่มต้น)
        """
        try:
            if not os.path.exists(pdf_path):
                messagebox.showerror("ข้อผิดพลาด", "ไม่พบไฟล์ PDF")
                return False
            
            # ถ้าไม่ได้ระบุเครื่องปริ้น ใช้เครื่องปริ้นที่บันทึกไว้
            if printer_name is None:
                printer_name = self.get_selected_printer()
            
            # แสดงพรีวิว PDF ในโปรแกรมที่เลือก (ใช้วิธี non-blocking ให้คงไว้)
            try:
                # เปิด PDF ด้วย default viewer (ไม่ปิดอัตโนมัติ)
                import subprocess
                subprocess.Popen(['start', '', pdf_path], shell=True)
                print(f"✓ เปิดพรีวิว PDF: {pdf_path}")
            except Exception as e:
                print(f"⚠ ไม่สามารถเปิดพรีวิว: {e}")
                import subprocess
                subprocess.Popen(f'start "" "{pdf_path}"', shell=True)
            
            # ปริ้นอัตโนมัติหากเปิดใช้งาน
            if self.receipt_auto_print:
                try:
                    os.startfile(pdf_path, "print")
                    print(f"✓ ส่งคำสั่งปริ้นอัตโนมัติ: {pdf_path}")
                except:
                    pass
            
            return True
            
        except Exception as e:
            print(f"✗ ปริ้นใบเสร็จไม่สำเร็จ: {e}")
            messagebox.showerror("ข้อผิดพลาด", f"ปริ้นไม่สำเร็จ: {str(e)}")
            return False

    def process_receipt_after_checkout(self, receipt_id, timestamp, items, total_bill, 
                                      discount_amount, final_total, payment_method, 
                                      used_coupon, received_coupon):
        """ประมวลผลใบเสร็จหลังจากชำระเงิน
        
        ฟังก์ชันนี้ถูกเรียกจาก run_checkout_thread
        """
        try:
            # 1. สร้าง PDF ใบเสร็จ
            pdf_path = self.generate_receipt_pdf(
                receipt_id, timestamp, items, total_bill, 
                discount_amount, final_total, payment_method, 
                used_coupon, received_coupon
            )
            
            if not pdf_path:
                print("⚠ ไม่สามารถสร้าง PDF ใบเสร็จ")
                return
            
            # 2. ตัดสินใจว่าจะปริ้นอัตโนมัติหรือให้ผู้ใช้เลือก
            if self.receipt_auto_print:
                # ปริ้นอัตโนมัติ
                self.print_receipt(pdf_path)
            else:
                # แสดงพรีวิวให้ผู้ใช้เลือก
                if self.app_running and self.winfo_exists():
                    self.after(0, lambda: self._show_receipt_options(pdf_path))
                    
        except Exception as e:
            print(f"✗ ประมวลผลใบเสร็จไม่สำเร็จ: {e}")
            import traceback
            traceback.print_exc()

    def _show_receipt_options(self, pdf_path):
        """แสดงตัวเลือกสำหรับใบเสร็จ (ดู, ปริ้น, บันทึก)"""
        try:
            # เปิด PDF preview ให้ดู
            import subprocess
            subprocess.Popen(['start', pdf_path], shell=True)
            
        except Exception as e:
            print(f"✗ แสดงตัวเลือกใบเสร็จไม่สำเร็จ: {e}")

    def get_selected_printer(self):
        """ดึงชื่อเครื่องปริ้นที่เลือก"""
        try:
            if hasattr(self, 'printer_name'):
                return self.printer_name
        except:
            pass
        return None

    def toggle_receipt_auto_print(self):
        """สลับโหมดปริ้นอัตโนมัติ"""
        self.receipt_auto_print = not self.receipt_auto_print
        self.save_receipt_settings()
        
        status = "เปิด" if self.receipt_auto_print else "ปิด"
        messagebox.showinfo("ตั้งค่า", f"ปริ้นอัตโนมัติ: {status}")
        
        # อัปเดตตัวบ่งชี้สถานะ
        self.update_auto_print_indicator()
    
    def update_auto_print_indicator(self):
        """อัปเดตตัวบ่งชี้สถานะปริ้นอัตโนมัติ"""
        if hasattr(self, 'lbl_auto_print_status'):
            if self.receipt_auto_print:
                self.lbl_auto_print_status.configure(text="🟢 เปิด", text_color="#27AE60")
            else:
                self.lbl_auto_print_status.configure(text="⭕ ปิด", text_color="#E74C3C")

if __name__ == "__main__":
    app = StockManagerApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.destroy()
