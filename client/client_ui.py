from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class Ui_Login(object):
    """
    The login window
    """
    def setupUi(self, Window):
        if not Window.objectName():
            Window.setObjectName(u"LoginWindow")
        Window.resize(400, 560)
        Window.setMaximumSize(QSize(600, 800))
        palette = QPalette()
        brush = QBrush(QColor(30, 30, 40, 255))
        palette.setBrush(QPalette.Active, QPalette.Window, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Window, brush)
        palette.setBrush(QPalette.Disabled, QPalette.Window, brush)
        Window.setPalette(palette)
        self.centralwidget = QWidget(Window)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(300, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer = QSpacerItem(20, 100, QSizePolicy.Minimum, QSizePolicy.Maximum)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")
        self.label.setEnabled(False)
        font = QFont()
        font.setFamily(u"Calibri")
        font.setPointSize(48)
        font.setBold(True)
        font.setWeight(96)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(u"QLabel{\n"
                                 "	color: rgb(255, 170, 0);\n"
                                 "}\n")

        self.verticalLayout.addWidget(self.label)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Preferred)

        self.verticalLayout.addItem(self.verticalSpacer_3)

        self.username_entry = QLineEdit(self.frame)
        self.username_entry.setObjectName(u"username_entry")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self.username_entry.sizePolicy().hasHeightForWidth())
        self.username_entry.setSizePolicy(sizePolicy)
        font1 = QFont()
        font1.setFamily(u"Calibri")
        font1.setPointSize(24)
        self.username_entry.setFont(font1)
        self.username_entry.setStyleSheet(u"QLineEdit{\n"
                                          "	border: 2px solid rgb(65, 65, 90);\n"
                                          "	border-radius: 15px;\n"
                                          "	color:#FFF;\n"
                                          "	padding-left: 20px;\n"
                                          "	padding-right: 20px;\n"
                                          "	background-color: rgb(50, 50, 70);\n"
                                          "}\n"
                                          "QLineEdit:hover{\n"
                                          "	border: 2px solid rgb(80, 80, 100);\n"
                                          "}")
        self.username_entry.setAlignment(Qt.AlignCenter)
        self.username_entry.setClearButtonEnabled(True)
        self.verticalLayout.addWidget(self.username_entry)

        self.verticalSpacer_4 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Maximum)

        self.verticalLayout.addItem(self.verticalSpacer_4)

        self.password_entry = QLineEdit(self.frame)
        self.password_entry.setObjectName(u"password_entry")
        self.password_entry.setEchoMode(QLineEdit.Password)
        sizePolicy.setHeightForWidth(self.password_entry.sizePolicy().hasHeightForWidth())
        self.password_entry.setSizePolicy(sizePolicy)
        self.password_entry.setFont(font1)
        self.password_entry.setStyleSheet(u"QLineEdit{\n"
                                          "	border: 2px solid rgb(65, 65, 90);\n"
                                          "	border-radius: 15px;\n"
                                          "	color:#FFF;\n"
                                          "	padding-left: 20px;\n"
                                          "	padding-right: 20px;\n"
                                          "	background-color: rgb(50, 50, 70);\n"
                                          "}\n"
                                          "QLineEdit:hover{\n"
                                          "	border: 2px solid rgb(80, 80, 100);\n"
                                          "}")
        self.password_entry.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.password_entry)

        self.verticalSpacer_5 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Maximum)

        self.verticalLayout.addItem(self.verticalSpacer_5)

        self.frame_2 = QFrame(self.frame)
        self.frame_2.setObjectName(u"frame_2")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy1)
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)

        self.horizontalLayout_2 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        # -------------------------------------------------------------------------------
        # Buttons
        font2 = QFont()
        font2.setFamily(u"Calibri")
        font2.setPointSize(24)
        font2.setBold(True)
        font2.setWeight(75)
        # sign-up button ----------------------------------------------------------------
        self.signup_btn = QPushButton(self.frame_2)
        self.signup_btn.setObjectName(u"signup_btn")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.signup_btn.sizePolicy().hasHeightForWidth())
        self.signup_btn.setSizePolicy(sizePolicy2)
        self.signup_btn.setFont(font2)
        self.signup_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.signup_btn.setStyleSheet(u"QPushButton{\n"
                                      "	border: 2px solid rgb(50, 50, 80);\n"
                                      "	border-radius: 20px;\n"
                                      "	color: rgb(25, 25, 30);\n"
                                      "	padding-left: 20px;\n"
                                      "	padding-right: 20px;\n"
                                      "	background-color: rgb(65, 65, 105);\n"
                                      "}\n"
                                      "\n"
                                      "QPushButton:hover{\n"
                                      "	border: 2px solid rgb(115, 115, 180);\n"
                                      "	\n"
                                      "	color: rgb(40, 40, 45);\n"
                                      "	background-color: rgb(80, 80, 120);\n"
                                      "}")
        # -------------------------------------------------------------------------------
        # login button ------------------------------------------------------------------
        self.login_btn = QPushButton(self.frame_2)
        self.login_btn.setObjectName(u"pushButton")
        sizePolicy2.setHeightForWidth(self.login_btn.sizePolicy().hasHeightForWidth())
        self.login_btn.setSizePolicy(sizePolicy2)
        self.login_btn.setFont(font2)
        self.login_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.login_btn.setStyleSheet(u"QPushButton{\n"
                                     "	border: 2px solid rgb(50, 50, 80);\n"
                                     "	border-radius: 20px;\n"
                                     "	color: rgb(25, 25, 30);\n"
                                     "	padding-left: 20px;\n"
                                     "	padding-right: 20px;\n"
                                     "	background-color: rgb(65, 65, 105);\n"
                                     "}\n"
                                     "\n"
                                     "QPushButton:hover{\n"
                                     "	border: 2px solid rgb(115, 115, 180);\n"
                                     "	\n"
                                     "	color: rgb(40, 40, 45);\n"
                                     "	background-color: rgb(80, 80, 120);\n"
                                     "}")

        # --------------------------------------------------------------------------
        # Laying buttons -----------------------------------------------------------
        self.horizontalLayout_2.addWidget(self.signup_btn)
        self.spacer = QSpacerItem(30, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(self.spacer)
        self.horizontalLayout_2.addWidget(self.login_btn)
        # -------------------------------------------------------------------------------

        self.verticalLayout.addWidget(self.frame_2)
        self.verticalSpacer_2 = QSpacerItem(20, 100, QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.horizontalLayout.addWidget(self.frame)

        self.horizontalSpacer_2 = QSpacerItem(300, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        Window.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(Window)
        self.statusbar.setObjectName(u"statusbar")
        Window.setStatusBar(self.statusbar)

        self.retranslateUi(Window)

        QMetaObject.connectSlotsByName(Window)

    # setupUi

    def retranslateUi(self, Window):
        Window.setWindowTitle(QCoreApplication.translate("LoginWindow", u"MY CLASS", None))
        self.label.setText(QCoreApplication.translate("LoginWindow", u"MY CLASS", None))
        self.username_entry.setPlaceholderText(QCoreApplication.translate("LoginWindow", u"ENTER USERNAME", None))
        self.password_entry.setPlaceholderText(QCoreApplication.translate("LoginWindow", u"ENTER PASSWORD", None))
        self.login_btn.setText(QCoreApplication.translate("LoginWindow", u"SIGN IN", None))
        self.signup_btn.setText(QCoreApplication.translate("LoginWindow", u"SIGN UP", None))
    # retranslateUi


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_Login()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())