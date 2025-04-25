from PyQt5.QtWidgets import  QGraphicsEllipseItem
from PyQt5.QtGui import QColor, QPen

class CircleAnnotation(QGraphicsEllipseItem):
    def __init__(self, pos, parent=None):
        super(CircleAnnotation, self).__init__(parent)
        
        self.center_point = pos
        self.default_size = 4

        color = QColor("red")
        self.set_rect(self.default_size, self.center_point)

        self.setPen(QPen(color, 1))
    
    def set_rect(self, size, pos = None):
        pos = pos if pos is not None else self.center_point
        self.setRect(pos.x() - (size/2), pos.y() - (size/2), size, size)
    
    def get_center(self):
        # Get the bounding rectangle of the ellipse item
        bounding_rect = self.boundingRect()

        # Get center coordinates from the rectangle
        center_x = bounding_rect.center().x()
        center_y = bounding_rect.center().y()

        return (center_x, center_y)