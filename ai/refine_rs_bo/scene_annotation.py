import cv2
import os
import subprocess
from PIL import Image

import geopandas as gpd
from PyQt5 import QtWidgets, QtCore, QtGui

from shapely.geometry import Polygon, Point
from shapely import simplify

from utils.geojson_processing import GeojsonProcessing
from utils.raster_metadata import Meta

from ui.components.message_box import CustomMessageBox
from ai.refine_rs_bo.polygon_annotation import PolygonAnnotation

from enums.message_box_type import MessageBoxTypeEnum
from enums.refine_rs_bo.instruction_type import Instructions


from utils.common import raster_to_png, get_file_extension

class AnnotationScene(QtWidgets.QGraphicsScene):
    started = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()
    on_drag_image = QtCore.pyqtSignal(QtCore.QEvent, int)

    def __init__(self, parent=None):
        super(AnnotationScene, self).__init__(parent)
        self.image_item = None

        self.is_open_file: bool = False

        self.initiate_scene_variables()

    def load_image(self, filepath=""):
        self.metadata = Meta(filepath)
        self.epsg = self.metadata.get_epsg_from_raster()
        self.extent = self.metadata.get_extent_from_raster()

        self.image = Image.open(filepath)

        self.image_item = QtWidgets.QGraphicsPixmapItem()
        self.image_item.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        self.addItem(self.image_item)

        self.image_item.setPixmap(QtGui.QPixmap(filepath))
        self.setSceneRect(self.image_item.boundingRect())


    def load_rs(self, filepath: str):
        self.rs_file = filepath

        if get_file_extension(filepath) == "shp":
            output_path = filepath.replace(".shp", "_res.geojson")
        else:
            output_path = filepath.replace(".geojson", "_res.geojson")

        # Read data from shapefile
        self.rs_gdf = gpd.read_file(filepath)

        self.rs_converter = GeojsonProcessing(
            self.rs_gdf, 
            output_path, 
            self.image.size,
            self.metadata.get_epsg_from_raster(), 
            self.metadata.get_extent_from_raster())
        self.rs_gdf = self.rs_converter.reduce_coordinates_values()

        self.refresh_scene()
    
    def load_bo(self, filepath: str):
        self.bo_file = filepath
        
        if get_file_extension(filepath) == "shp":
            output_path = filepath.replace(".shp", "_res.geojson")
        else:
            output_path = filepath.replace(".geojson", "_res.geojson")

        # Read data from shapefile
        self.bo_gdf = gpd.read_file(filepath)

        self.bo_converter = GeojsonProcessing(
            self.bo_gdf, 
            output_path, 
            self.image.size,
            self.metadata.get_epsg_from_raster(), 
            self.metadata.get_extent_from_raster())
        self.bo_gdf = self.bo_converter.reduce_coordinates_values()

        self.refresh_scene()

    def setCurrentInstruction(self, instruction):
        self.current_instruction = instruction

    def initiate_scene_variables(self):
        self.remove_all_polygons()

        self.current_instruction = Instructions.No_Instruction

        self.rs_file: str = ""
        self.bo_file: str = ""
        self.image: Image = None

        self.rs_gdf = None
        self.bo_gdf = None

        self.simplify_tolerance = 1
        self.points = []

    def is_ready(self):
        if self.rs_gdf is None and self.bo_gdf is None:
            message = CustomMessageBox(
                "Warning", 
                "You have to load the appropriate file first", 
                icon=MessageBoxTypeEnum.Warning.value)
            message.show()
            return False
        else: 
            return True

    def refresh_scene(self):
        self.remove_all_polygons()
        self.displaying_gdf()
    
    def set_simplify_tolerance(self, value: str):
        min_val = 1
        max_val = 5
        if value:
            self.simplify_tolerance = min(max(float(value.replace(",", ".")), min_val), max_val)
        else:
            self.simplify_tolerance = 1

    def move_vertex_coordinates(self):
        circle_point = self.get_last_point()

        if self.rs_gdf is not None:
            for index, row in self.rs_gdf.iterrows():
                geometry = row["geometry"]
                if geometry.geom_type == "Polygon":
                    # for circle_point in self.points:
                    coords = list(geometry.exterior.coords)
                    for i in range(len(coords)):
                        point = QtCore.QPointF(coords[i][0], coords[i][1])
                        if circle_point.contains(point):
                            coords[i] = circle_point.get_center()
                    self.rs_gdf.loc[index, "geometry"] = Polygon(coords)

        if self.bo_gdf is not None:
            for index, row in self.bo_gdf.iterrows():
                geometry = row["geometry"]
                if geometry.geom_type == "Polygon":
                    coords = list(geometry.exterior.coords)
                    for i in range(len(coords)):
                        point = QtCore.QPointF(coords[i][0], coords[i][1])
                        if circle_point.contains(point):
                            coords[i] = circle_point.get_center()
                    self.bo_gdf.loc[index, "geometry"] = Polygon(coords)

        self.refresh_scene()

    def remove_vertex_coordinates(self):
        circle_point = self.get_last_point()

        if self.rs_gdf is not None:
            for index, row in self.rs_gdf.iterrows():
                geometry = row["geometry"]
                if geometry.geom_type == "Polygon":
                    coords = list(geometry.exterior.coords)

                    ids_to_remove = []
                    for i in range(len(coords)):
                        point = QtCore.QPointF(coords[i][0], coords[i][1])
                        if circle_point.contains(point):
                            ids_to_remove.append(i)

                    if len(ids_to_remove):
                        new_coord = [coords[i] for i in range(len(coords)) if i not in ids_to_remove]
                        if len(new_coord) < 4:
                            self.rs_gdf.drop(index, inplace=True)
                        else:
                            self.rs_gdf.loc[index, "geometry"] = Polygon(new_coord)

        if self.bo_gdf is not None:
            for index, row in self.bo_gdf.iterrows():
                geometry = row["geometry"]
                if geometry.geom_type == "Polygon":
                    ids_to_remove = []

                    coords = list(geometry.exterior.coords)
                    for i in range(len(coords)):
                        point = QtCore.QPointF(coords[i][0], coords[i][1])
                        if circle_point.contains(point):
                            ids_to_remove.append(i)

                    if len(ids_to_remove):
                        new_coord = [coords[i] for i in range(len(coords)) if i not in ids_to_remove]
                        if len(new_coord) < 4:
                            self.bo_gdf.drop(index, inplace=True)
                        else:
                            self.bo_gdf.loc[index, "geometry"] = Polygon(new_coord)

        self.refresh_scene()    
    
    def simplify_polygon(self, pos: QtCore.QPointF):
        point = Point(pos.x(), pos.y())

        if self.rs_gdf is not None:
            for index, row in self.rs_gdf.iterrows():
                geometry = row["geometry"]
                if geometry.geom_type == "Polygon" and point.within(geometry):
                    simplified_rs_geom = simplify(geometry, tolerance=self.simplify_tolerance)
                    self.rs_gdf.loc[index, "geometry"] = simplified_rs_geom

        if self.bo_gdf is not None:
            for index, row in self.bo_gdf.iterrows():
                geometry = row["geometry"]
                if geometry.geom_type == "Polygon" and point.within(geometry):
                    simplified_bo_geom = simplify(geometry, tolerance=self.simplify_tolerance)
                    self.bo_gdf.loc[index, "geometry"] = simplified_bo_geom

        self.refresh_scene()
    

    def remove_all_polygons(self, in_scene_only: bool = False):
        for item in self.items():
            if isinstance(item, QtWidgets.QGraphicsPolygonItem):
                self.removeItem(item)  

            if isinstance(item, QtWidgets.QGraphicsEllipseItem):
                self.removeItem(item)            

    def displaying_gdf(self):
        if self.rs_gdf is not None:
            for index, row in self.rs_gdf.iterrows():
                geometry = row["geometry"]
                if geometry.geom_type == "Polygon":
                    polygon_item = PolygonAnnotation(geometry, color="#ffddff")
                    self.addItem(polygon_item)

        if self.bo_gdf is not None:
            for index, row in self.bo_gdf.iterrows():
                geometry = row["geometry"]
                if geometry.geom_type == "Polygon":
                    polygon_item = PolygonAnnotation(geometry, color="yellow")
                    self.addItem(polygon_item)
        
    
    def export(self, output_path: str):
        if not self.is_ready():
            return
        
        try:
            if self.rs_gdf is not None:
                rs_gdf = self.rs_gdf.copy()
                rs_gdf = self.rs_converter.revert_coordinates_values(rs_gdf)
                self.rs_converter.save_to_file(rs_gdf, output_path.replace(".geojson", "-rs.geojson"))

            if self.bo_gdf is not None:
                bo_gdf = self.bo_gdf.copy()
                bo_gdf = self.bo_converter.revert_coordinates_values(bo_gdf)
                self.bo_converter.save_to_file(bo_gdf, output_path.replace(".geojson", "-bo.geojson"))
        except Exception as e:
            message_box = CustomMessageBox("Warning", str(e), icon=MessageBoxTypeEnum.Critical.value, parent=self.parent())
        else:
            message_box = CustomMessageBox("Information", "Export file success", parent=self.parent())
        
        message_box.show()

        if self.is_open_file:
            folderpath = os.path.dirname(output_path)
            path = os.path.realpath(folderpath)
            subprocess.Popen(f"explorer {path}")

    def add_points(self, circle_item, instruction):
        self.addItem(circle_item)
        self.points.append([circle_item, instruction])
    
    def get_last_point(self):
        last_idx = len(self.points) - 1
        return self.points[last_idx][0]
