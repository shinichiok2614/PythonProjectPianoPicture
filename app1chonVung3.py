import cv2
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

SNAP_MARGIN = 10  # Khoảng cách snap vào cạnh canvas
EDGE_MARGIN = 8   # Khoảng cách để bắt viền rectangle

class VideoCropperAdvanced:
    def __init__(self, master):
        self.master = master
        self.master.title("Video Cropper Advanced")

        self.cap = None
        self.frame = None
        self.photo = None
        self.rect_start = None
        self.rect_end = None
        self.crop_coords = None
        self.dragging_edge = None  # None, 'left','right','top','bottom'
        self.video_path = None
        self.frame_count = 0
        self.current_frame = 0
        self.update_preview_flag = True

        # GUI
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

        # Key bindings
        self.master.bind("<Left>", lambda e: self.move_slider(-10))
        self.master.bind("<Right>", lambda e: self.move_slider(10))

    # Load video
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

    # Preview video
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

    # Show frame
    def show_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img.thumbnail((640,360))
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(0,0, anchor=tk.NW, image=self.photo)
        # Draw bounding box
        if self.rect_start and self.rect_end:
            self.canvas.create_rectangle(self.rect_start[0], self.rect_start[1],
                                         self.rect_end[0], self.rect_end[1],
                                         outline="red", width=2, tag="rect")

    # Slider
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

    # Mouse down: start crop hoặc bắt viền
    def on_mouse_down(self, event):
        x, y = event.x, event.y
        if self.rect_start and self.rect_end:
            # Kiểm tra gần viền để drag
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
                self.update_preview_flag = False  # pause video
        else:
            self.rect_start = (x,y)
            self.rect_end = (x,y)
            self.update_preview_flag = False

    # Mouse drag
    def on_mouse_drag(self, event):
        x, y = event.x, event.y
        # Snap vào cạnh canvas
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

    # Mouse up
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
        self.update_preview_flag = True  # resume video

    # Snap
    def snap(self, val, max_val):
        if abs(val) < SNAP_MARGIN:
            return 0
        elif abs(val - max_val) < SNAP_MARGIN:
            return max_val
        return val

    # Save cropped video
    def save_cropped_video(self):
        if not self.cap or not self.crop_coords:
            messagebox.showwarning("Warning", "Chưa chọn vùng crop!")
            return

        self.cap.release()
        self.cap = cv2.VideoCapture(self.video_path)
        x1,y1,x2,y2 = self.crop_coords
        width = x2 - x1
        height = y2 - y1
        fps = self.cap.get(cv2.CAP_PROP_FPS)

        save_path = filedialog.asksaveasfilename(title="Save video as", defaultextension=".mp4",
                                                 filetypes=[("MP4", "*.mp4")])
        if not save_path:
            return

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(save_path, fourcc, fps, (width, height))
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.progress["maximum"] = total_frames

        for i in range(total_frames):
            ret, frame = self.cap.read()
            if not ret:
                break
            cropped = frame[y1:y2, x1:x2]
            out.write(cropped)
            self.progress["value"] = i+1
            self.master.update_idletasks()

        self.cap.release()
        out.release()
        messagebox.showinfo("Done", "Crop video xong!")
        self.progress["value"] = 0
        self.update_preview_flag = True
        self.update_preview()

root = tk.Tk()
app = VideoCropperAdvanced(root)
root.mainloop()
