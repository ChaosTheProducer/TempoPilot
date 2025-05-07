from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QSizePolicy
from PyQt6.QtWebEngineWidgets import QWebEngineView

class MapView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # —— 1) 让 MapView 本身可膨胀 ——  
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        # （可选）给个最小尺寸，保证极小时也能看到内容
        self.setMinimumSize(200, 200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # —— 2) 让内部的浏览器也可膨胀 ——  
        self.browser = QWebEngineView(self)
        self.browser.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        layout.addWidget(self.browser)

    def navigate(self, origin: str, destination: str):
        """
        origin, destination 都是字符串，可以是地址或“lat,lon”形式
        """
        # 使用 Google Maps Directions API 的通用 URL
        url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={origin}"
            f"&destination={destination}"
            "&travelmode=driving"
        )
        self.browser.load(QUrl(url))
