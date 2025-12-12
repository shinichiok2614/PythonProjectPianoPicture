import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import math
import os
class ImageItem:
    def __init__(self, pil_img, x, y):
        self.original = pil_img
        self.x = x
        self.y = y
        self.scale = 1.0
        self.angle = 0
        self.tk_img = None
        self.canvas_id = None
        self.handles = []

    def render(self):
        # scale
        w = int(self.original.width * self.scale)
        h = int(self.original.height * self.scale)
        img = self.original.resize((w, h), Image.LANCZOS)

        # rotate
        img = img.rotate(self.angle, expand=True)

        self.tk_img = ImageTk.PhotoImage(img)
        return img
class EditorApp:
    HANDLE_SIZE = 10

    def __init__(self, root):
        self.root = root
        root.title("Pro Image Editor – Drag / Resize / Rotate / Merge")

        self.canvas = tk.Canvas(root, width=1200, height=800, bg="#444")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        btn = tk.Frame(root)
        btn.pack()

        tk.Button(btn, text="Add Image", command=self.add_image).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Export (Merge)", command=self.export_merge).pack(side=tk.LEFT, padx=5)

        # State
        self.images = []
        self.selected = None
        self.dragging = False
        self.last_mouse = (0, 0)
        self.active_handle = None

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    # ===== ADD IMAGE ==========================
    def add_image(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if not paths:
            return

        x, y = 50, 50
        for p in paths:
            img = Image.open(p).convert("RGBA")
            item = ImageItem(img, x, y)
            self.images.append(item)
            self.draw_item(item)

    # ===== DRAW ITEM ==========================
    def draw_item(self, item: ImageItem):
        img = item.render()
        if item.canvas_id:
            self.canvas.delete(item.canvas_id)
        for h in item.handles:
            self.canvas.delete(h)
        item.handles.clear()

        item.tk_img = ImageTk.PhotoImage(img)
        item.canvas_id = self.canvas.create_image(item.x, item.y, image=item.tk_img, anchor="nw")

        # Create resize handles
        w, h = img.width, img.height
        corners = [
            (item.x, item.y),
            (item.x + w, item.y),
            (item.x + w, item.y + h),
            (item.x, item.y + h),
        ]
        for cx, cy in corners:
            hid = self.canvas.create_rectangle(
                cx - self.HANDLE_SIZE, cy - self.HANDLE_SIZE,
                cx + self.HANDLE_SIZE, cy + self.HANDLE_SIZE,
                fill="yellow"
            )
            item.handles.append(hid)

        # Rotation handle (top-middle)
        rx = item.x + w // 2
        ry = item.y - 30
        rot = self.canvas.create_oval(
            rx - self.HANDLE_SIZE, ry - self.HANDLE_SIZE,
            rx + self.HANDLE_SIZE, ry + self.HANDLE_SIZE,
            fill="cyan"
        )
        item.handles.append(rot)

    # ===== CLICK ==========================
    def on_click(self, event):
        self.last_mouse = (event.x, event.y)

        clicked = self.canvas.find_withtag("current")
        if not clicked:
            self.selected = None
            return

        cid = clicked[0]

        # Check if clicked handle
        if self.selected:
            if cid in self.selected.handles:
                self.active_handle = cid
                return

        # Select image
        for item in reversed(self.images):  # top-most first
            if item.canvas_id == cid or cid in item.handles:
                self.selected = item
                return

    # ===== DRAG / RESIZE / ROTATE ==========================
    def on_drag(self, event):
        if not self.selected:
            return

        dx = event.x - self.last_mouse[0]
        dy = event.y - self.last_mouse[1]
        self.last_mouse = (event.x, event.y)

        item = self.selected

        # Rotate
        if self.active_handle and self.active_handle == item.handles[-1]:
            cx = item.x + (item.render().width // 2)
            cy = item.y + (item.render().height // 2)
            ang = math.degrees(math.atan2(event.y - cy, event.x - cx))
            item.angle = ang
            self.draw_item(item)
            return

        # Resize handle
        if self.active_handle and self.active_handle in item.handles[:-1]:
            # Scale uniformly
            s = item.scale + dx * 0.005
            if s < 0.1:
                s = 0.1
            item.scale = s
            self.draw_item(item)
            return

        # Move image
        item.x += dx
        item.y += dy
        self.draw_item(item)

    # ===== RELEASE ==========================
    def on_release(self, event):
        self.active_handle = None

    # ===== EXPORT MERGE (THEO TỌA ĐỘ THẬT) ==========================
    def export_merge(self):
        if not self.images:
            messagebox.showinfo("Info", "No images")
            return

        # compute bounding box
        xs, ys, xe, ye = [], [], [], []

        for it in self.images:
            img = it.render()
            xs.append(it.x)
            ys.append(it.y)
            xe.append(it.x + img.width)
            ye.append(it.y + img.height)

        min_x = min(xs)
        min_y = min(ys)
        max_x = max(xe)
        max_y = max(ye)

        W = max_x - min_x
        H = max_y - min_y

        out = Image.new("RGBA", (W, H), (0, 0, 0, 0))

        for it in self.images:
            img = it.render()
            out.paste(img, (it.x - min_x, it.y - min_y), img)

        save = filedialog.asksaveasfilename(defaultextension=".png")
        if save:
            out.save(save)
            messagebox.showinfo("OK", "Saved!")
root = tk.Tk()
app = EditorApp(root)
root.mainloop()
