from enum import Enum

class Instructions(Enum):
    No_Instruction = 0
    Polygon_Instruction = 1
    Point = 2
    Merge_Point = 3
    Remove = 4
    Simplify = 5
    Red_Point = 6
    Regularisation = 7
    Remove_Vertex = 8
    Split = 9

class EventTypes(Enum):
    Press = 0
    Move = 1