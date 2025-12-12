def save_image(self):
    if self.current_image_preview is None:
        self.preview_lines()
    # Ghi đè lên cùng tên ảnh gốc
    if self.current_image_cv is not None:
        # Lấy tên ảnh gốc
        original_name = self.image_list[self.listbox.curselection()[0]]
        save_path = os.path.join(self.folder_path, original_name)
        cv2.imwrite(save_path, self.current_image_preview)
        messagebox.showinfo("Done", f"Ảnh đã lưu và ghi đè: {save_path}")
