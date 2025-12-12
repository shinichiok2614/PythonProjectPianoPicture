import cv2
import tkinter as tk
from tkinter import filedialog, simpledialog
from PIL import Image, ImageTk
import os

class VideoScreenshotApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Video Screenshot")
        self.video_path = None
        self.cap = None
        self.frame_count = 0
        self.current_frame = 0

        tk.Button(master, text="Chọn video", command=self.load_video).pack()
        self.canvas = tk.Canvas(master, width=640, height=360)
        self.canvas.pack()
        self.slider = tk.Scale(master, from_=0, to=0, orient=tk.HORIZONTAL, length=600, label="Frame", command=self.update_frame)
        self.slider.pack()
        tk.Button(master, text="Lưu screenshot", command=self.save_screenshots).pack()
        self.interval_entry = tk.Entry(master)
        self.interval_entry.insert(0, "1")
        self.interval_entry.pack()
        tk.Label(master, text="Khoảng cách frame:").pack()

    def load_video(self):
        self.video_path = filedialog.askopenfilename(title="Chọn video", filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if not self.video_path:
            return
        self.cap = cv2.VideoCapture(self.video_path)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.slider.config(to=self.frame_count-1)
        self.update_frame(0)

    def update_frame(self, val):
        if not self.cap:
            return
        self.current_frame = int(val)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((640, 360))
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.create_image(0,0, anchor=tk.NW, image=self.photo)

    def save_screenshots(self):
        if not self.cap:
            return
        start = simpledialog.askinteger("Start Frame", "Nhập frame bắt đầu", minvalue=0, maxvalue=self.frame_count-1)
        end = simpledialog.askinteger("End Frame", "Nhập frame kết thúc", minvalue=0, maxvalue=self.frame_count-1)
        interval = int(self.interval_entry.get())
        folder = filedialog.askdirectory(title="Chọn folder lưu ảnh")
        if not folder:
            return

        for i in range(start, end+1, interval):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = self.cap.read()
            if ret:
                cv2.imwrite(os.path.join(folder, f"frame_{i:04d}.png"), frame)
        tk.messagebox.showinfo("Done", "Đã lưu screenshot!")

root = tk.Tk()
app = VideoScreenshotApp(root)
root.mainloop()
