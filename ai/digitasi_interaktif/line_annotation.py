from PyQt5.QtWidgets import  QGraphicsLineItem
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtCore import QLineF, QPointF

class LineAnnotation(QGraphicsLineItem):
    def __init__(self, pos: QPointF, parent=None):
        super(LineAnnotation, self).__init__(parent)
        
        self.start_point = pos
        self.end_point = pos
        self.setLine(QLineF(pos, pos))
        
        color = QColor("red")
        self.setPen(QPen(color, 1))
    
    def set_end_point(self, pos=None):
        self.end_point = pos
        self.setLine(QLineF(self.start_point, pos))
