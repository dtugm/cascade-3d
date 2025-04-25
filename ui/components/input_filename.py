from PyQt5 import QtWidgets, QtCore
from ui.components.button import Button
from utils.common import outline_stylesheet

class FilenameInputComponent(QtWidgets.QWidget):
    file_selected = QtCore.pyqtSignal(str)
    def __init__(
            self, 
            label="", 
            button_name="...", 
            button_width=40, 
            button_font_color="black", 
            button_color="#017FA7",  
            filetype="json",
            defaultValue="",
            parent=None):
        super().__init__(parent)

        self.label = label
        self.button_name = button_name
        self.button_width = button_width
        self.button_color = button_color
        self.button_font_color = button_font_color
        self.filetype = filetype

        self.filename = defaultValue

        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)

        label = QtWidgets.QLabel(self.label)
        layout.addWidget(label)

        button_hbox = QtWidgets.QHBoxLayout()
        button_hbox.minimumSize()
        layout.addLayout(button_hbox)

        # Text field to display filename
        self.filename_field = QtWidgets.QLineEdit()
        self.filename_field.setReadOnly(True)
        self.filename_field.setMinimumHeight(25)
        self.filename_field.setStyleSheet(outline_stylesheet)
        button_hbox.addWidget(self.filename_field)
        if self.filename:
            self.filename_field.setText(self.filename)

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
        type = f"{self.filetype.upper()} Files (*.{self.filetype})" if self.filetype else f"All Files (*)"
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", "", type)

        if filename:
            # update the text field with the choosen directory
            self.filename_field.setText(filename)
            # emit the signal with the choosen directory
            self.filename = filename
            self.file_selected.emit(filename)


