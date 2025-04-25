from PyQt5 import QtWidgets, QtCore

class CheckableToolButton(QtWidgets.QToolButton):
    def __init__(self, icon, tooltip, parent=None):
        super().__init__(parent)

        self.setIcon(icon)
        self.setToolTip(tooltip)

        self.setCheckable(True)

        self.setFixedSize(45, 45)
        self.setIconSize(QtCore.QSize(25, 25))

        self.setContentsMargins(0, 0, 0, 0)

        self.default_stylesheet = "border: 1px solid transparent; border-radius:5px;"
        self.setStyleSheet(self.default_stylesheet)
    
    def handle_click(self, is_checked: bool = False):
        self.toggled.emit(is_checked)

        # if self.isChecked():
        if is_checked:
        # Set different colors based on checked state
            self.setStyleSheet("border: 1px solid #D0CFCF; border-radius: 5px; background-color: #D0CFCF;")
        else:
            self.setStyleSheet(self.default_stylesheet)