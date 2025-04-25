from PyQt5 import QtWidgets, QtGui, QtCore

class NumberInputComponent(QtWidgets.QWidget):
    def __init__(self, label="", defaultValue=0, type="int", parent=None):
        super().__init__(parent)

        self.label = label
        self.type = type
        self.defaultValue = defaultValue
        self.input_value = defaultValue if defaultValue else None

        self.init_ui()
    
    def set_label(self, label=""):
        self.label_widget.setText(label)

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)

        self.label_widget = QtWidgets.QLabel(self.label)
        layout.addWidget(self.label_widget)

        self.input = QtWidgets.QLineEdit() 
        if self.defaultValue:
            self.input.setText(str(self.defaultValue))
        layout.addWidget(self.input)
        
        # input validator
        if self.type == "float":
            validator = QtGui.QDoubleValidator()
        else:
            validator = QtGui.QIntValidator()
        self.input.setValidator(validator)

        self.input.textChanged.connect(self.on_text_changed)

    def on_text_changed(self, text):
        if text and self.type == "float":
            self.input_value = float(text)
        else:
            self.input_value = int(text)

    def set_value(self, val: str = ""):
        self.input_value = val
        self.input.setText(val)