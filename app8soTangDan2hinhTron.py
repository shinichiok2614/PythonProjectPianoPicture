import os
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont
import math

CANVAS_WIDTH = 640
CANVAS_HEIGHT = 480

# 🔹 FOLDER MẶC ĐỊNH (SỬA ĐƯỜNG DẪN NÀY)
DEFAULT_FOLDER = r"C:\Users\PC\AppData\Roaming\KMP\Capture"
class ImageNumberMarker:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Number Marker")

        self.folder_path = None
        self.image_list = []
        self.current_image_index = None

        self.image_pil = None
        self.image_tk = None

        self.current_number = 1
        self.pause_increase = False

        # ===== Colors =====
        self.circle_color = (255, 255, 0)  # nền hình tròn
        self.text_color = (255, 0, 0)      # màu chữ

        self.circle_radius = tk.IntVar(value=16)
        self.font_size = tk.IntVar(value=20)

        # marker: x, y, number, circle_color, text_color, radius, font_size
        self.markers = []

        self.scale_x = 1
        self.scale_y = 1

        self.build_ui()

    # ================= UI =================
    def build_ui(self):
        left = tk.Frame(self.master)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        right = tk.Frame(self.master)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Button(left, text="Chọn folder", command=self.load_folder).pack(fill=tk.X, pady=3)

        self.listbox = tk.Listbox(left, width=30)
        self.listbox.pack(fill=tk.Y, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select_image)

        tk.Label(left, text="Số sẽ in").pack(pady=(6, 0))
        self.number_var = tk.StringVar(value="1")
        tk.Entry(left, textvariable=self.number_var,
                 state="readonly", justify="center").pack(fill=tk.X)

        num_btns = tk.Frame(left)
        num_btns.pack(fill=tk.X, pady=2)
        tk.Button(num_btns, text="−", command=self.decrease_number).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(num_btns, text="+", command=self.increase_number).pack(side=tk.LEFT, expand=True, fill=tk.X)

        tk.Button(left, text="Chọn màu hình tròn", command=self.choose_circle_color).pack(fill=tk.X, pady=3)
        tk.Button(left, text="Chọn màu chữ", command=self.choose_text_color).pack(fill=tk.X, pady=3)

        tk.Label(left, text="Bán kính hình tròn").pack()
        tk.Spinbox(left, from_=5, to=200, textvariable=self.circle_radius).pack(fill=tk.X)

        tk.Label(left, text="Cỡ chữ").pack()
        tk.Spinbox(left, from_=8, to=200, textvariable=self.font_size).pack(fill=tk.X)

        self.pause_btn = tk.Button(left, text="Ngừng tăng", command=self.toggle_pause)
        self.pause_btn.pack(fill=tk.X, pady=5)

        tk.Button(left, text="Lưu ảnh", command=self.save_image).pack(fill=tk.X, pady=10)

        self.canvas = tk.Canvas(right, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="gray")
        self.canvas.pack(expand=True)
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)

        # 🔹 TỰ ĐỘNG LOAD FOLDER MẶC ĐỊNH
        self.load_default_folder()

    # ================= Load default folder =================
    def load_default_folder(self):
        if os.path.isdir(DEFAULT_FOLDER):
            self.load_folder(DEFAULT_FOLDER)

    # ================= Load folder =================
    def load_folder(self, folder=None):
        if folder is None:
            folder = filedialog.askdirectory(title="Chọn folder chứa ảnh")
            if not folder:
                return

        self.folder_path = folder
        self.image_list = sorted([
            f for f in os.listdir(folder)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])

        self.listbox.delete(0, tk.END)
        for img in self.image_list:
            self.listbox.insert(tk.END, img)
    def on_select_image(self, event):
        if not self.listbox.curselection():
            return

        idx = self.listbox.curselection()[0]
        self.current_image_index = idx

        path = os.path.join(self.folder_path, self.image_list[idx])
        img_cv = cv2.imread(path)
        self.image_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))

        self.markers.clear()
        self.current_number = 1
        self.update_number_display()
        self.show_image()

    # ================= Render =================
    def show_image(self):
        img = self.image_pil.copy()
        img.thumbnail((CANVAS_WIDTH, CANVAS_HEIGHT))

        self.scale_x = self.image_pil.width / img.width
        self.scale_y = self.image_pil.height / img.height

        draw = ImageDraw.Draw(img)

        for x, y, num, c_color, t_color, r, fs in self.markers:
            cx = x / self.scale_x
            cy = y / self.scale_y

            sr = r / self.scale_x
            sfs = max(1, int(fs / self.scale_x))

            # Hình tròn TÔ
            draw.ellipse(
                (cx - sr, cy - sr, cx + sr, cy + sr),
                fill=c_color
            )

            # Chữ
            font = self.get_font(sfs)
            bbox = draw.textbbox((0, 0), str(num), font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]

            draw.text(
                (cx - tw / 2, cy - th / 2),
                str(num),
                fill=t_color,
                font=font
            )

        self.image_tk = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk)

    # ================= Click =================
    def on_left_click(self, event):
        if not self.image_pil:
            return

        x = int(event.x * self.scale_x)
        y = int(event.y * self.scale_y)

        self.markers.append((
            x, y,
            self.current_number,
            self.circle_color,
            self.text_color,
            self.circle_radius.get(),
            self.font_size.get()
        ))

        if not self.pause_increase:
            self.current_number += 1
            self.update_number_display()

        self.show_image()

    def on_right_click(self, event):
        if not self.markers:
            return

        x = int(event.x * self.scale_x)
        y = int(event.y * self.scale_y)

        for i in reversed(range(len(self.markers))):
            mx, my, _, _, _, r, _ = self.markers[i]
            if math.hypot(mx - x, my - y) <= r:
                self.markers.pop(i)
                self.show_image()
                return

    # ================= Number =================
    def increase_number(self):
        self.current_number += 1
        self.update_number_display()

    def decrease_number(self):
        if self.current_number > 1:
            self.current_number -= 1
            self.update_number_display()

    def update_number_display(self):
        self.number_var.set(str(self.current_number))

    # ================= Utils =================
    def toggle_pause(self):
        self.pause_increase = not self.pause_increase
        self.pause_btn.config(
            text="Đang ngừng" if self.pause_increase else "Ngừng tăng",
            relief=tk.SUNKEN if self.pause_increase else tk.RAISED
        )

    def choose_circle_color(self):
        c = colorchooser.askcolor()[0]
        if c:
            self.circle_color = tuple(map(int, c))

    def choose_text_color(self):
        c = colorchooser.askcolor()[0]
        if c:
            self.text_color = tuple(map(int, c))

    def get_font(self, size):
        try:
            return ImageFont.truetype("arial.ttf", size)
        except:
            return ImageFont.load_default()

    # ================= Save =================
    def save_image(self):
        img = self.image_pil.copy()
        draw = ImageDraw.Draw(img)

        for x, y, num, c_color, t_color, r, fs in self.markers:
            font = self.get_font(fs)

            draw.ellipse(
                (x - r, y - r, x + r, y + r),
                fill=c_color
            )

            bbox = draw.textbbox((0, 0), str(num), font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]

            draw.text(
                (x - tw / 2, y - th / 2),
                str(num),
                fill=t_color,
                font=font
            )

        path = os.path.join(self.folder_path, self.image_list[self.current_image_index])
        img.save(path)
        messagebox.showinfo("Done", "Đã lưu ảnh ghi đè!")


# ================= Run =================
root = tk.Tk()
app = ImageNumberMarker(root)
root.mainloop()
