from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(795, 590)

        self.ecran = QtWidgets.QLabel(Form)
        self.ecran.setGeometry(QtCore.QRect(20, 20, 751, 451))
        self.ecran.setScaledContents(True)  # Cho phép tự động điều chỉnh kích thước ảnh
        self.ecran.setObjectName("ecran")

        self.ecran_2 = QtWidgets.QLabel(Form)
        self.ecran_2.setGeometry(QtCore.QRect(20, 480, 351, 81))
        self.ecran_2.setScaledContents(True)
        self.ecran_2.setObjectName("ecran_2")

        self.ecran_3 = QtWidgets.QLabel(Form)
        self.ecran_3.setGeometry(QtCore.QRect(400, 480, 371, 81))
        self.ecran_3.setScaledContents(True)
        self.ecran_3.setObjectName("ecran_3")

        self.afficher = QtWidgets.QPushButton(Form)
        self.afficher.setGeometry(QtCore.QRect(20, 560, 93, 28))
        self.afficher.setObjectName("afficher")

        self.arreter = QtWidgets.QPushButton(Form)
        self.arreter.setGeometry(QtCore.QRect(160, 560, 93, 28))
        self.arreter.setObjectName("arreter")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)


    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.afficher.setText(_translate("Form", "Bat dau"))
        self.arreter.setText(_translate("Form", "Thoat"))
