import os
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

CANVAS_WIDTH = 640
CANVAS_HEIGHT = 480


class VerticalMergeApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Vertical Merge - Drag & Order")

        self.folder_path = None
        self.image_list = []
        self.selected_indices = []

        self.preview_image = None
        self.current_image_tk = None

        self.drag_index = None

        # ================= GUI =================
        self.left_frame = tk.Frame(master)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Button(self.left_frame, text="Chọn folder", command=self.load_folder).pack(pady=5)

        self.listbox = tk.Listbox(self.left_frame, selectmode=tk.MULTIPLE)
        self.listbox.pack(fill=tk.Y, expand=True, padx=5)

        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.bind("<Button-1>", self.on_drag_start)
        self.listbox.bind("<B1-Motion>", self.on_drag_motion)
        self.listbox.bind("<ButtonRelease-1>", self.on_drag_drop)

        self.canvas = tk.Canvas(
            self.right_frame,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg="gray"
        )
        self.canvas.pack(expand=True)

        tk.Button(self.right_frame, text="Preview Ghép", command=self.preview_merge).pack(pady=5)
        tk.Button(self.right_frame, text="Ghép ảnh & Lưu", command=self.merge_images).pack(pady=5)

    # ================= Load folder =================
    def load_folder(self):
        folder = filedialog.askdirectory(title="Chọn folder chứa ảnh")
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

    # ================= Select =================
    def on_select(self, event):
        self.selected_indices = list(self.listbox.curselection())
        if not self.selected_indices:
            return

        img_path = os.path.join(
            self.folder_path,
            self.image_list[self.selected_indices[0]]
        )
        img = cv2.imread(img_path)
        self.show_image(img)

    # ================= Drag & Drop =================
    def on_drag_start(self, event):
        self.drag_index = self.listbox.nearest(event.y)

    def on_drag_motion(self, event):
        if self.drag_index is None:
            return

        target = self.listbox.nearest(event.y)
        if target < 0 or target == self.drag_index:
            return

        self.image_list[self.drag_index], self.image_list[target] = \
            self.image_list[target], self.image_list[self.drag_index]

        self.refresh_listbox()

        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(target)
        self.drag_index = target

    def on_drag_drop(self, event):
        self.drag_index = None

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for img in self.image_list:
            self.listbox.insert(tk.END, img)

    # ================= Show image =================
    def show_image(self, img_cv):
        if img_cv is None:
            return

        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_pil.thumbnail((CANVAS_WIDTH, CANVAS_HEIGHT))

        self.current_image_tk = ImageTk.PhotoImage(img_pil)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image_tk)

    # ================= Preview merge =================
    def preview_merge(self):
        if not self.selected_indices:
            messagebox.showwarning("Warning", "Chưa chọn ảnh!")
            return

        images = []
        for idx in self.selected_indices:
            img = cv2.imread(os.path.join(self.folder_path, self.image_list[idx]))
            images.append(img)

        # ghép theo thứ tự listbox (ảnh chọn trước nằm trên)
        merged = images[0]
        positions = [0]

        for img in images[1:]:
            h1, w1 = merged.shape[:2]
            h2, w2 = img.shape[:2]
            max_w = max(w1, w2)

            canvas = 255 * np.ones((h1 + h2, max_w, 3), dtype=np.uint8)
            canvas[0:h1, 0:w1] = merged
            canvas[h1:h1 + h2, 0:w2] = img

            positions.append(h1)
            merged = canvas

        # vẽ số thứ tự
        y = 0
        for i, img in enumerate(images, start=1):
            cv2.putText(
                merged,
                str(i),
                (10, y + 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 0, 255),
                3,
                cv2.LINE_AA
            )
            y += img.shape[0]

        self.preview_image = merged
        self.show_image(merged)

    # ================= Merge & Save =================
    def merge_images(self):
        if self.preview_image is None:
            self.preview_merge()
            if self.preview_image is None:
                return

        names = [os.path.splitext(self.image_list[idx])[0]
                 for idx in self.selected_indices]

        filename = "_".join(names) + ".png"
        save_path = os.path.join(self.folder_path, filename)

        cv2.imwrite(save_path, self.preview_image)
        messagebox.showinfo("Done", f"Đã lưu ảnh:\n{save_path}")


# ================= RUN =================
if __name__ == "__main__":
    root = tk.Tk()
    app = VerticalMergeApp(root)
    root.mainloop()
