from PyQt5 import QtWidgets

class CheckBox(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_ui()

    def init_ui(self):
        print("init ui")