import os
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont

CANVAS_WIDTH = 640
CANVAS_HEIGHT = 480
CIRCLE_RADIUS = 10

class ImageNumberMarker:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Number Marker")

        # Data
        self.folder_path = None
        self.image_list = []
        self.current_image_index = None
        self.image_cv = None
        self.image_pil = None
        self.image_tk = None

        # Numbering
        self.current_number = 1
        self.pause_increase = False
        self.number_color = (255, 0, 0)  # đỏ
        self.markers = []  # (x, y, number, color)

        self.scale_x = 1
        self.scale_y = 1

        # GUI
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

        tk.Button(left, text="Chọn màu số", command=self.choose_color).pack(fill=tk.X, pady=3)

        self.pause_btn = tk.Button(left, text="Ngừng tăng", relief=tk.RAISED, command=self.toggle_pause)
        self.pause_btn.pack(fill=tk.X, pady=3)

        tk.Button(left, text="Lưu ảnh", command=self.save_image).pack(fill=tk.X, pady=10)

        self.canvas = tk.Canvas(right, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="gray")
        self.canvas.pack(expand=True)
        self.canvas.bind("<Button-1>", self.on_click)

    # ================= Load folder =================
    def load_folder(self):
        folder = filedialog.askdirectory()
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
        idx = self.listbox.curselection()[0]
        self.current_image_index = idx

        path = os.path.join(self.folder_path, self.image_list[idx])
        self.image_cv = cv2.imread(path)
        self.image_pil = Image.fromarray(cv2.cvtColor(self.image_cv, cv2.COLOR_BGR2RGB))

        self.markers.clear()
        self.current_number = 1
        self.show_image()

    # ================= Show image =================
    def show_image(self):
        img = self.image_pil.copy()
        img.thumbnail((CANVAS_WIDTH, CANVAS_HEIGHT))

        self.scale_x = self.image_pil.width / img.width
        self.scale_y = self.image_pil.height / img.height

        draw = ImageDraw.Draw(img)

        for x, y, num, color in self.markers:
            cx = x / self.scale_x
            cy = y / self.scale_y
            r = CIRCLE_RADIUS
            draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=color, width=3)
            draw.text((cx-6, cy-9), str(num), fill=color)

        self.image_tk = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk)

    # ================= Click =================
    def on_click(self, event):
        if self.image_pil is None:
            return

        x = int(event.x * self.scale_x)
        y = int(event.y * self.scale_y)

        number = self.current_number
        self.markers.append((x, y, number, self.number_color))

        if not self.pause_increase:
            self.current_number += 1

        self.show_image()

    # ================= Toggle pause =================
    def toggle_pause(self):
        self.pause_increase = not self.pause_increase
        if self.pause_increase:
            self.pause_btn.config(relief=tk.SUNKEN, text="Đang ngừng")
        else:
            self.pause_btn.config(relief=tk.RAISED, text="Ngừng tăng")

    # ================= Choose color =================
    def choose_color(self):
        color = colorchooser.askcolor()[0]
        if color:
            self.number_color = tuple(map(int, color))

    # ================= Save =================
    def save_image(self):
        if self.image_pil is None:
            return

        img = self.image_pil.copy()
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()

        for x, y, num, color in self.markers:
            r = CIRCLE_RADIUS
            draw.ellipse((x-r, y-r, x+r, y+r), outline=color, width=3)
            draw.text((x-6, y-9), str(num), fill=color, font=font)

        path = os.path.join(self.folder_path, self.image_list[self.current_image_index])
        img.save(path)

        messagebox.showinfo("Done", "Ảnh đã được lưu ghi đè!")

# ================= Run =================
root = tk.Tk()
app = ImageNumberMarker(root)
root.mainloop()
