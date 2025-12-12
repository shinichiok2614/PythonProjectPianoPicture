import cv2
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

SNAP_MARGIN = 10  # khoảng cách để snap vào cạnh

class VideoCropper:
    def __init__(self, master):
        self.master = master
        self.master.title("Video Cropper with Snap & Pause")

        self.cap = None
        self.frame = None
        self.photo = None
        self.rect_start = None
        self.rect_end = None
        self.cropping = False
        self.crop_coords = None
        self.video_path = None
        self.frame_count = 0
        self.current_frame = 0
        self.update_preview_flag = True

        # GUI
        tk.Button(master, text="Chọn video", command=self.load_video).pack()
        self.canvas = tk.Canvas(master, width=640, height=360)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.draw_crop)
        self.canvas.bind("<ButtonRelease-1>", self.end_crop)

        self.slider = tk.Scale(master, from_=0, to=0, orient=tk.HORIZONTAL, length=640,
                               label="Frame", command=self.slider_moved)
        self.slider.pack()

        self.progress = ttk.Progressbar(master, orient="horizontal", length=640, mode="determinate")
        self.progress.pack(pady=5)

        tk.Button(master, text="Crop và lưu video", command=self.save_cropped_video).pack(pady=10)

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

    # Hiển thị frame trên canvas
    def show_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img.thumbnail((640,360))
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(0,0, anchor=tk.NW, image=self.photo)
        # Vẽ crop rectangle nếu đã chọn
        if self.rect_start and self.rect_end:
            self.canvas.create_rectangle(self.rect_start[0], self.rect_start[1],
                                         self.rect_end[0], self.rect_end[1],
                                         outline="red", width=2, tag="rect")

    # Slider kéo
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

    # Bắt đầu crop: pause video
    def start_crop(self, event):
        self.rect_start = (event.x, event.y)
        self.cropping = True
        self.update_preview_flag = False  # pause video

    # Vẽ rectangle khi kéo, snap nếu gần cạnh
    def draw_crop(self, event):
        if self.cropping:
            x, y = event.x, event.y
            # Snap vào các cạnh canvas
            if abs(x) < SNAP_MARGIN:
                x = 0
            elif abs(x - 640) < SNAP_MARGIN:
                x = 640
            if abs(y) < SNAP_MARGIN:
                y = 0
            elif abs(y - 360) < SNAP_MARGIN:
                y = 360
            self.rect_end = (x, y)
            self.canvas.delete("rect")
            self.canvas.create_rectangle(self.rect_start[0], self.rect_start[1],
                                         self.rect_end[0], self.rect_end[1],
                                         outline="red", width=2, tag="rect")

    # Kết thúc crop: resume video
    def end_crop(self, event):
        self.cropping = False
        x, y = event.x, event.y
        # Snap cuối cùng
        if abs(x) < SNAP_MARGIN:
            x = 0
        elif abs(x - 640) < SNAP_MARGIN:
            x = 640
        if abs(y) < SNAP_MARGIN:
            y = 0
        elif abs(y - 360) < SNAP_MARGIN:
            y = 360
        self.rect_end = (x, y)
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

    # Lưu video crop
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
app = VideoCropper(root)
root.mainloop()
