from PyQt5 import QtWidgets, QtCore
from ui.components.button import Button
from utils.common import outline_stylesheet
from utils.handle_input import validate_file_extension

class FileInputComponent(QtWidgets.QWidget):
    file_selected = QtCore.pyqtSignal(str)
    def __init__(
            self, 
            label="", 
            button_name="...", 
            button_width=40, 
            button_font_color="black", 
            button_color="#017FA7",  
            defaultValue="",
            ext=[],
            parent=None):
        super().__init__(parent)

        self.label = label
        self.button_name = button_name
        self.button_width = button_width
        self.button_color = button_color
        self.button_font_color = button_font_color
        self.ext = ext

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
        if self.filename:
            self.filename_field.setText(self.filename)
        button_hbox.addWidget(self.filename_field)

        # Button to choose file
        self.choose_file_button = Button(
            name=self.button_name, 
            button_color=self.button_color, 
            button_font_color=self.button_font_color,
            fixed_width=self.button_width)
        self.choose_file_button.clicked.connect(self.get_file_name)
        button_hbox.addWidget(self.choose_file_button)

    def get_file_name(self):
        # Open file dialog for choosing a file
        options = QtWidgets.QFileDialog.Options()
        # Optionally, restrict to directories: options |= QFileDialog.ShowDirsOnly
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*);;Text Files (*.txt)", options=options)

        if filename and validate_file_extension(filename, self.ext, parent=self):
            # Update the text field with the chosen filename
            self.filename_field.setText(filename)
            # Emit the signal with the chosen filename
            self.filename = filename
            self.file_selected.emit(filename)

    def set_value(self, val: str):
        self.filename = val
        self.filename_field.setText(val)

