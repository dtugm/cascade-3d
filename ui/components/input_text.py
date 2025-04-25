from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit
from PyQt5.QtCore import Qt

class TextInputComponent(QWidget):
    def __init__(self, label="", defaultValue="", type="int", parent=None):
        super().__init__(parent)

        self.label = label
        self.type = type
        self.defaultValue = defaultValue if defaultValue else None

        self.init_ui()
    
    def set_label(self, label=""):
        self.label_widget.setText(label)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        self.label_widget = QLabel(self.label)
        layout.addWidget(self.label_widget)

        self.input = QLineEdit() 
        if self.defaultValue:
            self.input.setText(str(self.defaultValue))
        layout.addWidget(self.input)
    
    def read_only(self, is_read_only: bool = True):
        self.input.setReadOnly(is_read_only)

    def set_value(self, val: str):
        self.input.setText(val)

    @property
    def input_value(self):
        return self.input.text()