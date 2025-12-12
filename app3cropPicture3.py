import os
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

SNAP_MARGIN = 10
EDGE_MARGIN = 8

class ImageCropperMoveBox:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Cropper Move & Snap")

        self.folder_path = None
        self.image_list = []
        self.current_image_index = None
        self.current_image_cv = None
        self.current_image_tk = None

        # Bounding box
        self.rect_start = None
        self.rect_end = None
        self.dragging_edge = None
        self.dragging_box = False
        self.offset_x = 0
        self.offset_y = 0
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
        self.current_image_index = index
        img_path = os.path.join(self.folder_path, self.image_list[index])
        self.current_image_cv = cv2.imread(img_path)
        h, w = self.current_image_cv.shape[:2]
        # Bounding box mặc định bao trọn toàn bộ ảnh
        self.rect_start = (0, 0)
        self.rect_end = (w, h)
        self.show_image(self.current_image_cv)

    # ================= Show image =================
    def show_image(self, img_cv):
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_pil.thumbnail((640,480))
        self.current_image_tk = ImageTk.PhotoImage(img_pil)
        self.canvas.delete("all")
        self.canvas.create_image(0,0, anchor=tk.NW, image=self.current_image_tk)
        if self.rect_start and self.rect_end:
            self.canvas.create_rectangle(self.rect_start[0], self.rect_start[1],
                                         self.rect_end[0], self.rect_end[1],
                                         outline="red", width=2, tag="rect")

    # ================= Mouse crop =================
    def on_mouse_down(self, event):
        x, y = event.x, event.y
        left, top = self.rect_start
        right, bottom = self.rect_end
        # Kiểm tra kéo cạnh
        if abs(x-left) <= EDGE_MARGIN:
            self.dragging_edge = 'left'
        elif abs(x-right) <= EDGE_MARGIN:
            self.dragging_edge = 'right'
        elif abs(y-top) <= EDGE_MARGIN:
            self.dragging_edge = 'top'
        elif abs(y-bottom) <= EDGE_MARGIN:
            self.dragging_edge = 'bottom'
        elif left < x < right and top < y < bottom:
            # Kéo toàn bộ bounding box
            self.dragging_box = True
            self.offset_x = x - left
            self.offset_y = y - top
        else:
            self.dragging_edge = None
            self.dragging_box = False

    def on_mouse_drag(self, event):
        x, y = event.x, event.y
        left, top = self.rect_start
        right, bottom = self.rect_end
        img_w, img_h = self.current_image_cv.shape[1], self.current_image_cv.shape[0]

        if self.dragging_edge == 'left':
            x = self.snap(x, img_w)
            self.rect_start = (x, top)
        elif self.dragging_edge == 'right':
            x = self.snap(x, img_w)
            self.rect_end = (x, bottom)
        elif self.dragging_edge == 'top':
            y = self.snap(y, img_h)
            self.rect_start = (left, y)
        elif self.dragging_edge == 'bottom':
            y = self.snap(y, img_h)
            self.rect_end = (right, y)
        elif self.dragging_box:
            box_w = right - left
            box_h = bottom - top
            new_left = self.snap(x - self.offset_x, img_w)
            new_top = self.snap(y - self.offset_y, img_h)
            # Giữ kích thước box
            new_left = max(0, min(new_left, img_w - box_w))
            new_top = max(0, min(new_top, img_h - box_h))
            self.rect_start = (new_left, new_top)
            self.rect_end = (new_left + box_w, new_top + box_h)

        self.show_image(self.current_image_cv)

    def on_mouse_up(self, event):
        self.dragging_edge = None
        self.dragging_box = False
        left, top = self.rect_start
        right, bottom = self.rect_end
        self.crop_coords = (max(0,left), max(0,top), min(self.current_image_cv.shape[1],right),
                            min(self.current_image_cv.shape[0],bottom))

    # ================= Snap tất cả 4 cạnh =================
    def snap(self, val, max_val):
        if abs(val) < SNAP_MARGIN:
            return 0
        elif abs(val - max_val) < SNAP_MARGIN:
            return max_val
        return val

    # ================= Save image =================
    def save_image(self):
        if self.crop_coords is None or self.current_image_index is None:
            messagebox.showwarning("Warning", "Chưa crop ảnh!")
            return
        x1, y1, x2, y2 = self.crop_coords
        cropped = self.current_image_cv[y1:y2, x1:x2]
        img_path = os.path.join(self.folder_path, self.image_list[self.current_image_index])
        cv2.imwrite(img_path, cropped)
        self.current_image_cv = cropped
        self.show_image(self.current_image_cv)
        messagebox.showinfo("Done", "Ảnh đã được crop và ghi đè!")

root = tk.Tk()
app = ImageCropperMoveBox(root)
root.mainloop()
