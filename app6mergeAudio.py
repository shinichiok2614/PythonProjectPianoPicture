import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os

class AudioMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gắn lại âm thanh cho video")

        self.video_with_audio = None
        self.video_no_audio = None

        tk.Button(root, text="Chọn video GỐC (có âm thanh)",
                  width=40, command=self.select_video_with_audio).pack(pady=5)

        tk.Button(root, text="Chọn video CROP (thiếu âm thanh)",
                  width=40, command=self.select_video_no_audio).pack(pady=5)

        tk.Button(root, text="GẮN LẠI ÂM THANH",
                  width=40, height=2, command=self.merge_audio).pack(pady=15)

        self.status = tk.Label(root, text="Chưa chọn file", fg="blue")
        self.status.pack(pady=5)

    def select_video_with_audio(self):
        path = filedialog.askopenfilename(
            title="Chọn video có âm thanh",
            filetypes=[("Video files", "*.mp4 *.avi *.mov")]
        )
        if path:
            self.video_with_audio = path
            self.status.config(text="✔ Đã chọn video có âm thanh")

    def select_video_no_audio(self):
        path = filedialog.askopenfilename(
            title="Chọn video thiếu âm thanh",
            filetypes=[("Video files", "*.mp4 *.avi *.mov")]
        )
        if path:
            self.video_no_audio = path
            self.status.config(text="✔ Đã chọn video thiếu âm thanh")

    def merge_audio(self):
        if not self.video_with_audio or not self.video_no_audio:
            messagebox.showwarning("Thiếu file", "Hãy chọn đủ 2 video")
            return

        save_path = filedialog.asksaveasfilename(
            title="Lưu video sau khi gắn âm thanh",
            defaultextension=".mp4",
            filetypes=[("MP4", "*.mp4")]
        )
        if not save_path:
            return

        cmd = [
            "ffmpeg",
            "-y",
            "-i", self.video_no_audio,
            "-i", self.video_with_audio,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "copy",
            save_path
        ]

        try:
            subprocess.run(cmd, check=True)
            messagebox.showinfo("Hoàn tất", "🎉 Gắn âm thanh thành công!")
            self.status.config(text="✅ Hoàn tất", fg="green")
        except Exception as e:
            messagebox.showerror("Lỗi", f"FFmpeg lỗi:\n{e}")
            self.status.config(text="❌ Lỗi", fg="red")


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("420x220")
    app = AudioMergerApp(root)
    root.mainloop()
