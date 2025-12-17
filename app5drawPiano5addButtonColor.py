import os
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

CANVAS_WIDTH = 640
CANVAS_HEIGHT = 480
PIANO_HEIGHT = 300

WHITE_KEYS = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
BLACK_AFTER = {'C', 'D', 'F', 'G', 'A'}

class PianoApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Piano Color Painter")

        self.folder_path = None
        self.image_list = []
        self.current_image_cv = None
        self.current_image_preview = None
        self.current_image_tk = None

        self.start_x = None
        self.end_x = None
        self.num_cycles = tk.IntVar(value=1)

        self.selected_color_index = tk.IntVar(value=1)

        self.color_map = {
            1: ((0, 0, 255), "Đỏ"),
            2: ((0, 165, 255), "Cam"),
            3: ((0, 255, 255), "Vàng"),
            4: ((0, 255, 0), "Lục"),
            5: ((255, 255, 0), "Lam")
        }

        self.piano_keys = []

        # ===== GUI =====
        left = tk.Frame(master)
        left.pack(side=tk.LEFT, fill=tk.Y)
        right = tk.Frame(master)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Button(left, text="Chọn folder", command=self.load_folder).pack(pady=5)
        self.listbox = tk.Listbox(left)
        self.listbox.pack(fill=tk.Y, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select_image)

        tk.Label(left, text="Số chu kỳ").pack()
        tk.Entry(left, textvariable=self.num_cycles, width=5).pack()

        tk.Button(left, text="Chọn START", command=lambda: self.set_point("start")).pack(pady=3)
        tk.Button(left, text="Chọn END", command=lambda: self.set_point("end")).pack(pady=3)
        tk.Button(left, text="Preview Piano", command=self.preview).pack(pady=5)

        tk.Label(left, text="Chọn màu (1–5)").pack(pady=(10, 2))
        for i in range(1, 6):
            tk.Radiobutton(
                left, text=str(i),
                variable=self.selected_color_index,
                value=i
            ).pack(anchor="w")

        self.canvas = tk.Canvas(right, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
        self.canvas.pack(expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        self.setting_point = None

    # ===== Load =====
    def load_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.folder_path = folder
        self.image_list = sorted(f for f in os.listdir(folder) if f.lower().endswith(('.jpg','.png')))
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

    def show_image(self, img):
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        pil.thumbnail((CANVAS_WIDTH, CANVAS_HEIGHT))
        self.current_image_tk = ImageTk.PhotoImage(pil)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image_tk)

    # ===== Points =====
    def set_point(self, p):
        self.setting_point = p

    def on_canvas_click(self, event):
        if self.setting_point:
            scale_x = self.current_image_cv.shape[1] / CANVAS_WIDTH
            x = int(event.x * scale_x)
            if self.setting_point == "start":
                self.start_x = x
            else:
                self.end_x = x
            self.setting_point = None
            return

        if self.current_image_preview is None:
            return

        scale_x = self.current_image_preview.shape[1] / CANVAS_WIDTH
        scale_y = self.current_image_preview.shape[0] / CANVAS_HEIGHT
        x = int(event.x * scale_x)
        y = int(event.y * scale_y)

        for key in reversed(self.piano_keys):
            x1,y1,x2,y2 = key["rect"]
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.apply_color(key)
                return

    # ===== Piano =====
    def preview(self):
        src = self.current_image_cv
        h,w = src.shape[:2]

        img = np.zeros((h+PIANO_HEIGHT, w, 3), dtype=np.uint8)
        img[:h] = src
        img[h:] = (255,255,255)

        self.piano_keys.clear()

        total = self.end_x - self.start_x
        cycle_w = total / self.num_cycles.get()
        white_w = cycle_w / 7

        for c in range(self.num_cycles.get()):
            base = int(self.start_x + c*cycle_w)

            # white keys
            for i,k in enumerate(WHITE_KEYS):
                x1 = int(base + i*white_w)
                x2 = int(x1 + white_w)
                self.piano_keys.append({
                    "note": k,
                    "type": "white",
                    "rect": (x1, h, x2, h+PIANO_HEIGHT),
                    "color": None,
                    "label": None
                })
                cv2.rectangle(img, (x1,h),(x2,h+PIANO_HEIGHT),(0,0,0),2)

            # black keys
            for i,k in enumerate(WHITE_KEYS):
                if k not in BLACK_AFTER:
                    continue
                bx = int(base + (i+1)*white_w - white_w*0.3)
                bw = int(white_w*0.6)
                bh = int(PIANO_HEIGHT*0.6)
                self.piano_keys.append({
                    "note": k+"#",
                    "type": "black",
                    "rect": (bx, h, bx+bw, h+bh),
                    "color": None,
                    "label": None
                })
                cv2.rectangle(img, (bx,h),(bx+bw,h+bh),(0,0,0),-1)

        self.current_image_preview = img
        self.show_image(img)

    def apply_color(self, key):
        idx = self.selected_color_index.get()
        color,name = self.color_map[idx]
        key["color"] = color
        key["label"] = idx

        messagebox.showinfo(
            "Piano",
            f"Bạn đã click phím: {key['note']} ({key['type']})\nMàu: {name}"
        )
        self.redraw()

    def redraw(self):
        img = self.current_image_preview.copy()
        for k in self.piano_keys:
            if k["color"]:
                x1,y1,x2,y2 = k["rect"]
                cv2.rectangle(img,(x1,y1),(x2,y2),k["color"],-1)
                cx = (x1+x2)//2
                cy = y2-15
                cv2.putText(
                    img,str(k["label"]),
                    (cx-5,cy),
                    cv2.FONT_HERSHEY_SIMPLEX,0.6,
                    (0,0,0) if k["type"]=="white" else (255,255,255),2
                )
        self.show_image(img)

root = tk.Tk()
PianoApp(root)
root.mainloop()
