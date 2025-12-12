import os
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

SNAP_MARGIN = 10
EDGE_MARGIN = 8

class ImageCropperApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Cropper App 3")

        self.folder_path = None
        self.image_list = []
        self.current_image_index = None
        self.current_image_cv = None
        self.current_image_tk = None
        self.rect_start = None
        self.rect_end = None
        self.dragging_edge = None
        self.crop_coords = None

        # GUI layout
        self.left_frame = tk.Frame(master)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Button(self.left_frame, text="Chọn folder", command=self.load_folder).pack(pady=5)
        self.listbox = tk.Listbox(self.left_frame)
        self.listbox.pack(fill=tk.Y, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select_image)

        self.canvas = tk.Canvas(self.right_frame, width=640, height=480)
        self.canvas.pack(expand=True)
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        tk.Button(self.right_frame, text="Lưu ảnh", command=self.save_image).pack(pady=5)

    # ===================== Load folder =====================
    def load_folder(self):
        folder = filedialog.askdirectory(title="Chọn folder chứa ảnh")
        if not folder:
            return
        self.folder_path = folder
        self.image_list = sorted([f for f in os.listdir(folder) if f.lower().endswith(('.png','.jpg','.jpeg'))])
        self.listbox.delete(0, tk.END)
        for img in self.image_list:
            self.listbox.insert(tk.END, img)

    # ===================== Select image =====================
    def on_select_image(self, event):
        if not self.listbox.curselection():
            return
        index = self.listbox.curselection()[0]
        self.current_image_index = index
        img_path = os.path.join(self.folder_path, self.image_list[index])
        self.current_image_cv = cv2.imread(img_path)
        self.show_image(self.current_image_cv)
        self.rect_start = None
        self.rect_end = None
        self.crop_coords = None

    # ===================== Show image =====================
    def show_image(self, img_cv):
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_pil.thumbnail((640,480))
        self.current_image_tk = ImageTk.PhotoImage(img_pil)
        self.canvas.create_image(0,0, anchor=tk.NW, image=self.current_image_tk)
        if self.rect_start and self.rect_end:
            self.canvas.create_rectangle(self.rect_start[0], self.rect_start[1],
                                         self.rect_end[0], self.rect_end[1],
                                         outline="red", width=2, tag="rect")

    # ===================== Mouse crop =====================
    def on_mouse_down(self, event):
        x, y = event.x, event.y
        if self.rect_start and self.rect_end:
            left, top = self.rect_start
            right, bottom = self.rect_end
            if abs(y-top) <= EDGE_MARGIN:
                self.dragging_edge = 'top'
            elif abs(y-bottom) <= EDGE_MARGIN:
                self.dragging_edge = 'bottom'
            else:
                self.rect_start = (x,y)
                self.rect_end = (x,y)
                self.dragging_edge = None
        else:
            self.rect_start = (x,y)
            self.rect_end = (x,y)

    def on_mouse_drag(self, event):
        x, y = event.x, event.y
        y = self.snap(y, self.current_image_cv.shape[0])
        if self.dragging_edge:
            sx, sy = self.rect_start
            ex, ey = self.rect_end
            if self.dragging_edge == 'top':
                self.rect_start = (sx, y)
            elif self.dragging_edge == 'bottom':
                self.rect_end = (ex, y)
        else:
            self.rect_end = (x, y)
        self.show_image(self.current_image_cv)

    def on_mouse_up(self, event):
        self.dragging_edge = None
        if self.current_image_cv is not None:
            x1, y1 = self.rect_start
            x2, y2 = self.rect_end
            # Lưu crop chỉ trên/dưới
            self.crop_coords = (0, min(y1,y2), self.current_image_cv.shape[1], max(y1,y2))

    def snap(self, val, max_val):
        if abs(val) < SNAP_MARGIN:
            return 0
        elif abs(val - max_val) < SNAP_MARGIN:
            return max_val
        return val

    # ===================== Save image =====================
    def save_image(self):
        if self.crop_coords is None or self.current_image_index is None:
            messagebox.showwarning("Warning", "Chưa crop ảnh!")
            return
        x1, y1, x2, y2 = self.crop_coords
        cropped = self.current_image_cv[y1:y2, x1:x2]
        img_path = os.path.join(self.folder_path, self.image_list[self.current_image_index])
        cv2.imwrite(img_path, cropped)
        # Cập nhật hiển thị
        self.current_image_cv = cropped
        self.show_image(self.current_image_cv)
        messagebox.showinfo("Done", "Ảnh đã được crop và ghi đè!")

root = tk.Tk()
app = ImageCropperApp(root)
root.mainloop()
