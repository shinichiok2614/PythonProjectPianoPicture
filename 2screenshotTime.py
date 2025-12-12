import cv2

def capture_frame_at_time(video_path, time_sec, output_path="frame.jpg"):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("❌ Không mở được video:", video_path)
        return

    fps = cap.get(cv2.CAP_PROP_FPS)            # lấy FPS
    frame_index = int(fps * time_sec)          # tính frame cần nhảy đến

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)  # nhảy đến frame

    ret, frame = cap.read()
    if not ret:
        print("❌ Không lấy được frame tại thời điểm", time_sec)
        return

    cv2.imwrite(output_path, frame)
    print("✔ Đã lưu ảnh:", output_path)

    cap.release()

# Ví dụ: lấy ảnh lúc 3.5 giây
capture_frame_at_time("video.mp4", 35, "frame_3_5s.jpg")
