import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class VideoCropper:
    def __init__(self, master):
        self.master = master
        self.master.title("Video Cropper with Preview")

        self.cap = None
        self.frame = None
        self.photo = None
        self.rect_start = None
        self.rect_end = None
        self.cropping = False
        self.crop_coords = None

        # GUI
        tk.Button(master, text="Chọn video", command=self.load_video).pack()
        self.canvas = tk.Canvas(master, width=640, height=360)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.draw_crop)
        self.canvas.bind("<ButtonRelease-1>", self.end_crop)
        tk.Button(master, text="Crop và lưu video", command=self.save_cropped_video).pack(pady=10)

    def load_video(self):
        path = filedialog.askopenfilename(title="Chọn video", filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if not path:
            return
        self.cap = cv2.VideoCapture(path)
        self.video_path = path
        self.play_video()

    def play_video(self):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if ret:
            self.frame = frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img.thumbnail((640,360))
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.create_image(0,0, anchor=tk.NW, image=self.photo)
        self.master.after(30, self.play_video)  # khoảng 30ms ~ 33fps

    # Bắt đầu crop
    def start_crop(self, event):
        self.rect_start = (event.x, event.y)
        self.cropping = True

    # Vẽ rectangle
    def draw_crop(self, event):
        if self.cropping:
            self.rect_end = (event.x, event.y)
            self.canvas.delete("rect")
            self.canvas.create_rectangle(self.rect_start[0], self.rect_start[1],
                                         self.rect_end[0], self.rect_end[1],
                                         outline="red", width=2, tag="rect")

    # Kết thúc crop
    def end_crop(self, event):
        self.rect_end = (event.x, event.y)
        self.cropping = False
        # Lưu crop coords theo tỉ lệ video gốc
        if self.frame is not None:
            w_ratio = self.frame.shape[1] / 640
            h_ratio = self.frame.shape[0] / 360
            x1 = int(self.rect_start[0] * w_ratio)
            y1 = int(self.rect_start[1] * h_ratio)
            x2 = int(self.rect_end[0] * w_ratio)
            y2 = int(self.rect_end[1] * h_ratio)
            self.crop_coords = (min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2))
            print("Crop coords:", self.crop_coords)

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

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            cropped = frame[y1:y2, x1:x2]
            out.write(cropped)

        self.cap.release()
        out.release()
        messagebox.showinfo("Done", "Crop video xong!")

root = tk.Tk()
app = VideoCropper(root)
root.mainloop()
