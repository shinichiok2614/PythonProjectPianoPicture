import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

CANVAS_W = 800
CANVAS_H = 450


# ================= VẼ PIANO =================
def draw_piano_white_lines(img, start_x, end_x, num_cycles):
    h, w = img.shape[:2]
    white_keys = ['C', 'D', 'E', 'F', 'G', 'A', 'B']

    total_width = end_x - start_x
    cycle_width = total_width / num_cycles

    for i in range(num_cycles):
        cycle_start = int(start_x + i * cycle_width)
        cycle_end = int(cycle_start + cycle_width)
        key_width = cycle_width / len(white_keys)

        for k, key in enumerate(white_keys):
            x = int(cycle_start + k * key_width)

            if key == 'C':
                color = (0, 0, 255)
                thickness = 3
            else:
                color = (255, 255, 255)
                thickness = 2

            cv2.line(img, (x, 0), (x, h), color, thickness)

        cv2.line(img, (cycle_end, 0), (cycle_end, h), (0, 0, 255), 3)

    return img


# ================= APP =================
class VideoPianoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Piano Line Video Tool")

        self.cap = None
        self.video_path = None
        self.frame = None
        self.video_w = None
        self.video_h = None

        self.start_x = None
        self.end_x = None
        self.setting_point = None

        self.num_cycles = tk.IntVar(value=1)

        # ---------- UI ----------
        left = tk.Frame(root)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        right = tk.Frame(root)
        right.pack(side=tk.RIGHT, expand=True)

        tk.Button(left, text="📂 Mở video", command=self.open_video).pack(fill=tk.X, pady=3)
        tk.Label(left, text="Số chu kỳ:").pack()
        tk.Entry(left, textvariable=self.num_cycles, width=5).pack()

        tk.Button(left, text="Chọn START", command=lambda: self.set_point("start")).pack(fill=tk.X, pady=3)
        tk.Button(left, text="Chọn END", command=lambda: self.set_point("end")).pack(fill=tk.X, pady=3)

        tk.Button(left, text="▶ XỬ LÝ VIDEO", command=self.process_video).pack(fill=tk.X, pady=10)

        self.info = tk.Label(left, text="Start: -\nEnd: -")
        self.info.pack(pady=5)

        self.canvas = tk.Canvas(right, width=CANVAS_W, height=CANVAS_H, bg="black")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)

    # ---------- Open video ----------
    def open_video(self):
        path = filedialog.askopenfilename(
            filetypes=[("Video", "*.mp4 *.avi *.mov")]
        )
        if not path:
            return

        self.video_path = path
        self.cap = cv2.VideoCapture(path)

        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Error", "Không đọc được video")
            return

        self.frame = frame
        self.video_h, self.video_w = frame.shape[:2]
        self.show_frame(frame)

    # ---------- Show frame ----------
    def show_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        img.thumbnail((CANVAS_W, CANVAS_H))
        self.tk_img = ImageTk.PhotoImage(img)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

    # ---------- Set start / end ----------
    def set_point(self, point_type):
        self.setting_point = point_type

    def on_click(self, event):
        if self.setting_point is None:
            return

        scale_x = self.video_w / CANVAS_W
        x_real = int(event.x * scale_x)

        if self.setting_point == "start":
            self.start_x = x_real
        else:
            self.end_x = x_real

        self.setting_point = None
        self.update_info()

        preview = self.frame.copy()
        if self.start_x and self.end_x:
            preview = draw_piano_white_lines(
                preview,
                self.start_x,
                self.end_x,
                self.num_cycles.get()
            )
        self.show_frame(preview)

    def update_info(self):
        self.info.config(
            text=f"Start: {self.start_x}\nEnd: {self.end_x}"
        )

    # ---------- Process ----------
    def process_video(self):
        if not self.video_path or self.start_x is None or self.end_x is None:
            messagebox.showwarning("Thiếu dữ liệu", "Chưa chọn start/end")
            return

        output = os.path.splitext(self.video_path)[0] + "_piano.mp4"

        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        out = cv2.VideoWriter(
            output,
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (w, h)
        )

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = draw_piano_white_lines(
                frame,
                self.start_x,
                self.end_x,
                self.num_cycles.get()
            )
            out.write(frame)

        cap.release()
        out.release()
        messagebox.showinfo("Done", f"Xuất video:\n{output}")


# ================= RUN =================
if __name__ == "__main__":
    root = tk.Tk()
    app = VideoPianoApp(root)
    root.mainloop()
