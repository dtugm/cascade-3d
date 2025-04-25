from PyQt5 import QtWidgets, QtGui, QtCore
from .annotation_scene import AnnotationScene
from .di_enum import Instructions
from .circle_annotation import CircleAnnotation
from .line_annotation import LineAnnotation
class AnnotationView(QtWidgets.QGraphicsView):
    factor = 1.1

    def __init__(self, scene: AnnotationScene, parent=None):
        super(AnnotationView, self).__init__(parent)
        self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        self.setMouseTracking(True)
        QtWidgets.QShortcut(QtGui.QKeySequence.ZoomIn, self, activated=self.zoomIn)
        QtWidgets.QShortcut(QtGui.QKeySequence.ZoomOut, self, activated=self.zoomOut)

        self.scen = scene
        
        self._left_button_pressed = False
        self.__prevMousePos = QtCore.QPointF
        self._circle_item_pos = QtCore.QPointF
        self._mouse_move = False

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.handle_right_click)

    def handle_right_click(self, point):
        menu = QtWidgets.QMenu()

        menu.addAction("Merge", self.scen.merge_polygons)
        menu.addAction("Remove All Red Points", self.scen.remove_red_points)

        menu.exec_(self.mapToGlobal(point))


    def wheelEvent(self, event):
        delta = event.angleDelta().y()

        factor = AnnotationView.factor
        if delta < 0:
            factor = 1 / AnnotationView.factor
        # if delta > 0:
        #     self.zoom(AnnotationView.factor, event)
        # else:
        #     self.zoom(1 / AnnotationView.factor, event)
        
        view_pos = event.pos()
        scene_pos = self.mapToScene(view_pos)
        self.centerOn(scene_pos)
        self.scale(factor, factor)
        delta = self.mapToScene(view_pos) - self.mapToScene(self.viewport().rect().center())
        self.centerOn(scene_pos - delta)

        super().wheelEvent(event)
    
    def mousePressEvent(self, event):
        if self.scen.sam.predictor.is_image_set and event.button() == QtCore.Qt.LeftButton:
            self.__prevMousePos = event.pos()
            self._left_button_pressed = True
            
            mapped_pos = self.mapToScene(event.pos())

            if self.scen.current_instruction == Instructions.Remove_Vertex:
                self._circle_item_pos = mapped_pos

                circle_item = CircleAnnotation(mapped_pos)
                self.scen.add_circle(circle_item)

            elif self.scen.current_instruction == Instructions.Split:
                line_item = LineAnnotation(mapped_pos)
                self.scen.add_line(line_item)

        else:
            super(AnnotationView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        mapped_pos = self.mapToScene(event.pos())
        self._mouse_move = True

        if self._left_button_pressed and self.scen.current_instruction == Instructions.Remove_Vertex:
            circle_item: CircleAnnotation = self.scen.get_last_circle_item()
            offset = ((mapped_pos.x() - self._circle_item_pos.x()) ** 2 + (mapped_pos.y() - self._circle_item_pos.y()) ** 2) ** 0.5
            
            circle_item.set_rect(offset)

        elif self._left_button_pressed and self.scen.current_instruction == Instructions.Split:
            line_item: LineAnnotation = self.scen.get_last_line_item()
            line_item.set_end_point(mapped_pos)

        elif self._left_button_pressed:
            offset = self.__prevMousePos - event.pos()
            self.__prevMousePos = event.pos()

            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + offset.y())
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + offset.x())
        
        else:
            super(AnnotationView, self).mouseMoveEvent(event)
            self._mouse_move = False

    def mouseReleaseEvent(self, event):
        if self._left_button_pressed and not self._mouse_move:
            mapped_pos = self.mapToScene(event.pos())

            if self.scen.current_instruction == Instructions.No_Instruction:
                self.__prevMousePos = event.pos()
            elif self.scen.current_instruction == Instructions.Point:
                self.scen.predict(mapped_pos)
            elif self.scen.current_instruction == Instructions.Merge_Point:
                self.scen.add_merge_points(mapped_pos)
            elif self.scen.current_instruction == Instructions.Red_Point:
                self.scen.add_red_points(mapped_pos)
            elif self.scen.current_instruction == Instructions.Regularisation:
                self.scen.regularisation(mapped_pos)
            elif self.scen.current_instruction == Instructions.Remove:
                self.scen.remove_polygon(mapped_pos)
            elif self.scen.current_instruction == Instructions.Simplify:
                self.scen.simplify_polygon(mapped_pos)
        else:
            if self.scen.current_instruction == Instructions.Remove_Vertex:
                self.scen.remove_vertex_coordinates()
            elif self.scen.current_instruction == Instructions.Split:
                self.scen.split_polygon()
            self._mouse_move = False
            super(AnnotationView, self).mouseReleaseEvent(event)
        
        self._left_button_pressed = False    
        
    @QtCore.pyqtSlot()
    def zoomIn(self):
        self.zoom(AnnotationView.factor)

    @QtCore.pyqtSlot()
    def zoomOut(self):
        self.zoom(1 / AnnotationView.factor)

    def zoom(self, f):
        if self.scene() is not None:
            self.centerOn(self.scene().image_item)
        self.scale(f, f)


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