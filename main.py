# coding:utf-8
import json
import sqlite3
import sys

import pycountry
import qdarktheme
from PyQt6.QtCore import Qt, pyqtSignal, QEasingCurve, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QDialog, QComboBox, QLineEdit, \
    QPushButton
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (NavigationBar, NavigationItemPosition, MessageBox,
                            isDarkTheme, setTheme, Theme,
                            PopUpAniStackedWidget)
from qframelesswindow import FramelessWindow, TitleBar

# Customed classes
from Calendar import Calendar
from Settings import SettingInterface
from Dashboard import Dashboard
from DailyScheduleView import DailyScheduleView
from RecommendationView import RecommendationView
from MapView import MapView

APP_NAME = "TempoPilot"

with open("resources/misc/config.json") as config_file:
    _config = json.load(config_file)


class Onboarding(QDialog):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Onboarding')
        self.setGeometry(500, 200, 1100, 500)

        # Create main layout
        main_layout = QHBoxLayout(self)

        # Left layout
        self.left_layout = QVBoxLayout()
        self.left_layout.setContentsMargins(0, 0, 0, 0)

        self.country_edit = QComboBox(self)
        self.country_edit.setPlaceholderText("Select your country code (for Festivals data) (OPTIONAL)")
        country_codes = self.fetch_country_codes()
        self.country_edit.addItems(country_codes)

        self.zodiac_sign = QComboBox(self)
        self.zodiac_sign.setPlaceholderText("Select your Zodiac Sign (for Horoscopes)")
        zodiacs_list = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        self.zodiac_sign.addItems(zodiacs_list)

        self.api_key_edit = QLineEdit(self)
        self.api_key_edit.setPlaceholderText("Enter your Calendarific API key (for Festivals data) (OPTIONAL)")

        self.dob = QLineEdit(self)
        self.dob.setPlaceholderText("Enter your Date of Birth (YYYY-MM-DD) (OPTIONAL)")

        self.submit = QPushButton("Lets Go! -->")
        self.submit.clicked.connect(self.submit_details)

        self.left_layout.addWidget(self.dob)
        self.left_layout.addWidget(self.country_edit)
        self.left_layout.addWidget(self.api_key_edit)
        self.left_layout.addWidget(self.zodiac_sign)
        self.left_layout.addWidget(self.submit)

        # Right layout
        self.right_layout = QHBoxLayout()
        self.right_layout.setContentsMargins(10, 10, 10, 10)

        # Resize the image to make it smaller
        self.right_img = QPixmap("resources/icons/Designer.png").scaled(706, 500, Qt.AspectRatioMode.IgnoreAspectRatio)
        self.right_label = QLabel()
        self.right_label.setPixmap(self.right_img)

        self.right_layout.addWidget(self.right_label, alignment=Qt.AlignmentFlag.AlignTop)

        # Add left and right layouts to main layout
        main_layout.addLayout(self.left_layout)
        main_layout.addLayout(self.right_layout)

        # Set the dialog layout
        self.setLayout(main_layout)

    def fetch_country_codes(self):
        countries = list(pycountry.countries)
        country_codes = [country.alpha_2 for country in countries]
        return country_codes

    def submit_details(self):
        _config["api-key"] = self.api_key_edit.text()
        _config["country"] = self.country_edit.currentText()
        _config["start"] = "True"
        _config["zodiac"] = self.zodiac_sign.currentText()
        _config["dob"] = self.dob.text()

        with open("resources/misc/config.json", "w") as config_file:
            json.dump(_config, config_file)

    def goto_app(self):
        self.accept()
        global main_window
        main_window = Window()
        main_window.start()
        main_window.show()


