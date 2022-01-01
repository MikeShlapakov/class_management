from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class ComputerScreen(QLabel):
    clicked = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(ComputerScreen, self).__init__(parent)

        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QSize(240, 135))
        self.setMaximumSize(QSize(480, 270))
        self.setCursor(Qt.PointingHandCursor)
        # self.setStyleSheet(u"QLabel{background-color: rgb(150, 150, 150);\n"
        #                                         u"border-radius: 5px;}\n"
        #                                         u"QLabel:hover{\n"
        #                                         u"border: 5px solid rgb(80, 180, 80);\n"
        #                                         u"border-radius: 5px;\n"
        #                                         u"}")


    def mousePressEvent(self, event):
        self.params = {"name":self.objectName(),"action":"Click"}

    def mouseReleaseEvent(self, event):
        if self.params == {"name":self.objectName(),"action":"Click"}:
            QTimer.singleShot(QApplication.instance().doubleClickInterval(),
                              self.performSingleClickAction)
        else:
            self.clicked.emit(self.params)

    def mouseDoubleClickEvent(self, event):
        self.params = {"name":self.objectName(),"action":"Double Click"}

    def performSingleClickAction(self):
        if self.params == {"name":self.objectName(),"action":"Click"}:
            self.clicked.emit(self.params)

    def enterEvent(self, event):
        self.clicked.emit({"name": self.objectName(), "action":"Enter"})

    def leaveEvent(self, *args, **kwargs):
        self.clicked.emit({"name": self.objectName(), "action":"Leave"})


class ComputerScreenTab(QTabWidget):
    clicked = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(ComputerScreenTab, self).__init__(parent)
        self.setObjectName(u"tabWidget")
        self.setFont(QFont("Calibri", 14, QFont.Bold))
        self.setStyleSheet(u"QTabWidget:pane{background-color: rgb(25, 25, 35);"
                                     u"border-radius: 5px;"
                                     u"border: 2px solid rgb(25, 25, 35);}\n"
                                     u"QTabBar::tab { background-color: rgb(25,25,35); "
                                     u"color: rgb(125, 125, 150);"
                                     u"border: 2px solid rgb(90,90,100); border-bottom-color: rgb(90,90,100);"
                                     u"border-top-left-radius: 4px; "
                                     u"border-top-right-radius: 4px; min-width: 8ex; padding: 2px;}\n"
                                     u"QTabBar::tab:selected, QTabBar::tab:hover { "
                                     u"background: rgb(90,90,115);"
                                     u"color: rgb(25, 25, 35);}"
                                     u"QTabBar::tab:selected { border-color: rgb(30,30,40); border-bottom-color:rgb(40,40,50); }"
                                     u"QTabBar::tab:!selected { margin-top: 2px;}")

    # def mousePressEvent(self, *args, **kwargs):
    #     self.clicked.emit({"name":self.currentWidget().objectName()})
    #
    # def enterEvent(self, event):
    #     self.clicked.emit({"name":self.currentWidget().objectName()})


