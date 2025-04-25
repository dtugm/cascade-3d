from PyQt5 import QtWidgets

class ToggleAction(QtWidgets.QAction):
    def __init__(self, text, icon, parent=None):
        super().__init__(text, parent)
        self.setIcon(icon)
        self.setCheckable(False)

    def createWidget(self, parent):
        widget = QtWidgets.QToolButton(parent)
        widget.setText(self.text()) 
        widget.setIcon(self.icon())
        return widget
    
    def handle_click(self, is_cheked):
        self.setCheckable(is_cheked)
        self.setChecked(is_cheked)
        self.toggled.emit(is_cheked)