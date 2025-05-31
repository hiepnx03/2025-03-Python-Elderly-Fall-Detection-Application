import threading
import cv2
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from playsound import playsound
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from PIL import ImageFont, ImageDraw, Image
import numpy as np
from ecran import Ui_Form
import os



cv2.setNumThreads(8)  # Tăng số luồng xử lý của OpenCV lên 8 (số luồng của máy bạn)

class EcranWindow(QtWidgets.QWidget, Ui_Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setFixedWidth(795)
        self.setFixedHeight(590)
        self.setWindowIcon(QtGui.QIcon("security-camera.png"))
        self.ui.afficher.clicked.connect(self.affichage)
        self.ui.arreter.clicked.connect(self.fermer)

        # Timer to periodically update the image
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_image)
        self.timer.start(30)  # Update every 30ms (approx. 33fps)

    def update_image(self):
        """Update the image on the UI every 30ms."""
        if hasattr(self, 'frame'):  # Check if frame exists
            self.displayimage(self.frame)

    def draw_vietnamese_text(self, image, text, position, font_path="Roboto-Regular.ttf", font_size=32,
                             color=(255, 255, 255)):
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        font = ImageFont.truetype(font_path, font_size)
        draw = ImageDraw.Draw(pil_image)
        draw.text(position, text, font=font, fill=color)
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def send_email(self, chute=True):
        if chute:
            try:
                dateTimeNow = datetime.datetime.now()
                msg = MIMEMultipart()
                msg['From'] = "testheva@gmail.com"
                msg['To'] = "hiepnx03@gmail.com"
                password = "qcix unak alaj nlsi"
                msg['Subject'] = "CẢNH BÁO"
                body = "Phát hiện ngã tại vị trí: Nhà. Vào lúc: " + str(dateTimeNow)
                msg.attach(MIMEText(body, 'html'))

                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(msg['From'], password)
                print("Đăng nhập thành công")
                server.sendmail(msg['From'], msg['To'], msg.as_string())
                server.quit()
                print("Email đã được gửi!")
                QtWidgets.QMessageBox.information(self, "Thông báo", "Đã gửi email cảnh báo về việc phát hiện ngã!")
            except Exception as e:
                print(f"Lỗi: Không thể gửi email! {e}")
                QtWidgets.QMessageBox.warning(self, "Cảnh báo", "Không thể gửi email cảnh báo!")
        else:
            print("Không phát hiện ngã.")

    def affichage(self):
        def process_video():
            cap = cv2.VideoCapture(0)  # Use default webcam
            # cap = cv2.VideoCapture("http://9.49.179.37:8080/video")  # Sử dụng camera điện thoại

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Reduce width to 640
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Reduce height to 480

            if not cap.isOpened():
                QtWidgets.QMessageBox.warning(self, "Cảnh báo", "Không thể mở camera!")
                return

            # Lấy kích thước video
            vh = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            vl = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            print("Chiều cao: " + str(vh))
            print("Chiều rộng: " + str(vl))

            # Trừ nền ảnh
            fgbg = cv2.createBackgroundSubtractorMOG2(history=9000, varThreshold=100, detectShadows=True)

            prev_time = time.time()  # Lưu thời gian ban đầu để tính FPS
            frame_count = 0  # Đếm số khung hình đã xử lý
            j = 0
            sol = 0
            chute = False

            while True:
                ret, frame1 = cap.read()
                ret, frame2 = cap.read()
                if not ret:
                    print("Không thể đọc khung hình!")
                    break  # If frame is not read, break the loop

                try:
                    # Đếm số khung hình và tính FPS
                    frame_count += 1
                    current_time = time.time()
                    time_diff = current_time - prev_time

                    if time_diff >= 1:  # Sau mỗi giây
                        fps = frame_count / time_diff
                        # print(f"FPS: {fps:.2f}")  # In ra FPS
                        frame_count = 0  # Đặt lại số khung hình đã xử lý
                        prev_time = current_time  # Cập nhật thời gian

                    # Xử lý các khung hình ở đây...
                    gray = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
                    fgmask = fgbg.apply(gray)
                    fgmask = cv2.blur(fgmask, (5, 5))
                    fgmask = cv2.GaussianBlur(fgmask, (5, 5), 2)

                    contours, _ = cv2.findContours(fgmask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                    if contours:
                        areas = [cv2.contourArea(c) for c in contours]
                        max_area = max(areas, default=0)
                        max_area_index = areas.index(max_area)
                        cnt = contours[max_area_index]

                        M = cv2.moments(cnt)
                        x, y, w, h = cv2.boundingRect(cnt)

                        # Calculate the center position along the y-axis
                        cy = y + h // 2  # Center y of the object

                        if y + h != vh:
                            if sol < y + h:
                                sol = y + h

                        if cv2.contourArea(cnt) < 5000:
                            continue

                        cv2.drawContours(fgmask, [cnt], 0, (255, 255, 255), 3, maxLevel=0)

                        if h > w:
                            j = 0
                            cv2.putText(frame1, 'CHUYEN DONG', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (255, 255, 255),1)
                            cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            # print("CHUYỂN ĐỘNG")

                        if h < w:
                            j += 1
                            cv2.putText(frame1, '??????????', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (255, 255, 255), 1)
                            cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 255), 2)
                            # print("?????????")

                        if j > 20:
                            if (sol - cy < 200):
                                chute = True
                                cv2.putText(frame1, 'PHAT HIEN NGA', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.75,(255, 255, 255), 1)
                                cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 0, 255), 2)
                                print("PHAT HIEN NGA")
                    self.frame = frame1  # Store the current frame to display
                    frame1 = frame2

                    if cv2.waitKey(33) == 27:  # Press 'ESC' to exit
                        break
                except Exception as e:
                    break

            cap.release()

            if chute:
                self.send_email(chute=True)

        # Run video processing in a separate thread
        video_thread = threading.Thread(target=process_video)
        video_thread.daemon = True
        video_thread.start()

    def displayimage(self, img, window=1):
        """Displays an image on the UI."""
        qformat = QImage.Format_RGB888
        img = QImage(img, img.shape[1], img.shape[0], qformat)
        img = img.rgbSwapped()
        self.ui.ecran.setPixmap(QPixmap.fromImage(img))
        self.ui.ecran.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

    def fermer(self):
        """Handles application exit."""
        ret = QtWidgets.QMessageBox.question(self, "Thoát", "Bạn có muốn đóng ứng dụng không?")
        if ret == QtWidgets.QMessageBox.Yes:
            self.ui.cap.release()
            app.exit()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    widget = EcranWindow()
    widget.show()
    app.exec_()
