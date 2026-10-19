import cv2
import time
import threading
import ctypes
import base64
import io
import numpy as np
import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

# ==========================================
# 1. BẬT HỖ TRỢ HIỂN THỊ SẮC NÉT (HIGH DPI)
# ==========================================
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

# ==============================================================================
# CAU HINH THONG SO HE THONG
# ==============================================================================
BAUD_RATE = 115200

DELAY_M8 = 3.7  # Thoi gian (giay) tu luc phat hien M8 den khi kich xi lanh
DELAY_M12 = 7.7  # Thoi gian (giay) tu luc phat hien M12 den khi kich xi lanh

# Nguong kich thuoc & Hinh dang cho Camera
R_M8_MIN, R_M8_MAX = 80, 125  # Nâng dải bán kính M8 rộng hơn tránh nhiễu
R_M12_MIN, R_M12_MAX = 126, 165  # Nâng dải bán kính M12 rộng hơn tránh nhiễu

MIN_AREA = 2500  # Dien tich toi thieu
MAX_DIAMETER_PX = 340  # Duong kinh toi da (px)

MAX_ASPECT_RATIO = 1.35  # Ti le dai/rong linh hoat hon
MIN_SOLIDITY = 0.80  # Do dac Solidity

PIXEL_TO_MM = 0.1  # Ti le quy doi Pixel -> mm
MARGIN_BORDER = 10  # Khoang cach an toan tới mép


CTUT_LOGO_BASE64 = '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'


class SortingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HỆ THỐNG PHÂN LOẠI VÀ LƯU KHO TỰ ĐỘNG")
        self.root.geometry("1280x850")
        self.root.minsize(1024, 600)
        self.root.configure(bg="#2c3e50")

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Cong Serial
        self.ser = None
        self.is_running = True
        self.serial_lock = threading.Lock()

        # Camera
        self.cap = cv2.VideoCapture(0)
        self.is_auto_running = False

        # --- BIEN QUAN LY TRANG THAI NHAN DIEN ---
        self.object_detected_in_current_pass = False
        self.freeze_until = 0
        self.frozen_frame = None

        # Dem so luong dai oc & Cau hinh muc gom
        self.target_count = tk.IntVar(value=5)  # Giá trị mặc định là 5
        self.count_m8 = 0
        self.count_m12 = 0
        self.warehouse_status = [False] * 8

        # Thiet lap Giao dien
        self.setup_styles()
        self.create_widgets()

        # Luong doc Serial non-blocking
        self.serial_thread = threading.Thread(target=self.read_serial_loop, daemon=True)
        self.serial_thread.start()

        # Luong cap nhat Camera
        self.update_camera()

    def setup_styles(self):
        """Chỉ định dạng giao diện; không thay đổi thuật toán điều khiển."""
        self.ui = {
            "bg": "#EAF3FB", "panel": "#FFFFFF", "panel2": "#EDF5FC",
            "text": "#173454", "muted": "#607B97", "cyan": "#087BAA",
            "blue": "#2374B9", "green": "#10976D", "red": "#D8484C",
            "amber": "#D58A16", "border": "#C9DCEB",
        }
        c = self.ui
        self.root.configure(bg=c["bg"])
        self.root.geometry("1440x900")
        self.root.minsize(1120, 720)
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(".", background=c["bg"], foreground=c["text"],
                             font=("Segoe UI", 10))
        self.style.configure("TFrame", background=c["bg"])
        self.style.configure("Panel.TFrame", background=c["panel"])
        self.style.configure("TLabel", background=c["bg"], foreground=c["text"])
        self.style.configure("Panel.TLabel", background=c["panel"], foreground=c["text"])
        self.style.configure("Muted.TLabel", background=c["panel"], foreground=c["muted"])
        self.style.configure("Accent.TLabel", background=c["panel"], foreground=c["cyan"],
                             font=("Segoe UI", 12, "bold"))
        self.style.configure("Count.TLabel", background=c["panel"], foreground=c["text"],
                             font=("Segoe UI", 17, "bold"))
        self.style.configure("Position.TLabel", background=c["panel"], foreground=c["cyan"],
                             font=("Segoe UI", 18, "bold"))
        self.style.configure("TNotebook", background=c["bg"], borderwidth=0, tabmargins=[0, 4, 0, 0])
        self.style.configure("TNotebook.Tab", background=c["panel2"], foreground=c["text"],
                             padding=[22, 12], font=("Segoe UI", 11, "bold"), borderwidth=0)
        self.style.map("TNotebook.Tab",
                       background=[("selected", c["blue"]), ("active", "#D9EAF8")],
                       foreground=[("selected", "#FFFFFF"), ("active", c["text"])])
        self.style.configure("TLabelframe", background=c["panel"], bordercolor=c["border"],
                             lightcolor=c["border"], darkcolor=c["border"], relief="solid",
                             borderwidth=1)
        self.style.configure("TLabelframe.Label", background=c["panel"], foreground=c["cyan"],
                             font=("Segoe UI", 11, "bold"))
        self.style.configure("TButton", background=c["panel2"], foreground=c["text"],
                             padding=[12, 10], borderwidth=0, font=("Segoe UI", 10, "bold"))
        self.style.map("TButton", background=[("active", "#D5E8F7"), ("disabled", "#E1E8EF")],
                       foreground=[("disabled", "#7C8EA0")])
        for name, color, active in (
            ("Action", c["green"], "#059669"),
            ("Stop", c["red"], "#DC2626"),
            ("Reset", c["amber"], "#D97706"),
            ("Primary", c["blue"], "#1D4ED8"),
        ):
            self.style.configure(name + ".TButton", background=color, foreground="#FFFFFF",
                                 padding=[12, 10], borderwidth=0,
                                 font=("Segoe UI", 10, "bold"))
            self.style.map(name + ".TButton", background=[("active", active)])
        self.style.configure("M8.Horizontal.TProgressbar", background=c["cyan"], troughcolor="#DCEAF4", thickness=9)
        self.style.configure("M12.Horizontal.TProgressbar", background=c["amber"], troughcolor="#DCEAF4", thickness=9)
        self.style.configure("M8.Horizontal.TProgressbar", troughcolor="#DCEBF6",
                             background=c["cyan"], thickness=14, borderwidth=0)
        self.style.configure("M12.Horizontal.TProgressbar", troughcolor="#F4E7D2",
                             background=c["amber"], thickness=14, borderwidth=0)
        self.style.configure("TCombobox", fieldbackground=c["panel2"],
                             background=c["panel2"], foreground=c["text"],
                             arrowcolor=c["cyan"], padding=5)
        self.style.map("TCombobox", fieldbackground=[("readonly", c["panel2"])],
                       foreground=[("readonly", c["text"])])
        self.root.option_add("*TCombobox*Listbox.background", c["panel2"])
        self.root.option_add("*TCombobox*Listbox.foreground", c["text"])

    def _ui_card(self, parent, title, fill="x", expand=False, pady=7):
        card = ttk.LabelFrame(parent, text="  " + title + "  ")
        card.pack(fill=fill, expand=expand, pady=pady)
        return card

    def create_widgets(self):
        c = self.ui
        header = tk.Frame(self.root, bg=c["bg"], height=110)
        header.pack(fill="x", padx=22, pady=(12, 6))
        header.pack_propagate(False)
        # Logo được nhúng trực tiếp vào file Python: không cần chép thêm ảnh.
        logo_bytes = base64.b64decode(CTUT_LOGO_BASE64)
        self.ctut_logo = ImageTk.PhotoImage(Image.open(io.BytesIO(logo_bytes)))
        tk.Label(header, image=self.ctut_logo, bg=c["bg"], bd=0).pack(side="left", padx=(2, 18))
        header_text = tk.Frame(header, bg=c["bg"])
        header_text.pack(side="left", fill="both", expand=True)
        tk.Label(header_text, text="TRƯỜNG ĐẠI HỌC KỸ THUẬT – CÔNG NGHỆ CẦN THƠ",
                 bg=c["bg"], fg=c["text"],
                 font=("Segoe UI", 17, "bold"), anchor="w").pack(fill="x", pady=(5, 2))
        tk.Label(header_text, text="HỆ THỐNG PHÂN LOẠI VÀ LƯU KHO TỰ ĐỘNG",
                 bg=c["bg"], fg=c["cyan"],
                 font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x")
        tk.Label(header_text, text="GIAO DIỆN GIÁM SÁT VÀ ĐIỀU KHIỂN  •  M8 / M12",
                 bg=c["bg"], fg=c["muted"],
                 font=("Segoe UI", 10), anchor="w").pack(fill="x", pady=(4, 0))

        top_bar = ttk.LabelFrame(self.root, text="  KẾT NỐI THIẾT BỊ  |  SERIAL 115200 BAUD  ")
        top_bar.pack(fill="x", padx=22, pady=(4, 10))
        ttk.Label(top_bar, text="CỔNG COM", style="Panel.TLabel").pack(side="left", padx=(15, 8), pady=12)
        self.cb_ports = ttk.Combobox(top_bar, width=12, state="readonly")
        self.cb_ports.pack(side="left", padx=4, pady=12)
        self.refresh_ports()
        self.btn_refresh = ttk.Button(top_bar, text="LÀM MỚI", command=self.refresh_ports)
        self.btn_refresh.pack(side="left", padx=5, pady=12)
        self.btn_connect = ttk.Button(top_bar, text="KẾT NỐI", command=self.toggle_connect,
                                      style="Action.TButton", width=15)
        self.btn_connect.pack(side="left", padx=8, pady=12)
        self.lbl_serial_status = ttk.Label(top_bar, text="●  CHƯA KẾT NỐI",
                                            style="Panel.TLabel",
                                            font=("Segoe UI", 10, "bold"),
                                            foreground=c["red"])
        self.lbl_serial_status.pack(side="right", padx=18, pady=12)

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=22, pady=(0, 14))
        self.tab_auto = ttk.Frame(notebook)
        notebook.add(self.tab_auto, text="  GIÁM SÁT & TỰ ĐỘNG  ")
        self.tab_manual = ttk.Frame(notebook)
        notebook.add(self.tab_manual, text="  ĐIỀU KHIỂN THỦ CÔNG  ")
        self.setup_tab_auto()
        self.setup_tab_manual()

    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.cb_ports['values'] = ports
        if ports:
            self.cb_ports.current(0)

    def toggle_connect(self):
        if self.ser and self.ser.is_open:
            with self.serial_lock:
                self.ser.close()
                self.ser = None
            self.lbl_serial_status.config(text="Trạng thái: ĐÃ NGẮT KẾT NỐI", foreground='#e74c3c')
            self.btn_connect.config(text="⚡ KẾT NỐI", style='Action.TButton')
        else:
            port = self.cb_ports.get()
            if not port:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn cổng COM!")
                return
            try:
                with self.serial_lock:
                    self.ser = serial.Serial(port, BAUD_RATE, timeout=0.1)
                time.sleep(1.5)
                self.lbl_serial_status.config(text=f"Trạng thái: ĐÃ KẾT NỐI ({port})", foreground='#2ecc71')
                self.btn_connect.config(text="🔌 NGẮT KẾT NỐI", style='Stop.TButton')
            except Exception as e:
                messagebox.showerror("Lỗi kết nối", f"Không thể mở cổng {port}:\n{e}")

    def send_cmd(self, cmd):
        """Gửi lệnh Serial an toàn"""
        if self.ser and self.ser.is_open:
            try:
                with self.serial_lock:
                    self.ser.reset_output_buffer()
                    self.ser.write((cmd + '\r\n').encode('utf-8'))
                    self.ser.flush()
            except Exception as e:
                print(f"Lỗi gửi Serial ({cmd}): {e}")

    def setup_tab_auto(self):
        c = self.ui
        self.tab_auto.columnconfigure(0, weight=6)
        self.tab_auto.columnconfigure(1, weight=7)
        self.tab_auto.rowconfigure(0, weight=1)

        left_frame = ttk.LabelFrame(self.tab_auto, text="  CAMERA TRỰC TIẾP  |  FULL HD 1080P  ")
        left_frame.grid(row=0, column=0, padx=(0, 9), pady=10, sticky="nsew")
        # Giới hạn chiều cao vùng camera, tránh chiếm toàn bộ cột trái.
        cam_holder = tk.Frame(left_frame, bg="#E7F0F8", height=355)
        cam_holder.pack(fill="x", padx=10, pady=(10, 5))
        cam_holder.pack_propagate(False)
        self.lbl_cam = ttk.Label(cam_holder, background="#E7F0F8", anchor="center")
        self.lbl_cam.pack(fill="both", expand=True)
        camera_footer = tk.Frame(left_frame, bg=c["panel"], height=42)
        camera_footer.pack(fill="x", padx=10, pady=(0, 9))
        self.camera_hint = tk.Label(camera_footer, text="● CAMERA  |  Chờ khởi động nhận dạng",
                                    bg=c["panel"], fg=c["muted"], anchor="w",
                                    font=("Segoe UI", 10, "bold"))
        self.camera_hint.pack(side="left", padx=6, pady=7)
        tk.Label(camera_footer, text="M8  •  M12  •  SẢN PHẨM LỖI",
                 bg=c["panel"], fg=c["blue"],
                 font=("Segoe UI", 9, "bold")).pack(side="right", padx=6)

        # Phần trống dưới camera được dùng làm bảng hướng dẫn thao tác,
        # không bổ sung lệnh điều khiển hoặc thay đổi thuật toán.
        info = ttk.LabelFrame(left_frame, text="  THÔNG TIN VẬN HÀNH  ")
        info.pack(fill="both", expand=True, padx=10, pady=(8, 10))
        for heading, detail in (
            ("01  KẾT NỐI THIẾT BỊ", "Chọn cổng COM và kết nối Arduino Mega 2560."),
            ("02  THIẾT LẬP PHÂN LOẠI", "Chọn số lượng đai ốc cần gom vào mỗi hộp."),
            ("03  GIÁM SÁT NHẬN DẠNG", "Quan sát camera và bộ đếm đai ốc M8 / M12."),
            ("04  QUẢN LÝ LƯU KHO", "Theo dõi trạng thái 8 ô; xuất hộp khi có hàng."),
        ):
            item = tk.Frame(info, bg=c["panel"])
            item.pack(fill="x", padx=14, pady=5)
            tk.Label(item, text=heading, bg=c["panel"], fg=c["blue"],
                     font=("Segoe UI", 10, "bold"), anchor="w").pack(anchor="w")
            tk.Label(item, text=detail, bg=c["panel"], fg=c["muted"],
                     font=("Segoe UI", 9), anchor="w", wraplength=430,
                     justify="left").pack(anchor="w", pady=(1, 0))

        right_frame = ttk.Frame(self.tab_auto)
        right_frame.grid(row=0, column=1, padx=(9, 0), pady=10, sticky="nsew")

        ctrl_group = self._ui_card(right_frame, "ĐIỀU KHIỂN TỰ ĐỘNG", pady=4)
        cfg_frame = ttk.Frame(ctrl_group, style="Panel.TFrame")
        cfg_frame.pack(fill="x", padx=12, pady=(6, 3))
        ttk.Label(cfg_frame, text="SỐ SẢN PHẨM / HỘP", style="Muted.TLabel",
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        self.spn_target = tk.Spinbox(cfg_frame, from_=1, to=100, textvariable=self.target_count,
                                     width=5, command=self.on_target_change,
                                     bg="#FFFFFF", fg=c["text"], insertbackground=c["text"],
                                     buttonbackground=c["panel2"], relief="flat",
                                     font=("Segoe UI", 12, "bold"))
        self.spn_target.pack(side="right", padx=5)
        self.target_count.trace_add("write", lambda *args: self.on_target_change())
        btn_frame = ttk.Frame(ctrl_group, style="Panel.TFrame")
        btn_frame.pack(fill="x", padx=12, pady=(2, 7))
        self.btn_start = ttk.Button(btn_frame, text="▶  BẮT ĐẦU", style="Action.TButton",
                                    command=self.start_auto)
        self.btn_start.pack(side="left", fill="x", expand=True, padx=4)
        self.btn_stop = ttk.Button(btn_frame, text="■  DỪNG", style="Stop.TButton",
                                   command=self.stop_auto, state="disabled")
        self.btn_stop.pack(side="left", fill="x", expand=True, padx=4)
        self.run_hint = tk.Label(ctrl_group, text="● TRẠNG THÁI: CHƯA VẬN HÀNH",
                                 bg=c["panel"], fg=c["muted"], anchor="w",
                                 font=("Segoe UI", 9, "bold"))
        self.run_hint.pack(fill="x", padx=18, pady=(0, 5))

        status_group = self._ui_card(right_frame, "TIẾN ĐỘ GOM SẢN PHẨM", pady=4)
        counts = ttk.Frame(status_group, style="Panel.TFrame")
        counts.pack(fill="x", padx=12, pady=(5, 7))
        for col in range(2):
            counts.columnconfigure(col, weight=1)
        m8box = ttk.Frame(counts, style="Panel.TFrame")
        m8box.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        m12box = ttk.Frame(counts, style="Panel.TFrame")
        m12box.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        self.lbl_m8_count = ttk.Label(m8box, text=f"Đai ốc M8: 0 / {self.target_count.get()}",
                                      style="Count.TLabel", foreground=c["cyan"])
        self.lbl_m8_count.pack(anchor="w")
        self.progress_m8 = ttk.Progressbar(m8box, style="M8.Horizontal.TProgressbar", maximum=100)
        self.progress_m8.pack(fill="x", pady=(4, 0))
        self.lbl_m12_count = ttk.Label(m12box, text=f"Đai ốc M12: 0 / {self.target_count.get()}",
                                       style="Count.TLabel", foreground=c["amber"])
        self.lbl_m12_count.pack(anchor="w")
        self.progress_m12 = ttk.Progressbar(m12box, style="M12.Horizontal.TProgressbar", maximum=100)
        self.progress_m12.pack(fill="x", pady=(4, 0))
        self.btn_reset_count = ttk.Button(status_group, text="ĐẶT LẠI BỘ ĐẾM",
                                          style="Reset.TButton", command=self.reset_counts)
        self.btn_reset_count.pack(anchor="e", padx=12, pady=(0, 7))

        wh_group = self._ui_card(right_frame, "SƠ ĐỒ KỆ LƯU KHO  |  8 VỊ TRÍ",
                                  fill="both", expand=True, pady=4)
        overview = tk.Frame(wh_group, bg=c["panel"])
        overview.pack(fill="x", padx=10, pady=(5, 2))
        self.wh_summary = tk.Label(overview, text="ĐÃ CHỨA 00/08   •   CÒN TRỐNG 08",
                                   bg=c["panel"], fg=c["text"],
                                   font=("Segoe UI", 10, "bold"))
        self.wh_summary.pack(side="left")
        tk.Label(overview, text="● TRỐNG     ● CÓ HÀNG", bg=c["panel"],
                 fg=c["muted"], font=("Segoe UI", 9)).pack(side="right")

        rack_area = tk.Frame(wh_group, bg=c["panel"])
        rack_area.pack(fill="both", expand=True, padx=9, pady=(2, 7))
        rack_area.columnconfigure(0, weight=1, uniform="rack")
        rack_area.columnconfigure(1, weight=1, uniform="rack")
        rack_area.rowconfigure(1, weight=1)
        self.wh_labels = []
        self.wh_buttons = []
        self.wh_slot_cards = []
        self.wh_slot_indicators = []
        self.wh_slot_icons = []
        for rack, name, accent in ((0, "KỆ A  •  ĐAI ỐC M8", c["cyan"]),
                                   (1, "KỆ B  •  ĐAI ỐC M12", c["amber"])):
            tk.Label(rack_area, text=name, bg=c["panel"], fg=accent,
                     font=("Segoe UI", 10, "bold")).grid(row=0, column=rack, pady=(1, 4))
            rack_box = tk.Frame(rack_area, bg="#D2E2EE", padx=4, pady=4)
            rack_box.grid(row=1, column=rack, sticky="nsew", padx=4)
            for col in range(2):
                rack_box.columnconfigure(col, weight=1, uniform="cell")
            for row in range(2):
                rack_box.rowconfigure(row, weight=1, uniform="cell")
            for local in range(4):
                i = rack * 4 + local
                row, col = divmod(local, 2)
                card = tk.Frame(rack_box, bg=c["panel2"], highlightthickness=1,
                                highlightbackground=c["border"])
                card.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)
                self.wh_slot_cards.append(card)
                # Thiết kế gọn để nút xuất không bị cắt khi màn hình cao 900px.
                header = tk.Frame(card, bg=c["panel2"])
                header.pack(fill="x", padx=7, pady=(3, 0))
                tk.Label(header, text=f"Ô {i+1:02d}", bg=c["panel2"], fg=c["text"],
                         font=("Segoe UI", 10, "bold")).pack(side="left")
                indicator = tk.Label(header, text="○", bg=c["panel2"], fg=c["green"],
                                     font=("Segoe UI", 11, "bold"))
                indicator.pack(side="right")
                self.wh_slot_indicators.append(indicator)
                state_row = tk.Frame(card, bg=c["panel2"])
                state_row.pack(fill="x", padx=7, pady=(0, 2))
                icon = tk.Label(state_row, text="□", bg=c["panel2"], fg=c["muted"],
                                font=("Segoe UI", 11, "bold"))
                icon.pack(side="left", padx=(0, 5))
                self.wh_slot_icons.append(icon)
                lbl = tk.Label(state_row, text="TRỐNG", bg=c["panel2"], fg=c["green"],
                               font=("Segoe UI", 9, "bold"))
                lbl.pack(side="left")
                self.wh_labels.append(lbl)
                btn_exp = tk.Button(card, text="XUẤT HỘP", bg="#D8E9F7", fg=c["text"],
                                    activebackground="#B9D8EF", activeforeground=c["text"],
                                    relief="flat", bd=0, cursor="hand2",
                                    font=("Segoe UI", 9, "bold"), pady=2,
                                    command=lambda idx=i: self.send_cmd(f"EXPORT_{idx}"))
                btn_exp.pack(fill="x", padx=6, pady=(0, 4))
                self.wh_buttons.append(btn_exp)
        self.update_warehouse_visual()

    def update_count_visual(self):
        try:
            target = max(1, int(self.target_count.get()))
            self.progress_m8["value"] = min(100, self.count_m8 * 100 / target)
            self.progress_m12["value"] = min(100, self.count_m12 * 100 / target)
        except (ValueError, tk.TclError):
            pass

    def update_warehouse_visual(self):
        """Cập nhật phần hiển thị; không thay đổi trạng thái và lệnh điều khiển."""
        c = self.ui
        occupied = sum(bool(v) for v in self.warehouse_status)
        self.wh_summary.config(text=f"ĐÃ CHỨA {occupied:02d}/08   •   CÒN TRỐNG {8-occupied:02d}")
        for i, filled in enumerate(self.warehouse_status):
            self.wh_labels[i].config(text="CÓ HÀNG" if filled else "TRỐNG",
                                     fg=c["amber"] if filled else c["green"])
            self.wh_slot_indicators[i].config(text="●" if filled else "○",
                                               fg=c["amber"] if filled else c["green"])
            self.wh_slot_icons[i].config(text="■" if filled else "□",
                                         fg=c["amber"] if filled else c["muted"])
            self.wh_slot_cards[i].config(
                highlightbackground=c["amber"] if filled else c["border"])

    def on_target_change(self):
        """Cập nhật lại giao diện nhãn hiển thị khi số lượng đai ốc mong muốn thay đổi"""
        try:
            target = self.target_count.get()
            self.lbl_m8_count.config(text=f"Đai ốc M8: {self.count_m8} / {target}")
            self.lbl_m12_count.config(text=f"Đai ốc M12: {self.count_m12} / {target}")
            self.update_count_visual()
        except Exception:
            pass

    def setup_tab_manual(self):
        c = self.ui
        container = ttk.Frame(self.tab_manual)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        pulse_frame = self._ui_card(container, "VỊ TRÍ TRỤC HIỆN TẠI  |  STEP")
        for axis in ("X", "Y", "Z"):
            box = ttk.Frame(pulse_frame, style="Panel.TFrame")
            box.pack(side="left", fill="x", expand=True, padx=20, pady=18)
            ttk.Label(box, text="TRỤC " + axis, style="Muted.TLabel",
                      font=("Segoe UI", 11, "bold")).pack(anchor="center")
            lbl = ttk.Label(box, text=f"Trục {axis}: 0", style="Position.TLabel")
            lbl.pack(anchor="center", pady=6)
            setattr(self, "lbl_pulse_" + axis.lower(), lbl)

        home_frame = self._ui_card(container, "THIẾT LẬP VỊ TRÍ GỐC  |  HOME")
        for text, cmd in (("HOME Z", "HOME_Z"), ("HOME X", "HOME_X"),
                          ("HOME Y", "HOME_Y"), ("HOME TẤT CẢ", "HOME_ALL")):
            ttk.Button(home_frame, text=text, style="Primary.TButton",
                       command=lambda value=cmd: self.send_cmd(value)).pack(
                           side="left", fill="x", expand=True, padx=9, pady=18)

        cyl_frame = self._ui_card(container, "KIỂM TRA XI LANH & LƯU KHO")
        for title, cmd in (("XI LANH M8", "CYL_M8"), ("XI LANH M12", "CYL_M12"),
                           ("CẤT M8 (Ô 1–4)", "STORE_M8"),
                           ("CẤT M12 (Ô 5–8)", "STORE_M12")):
            ttk.Button(cyl_frame, text=title,
                       command=lambda value=cmd: self.send_cmd(value)).pack(
                           side="left", fill="x", expand=True, padx=9, pady=18)

        jog_frame = self._ui_card(container, "ĐIỀU KHIỂN JOG  |  GIỮ NÚT ĐỂ CHẠY – NHẢ ĐỂ DỪNG",
                                  fill="both", expand=True)
        grid_f = ttk.Frame(jog_frame, style="Panel.TFrame")
        grid_f.pack(expand=True, pady=12)
        for row, axis in enumerate(("X", "Y", "Z")):
            ttk.Label(grid_f, text="TRỤC " + axis, style="Accent.TLabel").grid(
                row=row, column=0, padx=28, pady=15)
            btn_neg = ttk.Button(grid_f, text=axis + "  −", width=17)
            btn_neg.grid(row=row, column=1, padx=18, pady=10)
            btn_neg.bind("<ButtonPress-1>", lambda e, a=axis: self.start_jog(a, "-"))
            btn_neg.bind("<ButtonRelease-1>", lambda e: self.stop_jog())
            btn_pos = ttk.Button(grid_f, text=axis + "  +", width=17)
            btn_pos.grid(row=row, column=2, padx=18, pady=10)
            btn_pos.bind("<ButtonPress-1>", lambda e, a=axis: self.start_jog(a, "+"))
            btn_pos.bind("<ButtonRelease-1>", lambda e: self.stop_jog())

    def start_jog(self, axis, direction):
        self.send_cmd(f"START_JOG_{axis}_{direction}")

    def stop_jog(self):
        self.send_cmd("STOP_JOG")

    def reset_counts(self):
        self.count_m8 = 0
        self.count_m12 = 0
        target = self.target_count.get() if self.target_count.get() > 0 else 1
        self.lbl_m8_count.config(text=f"Đai ốc M8: 0 / {target}")
        self.lbl_m12_count.config(text=f"Đai ốc M12: 0 / {target}")
        self.update_count_visual()

    def start_auto(self):
        self.is_auto_running = True
        self.object_detected_in_current_pass = False
        self.btn_start.config(state='disabled')
        self.btn_stop.config(state='normal')
        self.send_cmd("RESUME")

    def stop_auto(self):
        self.is_auto_running = False
        self.btn_start.config(state='normal')
        self.btn_stop.config(state='disabled')
        self.send_cmd("STOP")

    # ==============================================================================
    # HÀM XỬ LÝ ẢNH & THUẬT TOÁN NHẬN DIỆN (ĐÃ TỐI ƯU OTSU VÀ BÁN KÍNH)
    # ==============================================================================
    def calculate_solidity(self, cnt, area):
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        if hull_area == 0:
            return 0
        return float(area) / hull_area

    def is_fully_inside_frame(self, box_points, w_frame, h_frame, margin=MARGIN_BORDER):
        for pt in box_points:
            px, py = pt[0], pt[1]
            if px < margin or px > (w_frame - margin) or py < margin or py > (h_frame - margin):
                return False
        return True

    def classify_nut(self, radius, aspect_ratio, solidity):
        if aspect_ratio > MAX_ASPECT_RATIO or solidity < MIN_SOLIDITY:
            return "LOI", (0, 0, 255)

        if R_M8_MIN <= radius <= R_M8_MAX:
            return "M8", (0, 255, 0)
        elif R_M12_MIN <= radius <= R_M12_MAX:
            return "M12", (0, 255, 255)
        else:
            return "LOI", (0, 0, 255)

    def process_detection_logic(self, frame):
        h_frame, w_frame = frame.shape[:2]

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        # Sử dụng Otsu Threshold tự thích ứng ánh sáng môi trường
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        kernel = np.ones((5, 5), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detected_label = None
        target_box = None
        is_any_obj_present = False

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < MIN_AREA:
                continue

            rect = cv2.minAreaRect(cnt)
            (center_x, center_y), (w, h), angle = rect

            if w == 0 or h == 0:
                continue

            long_side = max(w, h)
            short_side = min(w, h)

            if long_side > MAX_DIAMETER_PX:
                continue

            box = cv2.boxPoints(rect)
            box = np.int32(box)

            if not self.is_fully_inside_frame(box, w_frame, h_frame, margin=MARGIN_BORDER):
                continue

            is_any_obj_present = True

            solidity = self.calculate_solidity(cnt, area)
            aspect_ratio = long_side / float(short_side)
            diameter_px = long_side
            radius = diameter_px / 2.0

            label, color = self.classify_nut(radius, aspect_ratio, solidity)

            cv2.drawContours(frame, [box], 0, color, 3)
            diameter_mm = diameter_px * PIXEL_TO_MM
            top_left_x = int(min(box[:, 0]))
            top_left_y = int(min(box[:, 1]))

            text_line1 = f"{label}"
            text_line2 = f"OD: {diameter_mm:.1f}mm ({int(diameter_px)}px)"

            cv2.putText(frame, text_line1, (top_left_x, max(top_left_y - 20, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.putText(frame, text_line2, (top_left_x, max(top_left_y - 5, 35)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            if label in ['M8', 'M12']:
                detected_label = label
                target_box = box
                break

        return detected_label, target_box, is_any_obj_present

    def update_camera(self):
        if not self.is_running:
            return

        ret, frame = self.cap.read()
        if ret:
            current_time = time.time()

            if self.is_auto_running and current_time < self.freeze_until and self.frozen_frame is not None:
                display_frame = self.frozen_frame
            else:
                if self.is_auto_running:
                    detected_type, nut_box, is_any_obj_present = self.process_detection_logic(frame)

                    if not is_any_obj_present:
                        self.object_detected_in_current_pass = False

                    elif detected_type in ['M8', 'M12'] and not self.object_detected_in_current_pass:
                        self.object_detected_in_current_pass = True
                        self.frozen_frame = frame.copy()
                        self.freeze_until = current_time + 1.2
                        self.process_detection(detected_type)

                display_frame = frame

            lbl_w = self.lbl_cam.winfo_width()
            lbl_h = self.lbl_cam.winfo_height()

            if lbl_w > 50 and lbl_h > 50:
                src_h, src_w = display_frame.shape[:2]
                scale = min(lbl_w / src_w, lbl_h / src_h)
                resized_frame = cv2.resize(
                    display_frame, (max(1, int(src_w * scale)), max(1, int(src_h * scale))))
            else:
                resized_frame = cv2.resize(display_frame, (800, 500))

            img = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img)
            img_tk = ImageTk.PhotoImage(image=img_pil)
            self.lbl_cam.img_tk = img_tk
            self.lbl_cam.config(image=img_tk)

        self.root.after(30, self.update_camera)

    def process_detection(self, nut_type):
        """Xử lý phân chuỗi thời gian chính xác, lấy định mức linh hoạt từ giao diện"""
        if not self.is_auto_running:
            return

        try:
            target_limit = self.target_count.get()
            if target_limit <= 0:
                target_limit = 1
        except Exception:
            target_limit = 5

        if nut_type == 'M8':
            self.count_m8 += 1
            is_full = (self.count_m8 >= target_limit)
            if is_full:
                self.count_m8 = 0

            self.lbl_m8_count.config(text=f"Đai ốc M8: {self.count_m8} / {target_limit}")
            self.update_count_visual()
            threading.Thread(target=self.sequence_trigger, args=(DELAY_M8, "CYL_M8", is_full, "STORE_M8"),
                             daemon=True).start()

        elif nut_type == 'M12':
            self.count_m12 += 1
            is_full = (self.count_m12 >= target_limit)
            if is_full:
                self.count_m12 = 0

            self.lbl_m12_count.config(text=f"Đai ốc M12: {self.count_m12} / {target_limit}")
            self.update_count_visual()
            threading.Thread(target=self.sequence_trigger, args=(DELAY_M12, "CYL_M12", is_full, "STORE_M12"),
                             daemon=True).start()

    def sequence_trigger(self, delay_sec, cyl_cmd, is_full, store_cmd):
        """Kích hoạt chuỗi tuần tự chuẩn xác"""
        time.sleep(delay_sec)
        if self.is_auto_running:
            self.send_cmd(cyl_cmd)
            if is_full:
                time.sleep(2.0)  # Chờ 2s để xi lanh đẩy hoàn tất mới gửi lệnh cất kho
                if self.is_auto_running:
                    self.send_cmd(store_cmd)

    # ==============================================================================
    # ĐỌC VÀ PHÂN TÍCH PHẢN HỒI TỪ SERIAL
    # ==============================================================================
    def read_serial_loop(self):
        while self.is_running:
            if self.ser and self.ser.is_open:
                try:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.root.after(0, self.parse_serial_line, line)
                except Exception:
                    pass
            time.sleep(0.01)

    def parse_serial_line(self, line):
        if line.startswith("P:"):
            parts = line[2:].split(',')
            if len(parts) == 3:
                self.lbl_pulse_x.config(text=f"Trục X: {parts[0]}")
                self.lbl_pulse_y.config(text=f"Trục Y: {parts[1]}")
                self.lbl_pulse_z.config(text=f"Trục Z: {parts[2]}")

        elif line.startswith("STORE_DONE:"):
            try:
                slot_idx = int(line.split(':')[1])
                if 0 <= slot_idx < 8:
                    self.warehouse_status[slot_idx] = True
                    self.update_warehouse_visual()
            except ValueError:
                pass

        elif line.startswith("EXPORT_DONE:"):
            try:
                slot_idx = int(line.split(':')[1])
                if 0 <= slot_idx < 8:
                    self.warehouse_status[slot_idx] = False
                    self.update_warehouse_visual()
            except ValueError:
                pass

    def on_closing(self):
        self.is_running = False
        self.is_auto_running = False
        if self.cap.isOpened():
            self.cap.release()
        if self.ser and self.ser.is_open:
            with self.serial_lock:
                self.ser.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SortingApp(root)
    root.mainloop()