class Login_UI(object):
    """
    The login window
    """

    def setupUi(self, Window):
        if not Window.objectName():
            Window.setObjectName(u"LoginWindow")
        Window.resize(400, 560)
        Window.setMaximumSize(QSize(700, 600))
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
        self.horizontalSpacer = QSpacerItem(300, 20, QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer = QSpacerItem(20, 100, QSizePolicy.Maximum, QSizePolicy.Maximum)

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
                                          "	color:#FFFF;\n"
                                          "	padding-left: 20px;\n"
                                          "	padding-right: 20px;\n"
                                          "	background-color: rgb(40, 40, 60);\n"
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
                                          "	background-color: rgb(40, 40, 60);\n"
                                          "}\n"
                                          "QLineEdit:hover{\n"
                                          "	border: 2px solid rgb(80, 80, 100);\n"
                                          "}")
        self.password_entry.setAlignment(Qt.AlignCenter)
        self.password_entry.setClearButtonEnabled(True)
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
                                      "	border-radius: 17px;\n"
                                      "	color: rgb(30, 30, 40);\n"
                                      "	padding-left: 20px;\n"
                                      "	padding-right: 20px;\n"
                                      "	background-color: rgb(65, 65, 90);\n"
                                      "}\n"
                                      "\n"
                                      "QPushButton:hover{\n"
                                      "	border: 2px solid rgb(115, 115, 180);\n"
                                      "	\n"
                                      "	color: rgb(180, 180, 180);\n"
                                      "	background-color: rgb(80, 80, 120);\n"
                                      "}")
        # -------------------------------------------------------------------------------
        # signin button ------------------------------------------------------------------
        self.signin_btn = QPushButton(self.frame_2)
        self.signin_btn.setObjectName(u"pushButton")
        sizePolicy2.setHeightForWidth(self.signin_btn.sizePolicy().hasHeightForWidth())
        self.signin_btn.setSizePolicy(sizePolicy2)
        self.signin_btn.setFont(font2)
        self.signin_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.signin_btn.setStyleSheet(u"QPushButton{\n"
                                      "	border: 2px solid rgb(50, 50, 80);\n"
                                      "	border-radius: 17px;\n"
                                      "	color: rgb(30, 30, 40);\n"
                                      "	padding-left: 20px;\n"
                                      "	padding-right: 20px;\n"
                                      "	background-color: rgb(65, 65, 90);\n"
                                      "}\n"
                                      "\n"
                                      "QPushButton:hover{\n"
                                      "	border: 2px solid rgb(115, 115, 180);\n"
                                      "	\n"
                                      "	color:rgb(180, 180, 180);\n"
                                      "	background-color: rgb(80, 80, 120);\n"
                                      "}")

        # --------------------------------------------------------------------------
        # Laying buttons -----------------------------------------------------------
        self.horizontalLayout_2.addWidget(self.signup_btn)
        self.spacer = QSpacerItem(30, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(self.spacer)
        self.horizontalLayout_2.addWidget(self.signin_btn)
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
        self.signin_btn.setText(QCoreApplication.translate("LoginWindow", u"SIGN IN", None))
        self.signup_btn.setText(QCoreApplication.translate("LoginWindow", u"SIGN UP", None))
    # retranslateUi


class MainWindow_UI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName(u"MainWindow")
        self.resize(1000, 700)
        palette = QPalette()
        brush = QBrush(QColor(30, 30, 40, 255))
        palette.setBrush(QPalette.Active, QPalette.Window, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Window, brush)
        palette.setBrush(QPalette.Disabled, QPalette.Window, brush)
        self.setPalette(palette)
        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")

        self.verticalSpacer = QSpacerItem(20, 50, QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.gridLayout.addItem(self.verticalSpacer, 0, 1, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 50, QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.gridLayout.addItem(self.verticalSpacer_2, 2, 1, 1, 1)

        self.horizontalSpacer = QSpacerItem(50, 20, QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.gridLayout.addItem(self.horizontalSpacer, 1, 0, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(50, 20, QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.gridLayout.addItem(self.horizontalSpacer_2, 1, 2, 1, 1)

        self.widget = QFrame(self.centralwidget)
        self.widget.setObjectName(u"widget")
        self.widget.setMinimumSize(QSize(960, 540))
        self.widget.setStyleSheet("background-color: rgb(65, 65, 90);")
        self.widget.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

        self.gridLayout_2 = QGridLayout(self.widget)
        self.gridLayout_2.setObjectName(u"gridLayout_2")

        # =====================================================================
        self.comp0 = ComputerScreen(self.widget)
        self.comp1 = ComputerScreen(self.widget)
        self.comp2 = ComputerScreen(self.widget)
        self.comp3 = ComputerScreen(self.widget)
        # =====================================================================
        self.gridLayout.addWidget(self.widget, 1, 1, 1, 1)

        self.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(self)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 990, 21))
        self.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName(u"statusbar")
        self.setStatusBar(self.statusbar)

        self.retranslateUi(self)

        QMetaObject.connectSlotsByName(self)

    # setupUi

    def retranslateUi(self, Window):
        Window.setWindowTitle(QCoreApplication.translate("MainWindow", u"My Class", None))
    # retranslateUi


class TabView_UI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName(u"TabWindow")
        self.resize(1000, 700)
        palette = QPalette()
        brush = QBrush(QColor(30, 30, 40, 255))
        palette.setBrush(QPalette.Active, QPalette.Window, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Window, brush)
        palette.setBrush(QPalette.Disabled, QPalette.Window, brush)
        self.setPalette(palette)
        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.back_to_main_btn = QPushButton(self.centralwidget)
        self.back_to_main_btn.setObjectName(u"back_to_main_btn")
        self.back_to_main_btn.setText(u"VIEW ALL")
        self.back_to_main_btn.setFont(QFont("Calibri", 14, QFont.Bold))
        self.back_to_main_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.back_to_main_btn.setStyleSheet(u"QPushButton{border: 2px solid rgb(50, 50, 80);\n"
                                            "border-radius: 5px;\n"
                                            "color: rgb(30, 30, 40);\n"
                                            "padding-left: 20px;\n"
                                            "padding-right: 20px;\n"
                                            "background-color: rgb(65, 65, 90);}"
                                            "QPushButton:hover{border: 2px solid rgb(115, 115, 180);\n"
                                            "color:rgb(180, 180, 180);\n"
                                            "background-color: rgb(80, 80, 120);}")

        self.verticalLayout.addWidget(self.back_to_main_btn)

        self.tabWidget = ComputerScreenTab(self.centralwidget)

        self.verticalLayout.addWidget(self.tabWidget)

        self.gridLayout.addLayout(self.verticalLayout, 1, 1, 1, 1)

        self.retranslateUi(self)

        self.setCentralWidget(self.centralwidget)

        QMetaObject.connectSlotsByName(self)
        # self.showMaximized()

    # setupUi

    def retranslateUi(self, Window):
        Window.setWindowTitle(QCoreApplication.translate("TabWindow", u"My Class", None))
        # retranslateUi



if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    # MainWindow = QMainWindow()
    # ui = MainWindow_UI()
    # ui.setupUi(MainWindow)
    # MainWindow.show()
    e = MainWindow_UI()
    # e = TabView_UI()
    e.show()
    sys.exit(app.exec_())
