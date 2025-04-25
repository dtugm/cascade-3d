from ._cityjson import create_model
from .multipart_to_singlepart import multipart_to_singlepart
from .generate_uuid import generate_uuid
from .interface import Py3dModelConfig

from PyQt5 import QtCore

class GenerateLOD1(QtCore.QObject):
    progress = QtCore.pyqtSignal(str, int)
    finished = QtCore.pyqtSignal(str, int)
    error = QtCore.pyqtSignal(str)

    def __init__(self, config: Py3dModelConfig, parent = None) -> None:
        super().__init__(parent)
        self.config = config

    def run(self):
        try:
            self.progress.emit("Generating LOD 1", 0)

            self.progress.emit("Convert Multipart to Singlepart", 10)
            multipart_to_singlepart(self.config.input_building, self.config.input_building)

            self.progress.emit("Generate UUID", 20)
            generate_uuid(self.config.input_building, fieldname="uuid_bgn", id_type="uuid", overwrite=True)

            self.progress.emit("Create model", 50)
            create_model(self.config)

            self.finished.emit("Finished", 100)
        except Exception as e:
            print(f"Error : {e}")
            self.error.emit(str(e))
        