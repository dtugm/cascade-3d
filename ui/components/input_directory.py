from PyQt5 import QtWidgets, QtCore
from ui.components.button import Button
from utils.common import outline_stylesheet

class DirectoryInputComponent(QtWidgets.QWidget):
    dir_selected = QtCore.pyqtSignal(str)
    def __init__(
            self, 
            label="", 
            button_name="...", 
            button_width=40, 
            button_font_color="black", 
            button_color="#017FA7",  
            defaultValue="",
            parent=None):
        super().__init__(parent)

        self.label = label
        self.button_name = button_name
        self.button_width = button_width
        self.button_color = button_color
        self.button_font_color = button_font_color
        self.defaultValue = defaultValue

        self.dir_name = defaultValue if defaultValue else ""

        self.init_ui()

    @property
    def input_value(self):
        return self.dir_name
    
    def set_value(self, dir_path):
        self.dir_name = dir_path
        self.dir_field.setText(dir_path)

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)

        label = QtWidgets.QLabel(self.label)
        layout.addWidget(label)

        button_hbox = QtWidgets.QHBoxLayout()
        button_hbox.minimumSize()
        layout.addLayout(button_hbox)

        # Text field to display filename
        self.dir_field = QtWidgets.QLineEdit()
        self.dir_field.setReadOnly(True)
        self.dir_field.setMinimumHeight(25)
        self.dir_field.setStyleSheet(outline_stylesheet)
        if self.defaultValue:
            self.dir_field.setText(self.defaultValue)
        button_hbox.addWidget(self.dir_field)

        # Button to choose directory
        self.choose_directory_button = Button(
            name=self.button_name, 
            button_color=self.button_color, 
            button_font_color=self.button_font_color,
            fixed_width=self.button_width)
        self.choose_directory_button.clicked.connect(self.get_directory)
        button_hbox.addWidget(self.choose_directory_button)

    def get_directory(self):
        # Open a file dialog for saving
        dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")

        if dir:
            # update the text field with the choosen directory
            self.dir_field.setText(dir)
            # emit the signal with the choosen directory
            self.dir_name = dir
            self.dir_selected.emit(dir)


