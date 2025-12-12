import os
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

SNAP_MARGIN = 10
EDGE_MARGIN = 8
CANVAS_WIDTH = 640
CANVAS_HEIGHT = 480

class ImageCropper:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Cropper 4 Edges")

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
        self.display_scale_x = 1
        self.display_scale_y = 1

        # GUI layout
        self.left_frame = tk.Frame(master)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Button(self.left_frame, text="Chọn folder", command=self.load_folder).pack(pady=5)
        self.listbox = tk.Listbox(self.left_frame)
        self.listbox.pack(fill=tk.Y, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select_image)

        self.canvas = tk.Canvas(self.right_frame, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
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
        # Bounding box mặc định trùng ảnh gốc
        self.rect_start = (0, 0)
        self.rect_end = (w, h)
        self.show_image()

    # ================= Show image =================
    def show_image(self):
        img_rgb = cv2.cvtColor(self.current_image_cv, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        # Scale ảnh xuống canvas nhưng giữ tỷ lệ
        img_pil.thumbnail((CANVAS_WIDTH, CANVAS_HEIGHT))
        self.display_scale_x = self.current_image_cv.shape[1] / img_pil.width
        self.display_scale_y = self.current_image_cv.shape[0] / img_pil.height
        self.current_image_tk = ImageTk.PhotoImage(img_pil)
        self.canvas.delete("all")
        self.canvas.create_image(0,0, anchor=tk.NW, image=self.current_image_tk)
        if self.rect_start and self.rect_end:
            # Vẽ bounding box trên canvas
            x1 = self.rect_start[0] / self.display_scale_x
            y1 = self.rect_start[1] / self.display_scale_y
            x2 = self.rect_end[0] / self.display_scale_x
            y2 = self.rect_end[1] / self.display_scale_y
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=2, tag="rect")

    # ================= Mouse down =================
    def on_mouse_down(self, event):
        x, y = event.x, event.y
        left = self.rect_start[0] / self.display_scale_x
        top = self.rect_start[1] / self.display_scale_y
        right = self.rect_end[0] / self.display_scale_x
        bottom = self.rect_end[1] / self.display_scale_y

        # Kéo cạnh
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

    # ================= Mouse drag =================
    def on_mouse_drag(self, event):
        x, y = event.x, event.y
        img_w = self.current_image_cv.shape[1]
        img_h = self.current_image_cv.shape[0]

        left = self.rect_start[0]
        top = self.rect_start[1]
        right = self.rect_end[0]
        bottom = self.rect_end[1]

        if self.dragging_edge:
            if self.dragging_edge in ['left', 'right']:
                x_new = self.snap(x * self.display_scale_x, img_w)
                if self.dragging_edge == 'left':
                    self.rect_start = (x_new, top)
                else:
                    self.rect_end = (x_new, bottom)
            else:  # top/bottom
                y_new = self.snap(y * self.display_scale_y, img_h)
                if self.dragging_edge == 'top':
                    self.rect_start = (left, y_new)
                else:
                    self.rect_end = (right, y_new)
        elif self.dragging_box:
            box_w = right - left
            box_h = bottom - top
            new_left = self.snap(x * self.display_scale_x - self.offset_x * self.display_scale_x, img_w)
            new_top = self.snap(y * self.display_scale_y - self.offset_y * self.display_scale_y, img_h)
            new_left = max(0, min(new_left, img_w - box_w))
            new_top = max(0, min(new_top, img_h - box_h))
            self.rect_start = (new_left, new_top)
            self.rect_end = (new_left + box_w, new_top + box_h)

        self.show_image()

    # ================= Mouse up =================
    def on_mouse_up(self, event):
        self.dragging_edge = None
        self.dragging_box = False
        self.crop_coords = (int(self.rect_start[0]), int(self.rect_start[1]),
                            int(self.rect_end[0]), int(self.rect_end[1]))

    # ================= Snap 4 cạnh =================
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
        # Cập nhật bounding box trùng ảnh cropped
        h, w = cropped.shape[:2]
        self.rect_start = (0, 0)
        self.rect_end = (w, h)
        self.show_image()
        messagebox.showinfo("Done", "Ảnh đã được crop và ghi đè!")

root = tk.Tk()
app = ImageCropper(root)
root.mainloop()
