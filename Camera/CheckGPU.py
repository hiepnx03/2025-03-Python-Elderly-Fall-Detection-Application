import cv2
import numpy as np

# Kiểm tra xem GPU có sẵn hay không
if cv2.cuda.getCudaEnabledDeviceCount() > 0:
    print("CUDA is enabled. Using GPU.")
else:
    print("CUDA is not available. Using CPU.")

# Mở video từ camera
cap = cv2.VideoCapture(0)

# Thiết lập độ phân giải video thấp hơn
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # Chuyển đổi frame sang ảnh xám
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Chuyển ảnh xám lên GPU
    gpu_frame = cv2.cuda_GpuMat()
    gpu_frame.upload(gray_frame)

    # Áp dụng GaussianBlur trên GPU
    gpu_blur = cv2.cuda.createGaussianFilter(cv2.CV_8UC1, -1, (5, 5))
    gpu_frame_blurred = gpu_blur.apply(gpu_frame)

    # Tải ảnh đã xử lý trở lại CPU
    blurred_frame = gpu_frame_blurred.download()

    # Hiển thị ảnh đã xử lý
    cv2.imshow("Blurred Frame", blurred_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
