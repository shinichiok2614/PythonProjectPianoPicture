import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

MAX_DISPLAY_WIDTH = 800
MAX_DISPLAY_HEIGHT = 600

class DraggableImageApp:
    def __init__(self, root):
        self.root = root
        root.title("Image Merger — Kéo ảnh bằng chuột")
        # Left control panel
        ctrl = tk.Frame(root)
        ctrl.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=6)

        tk.Button(ctrl, text="Add Image", width=18, command=self.add_images).pack(pady=4)
        tk.Button(ctrl, text="Remove Selected", width=18, command=self.remove_selected).pack(pady=4)
        tk.Button(ctrl, text="Merge Vertical", width=18, command=lambda: self.merge_images("vertical")).pack(pady=4)
        tk.Button(ctrl, text="Merge Horizontal", width=18, command=lambda: self.merge_images("horizontal")).pack(pady=4)
        tk.Button(ctrl, text="Save Canvas as PNG", width=18, command=self.save_canvas_snapshot).pack(pady=6)
        tk.Label(ctrl, text="Tip: kéo ảnh để thay đổi thứ tự/ vị trí.\nMerge theo X hoặc Y vị trí.", justify=tk.LEFT).pack(pady=8)

        # Canvas area
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(self.canvas_frame, width=MAX_DISPLAY_WIDTH, height=MAX_DISPLAY_HEIGHT, bg="#333")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # State
        self.items = {}  # canvas_id -> {'pil':Image, 'photo':ImageTk, 'orig_size':(w,h), 'scale':s}
        self.selected_id = None
        self._drag_data = {"x":0, "y":0, "item":None}

        # Bindings
        self.canvas.tag_bind("draggable", "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind("draggable", "<B1-Motion>", self.on_motion)
        self.canvas.tag_bind("draggable", "<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def add_images(self):
        paths = filedialog.askopenfilenames(title="Chọn ảnh", filetypes=[("Images","*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
        if not paths:
            return
        x, y = 20, 20
        padding = 10
        for p in paths:
            try:
                pil = Image.open(p).convert("RGBA")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không mở được {p}\n{e}")
                continue

            # Scale down for display if too large
            ow, oh = pil.size
            scale = min(1.0, MAX_DISPLAY_WIDTH / ow, MAX_DISPLAY_HEIGHT / oh, 0.9)
            disp_w = int(ow * scale)
            disp_h = int(oh * scale)
            disp = pil.resize((disp_w, disp_h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(disp)

            # create on canvas
            cid = self.canvas.create_image(x, y, image=photo, anchor="nw", tags=("draggable",))
            # keep reference to avoid GC
            self.items[cid] = {'pil': pil, 'photo': photo, 'orig_size': (ow, oh), 'scale': scale, 'path': p}
            # draw a border (rectangle) under item for selection visuals
            rect = self.canvas.create_rectangle(x-1, y-1, x+disp_w+1, y+disp_h+1, outline="", tags=(f"rect_{cid}",))
            # ensure rectangle is above image? we keep rectangle below by lowering it
            self.canvas.tag_lower(rect, cid)

            x += disp_w + padding
            if x > MAX_DISPLAY_WIDTH - 200:
                x = 20
                y += disp_h + padding

        # rebind (new items inherit tag)
        self.canvas.tag_bind("draggable", "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind("draggable", "<B1-Motion>", self.on_motion)
        self.canvas.tag_bind("draggable", "<ButtonRelease-1>", self.on_release)

    def on_canvas_click(self, event):
        # click on empty space -> deselect
        clicked = self.canvas.find_withtag("current")
        if not clicked:
            self.select_item(None)

    def on_press(self, event):
        # record the item and its location
        widget = event.widget
        cid = widget.find_withtag("current")[0]
        self._drag_data["item"] = cid
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self.select_item(cid)

    def on_motion(self, event):
        cid = self._drag_data.get("item")
        if cid is None:
            return
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        self.canvas.move(cid, dx, dy)
        # also move associated rect (if exists)
        rect_tag = f"rect_{cid}"
        items = self.canvas.find_withtag(rect_tag)
        if items:
            self.canvas.move(items[0], dx, dy)
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_release(self, event):
        self._drag_data["item"] = None

    def select_item(self, cid):
        # Clear previous outlines
        for k in list(self.items.keys()):
            rects = self.canvas.find_withtag(f"rect_{k}")
            for r in rects:
                self.canvas.itemconfigure(r, outline="", width=1)
        self.selected_id = cid
        if cid is None:
            return
        rects = self.canvas.find_withtag(f"rect_{cid}")
        if rects:
            self.canvas.itemconfigure(rects[0], outline="yellow", width=2)

    def remove_selected(self):
        if not self.selected_id:
            messagebox.showinfo("Info", "Chưa chọn ảnh nào")
            return
        # remove image and its rect
        cid = self.selected_id
        rects = self.canvas.find_withtag(f"rect_{cid}")
        if rects:
            self.canvas.delete(rects[0])
        self.canvas.delete(cid)
        if cid in self.items:
            del self.items[cid]
        self.selected_id = None

    def merge_images(self, mode="vertical"):
        if not self.items:
            messagebox.showinfo("Info", "Chưa có ảnh để ghép")
            return
        # Determine order by y (vertical) or x (horizontal) of the canvas
        pairs = []
        for cid, meta in self.items.items():
            coords = self.canvas.coords(cid)  # top-left (x,y)
            if not coords:
                continue
            x, y = coords[0], coords[1]
            pairs.append((cid, x, y, meta))
        if not pairs:
            messagebox.showerror("Error", "Không lấy được vị trí ảnh")
            return

        if mode == "vertical":
            pairs.sort(key=lambda t: t[2])  # sort by y
            # final image width = max original widths
            widths = [meta['orig_size'][0] for (_,_,_,meta) in pairs]
            heights = [meta['orig_size'][1] for (_,_,_,meta) in pairs]
            final_w = max(widths)
            final_h = sum(heights)
            final = Image.new("RGBA", (final_w, final_h), (255,255,255,0))
            y_offset = 0
            for cid, x, y, meta in pairs:
                pil = meta['pil']
                final.paste(pil, (0, y_offset), pil if pil.mode=="RGBA" else None)
                y_offset += pil.size[1]
        else:  # horizontal
            pairs.sort(key=lambda t: t[1])  # sort by x
            widths = [meta['orig_size'][0] for (_,_,_,meta) in pairs]
            heights = [meta['orig_size'][1] for (_,_,_,meta) in pairs]
            final_w = sum(widths)
            final_h = max(heights)
            final = Image.new("RGBA", (final_w, final_h), (255,255,255,0))
            x_offset = 0
            for cid, x, y, meta in pairs:
                pil = meta['pil']
                final.paste(pil, (x_offset, 0), pil if pil.mode=="RGBA" else None)
                x_offset += pil.size[0]

        # Ask save path
        out_p = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png"),("JPEG","*.jpg;*.jpeg")])
        if not out_p:
            return
        # Convert to RGB if saving JPG
        ext = os.path.splitext(out_p)[1].lower()
        if ext in [".jpg", ".jpeg"]:
            rgb = final.convert("RGB")
            rgb.save(out_p, quality=95)
        else:
            final.save(out_p)
        messagebox.showinfo("Done", f"Đã lưu: {out_p}")

    def save_canvas_snapshot(self):
        # Save canvas display as an image (rasterized) - useful for quick exports
        ps = self.canvas.postscript(colormode='color')
        try:
            from io import BytesIO
            img = Image.open(BytesIO(ps.encode('utf-8')))
            out_p = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png")])
            if not out_p:
                return
            img.save(out_p)
            messagebox.showinfo("Saved", f"Saved to {out_p}")
        except Exception as e:
            messagebox.showerror("Error", f"Không lưu được snapshot: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DraggableImageApp(root)
    root.mainloop()
