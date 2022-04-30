from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class CustomButton(QPushButton):
    def __init__(self, parent=None, name='Button'):
        super(CustomButton, self).__init__(parent)
        self.setText(name)
        self.setFont(QFont("Calibri", 14, QFont.Bold))
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(u"QPushButton{border: 2px solid rgb(50, 50, 80);\n"
                           "border-radius: 5px;\n"
                           "color: rgb(30, 30, 40);\n"
                           "padding-left: 20px;\n"
                           "padding-right: 20px;\n"
                           "background-color: rgb(65, 65, 90);}"
                           "QPushButton:hover{border: 2px solid rgb(115, 115, 180);\n"
                           "color:rgb(180, 180, 180);\n"
                           "background-color: rgb(80, 80, 120);}")


class ComputerScreen(QFrame):
    clicked = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(ComputerScreen, self).__init__(parent)
        self.setObjectName('frame')
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QSize(240, 135))
        self.setMaximumSize(QSize(480, 270))
        self.setCursor(Qt.PointingHandCursor)
        layout = QGridLayout()
        self.top_left = QLabel()
        self.top_left.setObjectName('top_left')
        layout.addWidget(self.top_left,0,0)

        self.top_right = QLabel()
        self.top_right.setObjectName('top_right')
        layout.addWidget(self.top_right,0,1)

        self.bottom_left = QLabel()
        self.bottom_left.setObjectName('bottom_left')
        layout.addWidget(self.bottom_left,1,0)

        self.bottom_right = QLabel()
        self.bottom_right.setObjectName('bottom_right')
        layout.addWidget(self.bottom_right,1,1)

        layout.setSpacing(0)
        self.setLayout(layout)
        self.setStyleSheet(u"QFrame#frame{background-color: rgb(150, 150, 150);\n"
                                                u"border-radius: 5px;}\n"
                                                u"QFrame#frame:hover{\n"
                                                u"border: 5px solid rgb(80, 180, 80);\n"
                                                u"border-radius: 5px;\n"
                                                u"}")


    def mousePressEvent(self, event):
        self.params = {"name": self.objectName(), "action": "Click"}

    def mouseReleaseEvent(self, event):
        if self.params == {"name": self.objectName(), "action": "Click"}:
            QTimer.singleShot(QApplication.instance().doubleClickInterval(),
                              self.performSingleClickAction)
        else:
            self.clicked.emit(self.params)

    def mouseDoubleClickEvent(self, event):
        self.params = {"name": self.objectName(), "action": "Double Click"}

    def performSingleClickAction(self):
        if self.params == {"name": self.objectName(), "action": "Click"}:
            self.clicked.emit(self.params)

    def enterEvent(self, event):
        self.clicked.emit({"name": self.objectName(), "action": "Enter"})

    def leaveEvent(self, *args, **kwargs):
        self.clicked.emit({"name": self.objectName(), "action": "Leave"})


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

    # def enterEvent(self, event):
    #     self.clicked.emit({"name": self.objectName(), "action":"Enter"})
    #
    # def leaveEvent(self, *args, **kwargs):
    #     self.clicked.emit({"name": self.objectName(), "action":"Leave"})


