import os
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

CANVAS_WIDTH = 640
CANVAS_HEIGHT = 480
PIANO_HEIGHT = 200

WHITE_KEYS = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
BLACK_AFTER = {'C', 'D', 'F', 'G', 'A'}

COLOR_MAP = {
    1: ((0, 0, 255), "Đỏ"),
    2: ((0, 165, 255), "Cam"),
    3: ((0, 255, 255), "Vàng"),
    4: ((0, 255, 0), "Lục"),
    5: ((255, 255, 0), "Lam")
}


class PianoAppFullFixed:
    def __init__(self, master):
        self.master = master
        self.master.title("Piano Drawer + Painter (FULL FIXED)")

        self.folder_path = None
        self.image_list = []

        self.current_image_cv = None
        self.current_image_preview = None
        self.current_image_tk = None

        self.start_x = None
        self.end_x = None

        self.num_cycles = tk.IntVar(value=1)
        self.piano_bg = tk.StringVar(value="white")
        self.selected_color_index = tk.IntVar(value=1)

        self.piano_keys = []
        self.preview_w = None
        self.preview_h = None
        self.setting_point = None

        # ===== GUI =====
        left = tk.Frame(master)
        left.pack(side=tk.LEFT, fill=tk.Y)
        right = tk.Frame(master)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Button(left, text="Chọn folder", command=self.load_folder).pack(pady=5)

        self.listbox = tk.Listbox(left, width=30, exportselection=False)
        self.listbox.pack(fill=tk.Y, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select_image)

        tk.Label(left, text="Số chu kỳ").pack(pady=5)
        tk.Entry(left, textvariable=self.num_cycles, width=5).pack()

        tk.Label(left, text="Nền piano").pack(pady=(10, 2))
        tk.Radiobutton(left, text="Nền trắng", variable=self.piano_bg, value="white").pack(anchor="w")
        tk.Radiobutton(left, text="Nền đen", variable=self.piano_bg, value="black").pack(anchor="w")

        tk.Button(left, text="Chọn START", command=lambda: self.set_point("start")).pack(pady=3)
        tk.Button(left, text="Chọn END", command=lambda: self.set_point("end")).pack(pady=3)

        tk.Button(left, text="Preview Piano", command=self.preview_piano).pack(pady=6)

        tk.Label(left, text="Chọn màu").pack(pady=(10, 2))
        for i in range(1, 6):
            tk.Radiobutton(
                left,
                text=f"Màu {i}",
                variable=self.selected_color_index,
                value=i
            ).pack(anchor="w")

        tk.Button(left, text="Lưu ảnh (ghi đè)", command=self.save_image).pack(pady=10)

        self.canvas = tk.Canvas(right, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
        self.canvas.pack(expand=True)

        self.canvas.bind("<Button-1>", lambda e: self.on_canvas_click(e, erase=False))
        self.canvas.bind("<Button-3>", lambda e: self.on_canvas_click(e, erase=True))

    # ========= LOAD =========
    def load_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.folder_path = folder
        self.image_list = sorted(
            f for f in os.listdir(folder)
            if f.lower().endswith(('.jpg', '.png', '.jpeg'))
        )
        self.listbox.delete(0, tk.END)
        for f in self.image_list:
            self.listbox.insert(tk.END, f)

    def on_select_image(self, event):
        if not self.listbox.curselection():
            return
        idx = self.listbox.curselection()[0]
        path = os.path.join(self.folder_path, self.image_list[idx])
        self.current_image_cv = cv2.imread(path)
        self.show_image(self.current_image_cv)

    # ========= DISPLAY =========
    def show_image(self, img):
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        pil.thumbnail((CANVAS_WIDTH, CANVAS_HEIGHT))
        self.preview_w, self.preview_h = pil.size
        self.current_image_tk = ImageTk.PhotoImage(pil)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image_tk)

    # ========= POINT =========
    def set_point(self, p):
        self.setting_point = p

    def on_canvas_click(self, event, erase=False):
        if self.setting_point:
            scale_x = self.current_image_cv.shape[1] / self.preview_w
            x = int(event.x * scale_x)
            if self.setting_point == "start":
                self.start_x = x
            else:
                self.end_x = x
            self.setting_point = None
            return

        if not self.piano_keys:
            return

        scale_x = self.current_image_preview.shape[1] / self.preview_w
        scale_y = self.current_image_preview.shape[0] / self.preview_h
        x = int(event.x * scale_x)
        y = int(event.y * scale_y)

        for key in reversed(self.piano_keys):
            x1, y1, x2, y2 = key["rect"]
            if x1 <= x <= x2 and y1 <= y <= y2:
                if erase:
                    key["color"] = None
                    key["label"] = None
                else:
                    idx = self.selected_color_index.get()
                    key["color"] = COLOR_MAP[idx][0]
                    key["label"] = idx
                self.redraw()
                return

    # ========= DRAW PIANO FRAME (CORE) =========
    def draw_piano_frame(self, img):
        h = self.current_image_cv.shape[0]
        piano_top = h
        piano_bottom = h + PIANO_HEIGHT

        if self.piano_bg.get() == "white":
            white_key_color = (255, 255, 255)
            black_key_color = (0, 0, 0)
            border_color = (0, 0, 0)
        else:
            white_key_color = (230, 230, 230)
            black_key_color = (0, 0, 0)
            border_color = (255, 255, 255)

        total_width = self.end_x - self.start_x
        cycle_width = total_width / self.num_cycles.get()

        black_key_width_ratio = 0.6
        black_key_height_ratio = 0.6
        black_height = int(PIANO_HEIGHT * black_key_height_ratio)

        for i in range(self.num_cycles.get()):
            cycle_start = int(self.start_x + i * cycle_width)
            cycle_end = int(cycle_start + cycle_width)
            white_key_width = cycle_width / 7

            # phím trắng
            for k, key in enumerate(WHITE_KEYS):
                x = int(cycle_start + k * white_key_width)
                if key == 'C':
                    color = (0, 0, 255)
                    thickness = 3
                else:
                    color = border_color
                    thickness = 2

                cv2.line(img, (x, piano_top), (x, piano_bottom), color, thickness)

            # cạnh phải B
            cv2.line(img, (cycle_end, piano_top), (cycle_end, piano_bottom), (0, 0, 255), 3)

            # phím đen
            for k, key in enumerate(WHITE_KEYS):
                if key not in BLACK_AFTER:
                    continue

                white_x = cycle_start + k * white_key_width
                next_white_x = white_x + white_key_width

                black_w = int(white_key_width * black_key_width_ratio)
                black_x = int(next_white_x - black_w / 2)

                cv2.rectangle(
                    img,
                    (black_x, piano_top),
                    (black_x + black_w, piano_top + black_height),
                    black_key_color,
                    -1
                )

        # viền ngoài
        cv2.rectangle(
            img,
            (self.start_x, piano_top),
            (self.end_x, piano_bottom),
            border_color,
            2
        )

    # ========= PREVIEW =========
    def preview_piano(self):
        if self.current_image_cv is None:
            messagebox.showwarning("Warning", "Chưa chọn ảnh!")
            return
        if self.start_x is None or self.end_x is None:
            messagebox.showwarning("Warning", "Chưa chọn START / END!")
            return

        src = self.current_image_cv
        h, w = src.shape[:2]

        bg = (255, 255, 255) if self.piano_bg.get() == "white" else (0, 0, 0)

        img = np.zeros((h + PIANO_HEIGHT, w, 3), dtype=np.uint8)
        img[:h] = src
        img[h:] = bg

        self.piano_keys.clear()

        total = self.end_x - self.start_x
        cycle_w = total / self.num_cycles.get()
        white_w = cycle_w / 7

        for c in range(self.num_cycles.get()):
            base_x = int(self.start_x + c * cycle_w)

            for i, k in enumerate(WHITE_KEYS):
                x1 = int(base_x + i * white_w)
                x2 = int(x1 + white_w)
                self.piano_keys.append({
                    "note": k,
                    "type": "white",
                    "rect": (x1, h, x2, h + PIANO_HEIGHT),
                    "color": None,
                    "label": None
                })

            for i, k in enumerate(WHITE_KEYS):
                if k not in BLACK_AFTER:
                    continue
                bw = int(white_w * 0.6)
                bh = int(PIANO_HEIGHT * 0.6)
                bx = int(base_x + (i + 1) * white_w - bw // 2)
                self.piano_keys.append({
                    "note": k + "#",
                    "type": "black",
                    "rect": (bx, h, bx + bw, h + bh),
                    "color": None,
                    "label": None
                })

        self.current_image_preview = img
        self.draw_piano_frame(self.current_image_preview)
        self.redraw()

    # ========= REDRAW =========
    def redraw(self):
        img = self.current_image_preview.copy()

        for k in self.piano_keys:
            if k["color"]:
                cv2.rectangle(img, k["rect"][:2], k["rect"][2:], k["color"], -1)

        for k in self.piano_keys:
            if k["label"]:
                x1, y1, x2, y2 = k["rect"]
                cx = (x1 + x2) // 2
                cy = y2 - 15
                txt = (255, 255, 255) if k["type"] == "black" else (0, 0, 0)
                cv2.putText(img, str(k["label"]),
                            (cx - 6, cy),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            txt, 2)

        self.show_image(img)

    # ========= SAVE =========
    def save_image(self):
        if self.current_image_cv is None:
            return

        h, w = self.current_image_cv.shape[:2]
        bg = (255, 255, 255) if self.piano_bg.get() == "white" else (0, 0, 0)

        final = np.zeros((h + PIANO_HEIGHT, w, 3), dtype=np.uint8)
        final[:h] = self.current_image_cv
        final[h:] = bg

        self.draw_piano_frame(final)

        for k in self.piano_keys:
            if k["color"]:
                cv2.rectangle(final, k["rect"][:2], k["rect"][2:], k["color"], -1)
            if k["label"]:
                x1, y1, x2, y2 = k["rect"]
                cx = (x1 + x2) // 2
                cy = y2 - 15
                txt = (255, 255, 255) if k["type"] == "black" else (0, 0, 0)
                cv2.putText(final, str(k["label"]),
                            (cx - 6, cy),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            txt, 2)

        idx = self.listbox.curselection()[0]
        path = os.path.join(self.folder_path, self.image_list[idx])
        cv2.imwrite(path, final)

        messagebox.showinfo("Done", f"Đã lưu ĐẦY ĐỦ khung piano:\n{path}")


# ========= RUN =========
root = tk.Tk()
PianoAppFullFixed(root)
root.mainloop()
