from PyQt5.QtWidgets import QMessageBox, QWidget
from enums.message_box_type import MessageBoxTypeEnum

class CustomMessageBox():
    def __init__(self, title, message, parent: QWidget=None, informative_message="", icon=MessageBoxTypeEnum.Information.value, buttons=QMessageBox.Ok) -> None:
        self.parent = parent
        self.title = title
        self.icon = icon
        self.buttons = buttons
        self.message = message
        self.informative_message = informative_message

    def show(self): 
        message_box = QMessageBox(self.parent)
        
        message_box.setWindowTitle(self.title)
        message_box.setIcon(self.icon)
        message_box.setText(self.message)
        message_box.setInformativeText(self.informative_message)
        message_box.setStandardButtons(self.buttons)

        return message_box.exec_()
