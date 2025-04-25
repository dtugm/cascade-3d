from enum import Enum
from PyQt5.QtWidgets import QMessageBox

class MessageBoxTypeEnum(Enum):
    Information = QMessageBox.Information
    Question = QMessageBox.Question
    Warning = QMessageBox.Warning
    Critical = QMessageBox.Critical