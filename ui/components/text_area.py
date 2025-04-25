from PyQt5 import QtWidgets, QtCore
from utils.common import outline_stylesheet

class TextArea(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)
        
        self.text_area = QtWidgets.QTextEdit()

        self.text_area.setStyleSheet(outline_stylesheet)
        self.text_area.setReadOnly(True)

        layout.addWidget(self.text_area)

    def set_text(self, text):
        self.text_area.setText(text)

    def add_text(self, text):
        self.text_area.append(text)