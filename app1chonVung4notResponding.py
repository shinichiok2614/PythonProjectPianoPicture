import cv2
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import threading
import queue

SNAP_MARGIN = 10
EDGE_MARGIN = 8

class VideoCropperFastSafe:
    def __init__(self, master):
        self.master = master
        self.master.title("Video Cropper Fast Safe")

        self.cap = None
        self.frame = None
        self.photo = None
        self.rect_start = None
        self.rect_end = None
        self.crop_coords = None
        self.dragging_edge = None
        self.video_path = None
        self.frame_count = 0
        self.current_frame = 0
        self.update_preview_flag = True

        self.progress_queue = queue.Queue()

        tk.Button(master, text="Chọn video", command=self.load_video).pack()
        self.canvas = tk.Canvas(master, width=640, height=360)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        self.slider = tk.Scale(master, from_=0, to=0, orient=tk.HORIZONTAL, length=640,
                               label="Frame", command=self.slider_moved)
        self.slider.pack()

        self.progress = ttk.Progressbar(master, orient="horizontal", length=640, mode="determinate")
        self.progress.pack(pady=5)

        tk.Button(master, text="Crop và lưu video", command=self.save_cropped_video).pack(pady=10)

        self.master.bind("<Left>", lambda e: self.move_slider(-10))
        self.master.bind("<Right>", lambda e: self.move_slider(10))

        self.master.after(100, self.update_progress_from_queue)

    # ======================= Video & slider =========================
    def load_video(self):
        path = filedialog.askopenfilename(title="Chọn video", filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if not path:
            return
        self.cap = cv2.VideoCapture(path)
        self.video_path = path
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.slider.config(to=self.frame_count-1)
        self.current_frame = 0
        self.update_preview_flag = True
        self.update_preview()

    def update_preview(self):
        if not self.cap or not self.update_preview_flag:
            return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.cap.read()
        if ret:
            self.frame = frame
            self.show_frame(frame)
        self.current_frame += 1
        if self.current_frame >= self.frame_count:
            self.current_frame = 0
        self.slider.set(self.current_frame)
        self.master.after(30, self.update_preview)

    def show_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img.thumbnail((640,360))
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(0,0, anchor=tk.NW, image=self.photo)
        if self.rect_start and self.rect_end:
            self.canvas.create_rectangle(self.rect_start[0], self.rect_start[1],
                                         self.rect_end[0], self.rect_end[1],
                                         outline="red", width=2, tag="rect")

    def slider_moved(self, val):
        if not self.cap:
            return
        self.update_preview_flag = False
        self.current_frame = int(val)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.cap.read()
        if ret:
            self.frame = frame
            self.show_frame(frame)

    def move_slider(self, step):
        if not self.cap:
            return
        new_frame = max(0, min(self.frame_count-1, self.current_frame + step))
        self.slider.set(new_frame)
        self.slider_moved(new_frame)

    # ===================== Mouse crop =========================
    def on_mouse_down(self, event):
        x, y = event.x, event.y
        if self.rect_start and self.rect_end:
            left, top = self.rect_start
            right, bottom = self.rect_end
            if abs(x-left) <= EDGE_MARGIN:
                self.dragging_edge = 'left'
            elif abs(x-right) <= EDGE_MARGIN:
                self.dragging_edge = 'right'
            elif abs(y-top) <= EDGE_MARGIN:
                self.dragging_edge = 'top'
            elif abs(y-bottom) <= EDGE_MARGIN:
                self.dragging_edge = 'bottom'
            else:
                self.rect_start = (x,y)
                self.rect_end = (x,y)
                self.dragging_edge = None
                self.update_preview_flag = False
        else:
            self.rect_start = (x,y)
            self.rect_end = (x,y)
            self.update_preview_flag = False

    def on_mouse_drag(self, event):
        x, y = event.x, event.y
        x = self.snap(x, 640)
        y = self.snap(y, 360)
        if self.dragging_edge:
            sx, sy = self.rect_start
            ex, ey = self.rect_end
            if self.dragging_edge == 'left':
                self.rect_start = (x, sy)
            elif self.dragging_edge == 'right':
                self.rect_end = (x, ey)
            elif self.dragging_edge == 'top':
                self.rect_start = (sx, y)
            elif self.dragging_edge == 'bottom':
                self.rect_end = (ex, y)
        else:
            self.rect_end = (x, y)
        self.show_frame(self.frame)

    def on_mouse_up(self, event):
        self.dragging_edge = None
        if self.frame is not None:
            w_ratio = self.frame.shape[1] / 640
            h_ratio = self.frame.shape[0] / 360
            x1 = int(self.rect_start[0] * w_ratio)
            y1 = int(self.rect_start[1] * h_ratio)
            x2 = int(self.rect_end[0] * w_ratio)
            y2 = int(self.rect_end[1] * h_ratio)
            self.crop_coords = (min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2))
            print("Crop coords:", self.crop_coords)
        self.update_preview_flag = True

    def snap(self, val, max_val):
        if abs(val) < SNAP_MARGIN:
            return 0
        elif abs(val - max_val) < SNAP_MARGIN:
            return max_val
        return val

    # ===================== Crop multi-thread =================
    def save_cropped_video(self):
        if not self.cap or not self.crop_coords:
            messagebox.showwarning("Warning", "Chưa chọn vùng crop!")
            return

        self.cap.release()
        self.cap = cv2.VideoCapture(self.video_path)
        x1, y1, x2, y2 = self.crop_coords
        width = x2 - x1
        height = y2 - y1
        fps = self.cap.get(cv2.CAP_PROP_FPS)

        save_path = filedialog.asksaveasfilename(title="Save video as", defaultextension=".mp4",
                                                 filetypes=[("MP4", "*.mp4")])
        if not save_path:
            return

        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.progress["maximum"] = total_frames

        frame_queue = queue.Queue(maxsize=50)
        stop_flag = threading.Event()

        def reader():
            for _ in range(total_frames):
                ret, frame = self.cap.read()
                if not ret:
                    break
                frame_queue.put(frame)
            stop_flag.set()

        def writer():
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(save_path, fourcc, fps, (width, height))
            count = 0
            while not stop_flag.is_set() or not frame_queue.empty():
                try:
                    frame = frame_queue.get(timeout=0.5)
                    cropped = frame[y1:y2, x1:x2]
                    out.write(cropped)
                    count += 1
                    self.progress_queue.put(count)
                except:
                    continue
            out.release()

        self.update_preview_flag = False
        t1 = threading.Thread(target=reader)
        t2 = threading.Thread(target=writer)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        messagebox.showinfo("Done", "Crop video xong!")
        self.progress["value"] = 0
        self.update_preview_flag = True
        self.update_preview()

    # ================= Update progress =====================
    def update_progress_from_queue(self):
        try:
            while True:
                value = self.progress_queue.get_nowait()
                self.progress["value"] = value
        except queue.Empty:
            pass
        self.master.after(100, self.update_progress_from_queue)

root = tk.Tk()
app = VideoCropperFastSafe(root)
root.mainloop()
