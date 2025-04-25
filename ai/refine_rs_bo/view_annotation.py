from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from enums.refine_rs_bo.instruction_type import Instructions

from .scene_annotation import AnnotationScene
from .circle_annotation import CircleAnnotation

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
        self._prevMousePos = QtCore.QPointF
        self._mouse_move = False
        self._add_new_point = False


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
        if event.button() == Qt.LeftButton:
            mapped_pos = self.mapToScene(event.pos())

            self._prevMousePos = event.pos()
            self._circle_item_pos = mapped_pos
            self._left_button_pressed = True

            if self.scen.current_instruction == Instructions.Point or self.scen.current_instruction == Instructions.Remove_Vertex:
                if not self.scen.is_ready():
                    return
                
                self._add_new_point = True

                circle_item = CircleAnnotation(mapped_pos)

                self.scen.add_points(circle_item, self.scen.current_instruction)
        else:
            super(AnnotationView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        mapped_pos = self.mapToScene(event.pos())
        
        if self._left_button_pressed and self._add_new_point:
            circle_item: CircleAnnotation = self.scen.get_last_point()

            offset = ((mapped_pos.x() - self._circle_item_pos.x()) ** 2 + (mapped_pos.y() - self._circle_item_pos.y()) ** 2) ** 0.5
            circle_item.set_rect(offset)
            
        elif self._left_button_pressed:
            self._mouse_move = True

            offset = self._prevMousePos - event.pos()
            self._prevMousePos = event.pos()

            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() + offset.y()))
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() + offset.x()))
        else:
            super(AnnotationView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._left_button_pressed and self._add_new_point:
            if self.scen.current_instruction == Instructions.Point:
                self.scen.move_vertex_coordinates()
            elif self.scen.current_instruction == Instructions.Remove_Vertex:
                self.scen.remove_vertex_coordinates()
            self._add_new_point = False
        elif self._left_button_pressed and not self._mouse_move:
            mapped_pos = self.mapToScene(event.pos())
            
            if self.scen.current_instruction == Instructions.No_Instruction:
                self._prevMousePos = event.pos()
            elif self.scen.current_instruction == Instructions.Simplify:
                self.scen.simplify_polygon(mapped_pos)
        else:
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