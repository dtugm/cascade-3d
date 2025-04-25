import os
import time
import shutil

from .interface import RoofFootprintParams

from utils.common import get_base_dir

from PyQt5.QtCore import QObject, pyqtSignal

class GenerateRoofFootprint(QObject):
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(str, int)
    error = pyqtSignal(str)

    def __init__(self, params: RoofFootprintParams, parent = None):
        super().__init__(parent)
        self.args: RoofFootprintParams = params

        # for temorary data
        self.temp_path = os.path.join(get_base_dir(), "temp")
        self.aspect_tif = os.path.join(self.temp_path, "aspect.tif")
        self.aspect_shp = os.path.join(self.temp_path, "aspect.shp")

    def run(self):
        self.progress.emit("Start Creating Roof Footprint ...", 0)

        if not os.path.exists(self.temp_path):
            os.makedirs(self.temp_path)
            self.progress.emit(f"Temporary directory : '{self.temp_path}' has been made", 5)

        try:
            pass
        except Exception as e:
            print(f"Error : {e}")
            self.error.emit(str(e))
        
        finally:
            if os.path.exists(self.temp_path):
                self.progress.emit(f"Remove Temporary Directory : '{self.temp_path}'", 95)
                shutil.rmtree(self.temp_path)

            self.finished.emit("Finished", 100)