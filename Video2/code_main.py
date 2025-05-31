from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QPixmap
import cv2
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import datetime
import time

from playsound import playsound


class EcranWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()  # Thiết lập giao diện người dùng

    def setup_ui(self):
        # Thiết lập kích thước cửa sổ và biểu tượng
        self.setWindowTitle("Phát hiện ngã")
        self.setFixedSize(1080, 720)
        self.setWindowIcon(QtGui.QIcon("security-camera.png"))

        # Tạo các label để hiển thị video và các khung hình xử lý
        self.ecran = QtWidgets.QLabel(self)
        self.ecran.setGeometry(QtCore.QRect(20, 20, 751, 451))
        self.ecran.setScaledContents(True)

        self.ecran_2 = QtWidgets.QLabel(self)
        self.ecran_2.setGeometry(QtCore.QRect(20, 480, 351, 81))
        self.ecran_2.setScaledContents(True)

        self.ecran_3 = QtWidgets.QLabel(self)
        self.ecran_3.setGeometry(QtCore.QRect(400, 480, 371, 81))
        self.ecran_3.setScaledContents(True)

        # Tạo nút "Bắt đầu" và kết nối sự kiện click
        self.afficher = QtWidgets.QPushButton("Bat dau", self)
        self.afficher.setGeometry(QtCore.QRect(20, 560, 93, 28))
        self.afficher.clicked.connect(self.affichage)

        # Tạo nút "Thoát" và kết nối sự kiện click
        self.arreter = QtWidgets.QPushButton("Thoat", self)
        self.arreter.setGeometry(QtCore.QRect(160, 560, 93, 28))
        self.arreter.clicked.connect(self.fermer)

    def affichage(self):
        # Mở video từ file hoặc camera
        # cap = cv2.VideoCapture(0)
        cap = cv2.VideoCapture("chute1.mp4")

        # Tính toán FPS
        fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"FPS của video: {fps}")

        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"Height of picture: {height}")

        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        print(f"Width of picture: {width}")

        # Khởi tạo bộ trừ nền để phát hiện chuyển động
        fgbg = cv2.createBackgroundSubtractorMOG2(history=9000, varThreshold=100, detectShadows=True)
        j, sol, chute = 0, 0, False  # Khởi tạo các biến để theo dõi trạng thái

        while True:
            ret, frame1 = cap.read()
            if not ret: break  # Thoát nếu không đọc được frame

            # Chuyển đổi frame sang ảnh xám và áp dụng bộ trừ nền
            gray = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            fgmask = fgbg.apply(gray)
            self.displayimage1(fgmask, 2)  # Hiển thị ảnh xám đã trừ nền

            # Làm mờ ảnh để giảm nhiễu
            fgmask = cv2.GaussianBlur(cv2.blur(fgmask, (5, 5)), (5, 5), 2)
            self.displayimage1(fgmask, 3)  # Hiển thị ảnh đã làm mờ

            # Tìm các đường viền trong ảnh
            contours, _ = cv2.findContours(fgmask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                cnt = max(contours, key=cv2.contourArea)  # Lấy đường viền lớn nhất
                if cv2.contourArea(cnt) < 5000: continue  # Bỏ qua các vật thể quá nhỏ

                x, y, w, h = cv2.boundingRect(cnt)  # Lấy tọa độ hình chữ nhật bao quanh vật thể

                # Cập nhật vị trí mặt đất (sol) nếu điểm dưới cùng của vật thể thấp hơn sol hiện tại
                if y + h > sol:
                    sol = y + h
                    print(f"Vị trí mặt đất được cập nhật: {sol}")

                # Vẽ đường kẻ mặt đất tại sol
                cv2.line(frame1, (0, sol), (frame1.shape[1], sol), (0, 255, 0), 2)  # Đường màu xanh lá cây

                # Kiểm tra lại vị trí đường kẻ sao cho nó nằm trong phạm vi của ảnh
                if sol + 200 < frame1.shape[0]:  # Kiểm tra nếu đường kẻ nằm trong phạm vi của ảnh
                    cv2.line(frame1, (0, sol + 200), (frame1.shape[1], sol + 200), (255, 0, 0), 2)  # Đường màu đỏ
                else:
                    # Điều chỉnh lại vị trí nếu nó vượt quá chiều cao ảnh
                    cv2.line(frame1, (0, frame1.shape[0] - 200), (frame1.shape[1], frame1.shape[0] - 200), (255, 0, 0), 2)

                # Tính toán trọng tâm của vật thể
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                else:
                    cx, cy = 0, 0

                if h > w:  # Nếu vật thể đứng
                    j = 0
                    cv2.putText(frame1, 'CHUYEN DONG', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (255, 255, 255), 1)
                    cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.circle(frame1, (cx, cy), 7, (255, 255, 255), -1)

                else:  # Nếu vật thể nằm ngang (có thể là ngã)
                    j += 1
                    cv2.putText(frame1, '', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (255, 255, 255), 1)
                    cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 255), 2)
                    cv2.circle(frame1, (cx, cy), 7, (255, 255, 255), -1)
                    # Ngưỡng = fps (1 giây) để kích hoạt cảnh báo

                if j > 60 and sol - cy < 200:  # Kiểm tra điều kiện ngã
                    print("sol - cy < 200 " , sol ,"-",cy , "=", sol-cy)
                    print("j: ", j)
                    # print(f"Trọng tâm của vật thể: ({cx}, {cy})")
                    print("== PHAT HIEN NGA ==")
                    chute = True
                    cv2.putText(frame1, 'PHAT HIEN NGA', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (255, 255, 255), 1)
                    cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 0, 255), 2)

            self.displayimage(frame1)  # Hiển thị frame gốc

            if cv2.waitKey(5) == 27: break  # Thoát nếu nhấn phím ESC

        if chute: self.send_email()  # Gửi email nếu phát hiện ngã
        cap.release()  # Giải phóng camera

    def send_email(self):
        try:
            # Tạo email cảnh báo
            msg = MIMEMultipart()
            msg['From'] = "testheva@gmail.com"
            msg['To'] = "hiepnx03@gmail.com"
            msg['Subject'] = "CẢNH BÁO"
            body = f"Loại => loại: Ngã Tại Tầng 2. {datetime.datetime.now()}"
            msg.attach(MIMEText(body, 'html'))

            # Gửi email qua SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(msg['From'], "qcix unak alaj nlsi")
            server.sendmail(msg['From'], msg['To'], msg.as_string())
            server.quit()

            QtWidgets.QMessageBox.information(self, "Information", "Email được gửi để báo cáo về vụ ngã !")
            print("Email được gửi để báo cáo về vụ ngã !")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Cảnh báo", f"Email không được gửi! {e}")

    def displayimage(self, img):
        # Hiển thị ảnh màu lên label chính
        self.ecran.setPixmap(
            QPixmap.fromImage(QImage(img, img.shape[1], img.shape[0], QImage.Format_RGB888).rgbSwapped()))

    def displayimage1(self, img, x):
        # Hiển thị ảnh xám lên label phụ (ecran_2 hoặc ecran_3)
        target = self.ecran_2 if x == 2 else self.ecran_3
        target.setPixmap(QPixmap.fromImage(QImage(img, img.shape[1], img.shape[0], QImage.Format_Grayscale8)))

    def fermer(self):
        # Hiển thị hộp thoại xác nhận khi đóng ứng dụng
        if QtWidgets.QMessageBox.question(self, "Thoát",
                                          "Bạn có muốn đóng ứng dụng không?") == QtWidgets.QMessageBox.Yes:
            self.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    widget = EcranWindow()
    widget.show()
    app.exec_()