class StackedWidget(QFrame):
    """ Stacked widget """

    currentChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.view = PopUpAniStackedWidget(self)

        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.view)

        self.view.currentChanged.connect(self.currentChanged)

    def addWidget(self, widget):
        """ add widget to view """
        self.view.addWidget(widget)

    def widget(self, index: int):
        return self.view.widget(index)

    def setCurrentWidget(self, widget, popOut=False):
        if not popOut:
            self.view.setCurrentWidget(widget, duration=300)
        else:
            self.view.setCurrentWidget(
                widget, True, False, 200, (QEasingCurve.Type.InQuad))

    def setCurrentIndex(self, index, popOut=False):
        self.setCurrentWidget(self.view.widget(index), popOut)


class CustomTitleBar(TitleBar):
    """ Title bar with icon and title """

    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedHeight(48)
        self.hBoxLayout.removeWidget(self.minBtn)
        self.hBoxLayout.removeWidget(self.maxBtn)
        self.hBoxLayout.removeWidget(self.closeBtn)

        # add window icon
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(20, 20)
        self.hBoxLayout.insertSpacing(0, 20)
        self.hBoxLayout.insertWidget(
            1, self.iconLabel, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.window().windowIconChanged.connect(self.setIcon)

        # add title label
        self.titleLabel = QLabel(self)
        self.hBoxLayout.insertWidget(
            2, self.titleLabel, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.titleLabel.setObjectName('titleLabel')
        self.window().windowTitleChanged.connect(self.setTitle)

        self.vBoxLayout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(0)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.buttonLayout.addWidget(self.minBtn)  # This line adds the minBtn
        self.buttonLayout.addWidget(self.maxBtn)  # This line adds the maxBtn
        self.buttonLayout.addWidget(self.closeBtn)  # This line adds the closeBtn
        self.vBoxLayout.addLayout(self.buttonLayout)
        self.vBoxLayout.addStretch(1)
        self.hBoxLayout.addLayout(self.vBoxLayout, 0)

    def setTitle(self, title):
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()

    def setIcon(self, icon):
        self.iconLabel.setPixmap(QIcon(icon).pixmap(20, 20))

    def resizeEvent(self, e):
        pass


class Window(FramelessWindow):

    def __init__(self):
        super().__init__()
        self.setTitleBar(CustomTitleBar(self))

        setTheme(Theme.DARK)
        #setTheme(Theme.LIGHT)

        self.hBoxLayout = QHBoxLayout(self)
        self.navigationBar = NavigationBar(self)
        self.stackWidget = StackedWidget(self)

        """
        Database Initiation
        """

        self.conn1 = sqlite3.connect('resources/misc/todos.db')
        self.cursor1 = self.conn1.cursor()

        # Create a table to store todos
        self.cursor1.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                time TEXT,
                description TEXT,
                status TEXT
            )
        ''')
        self.conn1.commit()

        self.conn2 = sqlite3.connect('resources/misc/special_dates.db')
        self.cursor2 = self.conn2.cursor()

        # Create a table to store todos
        self.cursor2.execute('''
            CREATE TABLE IF NOT EXISTS special_dates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                reason TEXT
            )
        ''')
        self.conn2.commit()

        self.conn3 = sqlite3.connect('resources/misc/reminders.db')
        self.cursor3 = self.conn3.cursor()

        # Create a table to store todos
        self.cursor3.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                time TEXT,
                description TEXT
            )
        ''')
        self.conn3.commit()

        self.homeInterface = None
        self.calendarInterface = None
        self.settingsInterface = None
        self.statsInterface = None

        if _config.get("start") == "True":
            self.start()
        else:
            qdarktheme.setup_theme("dark")
            onboarding = Onboarding()
            onboarding.exec()

    def start(self):
        # 1) 各个子界面实例化
        self.homeInterface      = Dashboard()
        self.calendarInterface  = Calendar()
        self.settingsInterface  = SettingInterface()

        raw_day                = DailyScheduleView()
        self.recommendInterface = RecommendationView(scheduler=raw_day)

        # 2) 用 QSplitter 把推荐和日视图 做左右布局
        from PyQt6.QtWidgets import QSplitter
        from PyQt6.QtCore import Qt

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.recommendInterface)
        splitter.addWidget(raw_day)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 800])

        self.dailyScheduleInterface = splitter
        self.dailyScheduleInterface.setObjectName("DailyView")

        # 3) 地图面板
        self.mapInterface = MapView()
        self.mapInterface.setObjectName("Map")

        # 4) 现在所有 interface 都准备好了，再一次性初始化布局和导航
        self.initLayout()
        self.initNavigation()
        self.initWindow()


    def initLayout(self):
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 48, 0, 0)
        self.hBoxLayout.addWidget(self.navigationBar)
        self.hBoxLayout.addWidget(self.stackWidget)
        self.hBoxLayout.setStretchFactor(self.stackWidget, 1)

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, 'Dashboard', selectedIcon=FIF.HOME)
        self.addSubInterface(self.calendarInterface, FIF.CALENDAR, 'Calendar', selectedIcon=FIF.CALENDAR)
        self.addSubInterface(self.dailyScheduleInterface, FIF.DATE_TIME, 'Day View', selectedIcon=FIF.DATE_TIME)
        self.addSubInterface(self.mapInterface, FIF.GLOBE,      'Map',      selectedIcon=FIF.GLOBE)
        self.addSubInterface(self.settingsInterface, FIF.SETTING, 'Settings', selectedIcon=FIF.SETTING)


        self.navigationBar.addItem(
            routeKey='About',
            icon=FIF.HELP,
            text='About',
            onClick=self.showMessageBox,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        self.stackWidget.currentChanged.connect(self.onCurrentInterfaceChanged)
        self.navigationBar.setCurrentItem(self.homeInterface.objectName())

    def initWindow(self):
        self.resize(1000, 600)
        self.setWindowIcon(QIcon('resources/icons/icon.png'))
        self.setWindowTitle(APP_NAME)
        self.setQss()

    def addSubInterface(self, interface, icon, text: str, position=NavigationItemPosition.TOP, selectedIcon=None):
        """ add sub interface """
        self.stackWidget.addWidget(interface)
        self.navigationBar.addItem(
            routeKey=interface.objectName(),
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(interface),
            selectedIcon=selectedIcon,
            position=position,
        )

    def setQss(self):
        color = 'dark' if isDarkTheme() else 'light'
        with open(f'resources/{color}/demo.qss', encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def switchTo(self, widget):
        self.stackWidget.setCurrentWidget(widget)

    def onCurrentInterfaceChanged(self, index):
        widget = self.stackWidget.widget(index)
        self.navigationBar.setCurrentItem(widget.objectName())

    def showMessageBox(self):
        text_for_about = (
            f"<b>{APP_NAME}</b> — JC3510 Group 6 Project<br><br>"
            "This application is built upon the open‑source <i>Tempus</i> scheduler by Rohan (gpl-3.0 License).<br><br>"
            "<b>Group Members:</b><br>"
            "• Yingjie Lei<br>"
            "• Jiayu Ye<br>"
            "• Ziyang Chen<br>"
            "• Zishen He<br>"
            "• Ruyuan Ge<br>"
            "• Zirui Zhu<br><br>"
            "Version: 1.0.0<br><br>"
            "Feel free to explore our code or contribute on GitHub, "
            "or learn more about our department on the college website."
        )
        w = MessageBox(
            APP_NAME,
            text_for_about,
            self
        )
        w.yesButton.setText('GitHub')
        w.cancelButton.setText('Aberdeen Insitute')

        result = w.exec()
        if result == QDialog.DialogCode.Accepted:
            # 打开 GitHub 仓库
            QDesktopServices.openUrl(QUrl("https://github.com/ChaosTheProducer"))
        else:
            # 打开学院官网
            QDesktopServices.openUrl(QUrl("https://abdn.scnu.edu.cn/"))


if __name__ == '__main__':
    """
    app = QApplication(sys.argv)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    """
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)


    qdarktheme.enable_hi_dpi()
    w = Window()
    qdarktheme.setup_theme("dark")
    w.show()

    sys.exit(app.exec())
