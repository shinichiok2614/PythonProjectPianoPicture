import os
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

# ===================== DEFAULT CONFIG =====================
CANVAS_WIDTH = 640
CANVAS_HEIGHT = 480

DEFAULT_NUM_CYCLES = 7

DEFAULT_START_X = 48    # ví dụ: 100
DEFAULT_END_X   = 1256    # ví dụ: 1200

WHITE_KEYS = ['C', 'D', 'E', 'F', 'G', 'A', 'B']

COLOR_RED = (0, 0, 255)
COLOR_WHITE = (255, 255, 255)

THICKNESS_C = 3
THICKNESS_OTHER = 2
THICKNESS_END = 3

WINDOW_TITLE = "Piano White Keys Drawer"

# 🔹 FOLDER MẶC ĐỊNH (SỬA ĐƯỜNG DẪN NÀY)
DEFAULT_FOLDER = r"C:\Users\PC\AppData\Roaming\KMP\Capture"
# ==========================================================


class PianoLineDrawerWhite:
    def __init__(self, master):
        self.master = master
        self.master.title(WINDOW_TITLE)

        self.folder_path = None
        self.image_list = []
        self.current_image_cv = None
        self.current_image_preview = None
        self.current_image_tk = None

        # ===== start / end mặc định =====
        self.start_x = DEFAULT_START_X
        self.end_x = DEFAULT_END_X

        self.num_cycles = tk.IntVar(value=DEFAULT_NUM_CYCLES)

        # ================= GUI layout =================
        self.left_frame = tk.Frame(master)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Button(self.left_frame, text="Chọn folder", command=self.load_folder).pack(pady=5)

        self.listbox = tk.Listbox(self.left_frame, width=30, exportselection=False)
        self.listbox.pack(fill=tk.Y, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select_image)

        tk.Label(self.left_frame, text="Số chu kỳ:").pack(pady=5)
        tk.Entry(self.left_frame, textvariable=self.num_cycles, width=5).pack()

        tk.Button(self.left_frame, text="Chọn điểm bắt đầu", command=self.set_start_point).pack(pady=5)
        tk.Button(self.left_frame, text="Chọn điểm kết thúc", command=self.set_end_point).pack(pady=5)
        tk.Button(self.left_frame, text="Preview", command=self.preview_lines).pack(pady=5)
        tk.Button(self.left_frame, text="Lưu ảnh", command=self.save_image).pack(pady=5)

        self.canvas = tk.Canvas(self.right_frame, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
        self.canvas.pack(expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        self.setting_point = None  # "start" hoặc "end"

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

    # ================= Select image =================
    def on_select_image(self, event):
        if not self.listbox.curselection():
            return
        index = self.listbox.curselection()[0]
        img_path = os.path.join(self.folder_path, self.image_list[index])
        self.current_image_cv = cv2.imread(img_path)
        self.show_image(self.current_image_cv)

    # ================= Show image =================
    def show_image(self, img_cv):
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_pil.thumbnail((CANVAS_WIDTH, CANVAS_HEIGHT))
        self.current_image_tk = ImageTk.PhotoImage(img_pil)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image_tk)

    # ================= Canvas click =================
    def on_canvas_click(self, event):
        if self.setting_point is None or self.current_image_cv is None:
            return

        scale_x = self.current_image_cv.shape[1] / CANVAS_WIDTH
        x = int(event.x * scale_x)

        if self.setting_point == "start":
            self.start_x = x
            msg = "bắt đầu"
        else:
            self.end_x = x
            msg = "kết thúc"

        self.setting_point = None
        messagebox.showinfo("OK", f"Đã đặt điểm {msg} tại x = {x}")

    def set_start_point(self):
        self.setting_point = "start"

    def set_end_point(self):
        self.setting_point = "end"

    # ================= Preview =================
    def preview_lines(self):
        if self.current_image_cv is None:
            messagebox.showwarning("Warning", "Chưa chọn ảnh!")
            return
        if self.start_x is None or self.end_x is None:
            messagebox.showwarning("Warning", "Chưa có start / end!")
            return

        img = self.current_image_cv.copy()
        num_cycles = self.num_cycles.get()

        total_width = self.end_x - self.start_x
        cycle_width = total_width / num_cycles

        for i in range(num_cycles):
            cycle_start = int(self.start_x + i * cycle_width)
            cycle_end = int(cycle_start + cycle_width)

            key_width = cycle_width / len(WHITE_KEYS)

            for k, key in enumerate(WHITE_KEYS):
                x = int(cycle_start + k * key_width)

                if key == 'C':
                    color = COLOR_RED
                    thickness = THICKNESS_C
                else:
                    color = COLOR_WHITE
                    thickness = THICKNESS_OTHER

                cv2.line(img, (x, 0), (x, img.shape[0]), color, thickness)

            cv2.line(
                img,
                (cycle_end, 0),
                (cycle_end, img.shape[0]),
                COLOR_RED,
                THICKNESS_END
            )

        self.current_image_preview = img
        self.show_image(img)

    # ================= Save =================
    def save_image(self):
        if self.current_image_preview is None:
            self.preview_lines()

        if self.current_image_cv is not None and self.listbox.curselection():
            original_name = self.image_list[self.listbox.curselection()[0]]
            save_path = os.path.join(self.folder_path, original_name)
            cv2.imwrite(save_path, self.current_image_preview)
            messagebox.showinfo("Done", f"Ảnh đã lưu và ghi đè:\n{save_path}")


root = tk.Tk()
app = PianoLineDrawerWhite(root)
root.mainloop()