class CustomDialog(QDialog):
    def __init__(self, parent=None, title="", message="", buttons=['Ok']):
        super().__init__(parent)

        self.setWindowTitle(title)

        dialog_buttons = ''
        for button in buttons:
            if button == buttons[-1]:
                dialog_buttons += f'QDialogButtonBox.{button}'
                break
            dialog_buttons += f'QDialogButtonBox.{button} | '

        self.buttonBox = QDialogButtonBox(eval(dialog_buttons))
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel(message))
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


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
        brush = QBrush(QColor(30, 30, 40))
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

        self.waitingLabal = QLabel('Waiting for connection...')
        font = QFont()
        font.setFamily(u"Calibri")
        font.setPointSize(24)
        font.setBold(True)
        font.setWeight(96)
        self.waitingLabal.setFont(font)
        self.waitingLabal.setAlignment(Qt.AlignCenter)
        self.waitingLabal.setStyleSheet(u"QLabel{\n"
                                 "	color: rgb(30, 30, 40);\n"
                                 "}\n")
        self.gridLayout_2.addWidget(self.waitingLabal)

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
        self._createActions()
        self._createToolBars()

        QMetaObject.connectSlotsByName(self)

    # setupUi
    def _createActions(self):
        # File actions
        self.blockInputButton = CustomButton(self.centralwidget, "BLOCK INPUT ALL")
        self.unblockInputButton = CustomButton(self.centralwidget, "UNBLOCK INPUT ALL")
        self.blockScreenButton = CustomButton(self.centralwidget, "BLOCK ALL SCREENS")
        self.unblockScreenButton = CustomButton(self.centralwidget, "UNBLOCK ALL SCREENS")
        self.shareScreenButton = CustomButton(self.centralwidget, "SHARE SCREEN ALL")
        self.chatButton = CustomButton(self.centralwidget, "CHAT ALL")
        self.shareFileButton = CustomButton(self.centralwidget, "SHARE FILE ALL")

    def _createToolBars(self):
        # File toolbar
        self.toolBar = QToolBar("TOOLS")
        self.addToolBar(Qt.LeftToolBarArea, self.toolBar)
        self.logBox = QGroupBox('LOG', self)  # alert box
        self.logBox.setMaximumSize(QSize(200, 400))
        # self.alertBox.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred))
        self.verticalLayout3 = QVBoxLayout(self.logBox)
        self.logBox.setStyleSheet("QGroupBox::title"
                                    "{"
                                    "border-top-left-radius: 9px;"
                                    "border-top-right-radius: 9px;"
                                    "padding: 2px 82px;"
                                    "background-color: rgb(65, 65, 90);"
                                    "font-weight:bold;"
                                    "color: rgb(30, 30, 40);"
                                    "}")

        self.logs = QListWidget(self.logBox)
        self.verticalLayout3.addWidget(self.logs)

        self.toolBar.addWidget(self.blockInputButton)
        self.toolBar.addWidget(self.unblockInputButton)
        self.toolBar.addWidget(self.blockScreenButton)
        self.toolBar.addWidget(self.unblockScreenButton)
        self.toolBar.addWidget(self.shareScreenButton)
        self.toolBar.addWidget(self.chatButton)
        self.toolBar.addWidget(self.shareFileButton)
        self.toolBar.addWidget(self.logBox)


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

        # self.verticalLayout.addWidget(self.back_to_main_btn)

        self.tabWidget = ComputerScreenTab(self.centralwidget)

        self.verticalLayout.addWidget(self.tabWidget)

        self.gridLayout.addLayout(self.verticalLayout, 1, 1, 1, 1)

        self.retranslateUi(self)

        self.setCentralWidget(self.centralwidget)

        self._createActions()
        self._createToolBars()
        self._createContextMenu()

        QMetaObject.connectSlotsByName(self)
        # self.showMaximized()

    # setupUi
    def _createActions(self):
        # File actions
        self.newAction = QAction(self)
        self.newAction.setText("&New")
        # # self.newAction.setIcon(QIcon(":file-new.svg"))
        self.blockInputAction = QAction(QIcon("./block.jpg"), "&Block Input", self)
        self.unblockInputAction = QAction(QIcon("./unblock.jpg"), "&Unblock Input", self)
        self.shareScreenAction = QAction("&Share Screen", self)
        # self.exitAction = QAction("&Exit", self)
        self.blockInputButton = CustomButton(self.centralwidget, "BLOCK INPUT")
        self.unblockInputButton = CustomButton(self.centralwidget, "UNBLOCK INPUT")
        self.blockScreenButton = CustomButton(self.centralwidget, "BLOCK SCREEN")
        self.shareScreenButton = CustomButton(self.centralwidget, "SHARE SCREEN")
        self.recordButton = CustomButton(self.centralwidget, "RECORD SCREEN")
        self.chatButton = CustomButton(self.centralwidget, "CHAT")
        self.shareFileButton = CustomButton(self.centralwidget, "SHARE FILE")
        self.back_to_main_btn = CustomButton(self.centralwidget, "VIEW ALL")


    def _createToolBars(self):
        # File toolbar
        self.toolBar = QToolBar("TOOLS")
        self.addToolBar(Qt.LeftToolBarArea, self.toolBar)
        self.alertBox = QGroupBox('ALERTS', self)  # alert box
        self.alertBox.setMaximumSize(QSize(200, 400))
        # self.alertBox.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred))
        self.verticalLayout3 = QVBoxLayout(self.alertBox)
        self.alertBox.setStyleSheet("QGroupBox::title"
                                    "{"
                                    "border-top-left-radius: 9px;"
                                    "border-top-right-radius: 9px;"
                                    "padding: 2px 82px;"
                                    "background-color: #FF17365D;"
                                    "color: rgb(255, 255, 255);"
                                    "}")

        self.alerts = QListWidget(self.alertBox)
        self.verticalLayout3.addWidget(self.alerts)

        self.toolBar.addWidget(self.blockInputButton)
        self.toolBar.addWidget(self.unblockInputButton)
        self.toolBar.addWidget(self.blockScreenButton)
        self.toolBar.addWidget(self.shareScreenButton)
        self.toolBar.addWidget(self.recordButton)
        self.toolBar.addWidget(self.chatButton)
        self.toolBar.addWidget(self.shareFileButton)
        self.toolBar.addWidget(self.alertBox)
        self.toolBar.addWidget(self.back_to_main_btn)

    def _createContextMenu(self):
        # Setting contextMenuPolicy
        self.centralwidget.setContextMenuPolicy(Qt.ActionsContextMenu)
        # Populating the widget with actions
        self.centralwidget.addAction(self.blockInputAction)
        self.centralwidget.addAction(self.unblockInputAction)
        self.centralwidget.addAction(self.shareScreenAction)

    def retranslateUi(self, Window):
        Window.setWindowTitle(QCoreApplication.translate("TabWindow", u"My Class", None))
        # retranslateUi


