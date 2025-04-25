from PyQt5 import QtWidgets, QtCore, QtGui
from ui.components.checkable_toolbutton import CheckableToolButton

class ToolbuttonWithInputNumberComponent(QtWidgets.QHBoxLayout):
    input_value_signal = QtCore.pyqtSignal(float)
    def __init__(
            self, 
            icon="",
            tooltip="",
            defaultValue=0,
            parent=None):
        super().__init__(parent)
        
        self.icon = icon
        self.tooltip = tooltip
        self.input_value = defaultValue if defaultValue else None

        self.init_ui()

    def init_ui(self):
        # button
        icon = QtGui.QIcon(self.icon)
        self.button = CheckableToolButton(icon, self.tooltip)
        # layout.addWidget(self.button)
        self.addWidget(self.button)

        # number input
        self.input = QtWidgets.QLineEdit(str(self.input_value))
        self.input.setFixedSize(30, 35)
        input_validator = QtGui.QDoubleValidator(1, 5, 10)
        self.input.setValidator(input_validator)
        self.addWidget(self.input)
