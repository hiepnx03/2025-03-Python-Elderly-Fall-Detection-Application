from ecran import Ui_Form

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage,QPixmap
import cv2
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import datetime

class EcranWindow(QtWidgets.QWidget,Ui_Form):
    def __init__(self, *args,**kwargs):
        super().__init__(*args, **kwargs)

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setFixedWidth(795)
        self.setFixedHeight(590)
        self.setWindowIcon(QtGui.QIcon("security-camera.png"))
        self.ui.afficher.clicked.connect(self.affichage)
        self.ui.arreter.clicked.connect(self.fermer)

    def affichage(self):
        # Sử dụng camera điện thoại thông qua địa chỉ IP

        cap = cv2.VideoCapture("chute1.mp4")
        # self.cap = cv2.VideoCapture("http://192.168.0.181:8080/video")
        # cap = cv2.VideoCapture(0)

        # Lấy kích thước video
        vh = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        vl = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        print(" Chiều cao : " + str(vh))
        print(" Chiều rộng : " + str(vl))
        print(" Mặt đất : ")

        # Trừ hình ảnh khỏi nền
        fgbg = cv2.createBackgroundSubtractorMOG2(history=9000, varThreshold=100, detectShadows=True)

        j = 0
        sol = 0
        chute = False

        # Lặp lại để phát video từng khung hình
        while True:
            ret, frame1 = cap.read()
            if not ret:
                break  # Nếu không đọc được frame, thoát khỏi vòng lặp

            ret, frame2 = cap.read()
            if not ret:
                break

            # Chuyển đổi từng khung hình sang đen trắng để việc trừ nền dễ dàng hơn
            try:
                gray = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
                fgmask = fgbg.apply(gray)
                self.displayimage1(fgmask, 1, 2)

                fgmask = cv2.blur(fgmask, (5, 5))
                fgmask = cv2.GaussianBlur(fgmask, (5, 5), 2)
                self.displayimage1(fgmask, 1, 3)

                # Tìm đường đồng mức
                contours, _ = cv2.findContours(fgmask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                if contours:
                    # Một danh sách chứa tất cả các vùng (khu vực)
                    areas = []

                    for contour in contours:
                        # Tính diện tích đường đồng mức
                        ar = cv2.contourArea(contour)
                        areas.append(ar)

                    # Xác định bề mặt lớn nhất
                    max_area = max(areas, default=0)
                    max_area_index = areas.index(max_area)
                    cnt = contours[max_area_index]

                    # Khoảnh khắc để tính toán trọng tâm
                    M = cv2.moments(cnt)

                    # Lấy tọa độ của hình chữ nhật
                    x, y, w, h = cv2.boundingRect(cnt)
                    if y + h != vh:
                        if sol < y + h:
                            sol = y + h
                            print(sol)

                    # Bỏ qua những vật thể quá nhỏ
                    if cv2.contourArea(cnt) < 5000:
                        continue

                    # Vẽ đường viền
                    cv2.drawContours(fgmask, [cnt], 0, (255, 255, 255), 3, maxLevel=0)

                    # Phát hiện ngã nếu chiều cao đường viền < chiều rộng
                    if h > w:
                        j = 0
                        cv2.putText(frame1, 'CHUYEN DONG', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (255, 255, 255), 1)
                        cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                        else:
                            cx, cy = 0, 0
                        cv2.circle(frame1, (cx, cy), 7, (255, 255, 255), -1)

                    if h < w:
                        j += 1
                        cv2.putText(frame1, '', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (255, 255, 255), 1)
                        cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 255), 2)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                        else:
                            cx, cy = 0, 0
                        cv2.circle(frame1, (cx, cy), 7, (255, 255, 255), -1)

                    # Ngưỡng = 60 (5 giây) để kích hoạt cảnh báo
                    if j > 60:
                        if sol - cy < 80:
                            print("== FALL ==")
                            chute = True
                            cv2.putText(frame1, 'PHAT HIEN NGA', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.75,
                                        (255, 255, 255), 1)
                            cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 0, 255), 2)

                    # Hiển thị frame màu nguyên bản
                    self.displayimage(frame1, 1)

                    if cv2.waitKey(33) == 27:
                        break
            except Exception as e:
                print(f"Erreur: {e}")
                break

        # Gửi email nếu phát hiện chute
        try:
            if chute:
                dateTimeNow = datetime.datetime.now()
                msg = MIMEMultipart()
                msg['From'] = "testheva@gmail.com"
                msg['To'] = "hiepnx03@gmail.com"
                password = "qcix unak alaj nlsi"
                msg['Subject'] = "CẢNH BÁO"
                body = f"Loại => loại: Ngã Tại Tầng 2. {dateTimeNow}"
                msg.attach(MIMEText(body, 'html'))
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(msg['From'], password)
                print("LOGIN success")
                server.sendmail(msg['From'], msg['To'], msg.as_string())
                server.quit()
                print("Email envoyé !")
                QtWidgets.QMessageBox.information(self, "Information", "Email được gửi để báo cáo về vụ ngã !")
        except Exception as e:
            print(f"Lỗi: Email không được gửi ! {e}")
            QtWidgets.QMessageBox.warning(self, "Cảnh báo", "Email không được gửi! Không báo cáo việc thả")

        # Giải phóng camera
        cap.release()

    def displayimage(self, img, window=1 ):
        qformat = QImage.Format_Indexed8
        qformat = QImage.Format_RGB888
        img = QImage(img, img.shape[1], img.shape[0], qformat)
        img = img.rgbSwapped()
        self.ui.ecran.setPixmap(QPixmap.fromImage(img))
        self.ui.ecran.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

    def displayimage1(self, img, window=1, x=1):
        qformat = QImage.Format_Indexed8
        qformat = QImage.Format_Grayscale8

        img = QImage(img, img.shape[1], img.shape[0], qformat)
        img = img.rgbSwapped()
        if(x==2):
             self.ui.ecran_2.setPixmap(QPixmap.fromImage(img))
             self.ui.ecran_2.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        if(x==3):
            self.ui.ecran_3.setPixmap(QPixmap.fromImage(img))
            self.ui.ecran_3.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

    def fermer(self):
        # QtWidgets.QMessageBox.information(self, "Quit", "Cảm ơn bạn đã sử dụng ứng dụng của chúng tôi!")
        ret = QtWidgets.QMessageBox.question(self, "Thoát", "Bạn có muốn đóng ứng dụng không?")
        if (ret == QtWidgets.QMessageBox.Yes):
            self.ui.cap.release()
            app.exit()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    widget = EcranWindow()
    widget.show()
    app.exec_()