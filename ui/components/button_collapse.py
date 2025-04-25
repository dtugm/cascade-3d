from PyQt5 import QtWidgets, QtCore, QtGui

class CollapseButton(QtWidgets.QWidget):
    btn_state_signal = QtCore.pyqtSignal(bool)
    def __init__(
            self, 
            label="",
            parent=None):
        super().__init__(parent)

        self.label_text = label
        self.visible = False 
        
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)

        desc_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(desc_layout)
        
        self.btn = QtWidgets.QToolButton()
        self.btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.btn.setStyleSheet("border: none; background-color: transparent; ")
        self.btn.setIcon(QtGui.QIcon("public/icon/arrow-down.png"))
        self.btn.clicked.connect(self.on_button_clicked)
        desc_layout.addWidget(self.btn)

        label = QtWidgets.QLabel(self.label_text)
        label.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        desc_layout.addWidget(label)

    def on_button_clicked(self):
        if self.visible:
            self.visible = False
            self.btn_state_signal.emit(False)
            self.btn.setIcon(QtGui.QIcon("public/icon/arrow-down.png"))
        else:
            self.visible = True
            self.btn.setIcon(QtGui.QIcon("public/icon/arrow-up.png"))
            self.btn_state_signal.emit(True)

