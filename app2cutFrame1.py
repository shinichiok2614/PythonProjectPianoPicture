import cv2
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

class VideoScreenshotApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Video Screenshot App 2")

        self.cap = None
        self.frame = None
        self.photo = None
        self.video_path = None
        self.frame_count = 0
        self.current_frame = 0
        self.update_preview_flag = True

        self.start_frame = None
        self.end_frame = None

        # GUI
        tk.Button(master, text="Chọn video", command=self.load_video).pack()
        self.canvas = tk.Canvas(master, width=640, height=360)
        self.canvas.pack()

        self.slider = tk.Scale(master, from_=0, to=0, orient=tk.HORIZONTAL, length=640,
                               label="Frame", command=self.slider_moved)
        self.slider.pack()

        frame_buttons = tk.Frame(master)
        frame_buttons.pack(pady=5)
        tk.Button(frame_buttons, text="Set Start Frame", command=self.set_start_frame).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_buttons, text="Set End Frame", command=self.set_end_frame).pack(side=tk.LEFT, padx=5)

        tk.Label(master, text="Frame step:").pack()
        self.step_entry = tk.Entry(master)
        self.step_entry.insert(0, "1")
        self.step_entry.pack()

        tk.Button(master, text="Lưu screenshots", command=self.save_screenshots).pack(pady=10)

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

    # Preview
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

    # Set start/end frame
    def set_start_frame(self):
        self.start_frame = self.current_frame
        messagebox.showinfo("Info", f"Start frame set: {self.start_frame}")

    def set_end_frame(self):
        self.end_frame = self.current_frame
        messagebox.showinfo("Info", f"End frame set: {self.end_frame}")

    # Save screenshots
    def save_screenshots(self):
        if self.start_frame is None or self.end_frame is None:
            messagebox.showwarning("Warning", "Chưa chọn start/end frame!")
            return
        step = int(self.step_entry.get())
        folder_path = os.path.splitext(self.video_path)[0]  # same name as video
        os.makedirs(folder_path, exist_ok=True)

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)
        for frame_num in range(self.start_frame, self.end_frame + 1, step):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = self.cap.read()
            if not ret:
                break
            img_path = os.path.join(folder_path, f"frame_{frame_num:05d}.png")
            cv2.imwrite(img_path, frame)
        messagebox.showinfo("Done", f"Screenshots saved in {folder_path}")

root = tk.Tk()
app = VideoScreenshotApp(root)
root.mainloop()
