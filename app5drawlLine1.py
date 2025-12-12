import os
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

CANVAS_WIDTH = 640
CANVAS_HEIGHT = 480

class PianoLineDrawerWhite:
    def __init__(self, master):
        self.master = master
        self.master.title("Piano White Keys Drawer")

        self.folder_path = None
        self.image_list = []
        self.current_image_cv = None
        self.current_image_preview = None
        self.current_image_tk = None

        self.start_x = None
        self.end_x = None
        self.num_cycles = tk.IntVar(value=1)

        # GUI layout
        self.left_frame = tk.Frame(master)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Button(self.left_frame, text="Chọn folder", command=self.load_folder).pack(pady=5)
        self.listbox = tk.Listbox(self.left_frame)
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

    # ================= Load folder =================
    def load_folder(self):
        folder = filedialog.askdirectory(title="Chọn folder chứa ảnh")
        if not folder:
            return
        self.folder_path = folder
        self.image_list = sorted([f for f in os.listdir(folder) if f.lower().endswith(('.png','.jpg','.jpeg'))])
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
        if self.setting_point is None:
            return
        # Scale click lên ảnh gốc
        scale_x = self.current_image_cv.shape[1] / CANVAS_WIDTH
        x = int(event.x * scale_x)
        if self.setting_point == "start":
            self.start_x = x
        elif self.setting_point == "end":
            self.end_x = x
        self.setting_point = None
        messagebox.showinfo("OK", f"Đã đặt điểm {('bắt đầu' if self.start_x == x else 'kết thúc')} tại x={x}")

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
            messagebox.showwarning("Warning", "Chưa chọn điểm bắt đầu/kết thúc!")
            return

        img = self.current_image_cv.copy()
        num_cycles = self.num_cycles.get()
        total_width = self.end_x - self.start_x
        cycle_width = total_width / num_cycles
        white_keys = ['C','D','E','F','G','A','B']

        for i in range(num_cycles):
            cycle_start = int(self.start_x + i * cycle_width)
            cycle_end = int(cycle_start + cycle_width)
            key_width = cycle_width / len(white_keys)
            for k, key in enumerate(white_keys):
                x = int(cycle_start + k * key_width)
                # Vẽ cạnh trái C đỏ, phím B cạnh trái trắng
                if key == 'C':
                    color = (0, 0, 255)  # đỏ
                    thickness = 3
                elif key == 'B':
                    color = (255, 255, 255)  # trắng
                    thickness = 2
                else:
                    color = (255, 255, 255)  # trắng
                    thickness = 2
                cv2.line(img, (x, 0), (x, img.shape[0]), color, thickness)

            # Vẽ cạnh phải của phím cuối B
            cv2.line(img, (cycle_end,0), (cycle_end,img.shape[0]), (0,0,255), 3)

        self.current_image_preview = img
        self.show_image(img)

    # ================= Save =================
    def save_image(self):
        if self.current_image_preview is None:
            self.preview_lines()
        # Ghi đè lên cùng tên ảnh gốc
        if self.current_image_cv is not None:
            # Lấy tên ảnh gốc
            original_name = self.image_list[self.listbox.curselection()[0]]
            save_path = os.path.join(self.folder_path, original_name)
            cv2.imwrite(save_path, self.current_image_preview)
            messagebox.showinfo("Done", f"Ảnh đã lưu và ghi đè: {save_path}")


root = tk.Tk()
app = PianoLineDrawerWhite(root)
root.mainloop()
