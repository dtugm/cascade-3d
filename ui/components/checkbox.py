from PyQt5 import QtWidgets, QtGui, QtCore

class CheckBox(QtWidgets.QWidget):
    clicked = QtCore.pyqtSignal(bool)

    def __init__(self, label="", parent=None):
        super().__init__(parent)

        self.is_checked = False
        self.label = label

        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignLeft)

        checkbox = QtWidgets.QCheckBox()
        checkbox.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        checkbox.stateChanged.connect(self.on_state_change)
        layout.addWidget(checkbox)

        label = QtWidgets.QLabel(self.label)
        label.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        layout.addWidget(label)
    
    def on_state_change(self, state):
        self.clicked.emit(state)
        
        if state == QtCore.Qt.Checked:
            self.is_checked = True
        else:
            self.is_checked = False
    
    @property
    def input_value(self):
        return self.is_checked