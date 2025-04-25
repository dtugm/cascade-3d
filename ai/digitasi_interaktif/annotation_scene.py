from PyQt5 import QtWidgets, QtCore, QtGui
from PIL import Image

from .annotation_polygon import PolygonAnnotation
from .thread import MyThread
from .di_enum import Instructions
from .line_annotation import LineAnnotation

from utils.regularisation_v2 import (
    get_angles_and_coords, 
    rotate_gdf, 
    create_grids,
    filter_grids_based_on_actual_geometry,
    filter_grids_based_on_rotated_geometry,
    to_gdf)
from utils.converter import to_json, Converter
from utils.raster_metadata import Meta

from ai.sam.runner_sam import SAM


from shapely.geometry import Polygon, MultiPolygon, Point, LineString
from shapely.ops import split
from shapely import simplify, union

import numpy as np
import cv2

import os
import subprocess

class AnnotationScene(QtWidgets.QGraphicsScene):
    started = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(str)
    on_drag_image = QtCore.pyqtSignal(QtCore.QEvent, int)

    def __init__(self, parent=None):
        super(AnnotationScene, self).__init__(parent)
        self.image_item = None

        self.is_open_file: bool = False

        self.initiate_scene_variables()

    def load_image(self, filename):
        self.started.emit("Load file. Please wait ...")

        self.file_path = filename
        self.image = Image.open(filename)
        self.sam.load_image(self.image)
        
        self.image_item.setPixmap(QtGui.QPixmap(filename))
        self.setSceneRect(self.image_item.boundingRect())
        
        self.finished.emit("Successfully saved building outline data.")


    def setCurrentInstruction(self, instruction):
        self.current_instruction = instruction
        # self.polygon_item = PolygonAnnotation()
        # self.addItem(self.polygon_item)

    # def keyReleaseEvent(self, event) -> None:  # new
    #     if event.key() == QtCore.Qt.Key.Key_Escape and self.current_instruction == Instructions.No_Instruction:
    #         pt = QtCore.QPointF(self.last_mouse_location[0], self.last_mouse_location[1])
    #         self.polygon_item.removeLastPoint()
    #         self.polygon_item.addPoint(pt)
    #         super(AnnotationScene, self).keyReleaseEvent(event)

    def add_merge_points(self, pos: QtCore.QPointF):
        is_intersect = False
        point = Point(pos.x(), pos.y())

        for idx, polygon in enumerate(self.polygons):
            if polygon.contains(point):
                is_intersect = True
                self.merge_points.append((pos.x(), pos.y()))
                self.merge_idx.append(idx)
                self.merge_polygon_list.append(polygon)
                break
        
        if is_intersect:
            size = 6
            color = QtGui.QColor("yellow")

            point_item = QtWidgets.QGraphicsEllipseItem(pos.x() - (size/2), pos.y() - (size/2), size, size)
            point_item.setPen(QtGui.QPen(color))
            point_item.setBrush(QtGui.QBrush(color))

            self.addItem(point_item)

    def remove_polygon(self, pos: QtCore.QPointF):
        point = Point(pos.x(), pos.y())
        
        for idx, polygon in enumerate(self.polygons):
            if polygon.contains(point):
                self.remove_polygon_by_index(idx)
                break

        self.remove_all_polygons(in_scene_only=True)    
        self.draw_polygons()
    
    def simplify_polygon(self, pos: QtCore.QPointF):
        point = Point(pos.x(), pos.y())

        for idx, polygon in enumerate(self.polygons):
            if polygon.contains(point):
                simplified_polygon = simplify(polygon, tolerance=self.simplify_tolerance)
                qt_polygon, contour = self.shapely_polygon_to_qpolygonf_and_contour(simplified_polygon)

                self.polygons[idx] = simplified_polygon
                self.qt_polygons[idx] = qt_polygon
                self.contours[idx] = contour
                break

        self.remove_all_polygons(in_scene_only=True)    
        self.draw_polygons()

    def add_red_points(self, pos: QtCore.QPointF):
        self.red_points.append(pos)
        
        size = 6
        color = QtGui.QColor("red")
        point_item = QtWidgets.QGraphicsEllipseItem(pos.x() - (size/2), pos.y() - (size/2), size, size)
        point_item.setPen(QtGui.QPen(color))
        point_item.setBrush(QtGui.QBrush(color))
        self.addItem(point_item)
    
    def remove_red_points(self):
        for item in self.items():
            if isinstance(item, QtWidgets.QGraphicsEllipseItem):
                self.removeItem(item)     
    
    def regularisation(self, pos: QtCore.QPointF):
        point = Point(pos.x(), pos.y())

        thread = MyThread(target=self.process_regularisation, args=(point,))
        thread.finished_signal.connect(self.restart_scene)
        thread.start()

    def process_regularisation(self, point):
        self.started.emit("Start regularisation")
        
        for idx, polygon in enumerate(self.polygons):
            if polygon.contains(point):
                gdf = to_gdf([polygon])
                anglest, coords = get_angles_and_coords(gdf)
                # rotate polygon
                rotated_gdf = rotate_gdf(gdf, -anglest)
                rotated_grids = create_grids(rotated_gdf, grid_size=10)

                filtered_grids = filter_grids_based_on_rotated_geometry(rotated_grids, rotated_gdf)
                # rotate gdf back
                grids = filtered_grids.rotate(anglest, origin=gdf.centroid.item())
                # Convert to GeoDataFrame using a dictionary
                grids = to_gdf(grids, case=True)
                filtered_grids = filter_grids_based_on_actual_geometry(grids, polygon)

                regularisated = filtered_grids.unary_union
                qt_polygon, contour = self.shapely_polygon_to_qpolygonf_and_contour(regularisated)

                self.polygons[idx] = regularisated
                self.qt_polygons[idx] = qt_polygon
                self.contours[idx] = contour
                break
    
        self.finished.emit("Regularisation finished")

    def predict(self, pos: QtCore.QPointF):
        contour = self.sam.predict([pos], self.red_points)
        self.draw_polygon(contour)
        self.restart_scene()

    def restart_scene(self):
        self.remove_all_polygons(in_scene_only=True)
        self.draw_polygons()

    def initiate_scene_variables(self):
        if self.image_item is not None:
            image_to_reset = self.image_item
            self.removeItem(image_to_reset)

        self.remove_all_polygons(is_include_ellipse=True)

        self.image_item = QtWidgets.QGraphicsPixmapItem()
        self.image_item.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        self.addItem(self.image_item)

        self.current_instruction = Instructions.No_Instruction

        self.last_mouse_location = [0, 0]  # new

        self.file_path: str = ''

        self.sam = SAM()
        self.contours = []
        self.qt_polygons = []
        self.polygons = []
        self.merge_points = []
        self.merge_idx = []
        self.merge_polygon_list = []
        self.red_points = []
        self.circle_items = []
        self.line_items = []

        self.simplify_tolerance = 1
        self.simplify_all_tolerance = 1

        self.cur_pos = QtCore.QPointF()
    
    def set_simplify_tolerance(self, value: str):
        min_val = 1
        max_val = 5
        if value:
            self.simplify_tolerance = min(max(float(value.replace(",", ".")), min_val), max_val)
        else:
            self.simplify_tolerance = 1
    
    def set_simplify_all_tolerance(self, value: str):
        min_val = 1
        max_val = 5
        if value:
            self.simplify_all_tolerance = min(max(float(value.replace(",", ".")), min_val), max_val)
        else:
            self.simplify_all_tolerance = 1

    def simplify_all_polygons(self):
        if not len(self.polygons):
            return
        
        for idx, polygon in enumerate(self.polygons):
            simplified_polygon = simplify(polygon, tolerance=self.simplify_all_tolerance)
            qt_polygon, contour = self.shapely_polygon_to_qpolygonf_and_contour(simplified_polygon)

            self.polygons[idx] = simplified_polygon
            self.qt_polygons[idx] = qt_polygon
            self.contours[idx] = contour
        
        self.restart_scene()
    
    def merge_polygons(self):
        if not len(self.merge_idx):
            return
        
        self.merge_idx.sort(reverse=True) # sorted descendingly
        res_idx = self.merge_idx.pop()
        merged_polygon = self.polygons[res_idx]

        for idx in self.merge_idx:
            # Define a buffer distance
            buffer_distance = 0.5

            # Create buffers around each polygon
            buffered_polygon1 = merged_polygon.buffer(buffer_distance)
            buffered_polygon2 = self.polygons[idx].buffer(buffer_distance)

            temp = union(buffered_polygon1, buffered_polygon2)
            
            if not self.is_multipolygon(temp):
                self.remove_polygon_by_index(idx)

                merged_polygon = temp

        qt_polygon, contour = self.shapely_polygon_to_qpolygonf_and_contour(merged_polygon)
        self.qt_polygons[res_idx] = qt_polygon
        self.contours[res_idx] = contour
        self.polygons[res_idx] = merged_polygon

        self.merge_idx = []
        self.remove_all_polygons(in_scene_only=True, is_include_ellipse=True)
        self.draw_polygons()


    def shapely_polygon_to_qpolygonf_and_contour(self, shapely_polygon):
        """Converts a Shapely Polygon to a QPolygonF object."""
        qpoint_f_list = []
        contour = []
        for coord in shapely_polygon.exterior.coords:
            qpoint_f_list.append(QtCore.QPointF(*coord))

            contour.append([[int(coord[0]), int(coord[1])]])
        return QtGui.QPolygonF(qpoint_f_list), np.array(contour)
    
    def qpolygonf_to_shapely_polygon(self, qpolygon_f):
        """Converts a QPolygonF to a Shapely Polygon object."""
        # Extract coordinates from QPointF objects
        shapely_coords = [np.array([point.x(), point.y()]) for point in qpolygon_f]
        # Create a Shapely Polygon (assuming a linear ring)
        return Polygon(shapely_coords)
    
    def contour_to_shapely_polygon_and_qpolygonf(self, contour):
        q_points = []
        points = []
        for point in contour.reshape(-1, 2):
            q_points.append(QtCore.QPointF(point[0], point[1]))
            points.append(np.array([point[0], point[1]]))

        return Polygon(points), QtGui.QPolygonF(q_points)
    

    def draw_polygons(self):
        for polygon in self.qt_polygons:
            polygon_item = QtWidgets.QGraphicsPolygonItem(polygon)
            polygon_item.setZValue(10)
            polygon_item.setPen(QtGui.QPen(QtGui.QColor("yellow"), 2))
            polygon_item.setAcceptHoverEvents(True)

            self.addItem(polygon_item)
        
    def is_multipolygon(self, data):
        if isinstance(data, MultiPolygon):
            return True
        return False
    
    def check_intersection_and_merge_polygons(self, polygon: Polygon):
        is_intersect = False
        intersect_idx = []
        if len(self.polygons):
            for idx, plg in enumerate(self.polygons):
                intersection = polygon.intersection(plg)
                if intersection.area > 0:
                    intersect_idx.append(idx)

        if len(intersect_idx):
            is_intersect = True
            merged_polygon = polygon
            if len(intersect_idx) == 1:
                merged_polygon = polygon.union(self.polygons[intersect_idx[0]])
                if not self.is_multipolygon(merged_polygon):
                    self.remove_polygon_by_index(intersect_idx[0])

                    polygon = merged_polygon
            else:
                for idx in reversed(intersect_idx):
                    temp = merged_polygon.union(self.polygons[idx])
                    
                    if not self.is_multipolygon(temp):
                        self.remove_polygon_by_index(idx)

                        merged_polygon = temp
                polygon = merged_polygon

        return is_intersect, polygon
    
    def draw_polygon(self, contour=None):
        if contour is None:
            return

        # convert contour to shapely polygon and qt polygon
        polygon, qt_polygon = self.contour_to_shapely_polygon_and_qpolygonf(contour)
        
        # check whether or not the current polygon have intersection with other existing polygons
        is_intersect, polygon = self.check_intersection_and_merge_polygons(polygon)

        qt_polygon, contour = self.shapely_polygon_to_qpolygonf_and_contour(polygon)
        self.polygons.append(polygon)
        self.qt_polygons.append(qt_polygon)
        self.contours.append(contour)

        self.red_points = []

        if is_intersect:
            self.restart_scene()
        else:
            polygon_item = QtWidgets.QGraphicsPolygonItem(qt_polygon)
            polygon_item.setZValue(10)
            polygon_item.setPen(QtGui.QPen(QtGui.QColor("yellow"), 2))
            polygon_item.setAcceptHoverEvents(True)

            self.addItem(polygon_item)
        
    def remove_all_polygons(self, in_scene_only: bool = False, is_include_ellipse: bool = False):
        for item in self.items():
            if isinstance(item, QtWidgets.QGraphicsPolygonItem):
                self.removeItem(item)

            if isinstance(item, QtWidgets.QGraphicsEllipseItem) and is_include_ellipse:
                self.removeItem(item) 

            if isinstance(item, QtWidgets.QGraphicsLineItem):
                self.removeItem(item)           

        if not in_scene_only:
            self.polygons = []
            self.qt_polygons = []
            self.contours = []
    
    def export(self, output_path=None):
        if not self.sam.predictor.is_image_set:
            return
        
        if output_path is None:
            output_path = json_path.replace(".json", ".geojson")
        
        json_path = to_json(self.polygons, self.file_path.replace(".tif", ".json"), self.image.height)
        # json_path = to_json(self.contours, self.file_path.replace(".tif", ".json"), self.image.height)

        # to geojson
        metadata = Meta(self.file_path) 
        ext = metadata.get_extent_from_raster()
        epsg = metadata.get_epsg_from_raster()

        # output_path = json_path.replace(".json", ".geojson")
        Converter(json_path, output_path, epsg, ext, self.image.height).to_geojson()

        if self.is_open_file:
            folderpath = os.path.dirname(output_path)
            path = os.path.realpath(folderpath)
            subprocess.Popen(f"explorer {path}")

    def remove_polygon_by_index(self, index):
        del self.polygons[index]
        del self.qt_polygons[index]
        del self.contours[index]
        
    # Remove Vertex
    def add_circle(self, circle_item):
        self.addItem(circle_item)
        self.circle_items.append(circle_item)
    
    def get_last_circle_item(self):
        last_idx = len(self.circle_items) - 1
        return self.circle_items[last_idx]
    
    def remove_vertex_coordinates(self):
        circle_point = self.get_last_circle_item()

        if len(self.polygons):
            for index, polygon in enumerate(self.polygons):
                coords = list(polygon.exterior.coords)

                ids_to_remove = []
                for i in range(len(coords)):
                    point = QtCore.QPointF(coords[i][0], coords[i][1])
                    if circle_point.contains(point):
                        ids_to_remove.append(i)

                if len(ids_to_remove):
                    new_coord = [coords[i] for i in range(len(coords)) if i not in ids_to_remove]
                    if len(new_coord) < 4:
                        self.remove_polygon_by_index(index)
                    else:
                        new_polygon = Polygon(new_coord)
                        qt_polygon, contour = self.shapely_polygon_to_qpolygonf_and_contour(new_polygon)
                        self.polygons[index] = new_polygon
                        self.qt_polygons[index] = qt_polygon
                        self.contours[index] = contour
            
        self.remove_all_polygons(in_scene_only=True, is_include_ellipse=True)
        self.draw_polygons()

    # Split polygon
    def add_line(self, line_item):
        self.addItem(line_item)
        self.line_items.append(line_item)
    
    def get_last_line_item(self):
        last_idx = len(self.line_items) - 1
        return self.line_items[last_idx]

    def split_polygon(self):
        line_item: LineAnnotation = self.get_last_line_item()
        linestring = LineString([
            (line_item.start_point.x(), line_item.start_point.y()),
            (line_item.end_point.x(), line_item.end_point.y())
            ])

        if len(self.polygons):
            for index, polygon in enumerate(self.polygons):
                if polygon.intersects(linestring):
                    polygons = split(polygon, linestring)
                    
                    for idx, polygon in enumerate(polygons.geoms):
                        qt_polygon, contour = self.shapely_polygon_to_qpolygonf_and_contour(polygon)
                        if idx == 0:
                            self.polygons[index] = polygon
                            self.qt_polygons[index] = qt_polygon
                            self.contours[index] = contour
                        else:
                            self.polygons.append(polygon)
                            self.qt_polygons.append(qt_polygon)
                            self.contours.append(contour)

        self.remove_all_polygons(in_scene_only=True)
        self.draw_polygons()