class ChatBox_UI(QMainWindow):
    def __init__(self, parent=None):
        super(ChatBox_UI, self).__init__(parent)
        self.horizontalLayout = QHBoxLayout(self)

        self.groupBox = QGroupBox(self)
        self.verticalLayout = QVBoxLayout(self.groupBox)

        self.listWidget = QListWidget(self.groupBox)  # chat
        # self.listWidget.setMaximumSize(QSize(200, 200))
        self.verticalLayout.addWidget(self.listWidget)

        self.lineEdit = QLineEdit(self.groupBox)
        self.lineEdit.setMinimumSize(QSize(0, 40))
        self.verticalLayout.addWidget(self.lineEdit)

        self.horizontalLayout.addWidget(self.groupBox)

        self.setCentralWidget(self.groupBox)


class ShareScreenWindow(QMainWindow):

    def __init__(self):
        super(ShareScreenWindow, self).__init__()

        self.setWindowTitle("My App")

        self.widget = QLabel("Hello")
        self.widget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.setCentralWidget(self.widget)
        self.showMaximized()
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint
        )


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    # MainWindow = QMainWindow()
    # ui = MainWindow_UI()
    # ui.setupUi(MainWindow)
    # MainWindow.show()
    # e = ComputerScreenTab()
    e = TabView_UI()
    comp = ComputerScreen(e)
    comp2 = ComputerScreen(e)
    # comp.label.setObjectName(f"comp{1}")
    # comp.label.setToolTip(f"{123}\'s computer")
    # comp.label.setStyleSheet(u"QLabel{background-color: rgb(150, 150, 150);\n"
    #                                         u"border-radius: 5px;}\n"
    #                                         u"QLabel:hover{\n"
    #                                         u"border: 5px solid rgb(80, 180, 80);\n"
    #                                         u"border-radius: 5px;\n"
    #                                         u"}")
    comp.setMinimumSize(QSize(240, 135))
    comp.setMaximumSize(QSize(1920, 1080))
    #
    # comp2 = ComputerScreenWidget(e)
    # comp2.label.setObjectName(f"comp{2}")
    # comp2.label.setToolTip(f"abs\'s computer")
    # comp2.label.setStyleSheet(u"QLabel{background-color: rgb(150, 150, 150);\n"
    #                                         u"border-radius: 5px;}\n"
    #                                         u"QLabel:hover{\n"
    #                                         u"border: 5px solid rgb(80, 180, 80);\n"
    #                                         u"border-radius: 5px;\n"
    #                                         u"}")
    # comp2.label.setMinimumSize(QSize(240, 135))
    # comp2.label.setMaximumSize(QSize(1920, 1080))

    e.tabWidget.addTab(comp, '123')
    e.tabWidget.addTab(comp2, 'abs')
    e = MainWindow_UI()
    e.show()
    sys.exit(app.exec_())
