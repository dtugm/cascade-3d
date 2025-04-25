from PyQt5 import QtWidgets, QtCore
from utils.common import outline_stylesheet

class DropdownComponent(QtWidgets.QWidget):
    on_changed = QtCore.pyqtSignal(str)

    def __init__(self, label="", options=[], dropdown_name="", default_index=0, parent = None) -> None:
        super().__init__(parent)

        self.label = label
        self.options = options
        self.default_index = default_index

        self.dropdown_name = dropdown_name

        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)

        label = QtWidgets.QLabel(self.label)
        layout.addWidget(label)


        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.setMinimumHeight(25)
        self.combo_box.setObjectName(self.dropdown_name)
        self.combo_box.setStyleSheet(outline_stylesheet)
        self.set_current_index(self.default_index)

        for option in self.options:
            self.combo_box.addItem(option)

        layout.addWidget(self.combo_box)

        self.combo_box.currentIndexChanged.connect(lambda: self.on_changed.emit(self.combo_box.currentText()))

    def set_current_index(self, index):
        self.combo_box.setCurrentIndex(index)

    @property
    def get_selected_item(self):
        return self.combo_box.currentText()