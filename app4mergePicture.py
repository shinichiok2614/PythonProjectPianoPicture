import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

class ImageMergeApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Merge Images Vertical")
        self.images = []
        self.selected = []

        tk.Button(master, text="Chọn folder", command=self.load_folder).pack()
        self.listbox = tk.Listbox(master, selectmode=tk.MULTIPLE, width=50)
        self.listbox.pack()
        tk.Button(master, text="Merge", command=self.merge_images).pack()

    def load_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.images = sorted([os.path.join(folder,f) for f in os.listdir(folder) if f.lower().endswith((".png",".jpg",".jpeg"))])
        self.listbox.delete(0, tk.END)
        for img in self.images:
            self.listbox.insert(tk.END, os.path.basename(img))

    def merge_images(self):
        selected_indices = list(self.listbox.curselection())
        if not selected_indices:
            messagebox.showwarning("Warning", "Chọn ít nhất 1 ảnh")
            return
        imgs = [Image.open(self.images[i]) for i in selected_indices]
        widths = [img.width for img in imgs]
        heights = [img.height for img in imgs]
        total_height = sum(heights)
        max_width = max(widths)
        merged = Image.new("RGB", (max_width, total_height))
        y = 0
        # ảnh chọn trước nằm dưới
        for img in reversed(imgs):
            merged.paste(img, (0,y))
            y += img.height
        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if save_path:
            merged.save(save_path)
            messagebox.showinfo("Done", f"Đã ghép và lưu {save_path}")

root = tk.Tk()
app = ImageMergeApp(root)
root.mainloop()
