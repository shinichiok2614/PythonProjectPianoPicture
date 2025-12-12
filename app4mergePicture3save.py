import os
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

CANVAS_WIDTH = 640
CANVAS_HEIGHT = 480

class VerticalMergeAppOrdered:
    def __init__(self, master):
        self.master = master
        self.master.title("Vertical Merge with Ordered Naming")

        self.folder_path = None
        self.image_list = []
        self.selected_indices = []
        self.current_image_cv = None
        self.current_image_tk = None
        self.preview_image = None

        # GUI layout
        self.left_frame = tk.Frame(master)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Button(self.left_frame, text="Chọn folder", command=self.load_folder).pack(pady=5)
        self.listbox = tk.Listbox(self.left_frame, selectmode=tk.MULTIPLE)
        self.listbox.pack(fill=tk.Y, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select_image)

        self.canvas = tk.Canvas(self.right_frame, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
        self.canvas.pack(expand=True)

        tk.Button(self.right_frame, text="Preview Ghép", command=self.preview_merge).pack(pady=5)
        tk.Button(self.right_frame, text="Ghép ảnh & Lưu", command=self.merge_images).pack(pady=5)

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
        self.selected_indices = list(self.listbox.curselection())
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
        self.canvas.create_image(0,0, anchor=tk.NW, image=self.current_image_tk)

    # ================= Merge preview =================
    def preview_merge(self):
        if not self.selected_indices:
            messagebox.showwarning("Warning", "Chưa chọn ảnh!")
            return
        images = [cv2.imread(os.path.join(self.folder_path, self.image_list[idx]))
                  for idx in self.selected_indices]

        # Ghép theo chiều dọc, ảnh chọn trước nằm dưới
        merged = images[-1]
        for img in reversed(images[:-1]):
            h1, w1 = merged.shape[:2]
            h2, w2 = img.shape[:2]
            max_w = max(w1, w2)
            canvas = 255 * np.ones((h1+h2, max_w, 3), dtype=np.uint8)
            canvas[0:h2, 0:w2] = img
            canvas[h2:h2+h1, 0:w1] = merged
            merged = canvas
        self.preview_image = merged
        self.show_image(merged)

    # ================= Merge & Save =================
    def merge_images(self):
        if self.preview_image is None:
            self.preview_merge()
        # Tạo tên file theo thứ tự các ảnh được chọn
        selected_names = [os.path.splitext(self.image_list[idx])[0] for idx in self.selected_indices]
        merged_name = "_".join(selected_names) + ".png"
        save_path = os.path.join(self.folder_path, merged_name)
        cv2.imwrite(save_path, self.preview_image)
        messagebox.showinfo("Done", f"Ảnh đã ghép và lưu: {save_path}")

root = tk.Tk()
app = VerticalMergeAppOrdered(root)
root.mainloop()
