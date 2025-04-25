from PyQt5 import QtWidgets, QtGui, QtCore

class PolygonAnnotation(QtWidgets.QGraphicsPolygonItem):
    def __init__(self, polygon, color="black", parent=None):
        super(PolygonAnnotation, self).__init__(parent)

        coords = polygon.exterior.coords
        qpoints = [QtCore.QPointF(*coord) for coord in coords]
        polygon = QtGui.QPolygonF(qpoints)

        self.setPolygon(polygon)
        self.setZValue(100)
        self.setPen(QtGui.QPen(QtGui.QColor(color), 2))
        self.setAcceptHoverEvents(True)

        