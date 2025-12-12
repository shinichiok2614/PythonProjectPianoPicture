import os
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

CANVAS_WIDTH = 640
CANVAS_HEIGHT = 480

class VerticalMergeAppAdvanced:
    def __init__(self, master):
        self.master = master
        self.master.title("Vertical Image Merge Advanced")

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
        # Drag & drop thay đổi thứ tự listbox
        self.listbox.bind("<Button-1>", self.click_listbox)
        self.listbox.bind("<B1-Motion>", self.drag_listbox)

        self.canvas = tk.Canvas(self.right_frame, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
        self.canvas.pack(expand=True)

        tk.Button(self.right_frame, text="Preview Ghép", command=self.preview_merge).pack(pady=5)
        tk.Button(self.right_frame, text="Ghép ảnh & Lưu", command=self.merge_images).pack(pady=5)

        # drag & drop variables
        self.drag_start_index = None

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
        if not self.listbox.curselection():
            messagebox.showwarning("Warning", "Chưa chọn ảnh!")
            return
        images = []
        for idx in self.listbox.curselection():
            img_path = os.path.join(self.folder_path, self.image_list[idx])
            img = cv2.imread(img_path)
            images.append(img)
        if not images:
            return
        # Ghép theo chiều dọc, ảnh chọn trước nằm dưới
        merged = images[-1]
        for img in reversed(images[:-1]):
            h1, w1 = merged.shape[:2]
            h2, w2 = img.shape[:2]
            max_w = max(w1, w2)
            merged_canvas = 255 * np.ones((h1+h2, max_w, 3), dtype=np.uint8)
            merged_canvas[0:h2, 0:w2] = img
            merged_canvas[h2:h2+h1, 0:w1] = merged
            merged = merged_canvas
        self.preview_image = merged
        self.show_image(merged)

    # ================= Merge & Save =================
    def merge_images(self):
        if self.preview_image is None:
            self.preview_merge()
        folder_name = os.path.basename(self.folder_path)
        save_path = os.path.join(self.folder_path, f"{folder_name}_merged.png")
        cv2.imwrite(save_path, self.preview_image)
        messagebox.showinfo("Done", f"Ảnh đã ghép và lưu: {save_path}")

    # ================= Listbox drag & drop =================
    def click_listbox(self, event):
        self.drag_start_index = self.listbox.nearest(event.y)

    def drag_listbox(self, event):
        new_index = self.listbox.nearest(event.y)
        if new_index != self.drag_start_index:
            # Swap items
            items = list(self.listbox.get(0, tk.END))
            items[self.drag_start_index], items[new_index] = items[new_index], items[self.drag_start_index]
            self.listbox.delete(0, tk.END)
            for item in items:
                self.listbox.insert(tk.END, item)
            # Update selection
            self.listbox.selection_set(new_index)
            self.drag_start_index = new_index

root = tk.Tk()
app = VerticalMergeAppAdvanced(root)
root.mainloop()
