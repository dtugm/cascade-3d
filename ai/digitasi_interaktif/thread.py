from PyQt5 import QtCore
import threading

class MyThread(QtCore.QObject, threading.Thread):
    finished_signal = QtCore.pyqtSignal()

    def __init__(self, target, args=()):
        super().__init__(target=target, args=args)

    def run(self):
        super().run()  # Call the parent's run method
        self.finished_signal.emit()  # Emit the signal when finished