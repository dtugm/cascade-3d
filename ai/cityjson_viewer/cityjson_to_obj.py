import os
import json
import os
import shutil

from tqdm import tqdm

from PyQt5.QtCore import QObject, pyqtSignal

from .interface import Cityjson2ObjParams

class Cityjson2Obj(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, params: Cityjson2ObjParams, parent = None):
        super().__init__(parent)
        self.args: Cityjson2ObjParams = params

    def run(self):
        if not os.path.exists(self.args.temp_dir):
            os.makedirs(self.args.temp_dir)

        try:
            with open(self.args.cityjson_path, 'r') as f:
                cityjson_data = json.load(f)

            vertices = cityjson_data.get("vertices", [])
            city_objects = cityjson_data.get("CityObjects", {})

            with tqdm(city_objects.items(), desc="Preparing City Object", unit="Object") as pbar:
                for idx, (obj_id, city_object) in enumerate(pbar):
                    obj_content = []
                    for vertex in vertices:
                        obj_content.append(f"v {vertex[0]} {vertex[1]} {vertex[2]}")

                    geometry = city_object.get("geometry", [])
                    for geom in geometry:
                        if geom.get("type") == "Solid":
                            for shell in geom.get("boundaries", []):
                                for face in shell:
                                    if isinstance(face[0], list):
                                        face = [vid for sublist in face for vid in sublist]
                                    face_indices = [f"{vid + 1}" for vid in face]
                                    obj_content.append(f"f {' '.join(face_indices)}")

                    obj_file = os.path.join(self.args.temp_dir, f"{obj_id}.obj")
                    with open(obj_file, 'w') as objf:
                        objf.write("\n".join(obj_content))

                    progress = int((idx+1)/pbar.total*80)
                    self.progress.emit(progress)

        except Exception as e:
            print(f"Error : {e}")
            self.error.emit(str(e))
        
        finally:
            # if os.path.exists(self.args.temp_dir):
            #     shutil.rmtree(self.args.temp_dir)

            self.finished.emit()