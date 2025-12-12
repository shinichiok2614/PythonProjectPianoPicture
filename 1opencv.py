import cv2
import numpy as np

def merge_vertical(img1_path, img2_path, output_path="merged.jpg"):
    # Đọc ảnh
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    # Lấy chiều rộng nhỏ nhất để resize cho khớp
    width = min(img1.shape[1], img2.shape[1])

    # Resize 2 ảnh về cùng chiều rộng
    img1_resized = cv2.resize(img1, (width, int(img1.shape[0] * width / img1.shape[1])))
    img2_resized = cv2.resize(img2, (width, int(img2.shape[0] * width / img2.shape[1])))

    # Ghép dọc
    merged = np.vstack((img1_resized, img2_resized))

    # Lưu ảnh
    cv2.imwrite(output_path, merged)
    print(f"Đã lưu ảnh ghép: {output_path}")

# Ví dụ sử dụng
merge_vertical("a.png", "b.png", "output.jpg")
