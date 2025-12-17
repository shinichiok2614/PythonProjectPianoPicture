import os
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont
import math

CANVAS_WIDTH = 640
CANVAS_HEIGHT = 480

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

        self.number_color = (255, 0, 0)
        self.circle_radius = tk.IntVar(value=18)
        self.font_size = tk.IntVar(value=20)

        # marker: x, y, number, color, radius, font_size
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

        tk.Label(left, text="Số sẽ in").pack(pady=(5, 0))
        self.number_var = tk.StringVar(value="1")
        tk.Entry(left, textvariable=self.number_var, state="readonly", justify="center").pack(fill=tk.X)

        tk.Button(left, text="Chọn màu số", command=self.choose_color).pack(fill=tk.X, pady=3)

        tk.Label(left, text="Bán kính vòng tròn").pack()
        tk.Spinbox(left, from_=5, to=100, textvariable=self.circle_radius).pack(fill=tk.X)

        tk.Label(left, text="Cỡ chữ").pack()
        tk.Spinbox(left, from_=8, to=100, textvariable=self.font_size).pack(fill=tk.X)

        self.pause_btn = tk.Button(left, text="Ngừng tăng", command=self.toggle_pause)
        self.pause_btn.pack(fill=tk.X, pady=5)

        tk.Button(left, text="Lưu ảnh", command=self.save_image).pack(fill=tk.X, pady=10)

        self.canvas = tk.Canvas(right, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="gray")
        self.canvas.pack(expand=True)
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)

    # ================= Load =================
    def load_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.folder_path = folder
        self.image_list = sorted(
            f for f in os.listdir(folder)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        )
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

        for x, y, num, color, r, fs in self.markers:
            cx = x / self.scale_x
            cy = y / self.scale_y

            draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=color, width=3)

            font = self.get_font(fs)
            bbox = draw.textbbox((0, 0), str(num), font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text((cx - tw/2, cy - th/2), str(num), fill=color, font=font)

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
            self.number_color,
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
            mx, my, _, _, r, _ = self.markers[i]
            if math.hypot(mx - x, my - y) <= r:
                self.markers.pop(i)
                self.show_image()
                return

    # ================= Utils =================
    def toggle_pause(self):
        self.pause_increase = not self.pause_increase
        if self.pause_increase:
            self.pause_btn.config(text="Đang ngừng", relief=tk.SUNKEN)
        else:
            self.pause_btn.config(text="Ngừng tăng", relief=tk.RAISED)

    def update_number_display(self):
        self.number_var.set(str(self.current_number))

    def choose_color(self):
        c = colorchooser.askcolor()[0]
        if c:
            self.number_color = tuple(map(int, c))

    def get_font(self, size):
        try:
            return ImageFont.truetype("arial.ttf", size)
        except:
            return ImageFont.load_default()

    # ================= Save =================
    def save_image(self):
        img = self.image_pil.copy()
        draw = ImageDraw.Draw(img)

        for x, y, num, color, r, fs in self.markers:
            font = self.get_font(fs)
            draw.ellipse((x-r, y-r, x+r, y+r), outline=color, width=3)

            bbox = draw.textbbox((0, 0), str(num), font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text((x - tw/2, y - th/2), str(num), fill=color, font=font)

        path = os.path.join(self.folder_path, self.image_list[self.current_image_index])
        img.save(path)
        messagebox.showinfo("Done", "Đã lưu ảnh ghi đè!")

# ================= Run =================
root = tk.Tk()
app = ImageNumberMarker(root)
root.mainloop()
