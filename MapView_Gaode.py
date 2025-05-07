import os
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QSizePolicy
from PyQt6.QtWebEngineWidgets import QWebEngineView

class MapView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.browser = QWebEngineView(self)
        self.browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.browser)

        # load the local HTML file you edited (make sure the filename matches)
        html_path = os.path.join(os.path.dirname(__file__), "HTMLPageUI2.html")
        self.browser.load(QUrl.fromLocalFile(html_path))

    def navigate(self, origin: str, destination: str):
        """
        origin / destination: strings like "Beijing, China" or "lat,lng"
        This will invoke the JS function navigateAMap(origin, destination)
        you defined in your HTML.
        """
        # escape quotes in place names
        o = origin.replace('"', r'\"')
        d = destination.replace('"', r'\"')
        js = f'navigateAMap("{o}", "{d}");'
        self.browser.page().runJavaScript(js)
