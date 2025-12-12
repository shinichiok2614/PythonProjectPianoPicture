import cv2
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

def crop_video():
    filepath = filedialog.askopenfilename(title="Chọn video", filetypes=[("Video files", "*.mp4 *.avi *.mov")])
    if not filepath:
        return

    cap = cv2.VideoCapture(filepath)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Nhập crop
    left = simpledialog.askinteger("Crop", "Left (px):", minvalue=0, maxvalue=width)
    right = simpledialog.askinteger("Crop", "Right (px):", minvalue=0, maxvalue=width)
    top = simpledialog.askinteger("Crop", "Top (px):", minvalue=0, maxvalue=height)
    bottom = simpledialog.askinteger("Crop", "Bottom (px):", minvalue=0, maxvalue=height)

    output_path = filedialog.asksaveasfilename(title="Save video as", defaultextension=".mp4", filetypes=[("MP4", "*.mp4")])
    if not output_path:
        return

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (right-left, bottom-top))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cropped = frame[top:bottom, left:right]
        out.write(cropped)

    cap.release()
    out.release()
    messagebox.showinfo("Done", "Crop video xong!")

root = tk.Tk()
root.title("Video Cropper")
tk.Button(root, text="Chọn Video và Crop", command=crop_video, width=30, height=2).pack(pady=20)
root.mainloop()
