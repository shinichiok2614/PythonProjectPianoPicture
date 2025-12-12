import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os

class ImageCropApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Crop Vertical")
        self.images = []
        self.index = 0
        self.crop_top = 0
        self.crop_bottom = 0

        tk.Button(master, text="Chọn folder", command=self.load_folder).pack()
        self.canvas = tk.Canvas(master, width=600, height=400)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.set_top)
        self.canvas.bind("<Button-3>", self.set_bottom)
        tk.Button(master, text="Crop và lưu", command=self.crop_save).pack()

    def load_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.images = sorted([os.path.join(folder,f) for f in os.listdir(folder) if f.lower().endswith((".png",".jpg",".jpeg"))])
        self.index = 0
        self.show_image()

    def show_image(self):
        if not self.images:
            return
        img = Image.open(self.images[self.index])
        self.img_original = img
        img.thumbnail((600,400))
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.create_image(0,0, anchor=tk.NW, image=self.tk_img)

    def set_top(self, event):
        self.crop_top = int(event.y * self.img_original.height / 400)
        print("Top:", self.crop_top)

    def set_bottom(self, event):
        self.crop_bottom = int(event.y * self.img_original.height / 400)
        print("Bottom:", self.crop_bottom)

    def crop_save(self):
        if not self.images:
            return
        cropped = self.img_original.crop((0, self.crop_top, self.img_original.width, self.crop_bottom))
        cropped.save(self.images[self.index])
        tk.messagebox.showinfo("Done", f"Đã crop {self.images[self.index]}")
        self.index += 1
        if self.index < len(self.images):
            self.show_image()

root = tk.Tk()
app = ImageCropApp(root)
root.mainloop()
