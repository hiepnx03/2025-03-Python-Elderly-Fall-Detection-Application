from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QPixmap
import cv2
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import datetime
import sys
from threading import Thread

class EcranWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.cap = None
        self.fgbg = cv2.createBackgroundSubtractorMOG2(history=9000, varThreshold=100, detectShadows=True)
        self.j, self.sol, self.chute = 0, 0, False

    def setup_ui(self):
        self.setWindowTitle("Phát hiện ngã")
        self.setFixedSize(1080, 720)
        self.setWindowIcon(QtGui.QIcon("security-camera.png"))

        self.ecran = QtWidgets.QLabel(self)
        self.ecran.setGeometry(QtCore.QRect(20, 20, 751, 451))
        self.ecran.setScaledContents(True)

        self.ecran_2 = QtWidgets.QLabel(self)
        self.ecran_2.setGeometry(QtCore.QRect(20, 480, 351, 81))
        self.ecran_2.setScaledContents(True)

        self.ecran_3 = QtWidgets.QLabel(self)
        self.ecran_3.setGeometry(QtCore.QRect(400, 480, 371, 81))
        self.ecran_3.setScaledContents(True)

        self.afficher = QtWidgets.QPushButton("Bat dau", self)
        self.afficher.setGeometry(QtCore.QRect(20, 560, 93, 28))
        self.afficher.clicked.connect(self.start_camera)

        self.arreter = QtWidgets.QPushButton("Thoat", self)
        self.arreter.setGeometry(QtCore.QRect(160, 560, 93, 28))
        self.arreter.clicked.connect(self.fermer)

    def start_camera(self):
        # self.cap = cv2.VideoCapture("chute1.mp4")  # Hoặc sử dụng camera: cv2.VideoCapture(0)
        # self.cap = cv2.VideoCapture(0)  # Hoặc sử dụng camera: cv2.VideoCapture(0)
        self.cap = cv2.VideoCapture("http://9.237.103.201:8080/video")

        self.timer.start(30)  # Cập nhật frame mỗi 30ms

    def update_frame(self):
        ret, frame1 = self.cap.read()
        if not ret:
            self.timer.stop()
            return

        gray = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        fgmask = self.fgbg.apply(gray)
        self.displayimage1(fgmask, 2)

        fgmask = cv2.GaussianBlur(cv2.blur(fgmask, (5, 5)), (5, 5), 2)
        self.displayimage1(fgmask, 3)

        contours, _ = cv2.findContours(fgmask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            cnt = max(contours, key=cv2.contourArea)
            if cv2.contourArea(cnt) < 5000:
                self.displayimage(frame1)
                return

            x, y, w, h = cv2.boundingRect(cnt)
            if y + h > self.sol:
                self.sol = y + h
                print(f"Vị trí mặt đất được cập nhật: {self.sol}")

            cv2.line(frame1, (0, self.sol), (frame1.shape[1], self.sol), (0, 255, 0), 2)
            if self.sol + 500 < frame1.shape[0]:
                cv2.line(frame1, (0, self.sol + 500), (frame1.shape[1], self.sol + 500), (500, 0, 0), 2)
            else:
                cv2.line(frame1, (0, frame1.shape[0] - 500), (frame1.shape[1], frame1.shape[0] - 500), (500, 0, 0), 2)

            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = 0, 0

            if h > w:
                self.j = 0
                cv2.putText(frame1, 'CHUYEN DONG', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (255, 255, 255), 1)
                cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.circle(frame1, (cx, cy), 7, (255, 255, 255), -1)
            else:
                self.j += 1
                cv2.putText(frame1, '', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (255, 255, 255), 1)
                cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 255), 2)
                cv2.circle(frame1, (cx, cy), 7, (255, 255, 255), -1)

            if self.j > 60 and self.sol - cy < 200:
                print("sol - cy < 200 ", self.sol, "-", cy, "=", self.sol - cy)
                print("j: ", self.j)
                print("== PHAT HIEN NGA ==")
                self.chute = True
                cv2.putText(frame1, 'PHAT HIEN NGA', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (255, 255, 255), 1)
                cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 0, 255), 2)

        self.displayimage(frame1)

        if self.chute:
            self.send_email()
            self.chute = False

    def send_email(self):
        try:
            msg = MIMEMultipart()
            msg['From'] = "testheva@gmail.com"
            msg['To'] = "hiepnx03@gmail.com"
            msg['Subject'] = "CẢNH BÁO"
            body = f"Loại => loại: Ngã Tại Tầng 2. {datetime.datetime.now()}"
            msg.attach(MIMEText(body, 'html'))

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
        self.ecran.setPixmap(
            QPixmap.fromImage(QImage(img, img.shape[1], img.shape[0], QImage.Format_RGB888).rgbSwapped()))

    def displayimage1(self, img, x):
        target = self.ecran_2 if x == 2 else self.ecran_3
        target.setPixmap(QPixmap.fromImage(QImage(img, img.shape[1], img.shape[0], QImage.Format_Grayscale8)))

    def fermer(self):
        if QtWidgets.QMessageBox.question(self, "Thoát",
                                          "Bạn có muốn đóng ứng dụng không?") == QtWidgets.QMessageBox.Yes:
            self.timer.stop()
            if self.cap:
                self.cap.release()
            self.close()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    widget = EcranWindow()
    widget.show()
    sys.exit(app.exec_())